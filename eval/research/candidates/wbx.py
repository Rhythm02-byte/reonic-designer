"""Wallbox threshold for the whole design (idea 4): a learned P(wallbox) on the base features (incl. the EV flag)
replaces the default's EV rule; include when P >= tau. Everything else is the default's output."""
from __future__ import annotations

import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier

from engine.policy.features import features
from research.lib import wallbox_size

KIND = "post-processor"
SETTINGS = {"t0.3": {"tau": 0.3}, "t0.5": {"tau": 0.5}, "t0.7": {"tau": 0.7}}


def fit(train, setting, ctx):
    installers = tuple(sorted(train.installer_id.astype(str).unique()))
    X = features(train, installers)
    cols = [c for c in X.columns if X[c].nunique(dropna=True) > 1]
    y = (train["wallbox_kw"].fillna(0) > 0).astype(int).to_numpy()
    clf = HistGradientBoostingClassifier(max_iter=200, learning_rate=0.08, max_depth=3, min_samples_leaf=40,
                                         random_state=0).fit(X[cols], y)
    base, size = ctx.base_predictor(), wallbox_size(ctx.base())

    def predict(test):
        sizes, extra = base(test)
        p = clf.predict_proba(features(test, installers)[cols])[:, 1]
        sizes = sizes.copy()
        sizes["wallbox_kw"] = np.where(p >= setting["tau"], size, 0.0)
        return sizes, extra
    return predict
