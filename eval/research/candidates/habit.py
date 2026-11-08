"""Installer's rolling package habit (idea 9). For each row: the same installer's TRAINING offers created strictly
before this row (within the window) -> n, median kWp, modal kWp (1 kWp buckets), battery share, median kWh,
median kWh/kWp, wallbox share. No row ever sees its own or a later label (unit-tested in eval/test_research.py)."""
from __future__ import annotations

import numpy as np
import pandas as pd

from research.lib import predictor, train_designer

KIND = "feature"
SETTINGS = {"30d": {"window_days": 30}, "90d": {"window_days": 90}, "all": {"window_days": None}}
COLS = ("hab_n", "hab_pv_med", "hab_pv_mode", "hab_bat_share", "hab_bat_med", "hab_bat_per_kwp", "hab_wb_share")


def _agg(g: pd.DataFrame) -> list[float]:
    if not len(g):
        return [0.0] + [np.nan] * (len(COLS) - 1)
    pv, bat, wb = g["pv_kwp"].to_numpy(float), g["battery_kwh"].to_numpy(float), g["wallbox_kw"].to_numpy(float)
    spv = pv[pv > 0]
    sb = bat[bat > 0]
    both = (pv > 0) & (bat > 0)
    mode = float(pd.Series(np.round(spv)).mode().iloc[0]) if len(spv) else np.nan
    return [float(len(g)), float(np.median(spv)) if len(spv) else np.nan, mode, float(np.mean(bat > 0)),
            float(np.median(sb)) if len(sb) else np.nan, float(np.median(bat[both] / pv[both])) if both.any() else np.nan,
            float(np.mean(np.nan_to_num(wb) > 0))]


def habit_features(history: pd.DataFrame, window_days: float | None):
    """-> fn(df): habit columns for df's rows, computed only from `history` rows earlier than each row."""
    hist = {str(i): g.sort_values("when", kind="stable") for i, g in history.groupby(history["installer_id"].astype(str))}

    def fn(df: pd.DataFrame) -> pd.DataFrame:
        rows = []
        for inst, when in zip(df["installer_id"].astype(str), df["when"]):
            g = hist.get(inst)
            if g is None:
                rows.append(_agg(g if g is not None else history.iloc[:0]))
                continue
            w = g["when"].to_numpy()
            hi = np.searchsorted(w, np.datetime64(when), side="left")            # strictly earlier
            lo = 0 if window_days is None else np.searchsorted(w, np.datetime64(when - pd.Timedelta(days=window_days)), side="left")
            rows.append(_agg(g.iloc[lo:hi]))
        return pd.DataFrame(rows, columns=list(COLS), index=df.index)
    return fn


def fit(train, setting, ctx):
    fn = habit_features(train, setting["window_days"])
    return predictor(train_designer(train, extra=fn), extra=fn)
