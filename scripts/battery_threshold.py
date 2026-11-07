"""Battery include cut-off, chosen by cross-validation on the training split only.

    python scripts/battery_threshold.py

Procedure (the 20% test split is looked at once, at the end):
  1. Same random 80/20 split as `reonic eval` (seed 0).
  2. On the 80% training split, 5-fold CV: train the designer on 4 folds, score the 5th at each candidate cut-off.
  3. Pick the cut-off with the best mean out-of-fold battery agreement (include/exclude and size within +/-25%).
  4. Train on the whole training split, apply that cut-off once to the test split, and compare with 0.5.

The heat pump is deliberately not tuned: only 13 of 1,593 designs include one, so any cut-off would be fitted to noise.
Writes reports/battery_threshold.json.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import KFold

from reonic import data, evaluate, model
from reonic.engine import Designer
from reonic.schema import INPUT_FIELDS, TARGETS

SEED = 0
GRID = [round(x, 2) for x in np.arange(0.30, 0.81, 0.05)]


def canonical(df: pd.DataFrame) -> pd.DataFrame:
    for c in INPUT_FIELDS:
        if c not in df.columns:
            df[c] = np.nan
    df[list(TARGETS)] = df[list(TARGETS)].apply(pd.to_numeric, errors="coerce").clip(lower=0)
    return df


def battery_agreement(designer: Designer, df: pd.DataFrame, cutoff: float) -> float:
    model.THRESHOLD["battery_kwh"] = cutoff
    pred = designer.design_batch(df)
    return evaluate.metrics(pred.reset_index(drop=True), df.reset_index(drop=True))["battery_kwh"]["within_tolerance"]


full = canonical(data.load_raw("data/raw"))
train, test = evaluate.split(full, 0.2, SEED, None)
train = train.reset_index(drop=True)

scores = {g: [] for g in GRID}
for tr, va in KFold(5, shuffle=True, random_state=SEED).split(train):
    d = Designer.train(train.iloc[tr])
    for g in GRID:
        scores[g].append(battery_agreement(d, train.iloc[va], g))
mean = {g: float(np.mean(v)) for g, v in scores.items()}
sd = {g: float(np.std(v)) for g, v in scores.items()}
best = max(mean, key=mean.get)

d = Designer.train(train)
test_default = battery_agreement(d, test, 0.5)
test_best = battery_agreement(d, test, best)
model.THRESHOLD["battery_kwh"] = 0.5

print(f"{'cut-off':>8} {'CV mean':>9} {'CV sd':>7}")
for g in GRID:
    print(f"{g:>8.2f} {mean[g]:>9.3f} {sd[g]:>7.3f}" + ("   <- best" if g == best else "") + ("   <- current" if g == 0.5 else ""))
print(f"\nchosen cut-off {best}: CV {mean[best]:.3f} vs {mean[0.5]:.3f} at 0.5 (gain {mean[best]-mean[0.5]:+.3f}, fold sd {sd[best]:.3f})")
print(f"test split, looked at once: {test_best:.3f} at {best} vs {test_default:.3f} at 0.5")

Path("reports").mkdir(exist_ok=True)
Path("reports/battery_threshold.json").write_text(json.dumps({
    "grid": GRID, "cv_mean": mean, "cv_sd": sd, "chosen": best, "cv_gain_vs_0.5": mean[best] - mean[0.5],
    "test_at_chosen": test_best, "test_at_0.5": test_default}, indent=2))
