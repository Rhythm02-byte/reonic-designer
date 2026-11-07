import numpy as np

from reonic import evaluate
from reonic.engine import Designer
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
