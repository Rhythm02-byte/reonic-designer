"""The agreement logic behind the deviation analysis, loaded from scripts/ (which is not a package)."""
import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

_spec = importlib.util.spec_from_file_location("deviation_analysis", Path(__file__).resolve().parents[1] / "scripts" / "deviation_analysis.py")
dev = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(dev)


def judge(truth, pred, t="pv_kwp"):
    return dev.judge(pd.Series(truth, dtype=float), pd.Series(pred, dtype=float), t)


def test_pv_agreement_uses_a_20_percent_tolerance_and_names_the_miss():
    j = judge([10, 10, 10, 10, 0, 0], [11.5, 7.0, 13.0, 0, 0, 5], "pv_kwp")
    assert list(j["ok"]) == [True, False, False, False, True, False]
    assert list(j["kind"]) == ["agrees", "too small", "too large", "missed (expert had it, we did not)",
                               "agrees", "extra (we added it, expert did not)"]


def test_unknown_expert_size_is_scored_on_include_only():
    j = judge([np.nan, np.nan], [4.0, 0.0])
    assert list(j["ok"]) == [True, False]  # offered but size unknown: any PV counts, none does not


def test_wallbox_size_never_matters_only_include():
    j = judge([11.0, 11.0, 0.0], [22.0, 0.0, 0.0], "wallbox_kw")
    assert list(j["ok"]) == [True, False, True]


def test_consumption_bands_isolate_the_placeholder_value():
    df = pd.DataFrame({"annual_consumption_kwh": [np.nan, 2000, 4000, 4500, 6000, 9000], "installer_id": "x",
                       "has_ev": [0.0] * 6, "existing_pv_kwp": [0.0] * 6, "n_options": [1] * 6, "pv_source": "s",
                       "heating_type": None})
    assert list(dev.bands(df)["consumption"]) == ["unknown", "<3,000 kWh", "3,000-4,499 kWh", "exactly 4,500 kWh",
                                                  "4,501-7,999 kWh", ">=8,000 kWh"]
