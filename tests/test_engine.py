import pytest

from reonic import evaluate, synth
from reonic.engine import Designer
from reonic.schema import TARGETS, HomeInputs


@pytest.fixture(scope="module")
def df():
    return synth.generate(800, seed=1)


@pytest.fixture(scope="module")
def designer(df):
    return Designer.train(df)


def test_design_is_complete_and_explained(designer):
    d = designer.design(HomeInputs(annual_consumption_kwh=5000, household_size=4, heating_type="oil"))
    assert all(getattr(d, t) >= 0 for t in TARGETS)
    assert d.explanation and set(d.probability) == set(TARGETS)


def test_missing_inputs_still_produce_a_design(designer):
    d = designer.design(HomeInputs())
    assert any("unknown" in line for line in d.explanation)


def test_planner_lock_is_respected_and_flows_downstream(designer):
    home = HomeInputs(annual_consumption_kwh=6000, household_size=4, heating_type="gas")
    d = designer.design(home, locked={"pv_kwp": 0})
    assert d.pv_kwp == 0 and d.battery_kwh == 0  # R02 applies downstream of the override


def test_ev_increases_pv_on_average(df, designer):
    with_ev, without = df.copy(), df.copy()
    with_ev["has_ev"], without["has_ev"] = True, False
    assert designer.design_batch(with_ev)["pv_kwp"].mean() > designer.design_batch(without)["pv_kwp"].mean()


def test_evaluation_report_shape(df, tmp_path):
    r = evaluate.run(df, out_dir=tmp_path)
    assert set(r) == {"n_train", "n_test", "model", "baseline"}
    assert 0 <= r["model"]["whole_design_within_tolerance"] <= 1
    assert (tmp_path / "test_predictions.csv").exists()
