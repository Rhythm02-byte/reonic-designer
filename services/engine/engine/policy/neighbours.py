"""k most similar past projects, for explanations and the 'unusual for a home like this' check."""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.neighbors import NearestNeighbors


class Neighbours:
    def fit(self, X: pd.DataFrame, Y: pd.DataFrame, k: int = 25) -> "Neighbours":
        self.center = X.median().fillna(0)
        self.scale = X.std().replace(0, 1).fillna(1)
        self.nn = NearestNeighbors(n_neighbors=min(k, len(X))).fit(self._z(X))
        self.Y = Y.reset_index(drop=True)
        return self

    def _z(self, X: pd.DataFrame) -> np.ndarray:
        X = X.reindex(columns=self.center.index)
        return ((X.fillna(self.center) - self.center) / self.scale).fillna(0).to_numpy()

    def query(self, X: pd.DataFrame) -> list[pd.DataFrame]:
        idx = self.nn.kneighbors(self._z(X), return_distance=False)
        return [self.Y.iloc[i] for i in idx]

    def query_with_distance(self, X: pd.DataFrame) -> list[tuple[pd.DataFrame, np.ndarray]]:
        dist, idx = self.nn.kneighbors(self._z(X))
        return [(self.Y.iloc[i], d) for i, d in zip(idx, dist)]

    def median_sizes(self, X: pd.DataFrame, targets) -> dict[str, np.ndarray]:
        """Per row, the median size among the neighbours that got the component (NaN if none did or all sizes unknown)."""
        nbs = self.query(X)
        return {t: np.array([n[t][n[t] > 0].median() if (n[t] > 0).any() else np.nan for n in nbs], dtype=float) for t in targets}
