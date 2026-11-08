"""Guardrails for the research tournament (synthetic data only): no future labels in habit / repeat-customer features,
no 2026 rows in a research split, and the harness's row-level metric equals metrics.policy_metrics."""
import importlib.util
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
from metrics import policy_metrics  # noqa: E402
from research.candidates.habit import habit_features  # noqa: E402
from research.candidates.repeat import earlier_design  # noqa: E402
from research.lib import TARGETS, row_ok  # noqa: E402

spec = importlib.util.spec_from_file_location("research_harness", HERE / "research.py")
harness = importlib.util.module_from_spec(spec)
spec.loader.exec_module(harness)


def frame(n=200, seed=0, start="2024-07-01"):
    rng = np.random.default_rng(seed)
    when = pd.Timestamp(start) + pd.to_timedelta(np.sort(rng.integers(0, 500, n)), unit="D")
    return pd.DataFrame({
        "project_id": [f"p{i}" for i in range(n)], "installer_id": rng.choice(["a", "b"], n),
        "customer_id": rng.choice([f"c{i}" for i in range(n // 3)], n), "when": when,
        "pv_kwp": rng.choice([0.0, 6.3, 8.1, 9.9, 12.2], n), "battery_kwh": rng.choice([0.0, 5.0, 7.7, 10.0], n),
        "heat_pump_kw": rng.choice([0.0, 9.0], n, p=[0.9, 0.1]), "wallbox_kw": rng.choice([0.0, 11.0], n)})


def scramble_after(df, t0, seed=1):
    """Same rows, every label of an offer created after t0 replaced by noise."""
    out = df.copy()
    late = out["when"] > t0
    rng = np.random.default_rng(seed)
    for t in TARGETS:
        out.loc[late, t] = rng.uniform(0, 30, late.sum())
    return out


@pytest.mark.parametrize("window", [30, 90, None])
def test_habit_features_never_see_later_or_own_labels(window):
    df = frame()
    t0 = df["when"].iloc[len(df) // 2]
    early = df["when"] <= t0
    a = habit_features(df, window)(df)
    b = habit_features(scramble_after(df, t0), window)(df)
    pd.testing.assert_frame_equal(a[early], b[early])          # future rows changed, earlier features did not
    own = df.copy()
    own.loc[own.index[10], list(TARGETS)] = 99.0              # a row's own label never feeds its own features
    pd.testing.assert_frame_equal(habit_features(own, window)(df).iloc[[10]], a.iloc[[10]])
    assert (a["hab_n"] > 0).any() and (a.loc[df.index[0], "hab_n"] == 0)


def test_habit_features_for_unseen_rows_use_only_earlier_history():
    hist, test = frame(seed=2), frame(n=40, seed=3, start="2024-09-01")
    t0 = test["when"].min()
    a = habit_features(hist, 90)(test.iloc[[0]])
    b = habit_features(scramble_after(hist, t0 - pd.Timedelta(seconds=1)), 90)(test.iloc[[0]])
    pd.testing.assert_frame_equal(a, b)


def test_repeat_customer_uses_only_strictly_earlier_offers():
    df = frame()
    t0 = df["when"].iloc[len(df) // 2]
    early = df["when"] <= t0
    a = earlier_design(df)(df)
    b = earlier_design(scramble_after(df, t0))(df)
    pd.testing.assert_frame_equal(a[early], b[early])
    assert a["rep_flag"].sum() > 0
    first = df.sort_values("when").groupby("customer_id").head(1).index   # a customer's first offer has no history
    assert (a.loc[first, "rep_flag"] == 0).all()


def test_research_splits_refuse_2026_rows():
    df = frame(n=50)
    df["when"] = pd.Timestamp("2025-06-01")
    late = pd.concat([df, df.iloc[[0]].assign(when=pd.Timestamp("2026-01-05"))], ignore_index=True)
    assert harness.pre_cutoff(late)["when"].max() <= harness.R.CUTOFF
    with pytest.raises(AssertionError):
        harness.units(late, seeds=(0,))


def test_row_ok_matches_policy_metrics():
    rng = np.random.default_rng(4)
    truth = frame(n=300, seed=5)[list(TARGETS)].astype(float)
    truth.loc[truth.sample(20, random_state=0).index, "pv_kwp"] = np.nan      # offered, size unknown
    pred = truth.fillna(8.0) * rng.uniform(0.7, 1.3, truth.shape)
    pred.loc[pred.sample(30, random_state=1).index, "battery_kwh"] = 0.0
    assert abs(row_ok(pred, truth).mean() - policy_metrics(pred, truth)["wholeDesignWithinTolerance"]) < 1e-12


def test_decision_rule():
    u = lambda b, c: {"base": {"whole": b, "ems": 50.0}, "cand": {"whole": c, "ems": 50.0}}  # noqa: E731
    folds = [u(0.2, 0.22)] * 4
    assert harness.decide(folds, [u(0.2, 0.21), u(0.2, 0.215), u(0.2, 0.212)])["adopt"]
    assert not harness.decide(folds, [u(0.2, 0.25), u(0.2, 0.17), u(0.2, 0.21)])["adopt"]   # gain < 1 sd
