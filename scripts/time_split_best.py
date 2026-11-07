"""Does the best setting also hold when the test projects are LATER than the training projects?

    python scripts/time_split_best.py

Within each installer, train on the earliest 80% of offers and test on the latest 20% (as scripts/leakage_checks.py),
and also on three rolling windows (train on everything before a cut-off, test on the next fifth). Compares the current
model, the best setting (coverage sizing + 40 battery sizes) and the typical design. Real export only.
Added after a teammate's port of the idea found the gain did not reproduce on their time-ordered validation window.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

from reonic import data, evaluate
from reonic.baseline import typical_design
from reonic.engine import Designer
from reonic.schema import INPUT_FIELDS, TARGETS

BEST = dict(sizing="coverage", battery_catalog_top=40)
full = data.load_raw("data/raw")
for c in INPUT_FIELDS:
    if c not in full.columns:
        full[c] = np.nan
full[list(TARGETS)] = full[list(TARGETS)].apply(pd.to_numeric, errors="coerce").clip(lower=0)
dated = full[full["offer_created_at"].notna()].reset_index(drop=True)
order = dated["offer_created_at"].rank(method="first")


def row(train: pd.DataFrame, test: pd.DataFrame) -> dict:
    t = test.reset_index(drop=True)
    out = {}
    for name, pred in (("current", Designer.train(train).design_batch(t)), ("best", Designer.train(train, **BEST).design_batch(t)), ("typical", typical_design(train, t))):
        m = evaluate.metrics(pred, t)
        out[name] = {"whole": m["whole_design_within_tolerance"], "pv": m["pv_kwp"]["within_tolerance"], "battery": m["battery_kwh"]["within_tolerance"]}
    out["n_test"] = int(len(t))
    return out


report = {}
# A. earliest 80% / latest 20% inside each installer
tr, te = [], []
for _, g in dated.groupby("installer_id"):
    g = g.sort_values("offer_created_at")
    cut = int(len(g) * 0.8)
    tr.append(g.iloc[:cut]); te.append(g.iloc[cut:])
report["last_20_percent_per_installer"] = row(pd.concat(tr), pd.concat(te))
# B. rolling windows over the whole timeline: train before the cut-off, test the next fifth
n = len(dated)
for i, (a, b) in enumerate(((0.6, 0.8), (0.7, 0.9), (0.8, 1.0))):
    train = dated[order <= a * n]
    test = dated[(order > a * n) & (order <= b * n)]
    report[f"window_{i + 1}_train_first_{int(a * 100)}pct_test_next_20pct"] = row(train, test)
Path("reports").mkdir(exist_ok=True)
Path("reports/time_split_best.json").write_text(json.dumps(report, indent=2, default=float))
print(f"{'split':52}{'n':>5}   whole design: current / best / typical     PV (cur/best)    battery (cur/best)")
for k, r in report.items():
    print(f"{k:52}{r['n_test']:5}   {r['current']['whole']:6.1%} / {r['best']['whole']:6.1%} / {r['typical']['whole']:6.1%}"
          f"      {r['current']['pv']:5.1%} / {r['best']['pv']:5.1%}    {r['current']['battery']:5.1%} / {r['best']['battery']:5.1%}")
