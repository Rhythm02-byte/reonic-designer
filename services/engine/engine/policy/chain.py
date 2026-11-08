"""Learned part: a chain of (include? classifier, size regressor) per component.

Order follows the physics: the heat pump changes demand, demand drives PV size, PV size drives battery value.
Each step sees the decisions made before it (teacher forcing at training time), so the design is coherent and a
planner lock flows downstream. Sized components also get p10/p90 quantile regressors.

The wallbox is NOT learned: rule "home has an EV -> wallbox, else none" (the teammate's CV showed a model adds
nothing over the EV flag; size = most common installed size).
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier, HistGradientBoostingRegressor

ORDER = ("heat_pump_kw", "pv_kwp", "battery_kwh", "wallbox_kw")
MIN_ROWS_FOR_REGRESSOR = 20
RULE_BASED = {"wallbox_kw"}
DEFAULT_WALLBOX_KW = 11.0
THRESHOLD = {"heat_pump_kw": 0.5, "pv_kwp": 0.5, "battery_kwh": 0.5}
QUANTILES = (0.1, 0.9)
COVERAGE_QUANTILES = (0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9)  # plausible expert sizes for coverage sizing
# Same tolerances as eval/metrics.TOLERANCE: a size counts as right if |ours - expert| <= tol * expert.
SIZE_TOLERANCE = {"heat_pump_kw": 0.25, "pv_kwp": 0.20, "battery_kwh": 0.25}


def coverage_size(samples: np.ndarray, tol: float, candidates: np.ndarray | None = None) -> np.ndarray:
    """Per row, the size that lands within tolerance of the most plausible expert sizes (ported from the teammate prototype).

    `samples` is (rows, k): k plausible expert sizes per home (predicted quantiles, sorted to repair crossings). A candidate
    c is right for an expert size y when |c - y| <= tol * y. Candidates are the samples themselves, or, with `candidates`
    (a 1-D list of catalog sizes), the installer catalog. The candidate covered by the most samples wins; ties go to the
    one closest to the median sample. This targets the within-tolerance metric, where a mean prediction targets squared error."""
    samples = np.sort(np.clip(np.asarray(samples, dtype=float), 0, None), axis=1)
    lo, hi = samples * (1 - tol), samples * (1 + tol)
    med = np.median(samples, axis=1)
    out = np.empty(len(samples))
    cat = None if candidates is None or len(candidates) == 0 else np.asarray(candidates, dtype=float)
    for i in range(len(samples)):
        cand = samples[i] if cat is None else cat
        hits = ((cand[:, None] >= lo[i][None, :] - 1e-12) & (cand[:, None] <= hi[i][None, :] + 1e-12)).sum(axis=1)
        best = np.flatnonzero(hits == hits.max())
        out[i] = cand[best[np.argmin(np.abs(cand[best] - med[i]))]]
    return out


def has_ev(X: pd.DataFrame) -> np.ndarray:
    """1.0 where the home has an EV, else 0.0. An unknown EV flag counts as no EV (never guess a wallbox)."""
    if "has_ev" not in X.columns:
        return np.zeros(len(X))
    return X["has_ev"].fillna(0).astype(float).clip(0, 1).to_numpy()


class _Cols:
    """A model fitted on a column subset (columns constant among the rows it was fitted on break the tree binning)."""
    def __init__(self, model, cols):
        self.model, self.cols = model, list(cols)

    def predict(self, X):
        return self.model.predict(X[self.cols])


class _Const:
    def __init__(self, v: float):
        self.v = float(v)

    def predict(self, X):
        return np.full(len(X), self.v)

    def predict_proba(self, X):
        p = np.full(len(X), self.v)
        return np.column_stack([1 - p, p])


def hgb_params(p: dict | None) -> dict:
    """Regularisation overrides for the boosted trees: {"maxDepth", "minLeaf", "l2", "maxIter", "learningRate"} (all optional)."""
    p = p or {}
    out = {}
    for src, dst in (("maxDepth", "max_depth"), ("minLeaf", "min_samples_leaf"), ("l2", "l2_regularization")):
        if p.get(src) is not None:
            out[dst] = p[src]
    return out


class DesignModel:
    def fit(self, X: pd.DataFrame, Y: pd.DataFrame, params: dict | None = None, coverage: tuple = ()) -> "DesignModel":
        """`coverage`: targets that also get the nine size quantiles needed for coverage sizing (opt-in, ~3x training time)."""
        self.steps: dict = {}
        self.quants: dict = {}
        kw = hgb_params(params)
        it_c, it_r = (params or {}).get("maxIter"), (params or {}).get("maxIter")
        self.cols = [c for c in X.columns if X[c].notna().any()]  # all-empty columns break the binning
        Xc = X[self.cols].copy()
        for t in ORDER:
            y = Y[t].to_numpy(float)
            if t in RULE_BASED:
                sizes = y[y > 0]
                size = float(pd.Series(sizes).mode().iloc[0]) if len(sizes) else DEFAULT_WALLBOX_KW
                self.steps[t] = ("rule", size, None, None, [])
                continue
            use = [c for c in Xc.columns if Xc[c].nunique(dropna=True) > 1]  # constant columns break the binning too
            present = ((y > 0) | np.isnan(y)).astype(int)  # NaN = offered, size unknown
            if 0 < present.sum() < len(present):
                clf = HistGradientBoostingClassifier(max_iter=it_c or 200, learning_rate=0.08, random_state=0, **kw).fit(Xc[use], present)
            else:
                clf = _Const(present.mean() if len(present) else 0.0)
            mask = (present == 1) & ~np.isnan(y)
            ur = [c for c in use if Xc.loc[mask, c].nunique(dropna=True) > 1] if mask.any() else use  # non-constant among sized rows
            wrap = (lambda m: m) if ur == use else (lambda m: _Cols(m, ur))
            if mask.sum() >= MIN_ROWS_FOR_REGRESSOR and ur:
                reg = wrap(HistGradientBoostingRegressor(max_iter=it_r or 300, learning_rate=0.06, random_state=0, **kw).fit(Xc.loc[mask, ur], y[mask]))
                lo, hi = (wrap(HistGradientBoostingRegressor(loss="quantile", quantile=q, max_iter=200, learning_rate=0.06,
                                                             random_state=0, **kw).fit(Xc.loc[mask, ur], y[mask])) for q in QUANTILES)
            else:
                med = np.median(y[mask]) if mask.any() else 0.0
                reg = _Const(med)
                lo, hi = (_Const(np.quantile(y[mask], q) if mask.any() else 0.0) for q in QUANTILES)
            if t in coverage and mask.sum() >= MIN_ROWS_FOR_REGRESSOR and ur:
                self.quants[t] = [wrap(HistGradientBoostingRegressor(loss="quantile", quantile=q, max_iter=120, learning_rate=0.08,
                                                                     random_state=0, **kw).fit(Xc.loc[mask, ur], y[mask]))
                                  for q in COVERAGE_QUANTILES]
            self.steps[t] = (clf, reg, lo, hi, use)
            Xc[t] = y  # teacher forcing: downstream steps learn from the expert's upstream choice
        return self

    def predict(self, X: pd.DataFrame, fixed: dict | None = None, until: str | None = None,
                thresholds: dict | None = None, only: str | None = None, coverage: tuple = (), cover_catalog: dict | None = None,
                similar: dict | None = None, blend: float = 0.0) -> pd.DataFrame:
        """`fixed` maps component -> scalar or per-row array used as-is downstream.
        Columns per component t: t (decided size, 0 = not included), p_t (P(include)), size_t / lo_t / hi_t
        (median, p10, p90 size if included). `until` stops the chain after that component.
        `thresholds` overrides the include gate per component (e.g. {"pv_kwp": 0.4}).
        `only` computes just that component, taking every upstream component from `fixed` (one step instead of re-running
        the chain: what the engine uses per request).
        `coverage`: targets sized by coverage_size over the trained quantiles (needs fit(coverage=...); silently the plain
        regressor otherwise); `cover_catalog` maps target -> catalog sizes used as the candidates instead of the samples.
        `similar` maps target -> per-row median size among the most similar past homes (NaN if none); with `blend` > 0 the
        size becomes (1 - blend) * model + blend * similar (the include decision stays the model's)."""
        fixed = fixed or {}
        gate = {**THRESHOLD, **(thresholds or {})}
        Xc = X[self.cols].copy()
        n = len(X)
        out = pd.DataFrame(index=X.index)
        for t in ORDER:
            if only is not None and t != only:
                if t in fixed:
                    Xc[t] = np.broadcast_to(np.asarray(fixed[t], dtype=float), (n,))
                continue
            if t in RULE_BASED:
                p = has_ev(X)
                size = np.full(n, self.steps[t][1])
                val = np.where(p >= 1.0, size, 0.0)
                lo = hi = size
            else:
                clf, reg, qlo, qhi, cols = self.steps[t]
                p = clf.predict_proba(Xc[cols])[:, 1]
                size = np.clip(reg.predict(Xc[cols]), 0, None)
                qs = getattr(self, "quants", {}).get(t)
                if qs and t in coverage:
                    cat = (cover_catalog or {}).get(t)
                    size = coverage_size(np.column_stack([m.predict(Xc[cols]) for m in qs]), SIZE_TOLERANCE[t],
                                         np.asarray(cat) if cat else None)
                if blend and similar and t in similar:
                    med = np.asarray(similar[t], dtype=float)
                    size = np.where(np.isnan(med), size, (1 - blend) * size + blend * med)
                lo = np.clip(qlo.predict(Xc[cols]), 0, None)
                hi = np.clip(qhi.predict(Xc[cols]), 0, None)
                val = np.where(p >= gate[t], size, 0.0)
            if t in fixed:
                val = np.broadcast_to(np.asarray(fixed[t], dtype=float), (n,)).copy()
            lo, hi = np.minimum(lo, size), np.maximum(hi, size)  # keep p10 <= p50 <= p90
            out[t], out[f"p_{t}"], out[f"size_{t}"], out[f"lo_{t}"], out[f"hi_{t}"] = val, p, size, lo, hi
            Xc[t] = val
            if t == until or t == only:
                break
        return out
