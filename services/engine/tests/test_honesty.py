"""Honesty checks on SYNTHETIC data (eval/honesty.py): fuzzing, shuffled labels, repeated splits. No confidential rows."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "eval"))
import honesty as H  # noqa: E402

from engine.policy.designer import Designer  # noqa: E402
from engine.policy.features import TARGETS  # noqa: E402
from policy_synth import generate  # noqa: E402

COMPOSITE = {"mode": "composite", "pvGate": 0.5, "sources": {"pv": "M1", "battery": "M1", "heatPump": "M1", "wallbox": "B0c"},
             "conformal": {"pv_kwp": 0.5, "battery_kwh": 0.5},
             "sizing": {"coverage": ["battery"], "blend": 0.5, "batteryCatalogTop": 0}}
LEARNED = {"mode": "learned", "sizing": {}}
PLAIN = {"mode": "hybrid", "sizing": {}}


@pytest.fixture(scope="module")
def df():
    return generate(1200, seed=1)


@pytest.fixture(scope="module", params=["hybrid", "composite+sizing"])
def designer(request, df):
    return Designer.train(df, config=PLAIN if request.param == "hybrid" else COMPOSITE, synthetic=True)


# -- fuzzing: 2,000 random / extreme homes ----------------------------------------------------------------------------
def test_fuzz_2000_homes_batch_api_hold_every_rule(designer):
    r = H.fuzz_batch(designer, 2000, seed=0)
    assert r["passed"], r["examples"]


def test_fuzz_design_api_with_planner_locks(designer):
    r = H.fuzz(designer, 150, seed=3)  # alternates raw rows and HomeInputs; random locks; determinism sampled
    assert r["crashes"] == 0 and r["passed"], r["examples"]


def test_check_design_flags_every_rule():
    row = {"heating_type": "Heatpump", "has_existing_pv": False, "has_ev": False, "roof_max_kwp": 4.0}
    values = {"pv_kwp": 31.0, "battery_kwh": 12.0, "heat_pump_kw": 8.0, "wallbox_kw": 11.0}
    p = dict.fromkeys(TARGETS, 0.5)
    iv = {t: (0.0, v, v) for t, v in values.items()}
    bad = " | ".join(H.check_design(values, p, iv, row, {}))
    for tag in ("R03", "R07", "R04", "R01", "wallbox"):
        assert tag in bad
    assert "R02" not in bad and not H.check_design(values, p, iv, row, dict.fromkeys(TARGETS, 0.0)) == []  # locks must match values
    assert "lock on pv_kwp" in " ".join(H.check_design(values, p, iv, row, {"pv_kwp": 3.0}))


# -- shuffled labels --------------------------------------------------------------------------------------------------
def test_shuffle_keeps_inputs_and_target_marginals(df):
    s = H.shuffle_labels(df, 0)
    assert s["demand_kwh"].equals(df["demand_kwh"])
    for t in TARGETS:
        assert np.allclose(np.sort(s[t].fillna(-1)), np.sort(df[t].fillna(-1)))
    assert not s[list(TARGETS)].equals(df[list(TARGETS)])


def test_shuffled_label_model_falls_to_the_baseline(df):
    make = lambda d: Designer.train(d, config=LEARNED, synthetic=True)
    r = H.shuffled_labels(df.iloc[:900], df.iloc[900:], seeds=(0, 1), make=make)
    assert r["real"]["pv"] > r["b0"]["pv"] + 0.10                      # the real model has information the baseline lacks
    assert r["shuffled"]["pv"]["mean"] < r["real"]["pv"] - 0.10        # scrambling the answers destroys it
    assert r["shuffled"]["pv"]["mean"] < r["b0"]["pv"] + 0.10          # ... down to about the no-information level
    assert r["realWholeMinusShuffled"] > 0


# -- repeated splits --------------------------------------------------------------------------------------------------
def test_repeated_splits_report_mean_sd_and_paired_gap(df):
    make = lambda d: Designer.train(d, config=LEARNED, synthetic=True)
    r = H.repeated_splits(df.head(600), seeds=(0, 1, 2), make=make)
    assert r["nSplits"] == 3 and r["seeds"] == [0, 1, 2]
    for who in ("ours", "b0"):
        for k in ("whole", "pv", "battery"):
            m = r[who][k]
            assert 0.0 <= m["mean"] <= 1.0 and m["sd"] >= 0.0 and m["n"] == 3
    assert r["oursMinusB0"]["pv"]["mean"] > 0   # synthetic PV depends on demand: the model should beat the median
    assert 0 <= r["splitsOursBeatsB0Whole"] <= 3
    assert isinstance(df, pd.DataFrame)
