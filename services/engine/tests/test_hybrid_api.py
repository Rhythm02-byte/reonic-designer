"""H1 policy, simulator metrics in /design, and the demo endpoints. SYNTHETIC data only (tests/policy_synth.py)."""
import json
import math
import time

import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient

from engine import baseline as bl
from engine import demo
from engine.api.main import app, get_holdout, get_store
from engine.design import Store
from engine.models.schemas import HomeInputs
from engine.policy.designer import Designer, load_config
from engine.policy.features import TARGETS, row_from_inputs
from policy_synth import generate

HOME = {"installerId": "synthB", "demandKwh": 6200, "ev": {"has": True, "kmPerYear": 14000}}


@pytest.fixture(scope="module")
def df():
    return generate(1200, seed=1)


@pytest.fixture(scope="module")
def designer(df):
    return Designer.train(df, config={"mode": "hybrid", "pvGate": 0.5}, synthetic=True)


@pytest.fixture()
def client(processed, designer, tmp_path):
    path = tmp_path / "designer.joblib"
    designer.save(path)
    store = Store(processed, model_path=path)  # one instance, like the lru_cached get_store in production
    app.dependency_overrides[get_store] = lambda: store
    yield TestClient(app)
    app.dependency_overrides.clear()


def finite(x) -> bool:
    return x is None or (isinstance(x, (int, float)) and math.isfinite(x))


# -- H1 ---------------------------------------------------------------------------------------------------------
def test_installer_stats_are_stored_in_the_artifact(designer, tmp_path):
    designer.save(tmp_path / "d.joblib")
    d = Designer.load(tmp_path / "d.joblib", apply_config=False)
    assert {"all", "synthA", "synthB"} <= set(d.battery_stats)
    st = d.battery_stats["synthA"]
    assert 0 < st["share"] <= 1 and st["sizes"] and st["p10"] <= st["median"] <= st["p90"]
    assert d.mode == "hybrid" and d.synthetic


def test_h1_battery_is_the_installers_usual_one_and_needs_pv(designer, df):
    out = designer.design_batch(df.head(400))
    st = designer.battery_stats
    for (_, r), (_, row) in zip(out.iterrows(), df.head(400).iterrows()):
        s = st[row.installer_id]
        assert r.battery_kwh == 0 or r.battery_kwh in s["sizes"] or r.battery_kwh < min(s["sizes"])  # R04 may cap, never invents sizes
        existing = bool(row.existing_pv_trusted) and (row.existing_pv_kwp or 0) > 0
        if not (r.pv_kwp > 0 or existing):
            assert r.battery_kwh == 0
    assert (out.battery_kwh > 0).any()
    bat = out.battery_kwh[out.battery_kwh > 0]
    assert bat.nunique() <= 4  # one usual battery per installer, shifted down only by the 2 kWh/kWp cap


def test_h1_heat_pump_is_the_structural_rule_and_wallbox_the_ev_rule(designer, df):
    out = designer.design_batch(df)
    expect = np.array([bl.hp_rule(r) for r in df.to_dict("records")])
    assert np.allclose(out.heat_pump_kw.to_numpy(), expect)
    assert ((out.wallbox_kw > 0) == df.has_ev.to_numpy()).all()


def test_h1_differs_from_learned_and_gate_changes_pv_inclusion(designer, df):
    h, m = designer.design_batch(df), designer.with_config("learned").design_batch(df)
    assert not np.allclose(h.heat_pump_kw, m.heat_pump_kw) or not np.allclose(h.battery_kwh, m.battery_kwh)
    lo, hi = designer.with_config(pv_gate=0.05).design_batch(df), designer.with_config(pv_gate=0.95).design_batch(df)
    assert (lo.pv_kwp > 0).sum() >= (hi.pv_kwp > 0).sum()


def test_h1_locks_win_and_propagate(designer):
    home = HomeInputs(installer_id="synthA", demand_kwh=6000, ev={"has": True})
    d = designer.design(home, locked={"pv_kwp": 0})
    assert d.values["pv_kwp"] == 0 and d.values["battery_kwh"] == 0
    d = designer.design(home, locked={"battery_kwh": 11.0, "heat_pump_kw": 3.0, "wallbox_kw": 0.0})
    assert d.values["battery_kwh"] == 11.0 and d.values["heat_pump_kw"] == 3.0 and d.values["wallbox_kw"] == 0.0
    d = designer.design(home, locked={"pv_kwp": 8.0})
    assert d.values["pv_kwp"] == 8.0 and d.values["battery_kwh"] > 0 and d.values["battery_kwh"] <= 2.0 * 8.0
    assert any(r.code == "BATTERY_INSTALLER_USUAL" for r in d.reasons)


def test_policy_config_file_roundtrip(tmp_path):
    p = tmp_path / "policy.json"
    p.write_text(json.dumps({"mode": "learned", "pvGate": 0.4, "chosen": "M1"}), encoding="utf-8")
    assert load_config(p) == {"mode": "learned", "pvGate": 0.4}
    assert load_config(tmp_path / "missing.json")["mode"] == "composite"


# -- /design with simulator metrics -----------------------------------------------------------------------------
def design(client, **kw):
    r = client.post("/design", json={"inputs": HOME, **kw})
    assert r.status_code == 200, r.text
    return r.json()


def test_design_attaches_finite_metrics_curves_and_physics(client):
    d = design(client)
    assert {"proposal"} <= set(d["metrics"])
    for sid in [d["proposal"]["id"], *[a["id"] for a in d["alternatives"]]]:
        m = d["metrics"][sid]
        assert m["pvYieldKwh"] > 0 and 0 <= m["autarky"] <= 1 and 0 <= m["selfConsumption"] <= 1
        assert all(finite(v) for v in m.values() if not isinstance(v, dict))
    assert d["metrics"]["proposal"]["hourlyTypicalDays"]["summer"]["pvKwh"]
    cur = d["curves"]
    sizes = [p["kwh"] for p in cur["battery"]]
    assert 0 in sizes and sizes == sorted(sizes) and len(sizes) >= 3
    assert {"kwh", "autarky", "selfConsumption", "savingsEurYear", "paybackYears", "npv20", "fullCyclesPerYear"} <= set(cur["battery"][0])
    assert len(cur["pv"]) >= 3 and all(finite(v) for p in cur["pv"] for v in p.values())
    kwps = [p["kwp"] for p in cur["pv"]]
    assert min(kwps) < d["proposal"]["pv"]["kwp"] < max(kwps) and min(kwps) >= 0.55 * d["proposal"]["pv"]["kwp"]
    assert set(d["physics"]) == {"economicKwh", "maxAutarkyKwh", "nightLoadKwh"} and d["physics"]["nightLoadKwh"] > 0


def test_alternatives_are_battery_variants(client):
    d = design(client)
    labels = {a["label"] for a in d["alternatives"]}
    assert labels <= {"Without battery", "Economic battery", "Max independence"}
    base = d["proposal"]["battery"]["kwh"] if d["proposal"]["battery"] else 0
    for a in d["alternatives"]:
        assert (a["battery"]["kwh"] if a["battery"] else 0) != base
        assert a["pv"] == d["proposal"]["pv"]
    if d["proposal"]["battery"]:
        assert "Without battery" in labels


def test_oversized_locked_battery_fires_r06(client):
    cur = {"pv": {"modules": 11, "moduleWp": 450, "kwp": 4.95}, "battery": {"kwh": 15}}
    d = design(client, locks=["pv", "battery"], current=cur)
    r06 = [f for f in d["flags"] if f["code"] == "R06"]
    assert r06 and r06[0]["severity"] == "warn" and r06[0]["component"] == "battery"
    assert "pp autarky" in r06[0]["message"] and "EUR" in r06[0]["message"]
    assert d["alternatives"] == []  # battery locked: no battery variants offered


def test_economic_battery_does_not_fire_r06(client):
    d = design(client)
    eco = d["physics"]["economicKwh"]
    cur = {"pv": d["proposal"]["pv"], "battery": {"kwh": eco}} if eco > 0 else {"pv": d["proposal"]["pv"]}
    d2 = design(client, locks=["pv", "battery"], current=cur)
    assert not any(f["code"] == "R06" for f in d2["flags"])


def test_design_latency_on_warm_cache(client):
    design(client)  # warm: model, simulator resources, sim cache
    t = []
    for _ in range(5):
        s = time.perf_counter()
        design(client)
        t.append((time.perf_counter() - s) * 1000)
    assert float(np.percentile(t, 95)) < 400, t


def test_design_latency_cold_inputs_under_budget(client):
    design(client)
    t = []
    for k in range(6):  # new demand each time: nothing cached
        body = {"inputs": {**HOME, "demandKwh": 4000 + 130 * k}}
        s = time.perf_counter()
        assert client.post("/design", json=body).status_code == 200
        t.append((time.perf_counter() - s) * 1000)
    assert float(np.percentile(t, 95)) < 1000, t  # generous CI bound; the real p95 is reported by the build script


# -- /simulate, /validate ---------------------------------------------------------------------------------------
def test_simulate_endpoint_is_fast_path_without_policy(client):
    body = {"inputs": HOME, "system": {"pv": {"modules": 22, "moduleWp": 450, "kwp": 9.9}, "battery": {"kwh": 10}}}
    m = client.post("/simulate", json=body).json()
    assert m["pvYieldKwh"] > 0 and 0 < m["autarky"] < 1 and m["npv20"] is not None
    none = client.post("/simulate", json={"inputs": HOME, "system": {}}).json()
    assert none["pvYieldKwh"] == 0 and m["autarky"] > none["autarky"]


def test_simulate_works_without_trained_model(processed):
    app.dependency_overrides[get_store] = lambda: Store(processed)
    try:
        r = TestClient(app).post("/simulate", json={"inputs": {"installerId": "x"}, "system": {"pv": {"modules": 10, "moduleWp": 450, "kwp": 4.5}}})
    finally:
        app.dependency_overrides.clear()
    assert r.status_code == 200 and r.json()["pvYieldKwh"] > 0


def test_validate_includes_metrics(client):
    body = {"inputs": {"installerId": "synthA", "demandKwh": 3000},
            "system": {"pv": {"modules": 20, "moduleWp": 450, "kwp": 9.0}, "battery": {"kwh": 17}}}
    v = client.post("/validate", json=body).json()
    assert v["metrics"]["pvYieldKwh"] > 0 and "R05" in [f["code"] for f in v["flags"]]


# -- /meta ------------------------------------------------------------------------------------------------------
def test_meta_lists_fields_targets_installers(client):
    m = client.get("/meta").json()
    assert {f["kind"] for f in m["fields"]} == {"number", "bool", "choice"}
    heating = next(f for f in m["fields"] if f["name"] == "heating.type")
    assert "Gas" in heating["choices"] and heating["label"]
    assert [t["name"] for t in m["targets"]] == ["pvKwp", "batteryKwh", "heatPumpKw", "wallboxKw"]
    assert all(t["unit"] and t["catalog"] == sorted(t["catalog"]) and t["catalog"] for t in m["targets"])
    assert m["installers"] == ["synthA", "synthB"] and m["synthetic"] is True and m["engineVersion"] == "policy-1"


# -- /eval/summary ----------------------------------------------------------------------------------------------
def _policy(w):
    return {"wholeDesignWithinTolerance": w, "pv_kwp": {"withinTolerance": 0.5}, "battery_kwh": {"withinTolerance": 0.6},
            "heat_pump_kw": {"withinTolerance": 0.9}, "wallbox_kw": {"withinTolerance": 0.95}}


def test_eval_summary_404_without_results_and_compact_view_with(tmp_path, monkeypatch):
    c = TestClient(app)
    monkeypatch.setenv("ENGINE_EVAL_RESULTS", str(tmp_path / "nope.json"))
    assert c.get("/eval/summary").status_code == 404
    base = {m: {"overall": {"expertMatchPrimary": 60.0 + i, "policy": _policy(0.1 * i)}} for i, m in enumerate(["B0", "B0c", "B1", "M1", "H1"])}
    f = tmp_path / "latest.json"
    f.write_text(json.dumps({"generatedAt": "2026-11-07T10:00:00+00:00", "splits": {"temporal": {"nTest": 99, "baselines": base}},
                             "selection": {"chosen": {"model": "H1", "pvGate": 0.4}, "validation": {}}}), encoding="utf-8")
    monkeypatch.setenv("ENGINE_EVAL_RESULTS", str(f))
    s = c.get("/eval/summary").json()
    assert s["split"] == "temporal" and s["nTest"] == 99 and s["chosen"] == "H1" and s["generatedAt"].startswith("2026")
    assert {"B0", "B1", "H1"} <= set(s["models"]) and set(s["models"]["H1"]) == {"ems", "wholeDesign", "pv", "battery", "heatPump", "wallbox"}
    assert s["models"]["H1"]["ems"] == 64.0 and s["selection"]["chosen"]["pvGate"] == 0.4
    f.write_text("not json", encoding="utf-8")
    assert c.get("/eval/summary").status_code == 404


# -- /holdout ---------------------------------------------------------------------------------------------------
@pytest.fixture()
def holdout_client(df, designer, monkeypatch):
    D = df.copy()
    D["when"] = pd.Timestamp("2025-06-01") + pd.to_timedelta(np.arange(len(D)) * 0.4, unit="D")  # last ~25% fall in 2026
    svc = demo.HoldoutService(D, designer=designer, synthetic=True)
    app.dependency_overrides[get_holdout] = lambda: svc
    monkeypatch.delenv("DEMO_HOLDOUT", raising=False)
    yield TestClient(app), D
    app.dependency_overrides.clear()


def test_holdout_rows_are_diverse_test_homes(holdout_client):
    c, D = holdout_client
    rows = c.get("/holdout?n=12").json()["rows"]
    assert len(rows) == 12 and len({r["projectId"] for r in rows}) == 12
    test_ids = set(D[D["when"] > demo.HOLDOUT_CUTOFF].project_id)
    assert all(r["projectId"] in test_ids for r in rows)
    r0 = rows[0]
    assert {"demandKwh", "ev", "heating", "installerId"} <= set(r0["inputs"])
    assert set(r0["expert"]) == set(r0["ours"]) == {"pvKwp", "batteryKwh", "heatPumpKw", "wallboxKw"}
    assert any((r["expert"]["batteryKwh"] or 0) > 0 for r in rows) and any(r["expert"]["batteryKwh"] == 0 for r in rows)
    assert any(r["inputs"]["ev"]["has"] for r in rows) and any((r["expert"]["heatPumpKw"] or 0) > 0 for r in rows)
    assert any(r["expert"]["pvKwp"] == 0 for r in rows)


def test_holdout_ours_matches_design_endpoint_inputs(holdout_client, designer):
    c, _ = holdout_client
    r = c.get("/holdout?n=3").json()["rows"][0]
    res = designer.design(HomeInputs.model_validate(r["inputs"]))
    assert abs(r["ours"]["batteryKwh"] - res.values["battery_kwh"]) < 0.01
    assert abs(r["ours"]["pvKwp"] - res.values["pv_kwp"]) <= 0.25  # module-snapped


def test_holdout_is_gated_and_404_without_data(holdout_client, monkeypatch):
    c, _ = holdout_client
    monkeypatch.setenv("DEMO_HOLDOUT", "0")
    assert c.get("/holdout").status_code == 403
    monkeypatch.setenv("DEMO_HOLDOUT", "1")
    app.dependency_overrides[get_holdout] = lambda: None
    assert c.get("/holdout").status_code == 404


def test_inputs_from_row_roundtrips_through_the_feature_row():
    row = {"installer_id": "x", "demand_kwh": 5200.0, "price_eur_kwh": 0.33, "price_escalation": 0.03, "load_family": "family",
           "has_ev": True, "ev_km": 15000.0, "has_existing_pv": True, "existing_pv_kwp": 6.0, "existing_pv_trusted": True,
           "heating_type": "Gas", "heat_demand_kwh": 17000.0}
    back = row_from_inputs(demo.inputs_from_row(row))
    for k in ("installer_id", "demand_kwh", "load_family", "has_ev", "ev_km", "existing_pv_kwp", "existing_pv_trusted", "heating_type", "heat_demand_kwh"):
        assert back[k] == row[k], k


def test_cors_allows_the_web_dev_origin():
    r = TestClient(app).options("/design", headers={"Origin": "http://localhost:3000", "Access-Control-Request-Method": "POST"})
    assert r.headers.get("access-control-allow-origin") == "http://localhost:3000"
