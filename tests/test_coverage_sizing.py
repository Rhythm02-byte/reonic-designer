import numpy as np

from reonic import evaluate
from reonic.engine import LEGACY, Designer
from reonic.model import SIZE_TOLERANCE, coverage_size
from reonic import synth


def test_tolerances_match_the_metric():
    for t, tol in SIZE_TOLERANCE.items():
        assert tol == evaluate.TOLERANCE[t]


def test_picks_the_size_that_fits_most_plausible_expert_sizes():
    # four plausible sizes cluster near 6, one outlier at 12: the mean (7.2) fits only the outlier-free cluster poorly
    samples = np.array([[5.8, 6.0, 6.0, 6.2, 12.0]])
    c = coverage_size(samples, 0.20)[0]
    assert 5.8 <= c <= 6.2


def test_result_is_one_of_the_samples_and_non_negative_and_handles_crossing():
    s = np.array([[3.0, 1.0, 2.0, 2.5, 0.5], [0.0, 0.0, 0.0, 0.0, 0.0]])
    c = coverage_size(s, 0.25)
    assert c[0] in s[0] and c[1] == 0.0


def test_coverage_designer_trains_and_keeps_rules():
    df = synth.generate(400, seed=2)
    d = Designer.train(df, sizing="coverage")
    out = d.design_batch(df.head(30))
    assert np.isfinite(out[["pv_kwp", "battery_kwh"]].to_numpy()).all()
    assert (out["battery_kwh"] <= 2.0 * out["pv_kwp"] + 1e-9).all()


def test_blend_and_wider_battery_catalogue_keep_the_rules():
    from reonic.schema import HomeInputs
    df = synth.generate(500, seed=3)
    narrow = Designer.train(df, **LEGACY)
    wide = Designer.train(df, sizing="coverage", blend=0.5, battery_catalog_top=40)
    assert len(wide.catalog["battery_kwh"]) >= len(narrow.catalog["battery_kwh"])
    out = wide.design_batch(df.head(40))
    assert np.isfinite(out.to_numpy()).all() and (out["pv_kwp"] <= 30.0).all()
    existing = df.head(40)["existing_pv_kwp"].fillna(0).clip(lower=0)  # R04 counts PV the home already has
    assert (out["battery_kwh"] <= 2.0 * (out["pv_kwp"] + existing) + 1e-9).all()
    d = wide.design(HomeInputs(annual_consumption_kwh=5000, has_ev=True), {"pv_kwp": 8.0})
    assert d.pv_kwp == 8.0 and d.wallbox_kw > 0


def test_blend_pulls_size_toward_similar_homes():
    df = synth.generate(500, seed=4)
    a = Designer.train(df).design_batch(df.head(60))
    b = Designer.train(df, blend=1.0).design_batch(df.head(60))
    assert not np.allclose(a["pv_kwp"], b["pv_kwp"])


def test_small_training_set_without_a_heat_pump_still_trains():
    df = synth.generate(300, seed=5)
    df["heat_pump_kw"] = 0.0  # a column that only ever holds one value breaks the gradient-boosting binning
    small = df.head(60)
    for sizing in ("mean", "coverage"):
        out = Designer.train(small, sizing=sizing).design_batch(df.tail(20))
        assert np.isfinite(out.to_numpy()).all()
