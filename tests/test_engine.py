import pandas as pd
import pytest

from reonic import evaluate, synth
from reonic.engine import Designer
from reonic.schema import TARGETS, HomeInputs


@pytest.fixture(scope="module")
def df():
    return synth.generate(1200, seed=1)


@pytest.fixture(scope="module")
def designer(df):
    return Designer.train(df)


def test_design_is_complete_and_explained(designer):
    d = designer.design(HomeInputs(annual_consumption_kwh=5000, electricity_price_eur_kwh=0.35, heating_type="oil", heating_demand_kwh=18000))
    assert all(getattr(d, t) >= 0 for t in TARGETS)
    assert d.explanation and set(d.probability) == set(TARGETS)


def test_missing_inputs_still_produce_a_design(designer):
    d = designer.design(HomeInputs())
    assert any("unknown" in line for line in d.explanation)


def test_planner_lock_is_respected_and_flows_downstream(designer):
    home = HomeInputs(annual_consumption_kwh=6000, existing_pv_kwp=0)
    d = designer.design(home, locked={"pv_kwp": 0})
    assert d.pv_kwp == 0 and d.battery_kwh == 0  # R02 applies downstream of the override


def test_ev_increases_pv_on_average(df, designer):
    with_ev, without = df.copy(), df.copy()
    with_ev["has_ev"], without["has_ev"] = True, False
    assert designer.design_batch(with_ev)["pv_kwp"].mean() > designer.design_batch(without)["pv_kwp"].mean()


def test_evaluation_report_shape(df, tmp_path):
    r = evaluate.run(df, out_dir=tmp_path)
    assert {"n_train", "n_test", "split", "model", "baseline", "typical"} <= set(r)
    assert 0 <= r["model"]["whole_design_within_tolerance"] <= 1
    assert (tmp_path / "test_predictions.csv").exists()


def test_installer_holdout_and_unknown_pv_sizes(df, tmp_path):
    assert df["pv_kwp"].isna().any()  # synthetic data mimics offered-but-unknown PV sizes
    r = evaluate.run(df, out_dir=tmp_path, group_col="installer_id")
    assert r["split"] == "installer_id" and r["n_train"] > 0 and r["n_test"] > 0


def test_wallbox_follows_the_has_ev_rule_exactly(df, designer):
    """The wallbox is deterministic: a wallbox if and only if the home has an EV."""
    out = designer.design_batch(df)
    has_ev = df["has_ev"].astype(bool).to_numpy()
    assert ((out["wallbox_kw"].to_numpy() > 0) == has_ev).all()
    assert set(out.loc[has_ev, "wallbox_kw"].unique()) <= {11.0, 22.0}


def test_wallbox_rule_ignores_everything_but_the_ev_flag(designer):
    base = HomeInputs(annual_consumption_kwh=9000, existing_pv_kwp=10, heating_type="gas", has_ev=True)
    assert designer.design(base).wallbox_kw > 0
    assert designer.design(HomeInputs(annual_consumption_kwh=9000, has_ev=False)).wallbox_kw == 0


def test_unknown_ev_flag_gives_no_wallbox(designer):
    assert designer.design(HomeInputs(annual_consumption_kwh=5000, has_ev=None)).wallbox_kw == 0


def test_include_precision_recall_f1_f2():
    """Truth: wallbox for 2 of 4 homes. Prediction: wallbox for 1 of those 2 and none elsewhere.
    precision = 1/1 = 1.0, recall = 1/2 = 0.5, F1 = 2/3, F2 = 5*P*R / (4*P + R) = 2.5/4.5."""
    zeros = [0.0] * 4
    truth = pd.DataFrame({"pv_kwp": zeros, "battery_kwh": zeros, "heat_pump_kw": zeros,
                          "wallbox_kw": [11.0, 11.0, 0.0, 0.0]})
    pred = truth.assign(wallbox_kw=[11.0, 0.0, 0.0, 0.0])
    m = evaluate.metrics(pred, truth)["wallbox_kw"]
    assert m["include_precision"] == pytest.approx(1.0)
    assert m["include_recall"] == pytest.approx(0.5)
    assert m["include_f1"] == pytest.approx(2 / 3)
    assert m["include_f2"] == pytest.approx(2.5 / 4.5)


def test_typical_design_ignores_the_home_and_uses_training_medians():
    from reonic.baseline import typical_design

    train = pd.DataFrame({"pv_kwp": [6.0, 8.0, 10.0, 0.0], "battery_kwh": [5.0, 5.0, 10.0, 0.0],
                          "heat_pump_kw": [0.0, 0.0, 0.0, 0.0], "wallbox_kw": [0.0] * 4})
    test = pd.DataFrame({"has_ev": [True, False, None]}, index=[10, 11, 12])
    out = typical_design(train, test)
    assert (out["pv_kwp"] == 8.0).all() and (out["battery_kwh"] == 5.0).all()  # medians of the included homes
    assert (out["heat_pump_kw"] == 0).all()  # most homes got none
    assert list(out["wallbox_kw"]) == [11.0, 0.0, 0.0]  # the EV rule, unknown EV means none
