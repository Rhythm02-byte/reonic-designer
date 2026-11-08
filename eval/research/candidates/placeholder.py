"""Placeholder demand (idea 11). The ETL default 4,500 kWh (and 0 kWh) carries no information about the home.
`nan`: treat it as unknown (input transform on train and test rows); `interact`: placeholder flag x installer columns."""
from __future__ import annotations

import numpy as np
import pandas as pd

from engine.etl.normalize import DEFAULT_DEMAND_KWH
from research.lib import predictor, train_designer

KIND = "feature"
SETTINGS = {"nan": {"mode": "nan"}, "interact": {"mode": "interact"}}


def is_placeholder(df: pd.DataFrame) -> pd.Series:
    d = pd.to_numeric(df["demand_kwh"], errors="coerce")
    return ((d - DEFAULT_DEMAND_KWH).abs() < 1e-6) | (d == 0)


def to_nan(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out.loc[is_placeholder(df), "demand_kwh"] = np.nan
    return out


def fit(train, setting, ctx):
    if setting["mode"] == "nan":
        return predictor(train_designer(to_nan(train)), transform=to_nan)
    installers = sorted(train.installer_id.astype(str).unique())

    def fn(df):
        ph = is_placeholder(df).astype(float)
        return pd.DataFrame({f"ph_x_{i}": ph * (df.installer_id.astype(str) == i) for i in installers}, index=df.index)
    return predictor(train_designer(train, extra=fn), extra=fn)
