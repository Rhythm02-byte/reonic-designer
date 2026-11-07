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
RULE_BASED = {"wallbox_kw"}  # components decided by a fixed rule, not a model
DEFAULT_WALLBOX_KW = 11.0
# Include cut-off for the learned components.
THRESHOLD = {"heat_pump_kw": 0.5, "pv_kwp": 0.5, "battery_kwh": 0.5}


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


class DesignModel:
    def fit(self, X: pd.DataFrame, Y: pd.DataFrame) -> "DesignModel":
        self.steps = {}
        self.cols = [c for c in X.columns if X[c].notna().any()]  # all-empty columns break the binning
        Xc = X[self.cols].copy()
        for t in ORDER:
            y = Y[t].to_numpy(float)
            if t in RULE_BASED:
                sizes = y[y > 0]  # most common installed size, e.g. 11 kW
                size = float(pd.Series(sizes).mode().iloc[0]) if len(sizes) else DEFAULT_WALLBOX_KW
                self.steps[t] = ("rule", size, [])
                continue
            present = ((y > 0) | np.isnan(y)).astype(int)  # NaN = offered, size unknown
            if 0 < present.sum() < len(present):
                clf = HistGradientBoostingClassifier(max_iter=200, learning_rate=0.08, random_state=0).fit(Xc, present)
            else:
                clf = _Const(present.mean() if len(present) else 0.0)
            mask = (present == 1) & ~np.isnan(y)
            if mask.sum() >= MIN_ROWS_FOR_REGRESSOR:
                reg = HistGradientBoostingRegressor(max_iter=300, learning_rate=0.06, random_state=0).fit(Xc[mask], y[mask])
            else:
                reg = _Const(np.median(y[mask]) if mask.any() else 0.0)
            self.steps[t] = (clf, reg, list(Xc.columns))
            Xc[t] = y  # teacher forcing: downstream steps learn from the expert's upstream choice
        return self

    def predict(self, X: pd.DataFrame, fixed: dict | None = None) -> pd.DataFrame:
        """`fixed` maps component -> scalar or per-row array; those values are used as-is downstream."""
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
            clf, reg, cols = self.steps[t]
            p = clf.predict_proba(Xc[cols])[:, 1]
            size = np.clip(reg.predict(Xc[cols]), 0, None)
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

    def query(self, X: pd.DataFrame) -> list[pd.DataFrame]:
        idx = self.nn.kneighbors(self._z(X), return_distance=False)
        return [self.Y.iloc[i] for i in idx]
