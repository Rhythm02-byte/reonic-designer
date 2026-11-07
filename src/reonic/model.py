"""Learned part: a chain of (include? classifier, size regressor) per component.

Order follows the physics: the heat pump changes demand, demand drives PV size, PV size drives
battery value. Each step sees the decisions made before it, so the design is coherent, not
three independent guesses, and a planner override flows downstream.

The wallbox is NOT learned. It follows the deterministic rule "home has an EV -> wallbox, else none"
(size = most common installed size). Cross-validation showed the learned wallbox model did no better than
this rule (scripts/wallbox_threshold.py), so a rule is simpler and easier to defend.
"""
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier, HistGradientBoostingRegressor
from sklearn.neighbors import NearestNeighbors

ORDER = ("heat_pump_kw", "pv_kwp", "battery_kwh", "wallbox_kw")
MIN_ROWS_FOR_REGRESSOR = 20
BLEND_TARGETS = ("pv_kwp", "battery_kwh")  # sizes that can be blended with what similar homes got
RULE_BASED = {"wallbox_kw"}  # components decided by a fixed rule, not a model
DEFAULT_WALLBOX_KW = 11.0
# Include cut-off for the learned components.
THRESHOLD = {"heat_pump_kw": 0.5, "pv_kwp": 0.5, "battery_kwh": 0.5}
# Same tolerances as evaluate.TOLERANCE (a test keeps them equal): a size counts as right if |ours - expert| <= tol * expert.
SIZE_TOLERANCE = {"heat_pump_kw": 0.25, "pv_kwp": 0.20, "battery_kwh": 0.25}
QUANTILES = (0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9)


def coverage_size(samples: np.ndarray, tol: float) -> np.ndarray:
    """Pick, per row, the size that lands within tolerance of the most plausible expert sizes.

    `samples` is (rows, k): k plausible expert sizes per home (predicted quantiles). A candidate c is right for an
    expert size y when |c - y| <= tol * y, i.e. y*(1-tol) <= c <= y*(1+tol). We take the candidate covered by the most
    samples; ties go to the one closest to the median. This targets our metric directly, where a plain mean
    prediction targets squared error.
    """
    samples = np.sort(np.clip(samples, 0, None), axis=1)  # quantile models can cross; sorting repairs that
    lo, hi = samples * (1 - tol), samples * (1 + tol)
    med = np.median(samples, axis=1)
    out = np.empty(len(samples))
    for i in range(len(samples)):
        cand = samples[i]
        hits = ((cand[:, None] >= lo[i][None, :] - 1e-12) & (cand[:, None] <= hi[i][None, :] + 1e-12)).sum(axis=1)
        best = np.flatnonzero(hits == hits.max())
        out[i] = cand[best[np.argmin(np.abs(cand[best] - med[i]))]]
    return out


def _has_ev(X: pd.DataFrame) -> np.ndarray:
    """1.0 where the home has an EV, else 0.0. An unknown EV flag counts as no EV (never guess a wallbox)."""
    if "has_ev" not in X.columns:
        return np.zeros(len(X))
    return X["has_ev"].fillna(0).astype(float).clip(0, 1).to_numpy()


class _Const:
    def __init__(self, v: float):
        self.v = float(v)

    def predict(self, X):
        return np.full(len(X), self.v)

    def predict_proba(self, X):
        p = np.full(len(X), self.v)
        return np.column_stack([1 - p, p])


class _Cols:
    """A fitted estimator that only looks at the columns it was trained on."""

    def __init__(self, model, cols):
        self.model, self.cols = model, cols

    def predict(self, X):
        return self.model.predict(X[self.cols])

    def predict_proba(self, X):
        return self.model.predict_proba(X[self.cols])


def _fit_usable(est, X: pd.DataFrame, y, sample_weight=None, fallback: float = 0.0):
    """Fit on the columns that vary in this subset. A column with a single value (or none) breaks the binning, which
    happens when a small training subset has, say, no heat pump at all. If nothing varies, predict the fallback."""
    cols = [c for c in X.columns if X[c].nunique(dropna=True) > 1]
    if not cols:
        return _Const(fallback)
    return _Cols(est.fit(X[cols], y, sample_weight=sample_weight), cols)


class DesignModel:
    def __init__(self, sizing: str = "mean", params: dict | None = None):
        """sizing: "mean" = one regressor's point estimate; "coverage" = the size that fits the most plausible expert sizes."""
        assert sizing in ("mean", "coverage")
        self.sizing = sizing
        self.params = params or {}  # extra HistGradientBoosting settings, for tuning experiments

    def fit(self, X: pd.DataFrame, Y: pd.DataFrame, sample_weight: np.ndarray | None = None) -> "DesignModel":
        self.steps = {}
        w = None if sample_weight is None else np.asarray(sample_weight, dtype=float)
        hp = lambda base: {**base, **self.params}
        self.cols = [c for c in X.columns if X[c].notna().any()]  # all-empty columns break the binning
        Xc = X[self.cols].copy()
        for t in ORDER:
            y = Y[t].to_numpy(float)
            if t in RULE_BASED:
                sizes = y[y > 0]  # most common installed size, e.g. 11 kW
                size = float(pd.Series(sizes).mode().iloc[0]) if len(sizes) else DEFAULT_WALLBOX_KW
                self.steps[t] = ("rule", size, [], None)
                continue
            present = ((y > 0) | np.isnan(y)).astype(int)  # NaN = offered, size unknown
            if 0 < present.sum() < len(present):
                clf = _fit_usable(HistGradientBoostingClassifier(**hp(dict(max_iter=200, learning_rate=0.08, random_state=0))), Xc, present, w, present.mean())
            else:
                clf = _Const(present.mean() if len(present) else 0.0)
            mask = (present == 1) & ~np.isnan(y)
            if mask.sum() >= MIN_ROWS_FOR_REGRESSOR:
                reg = _fit_usable(HistGradientBoostingRegressor(**hp(dict(max_iter=300, learning_rate=0.06, random_state=0))), Xc[mask], y[mask], None if w is None else w[mask], float(np.median(y[mask])))
            else:
                reg = _Const(np.median(y[mask]) if mask.any() else 0.0)
            quants = None
            if self.sizing == "coverage" and mask.sum() >= MIN_ROWS_FOR_REGRESSOR:
                quants = [_fit_usable(HistGradientBoostingRegressor(loss="quantile", quantile=q, max_iter=120, learning_rate=0.08, random_state=0), Xc[mask], y[mask],
                                      None if w is None else w[mask], float(np.median(y[mask]))) for q in QUANTILES]
            self.steps[t] = (clf, reg, list(Xc.columns), quants)
            Xc[t] = y  # teacher forcing: downstream steps learn from the expert's upstream choice
        return self

    def predict(self, X: pd.DataFrame, fixed: dict | None = None, similar: dict | None = None, blend: float = 0.0) -> pd.DataFrame:
        """`fixed` maps component -> scalar or per-row array; those values are used as-is downstream.

        `similar` maps component -> per-row median size among the most similar past homes (NaN if none had it). With
        `blend` > 0 the size becomes (1 - blend) * model + blend * similar. Include/exclude is still the model's call.
        """
        fixed = fixed or {}
        Xc = X[self.cols].copy()
        out = pd.DataFrame(index=X.index)
        for t in ORDER:
            if t in RULE_BASED:
                p = _has_ev(X)
                val = np.where(p >= 1.0, self.steps[t][1], 0.0)
                if t in fixed:
                    val = np.broadcast_to(np.asarray(fixed[t], dtype=float), (len(X),)).copy()
                out[t], out[f"p_{t}"] = val, p
                Xc[t] = val
                continue
            clf, reg, cols, quants = self.steps[t]
            p = clf.predict_proba(Xc[cols])[:, 1]
            size = np.clip(reg.predict(Xc[cols]), 0, None)
            if quants is not None:
                size = coverage_size(np.column_stack([m.predict(Xc[cols]) for m in quants]), SIZE_TOLERANCE[t])
            if blend and similar and t in similar:
                med = np.asarray(similar[t], dtype=float)
                size = np.where(np.isnan(med), size, (1 - blend) * size + blend * med)
            val = np.where(p >= THRESHOLD[t], size, 0.0)
            if t in fixed:
                val = np.broadcast_to(np.asarray(fixed[t], dtype=float), (len(X),)).copy()
            out[t], out[f"p_{t}"] = val, p
            Xc[t] = val
        return out


class Neighbours:
    """k most similar past projects, for explanations and the 'unusual for a home like this' check."""

    def fit(self, X: pd.DataFrame, Y: pd.DataFrame, k: int = 25) -> "Neighbours":
        self.center = X.median().fillna(0)
        self.scale = X.std().replace(0, 1).fillna(1)
        self.nn = NearestNeighbors(n_neighbors=min(k, len(X))).fit(self._z(X))
        self.Y = Y.reset_index(drop=True)
        return self

    def _z(self, X: pd.DataFrame) -> np.ndarray:
        return ((X.fillna(self.center) - self.center) / self.scale).fillna(0).to_numpy()

    def median_sizes(self, X: pd.DataFrame, targets) -> dict[str, np.ndarray]:
        """Per row, the median size among neighbours that got the component (NaN if none did or all sizes unknown)."""
        nbs = self.query(X)
        out = {}
        for t in targets:
            out[t] = np.array([n[t][n[t] > 0].median() if (n[t] > 0).any() else np.nan for n in nbs], dtype=float)
        return out

    def query(self, X: pd.DataFrame) -> list[pd.DataFrame]:
        idx = self.nn.kneighbors(self._z(X), return_distance=False)
        return [self.Y.iloc[i] for i in idx]
