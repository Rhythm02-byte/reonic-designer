"""Policy tests on SYNTHETIC data only (tests/policy_synth.py)."""
import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient

from engine.api.main import app, get_store
from engine.design import Store
from engine.models.schemas import HomeInputs
from engine.policy import rules
from engine.policy.designer import Designer
from engine.policy.features import TARGETS, features, mask_inputs, row_from_inputs, training_frame
from policy_synth import generate

CAT = {"battery_kwh": [5.0, 10.0, 15.0], "heat_pump_kw": [8.0, 12.0], "pv_kwp": [], "wallbox_kw": [11.0, 22.0]}
NO_PV = {"heating_type": "Unknown", "existing_pv_kwp": 0.0}


@pytest.fixture(scope="module")
def df():
    return generate(1200, seed=1)


@pytest.fixture(scope="module")
def designer(df):
    return Designer.train(df)


def ids(hits):
    return [h.id for h in hits]


# -- rules (ported) ---------------------------------------------------------------------------------------------
def test_r01_existing_heat_pump():
    v, applied, _ = rules.apply_one("heat_pump_kw", 10, {}, {"heating_type": "Heatpump"}, CAT)
    assert v == 0 and ids(applied) == ["R01"]


def test_r02_no_battery_without_pv():
    v, applied, _ = rules.apply_one("battery_kwh", 10, {"pv_kwp": 0}, NO_PV, CAT)
    assert v == 0 and ids(applied) == ["R02"]


def test_r02_battery_allowed_for_existing_pv():
    v, applied, _ = rules.apply_one("battery_kwh", 10, {"pv_kwp": 0}, {"existing_pv_kwp": 8}, CAT)
    assert v == 10.0 and applied == []


def test_r03_residential_pv_cap():
    v, applied, _ = rules.apply_one("pv_kwp", 45, {}, NO_PV, CAT)
    assert v == rules.PV_MAX_KWP and ids(applied) == ["R03"]


def test_r04_hard_cap_and_snap():
    v, applied, _ = rules.apply_one("battery_kwh", 30, {"pv_kwp": 6}, NO_PV, CAT)
    assert v == 10.0 and "R04" in ids(applied)  # capped to 12, snapped to the largest catalog size <= 12


def test_wallbox_snaps_to_catalog():
    assert rules.apply_one("wallbox_kw", 14, {}, NO_PV, CAT)[0] == 11.0


def test_common_sizes_picks_frequent_values():
    assert rules.common_sizes([10, 10, 10, 7.5, 7.5, 5, 0], top=2) == [7.5, 10.0]


def test_unknown_size_stays_nan():
    v, applied, flags = rules.apply_one("pv_kwp", float("nan"), {}, NO_PV, CAT)
    assert np.isnan(v) and not applied and not flags


def test_r05_amber_flag_fires_but_never_changes_value():
    # 6 kWp PV, 7 kWh nominal = 6.3 usable = 1.05 kWh/kWp: fine. 10 kWh = 9 usable = 1.5: boundary, no flag.
    assert not any(h.id == "R05" for h in rules.apply_one("battery_kwh", 7, {"pv_kwp": 6}, NO_PV, CAT)[2])
    v, applied, flags = rules.apply_one("battery_kwh", 10.0, {"pv_kwp": 5}, NO_PV, {**CAT, "battery_kwh": [10.0]})
    assert v == 10.0 and "R05" in ids(flags) and all(h.severity == "amber" for h in flags if h.id == "R05")


def test_locked_value_is_kept_but_flagged_red():
    v, applied, flags = rules.apply_one("battery_kwh", 10, {"pv_kwp": 0}, NO_PV, CAT, locked=True)
    assert v == 10 and applied == [] and flags[0].id == "R02" and flags[0].severity == "red"
    v, _, flags = rules.apply_one("battery_kwh", 30, {"pv_kwp": 6}, NO_PV, CAT, locked=True)
    assert v == 30 and "R04" in ids(flags) and "R05" in ids(flags)


def test_audit_checks_a_whole_design():
    hits = rules.audit({"pv_kwp": 6, "battery_kwh": 11.5, "heat_pump_kw": 8, "wallbox_kw": 11}, {"heating_type": "Heatpump"}, CAT)
    assert {"R01", "R05"} <= set(ids(hits)) and "R04" not in ids(hits)


# -- engine -----------------------------------------------------------------------------------------------------
def test_design_is_complete_and_explained(designer):
    d = designer.design(HomeInputs(installer_id="synthA", demand_kwh=5000, heating={"type": "Oil", "heatDemandKwh": 18000}))
    assert all(d.values[t] >= 0 for t in TARGETS) and set(d.probability) == set(TARGETS)
    codes = [r.code for r in d.reasons]
    assert len([c for c in codes if c.split("_")[0] in ("PV", "BATTERY", "HEAT", "WALLBOX")]) == 4
    ev = d.reasons[0].evidence
    assert {"probability", "similar_share", "similar_median", "n_similar"} <= set(ev) and d.reasons[0].text


def test_intervals_are_ordered(designer, df):
    sizes, extra = designer.design_batch_full(df.head(200))
    for t in TARGETS:
        assert (extra[f"lo_{t}"] <= extra[f"hi_{t}"] + 1e-9).all()


def test_quantile_interval_covers_most_experts_on_training_data(designer, df):
    _, extra = designer.design_batch_full(df)
    y, ok = df["pv_kwp"].to_numpy(), df["pv_kwp"].gt(0).to_numpy()
    cov = ((y >= extra["lo_pv_kwp"]) & (y <= extra["hi_pv_kwp"]))[ok].mean()
    assert 0.6 < cov <= 1.0


@pytest.mark.parametrize("comp", TARGETS)
def test_locked_component_never_changes(designer, comp):
    for v in (0.0, 3.3, 27.0):
        d = designer.design(HomeInputs(installer_id="synthA", demand_kwh=9000, ev={"has": True}), locked={comp: v})
        assert d.values[comp] == v


def test_lock_flows_downstream_and_conflict_is_flagged(designer):
    home = HomeInputs(installer_id="synthA", demand_kwh=6000)
    d = designer.design(home, locked={"pv_kwp": 0})
    assert d.values["pv_kwp"] == 0 and d.values["battery_kwh"] == 0  # R02 applies downstream of the override
    d = designer.design(home, locked={"pv_kwp": 0, "battery_kwh": 10})
    assert d.values["battery_kwh"] == 10 and any(f.code == "R02" and f.severity == "error" for f in d.flags)


def test_locked_oversized_battery_fires_r04_and_r05(designer):
    d = designer.design(HomeInputs(installer_id="synthA"), locked={"pv_kwp": 5.0, "battery_kwh": 14.0})
    assert d.values["battery_kwh"] == 14.0
    codes = {f.code for f in d.flags}
    assert {"R04", "R05"} <= codes


def test_adding_an_ev_never_removes_the_wallbox(designer, df):
    with_ev, without = df.copy(), df.copy()
    with_ev["has_ev"], without["has_ev"] = True, False
    a, b = designer.design_batch(with_ev)["wallbox_kw"], designer.design_batch(without)["wallbox_kw"]
    assert ((a > 0) | (b == 0)).all() and (a > 0).all() and (b == 0).all()


def test_unknown_ev_flag_gives_no_wallbox(designer):
    row = row_from_inputs(HomeInputs(installer_id="synthA"))
    row["has_ev"] = np.nan
    assert designer.design_row(row).values["wallbox_kw"] == 0


def test_existing_heat_pump_means_no_new_one(designer, df):
    x = df.copy()
    x["heating_type"] = "Heatpump"
    assert (designer.design_batch(x)["heat_pump_kw"] == 0).all()


def test_ev_increases_pv_on_average(designer, df):
    with_ev, without = df.copy(), df.copy()
    with_ev["has_ev"], without["has_ev"] = True, False
    assert designer.design_batch(with_ev)["pv_kwp"].mean() > designer.design_batch(without)["pv_kwp"].mean()


def test_missing_inputs_still_produce_a_design(designer, df):
    out = designer.design_batch(mask_inputs(df.head(100), 0.6))
    assert len(out) == 100 and out.notna().all().all()


def test_validate_flags_unusual_design(designer):
    v = designer.validate(HomeInputs(installer_id="synthA", demand_kwh=3000), {"pv_kwp": 9, "battery_kwh": 17, "heat_pump_kw": 0, "wallbox_kw": 0})
    assert any(f.code == "R05" for f in v.flags) and v.n_similar > 0 and set(v.percentiles) == {"pv", "battery", "heatPump", "wallbox"}


def test_unknown_stays_nan_in_features():
    X = features(pd.DataFrame([{"installer_id": "x", "demand_kwh": np.nan, "has_ev": None, "heating_type": None}]), ("a",))
    assert np.isnan(X["demand_kwh"].iat[0]) and np.isnan(X["demand_is_default"].iat[0]) and np.isnan(X["has_ev"].iat[0])
    assert np.isnan(X["heating_Gas"].iat[0]) and X["installer_a"].iat[0] == 0


def test_features_use_trusted_existing_pv_only():
    base = {"installer_id": "x", "has_existing_pv": True, "existing_pv_kwp": 8.0}
    f = lambda trusted: features(pd.DataFrame([{**base, "existing_pv_trusted": trusted}]))["existing_pv_kwp"].iat[0]
    assert f(True) == 8.0 and np.isnan(f(False))
    assert features(pd.DataFrame([{"installer_id": "x", "has_existing_pv": False}]))["existing_pv_kwp"].iat[0] == 0


def test_training_frame_from_etl_tables(processed):
    P, O = pd.read_parquet(processed / "projects.parquet"), pd.read_parquet(processed / "options.parquet")
    t = training_frame(P, O)
    assert len(t) == int(P.has_parts.sum()) and set(TARGETS) <= set(t.columns)
    assert t.set_index("project_id").loc["C", "heat_pump_kw"] > 0 and t.set_index("project_id").loc["B", "wallbox_kw"] == 0


# -- API --------------------------------------------------------------------------------------------------------
@pytest.fixture()
def client(processed, designer, tmp_path):
    path = tmp_path / "designer.joblib"
    designer.save(path)
    app.dependency_overrides[get_store] = lambda: Store(processed, model_path=path)
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_api_serves_policy_when_model_exists(client):
    assert client.get("/health").json()["engineVersion"] == "policy-1"
    d = client.post("/design", json={"inputs": {"installerId": "synthA", "demandKwh": 6000, "ev": {"has": True}}}).json()
    assert d["engineVersion"] == "policy-1" and d["proposal"]["wallbox"]["kw"] > 0
    assert {"p10", "p50", "p90", "probIncluded"} <= set(d["confidence"]["pv"])
    assert all("text" in r for r in d["reasons"])


def test_api_locks_map_to_locked_components(client):
    cur = {"pv": {"modules": 40, "moduleWp": 450, "kwp": 18.0}}
    d = client.post("/design", json={"inputs": {"installerId": "synthA"}, "locks": ["pv", "battery"], "current": cur}).json()
    assert d["proposal"]["pv"]["kwp"] == 18.0 and d["proposal"]["battery"] is None and d["proposal"]["locks"] == ["pv", "battery"]


def test_api_validate_flags_r05_and_percentiles(client):
    body = {"inputs": {"installerId": "synthA", "demandKwh": 3000},
            "system": {"pv": {"modules": 20, "moduleWp": 450, "kwp": 9.0}, "battery": {"kwh": 17}}}
    v = client.post("/validate", json=body).json()
    assert "R05" in [f["code"] for f in v["flags"]] and v["nSimilar"] > 0 and "battery" in v["percentiles"]


def test_validate_without_model_checks_rules_only(processed):
    app.dependency_overrides[get_store] = lambda: Store(processed)
    try:
        v = TestClient(app).post("/validate", json={"inputs": {"installerId": "inst1", "heating": {"type": "Heatpump"}},
                                                    "system": {"heatPump": {"kw": 8}}}).json()
    finally:
        app.dependency_overrides.clear()
    assert [f["code"] for f in v["flags"]] == ["R01"] and v["flags"][0]["severity"] == "error"


def test_pv_target_is_nan_when_offered_with_unknown_size():
    P = pd.DataFrame({"project_id": ["a", "b", "c"], "installer_id": "x", "has_parts": True, "offer_at": pd.Timestamp("2025-01-01"),
                      "request_at": pd.NaT, "signed_at": pd.NaT})
    O = pd.DataFrame({"project_id": ["a", "b", "c"], "is_primary": True, "kwp": [8.0, 0.0, 0.0], "has_pv": [True, False, False],
                      "has_solar_tech": [True, True, False], "battery_kwh": 0.0, "has_battery": False, "hp_kw": 0.0,
                      "has_heatpump": False, "wallbox_kw": np.nan, "has_wallbox": False})
    t = training_frame(P, O).set_index("project_id")
    assert t.loc["a", "pv_kwp"] == 8.0 and np.isnan(t.loc["b", "pv_kwp"]) and t.loc["c", "pv_kwp"] == 0.0
