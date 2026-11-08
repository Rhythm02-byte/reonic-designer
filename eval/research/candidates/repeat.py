"""Repeat customer via customer_id (idea 10). An earlier TRAINING offer of the same customer (created strictly before
this row, never the row itself) -> flag + its four sizes as features (`feature`), or served as the design (`copy`)."""
from __future__ import annotations

import numpy as np
import pandas as pd

from research.lib import TARGETS, predictor, train_designer

KIND = "feature"
SETTINGS = {"feature": {"mode": "feature"}, "copy": {"mode": "copy"}}
COLS = ("rep_flag", "rep_pv", "rep_bat", "rep_hp", "rep_wb")


def earlier_design(history: pd.DataFrame):
    """-> fn(df): per row the latest earlier offer of the same customer in `history` (NaN row + flag 0 if none)."""
    by = {c: g.sort_values("when", kind="stable") for c, g in history.groupby(history["customer_id"].astype(str))}

    def fn(df: pd.DataFrame) -> pd.DataFrame:
        rows = []
        for cust, when, pid in zip(df["customer_id"].astype(str), df["when"], df["project_id"]):
            g = by.get(cust)
            g = g[(g["when"] < when) & (g["project_id"] != pid)] if g is not None else None
            if g is None or not len(g):
                rows.append([0.0, np.nan, np.nan, np.nan, np.nan])
            else:
                last = g.iloc[-1]
                rows.append([1.0] + [float(last[t]) for t in TARGETS])
        return pd.DataFrame(rows, columns=list(COLS), index=df.index)
    return fn


def fit(train, setting, ctx):
    fn = earlier_design(train)
    if setting["mode"] == "feature":
        return predictor(train_designer(train, extra=fn), extra=fn)
    base = ctx.base_predictor()

    def predict(test):
        sizes, extra = base(test)
        E = fn(test)
        sizes = sizes.copy()
        for t, c in zip(TARGETS, COLS[1:]):
            use = (E["rep_flag"] == 1) & E[c].notna()
            sizes.loc[use, t] = E.loc[use, c]
        return sizes, extra
    return predict
