"""Shared helpers for the research tournament plug-ins (eval/research/candidates/*).

A candidate never edits engine code. It builds a predictor from a training frame with one of three wrappers:
  * feature transform   `extra_features(fn)`: extra columns appended to engine.policy.features.features() while training
                         and predicting (the Designer keeps everything else: chain, rules, composite sources);
  * config override     `train_designer(train, config=...)`: Designer.train with a decision/sizing override;
  * post-processor      a function of the default Designer's output (sizes + p/lo/hi columns) and the training frame.
Plus `sample_weights(w)`: per-row weights for every boosted tree in the chain (recency weighting).

Every predictor is `fn(test_frame) -> (sizes DataFrame[TARGETS] indexed like test, extra DataFrame | None)`.
"""
from __future__ import annotations

from contextlib import contextmanager
from typing import Callable

import numpy as np
import pandas as pd

from engine.policy import rules
from engine.policy.chain import ORDER
from engine.policy.designer import Designer, load_config
from engine.policy.features import TARGETS

TOL = {"pv_kwp": 0.20, "battery_kwh": 0.25, "heat_pump_kw": 0.25, "wallbox_kw": float("inf")}  # = eval/metrics.TOLERANCE


# ---- wrappers ----------------------------------------------------------------------------------------------------------
@contextmanager
def extra_features(fn: Callable[[pd.DataFrame], pd.DataFrame] | None):
    """Append fn(df) columns to every feature matrix the Designer builds inside the block (training and prediction)."""
    if fn is None:
        yield
        return
    import engine.policy.designer as dz
    orig = dz.features

    def wrapped(df, *a, **k):
        X = orig(df, *a, **k)
        E = fn(df).reindex(df.index).astype(float)
        return pd.concat([X, E], axis=1)

    dz.features = wrapped
    try:
        yield
    finally:
        dz.features = orig


@contextmanager
def sample_weights(w: pd.Series | None):
    """Every HistGradientBoosting fit inside the block gets sample_weight = w (looked up by the training row index)."""
    if w is None:
        yield
        return
    import engine.policy.chain as ch
    origs = ch.HistGradientBoostingClassifier, ch.HistGradientBoostingRegressor

    def weighted(base):
        class W(base):
            def fit(self, X, y, sample_weight=None):
                sw = w.reindex(X.index).fillna(1.0).to_numpy(float) if hasattr(X, "index") else None
                return super().fit(X, y, sample_weight=sw)
        W.__name__ = base.__name__
        return W

    ch.HistGradientBoostingClassifier, ch.HistGradientBoostingRegressor = (weighted(b) for b in origs)
    try:
        yield
    finally:
        ch.HistGradientBoostingClassifier, ch.HistGradientBoostingRegressor = origs


def train_designer(train: pd.DataFrame, config: dict | None = None, extra=None, weights: pd.Series | None = None) -> Designer:
    with extra_features(extra), sample_weights(weights):
        return Designer.train(train, config=config)


def predictor(dz: Designer, extra=None, transform: Callable | None = None):
    """Predictor over a trained Designer; `extra` must be the same feature fn used at training time."""
    def fn(test: pd.DataFrame):
        t = transform(test) if transform else test
        with extra_features(extra):
            sizes, ext = dz.design_batch_full(t)
        return sizes.set_axis(test.index), ext.set_axis(test.index)
    return fn


def default_predictor(train: pd.DataFrame):
    """The reference: the current default config (config/policy.json), trained on `train`."""
    return predictor(Designer.train(train))


# ---- time-safe history -------------------------------------------------------------------------------------------------
def earlier_rows(history: pd.DataFrame, when: pd.Timestamp, window_days: float | None = None) -> pd.DataFrame:
    """History rows created strictly before `when` (and within the window). The ONLY way habit features see labels."""
    m = history["when"] < when
    if window_days is not None:
        m &= history["when"] >= when - pd.Timedelta(days=window_days)
    return history[m]


# ---- rules + scoring helpers ------------------------------------------------------------------------------------------
def apply_rules(test: pd.DataFrame, sizes: pd.DataFrame, catalog: dict) -> pd.DataFrame:
    """Hard rules R01-R05 + snapping, in decision order, on proposed sizes (what Designer._run does for its own values)."""
    out = sizes.copy()
    for i, row in zip(sizes.index, test.to_dict("records")):
        ctx, cur = rules.ctx_from_row(row), {}
        for t in ORDER:
            v, _, _ = rules.apply_one(t, float(sizes.at[i, t]), cur, ctx, catalog)
            out.at[i, t] = v
            cur[t] = v
    return out


def hits(pred: np.ndarray, truth: np.ndarray, t: str) -> np.ndarray:
    """Elementwise: pred size within tolerance of truth (same definition as metrics.policy_metrics). NaN truth = include only."""
    y, p = np.asarray(truth, float), np.asarray(pred, float)
    known = ~np.isnan(y)
    has_y, has_p = (y > 0) | ~known, p > 0
    rel = np.abs(p - np.nan_to_num(y)) / np.where(y > 0, y, 1)
    return np.where(has_y, has_p & (~known | (rel <= TOL[t])), ~has_p)


def row_ok(pred: pd.DataFrame, truth: pd.DataFrame) -> np.ndarray:
    ok = np.ones(len(truth), dtype=bool)
    for t in TARGETS:
        ok &= hits(pred[t].to_numpy(float), truth[t].to_numpy(float), t)
    return ok


def wallbox_size(dz: Designer) -> float:
    return float(dz.model.steps["wallbox_kw"][1])


__all__ = ["extra_features", "sample_weights", "train_designer", "predictor", "default_predictor", "earlier_rows",
           "apply_rules", "hits", "row_ok", "wallbox_size", "load_config", "TARGETS", "ORDER"]
