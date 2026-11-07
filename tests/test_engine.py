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
    assert {"n_train", "n_test", "split", "model", "baseline"} <= set(r)
    assert 0 <= r["model"]["whole_design_within_tolerance"] <= 1
    assert (tmp_path / "test_predictions.csv").exists()


def test_installer_holdout_and_unknown_pv_sizes(df, tmp_path):
    assert df["pv_kwp"].isna().any()  # synthetic data mimics offered-but-unknown PV sizes
    r = evaluate.run(df, out_dir=tmp_path, group_col="installer_id")
    assert r["split"] == "installer_id" and r["n_train"] > 0 and r["n_test"] > 0
