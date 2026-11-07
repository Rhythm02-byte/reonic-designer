"""Isolate the wallbox include decision and tune its threshold without touching the test set.

    python scripts/wallbox_threshold.py

Procedure (nothing is tuned on the test split):
  1. Same random 80/20 split as `reonic eval` (seed 0). The 20% test split is only scored at the end.
  2. On the 80% training split, 5-fold cross-validation gives out-of-fold probabilities that a home gets a wallbox.
  3. Choose the probability threshold that maximises out-of-fold accuracy (the metric `evaluate.py` reports).
  4. Fit on all training data, apply the chosen threshold once to the test split, and compare with the baseline.

Baseline (baseline.py): include a wallbox if the home has an EV. Target: include/exclude agreement, as in evaluate.py.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.model_selection import StratifiedKFold

from reonic import data, evaluate
from reonic.baseline import rule_of_thumb
from reonic.schema import INPUT_FIELDS, TARGETS

SEED = 0
THRESHOLDS = np.round(np.arange(0.10, 0.91, 0.02), 2)


def canonical(df: pd.DataFrame) -> pd.DataFrame:
    for c in INPUT_FIELDS:
        if c not in df.columns:
            df[c] = np.nan
    df[list(TARGETS)] = df[list(TARGETS)].apply(pd.to_numeric, errors="coerce").clip(lower=0)
    return df


def fit_clf(X: pd.DataFrame, y: np.ndarray) -> HistGradientBoostingClassifier:
    return HistGradientBoostingClassifier(max_iter=200, learning_rate=0.08, random_state=SEED).fit(X, y)


def accuracy(p: np.ndarray, y: np.ndarray, t: float) -> float:
    return float(((p >= t).astype(int) == y).mean())


full = canonical(data.load_raw("data/raw"))
train, test = evaluate.split(full, 0.2, SEED, None)
X_tr, X_te = data.features(train), data.features(test)
y_tr = (train["wallbox_kw"].to_numpy() > 0).astype(int)
y_te = (test["wallbox_kw"].to_numpy() > 0).astype(int)

# -- 2. out-of-fold probabilities on the training split -----------------------------------------------
oof = np.zeros(len(train))
skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED)
for tr_idx, va_idx in skf.split(X_tr, y_tr):
    oof[va_idx] = fit_clf(X_tr.iloc[tr_idx], y_tr[tr_idx]).predict_proba(X_tr.iloc[va_idx])[:, 1]

# -- 3. choose the threshold on out-of-fold data only -------------------------------------------------
curve = {float(t): accuracy(oof, y_tr, t) for t in THRESHOLDS}
best_t = max(curve, key=curve.get)
ev_baseline_train = float(((train["has_ev"].fillna(False).astype(bool).to_numpy()).astype(int) == y_tr).mean())

# -- 4. one look at the test split --------------------------------------------------------------------
clf = fit_clf(X_tr, y_tr)
p_te = clf.predict_proba(X_te)[:, 1]
model_test_acc = accuracy(p_te, y_te, best_t)
model_default_acc = accuracy(p_te, y_te, 0.5)
base = rule_of_thumb(test)["wallbox_kw"].to_numpy() > 0
baseline_test_acc = float((base.astype(int) == y_te).mean())

report = {
    "seed": SEED,
    "n_train": int(len(train)), "n_test": int(len(test)),
    "wallbox_share_train": float(y_tr.mean()),
    "oof_threshold_curve": {str(k): round(v, 4) for k, v in curve.items()},
    "chosen_threshold": best_t,
    "oof_accuracy_at_chosen": round(curve[best_t], 4),
    "oof_baseline_accuracy_ev_rule": round(ev_baseline_train, 4),
    "test_accuracy_model_chosen_threshold": round(model_test_acc, 4),
    "test_accuracy_model_default_0_5": round(model_default_acc, 4),
    "test_accuracy_baseline_ev_rule": round(baseline_test_acc, 4),
}
Path("reports").mkdir(exist_ok=True)
Path("reports/wallbox_threshold.json").write_text(json.dumps(report, indent=2))
print(json.dumps(report, indent=2))
