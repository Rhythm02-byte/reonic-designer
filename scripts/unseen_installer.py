"""Unseen-installer evaluation, both directions.

    python scripts/unseen_installer.py

Trains on one installer's projects and tests on the other's, then swaps. This is a stricter test than a random
split: the model never sees the held-out installer's products, pricing or customers. Both directions are
reported because the installers differ in size (about 1,257 vs 336 projects) and behaviour.

The random-split result is shown alongside for comparison. Real export only. Writes reports/unseen_installer.json.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

from reonic import data, evaluate
from reonic.baseline import rule_of_thumb, typical_design
from reonic.engine import Designer
from reonic.schema import INPUT_FIELDS, TARGETS


def canonical(df: pd.DataFrame) -> pd.DataFrame:
    for c in INPUT_FIELDS:
        if c not in df.columns:
            df[c] = np.nan
    df[list(TARGETS)] = df[list(TARGETS)].apply(pd.to_numeric, errors="coerce").clip(lower=0)
    return df


def row(m: dict, b: dict, y: dict, n_train: int, n_test: int) -> dict:
    w = m["wallbox_kw"]
    return {
        "n_train": n_train, "n_test": n_test,
        "whole_design": m["whole_design_within_tolerance"], "baseline_whole_design": b["whole_design_within_tolerance"],
        "pv_within_tolerance": m["pv_kwp"]["within_tolerance"], "baseline_pv": b["pv_kwp"]["within_tolerance"],
        "battery_within_tolerance": m["battery_kwh"]["within_tolerance"], "baseline_battery": b["battery_kwh"]["within_tolerance"],
        "typical_whole_design": y["whole_design_within_tolerance"], "typical_pv": y["pv_kwp"]["within_tolerance"],
        "typical_battery": y["battery_kwh"]["within_tolerance"],
        "wallbox_precision": w["include_precision"], "wallbox_recall": w["include_recall"],
        "wallbox_f1": w["include_f1"], "wallbox_f2": w["include_f2"],
    }


full = canonical(data.load_raw("data/raw"))
installers = sorted(full["installer_id"].unique())
assert len(installers) == 2, installers
results = {"installers": {k: int((full["installer_id"] == k).sum()) for k in installers}}

# Random split, for comparison with the unseen-installer numbers
train, test = evaluate.split(full, 0.2, 0, None)
d = Designer.train(train)
results["random_split"] = row(evaluate.metrics(d.design_batch(test), test),
                              evaluate.metrics(rule_of_thumb(test), test),
                              evaluate.metrics(typical_design(train, test), test), len(train), len(test))

for held_out in installers:
    train = full[full["installer_id"] != held_out]
    test = full[full["installer_id"] == held_out]
    d = Designer.train(train)
    key = f"train_on_{[i for i in installers if i != held_out][0]}__test_on_{held_out}"
    results[key] = row(evaluate.metrics(d.design_batch(test), test),
                       evaluate.metrics(rule_of_thumb(test), test),
                       evaluate.metrics(typical_design(train, test), test), len(train), len(test))

Path("reports").mkdir(exist_ok=True)
Path("reports/unseen_installer.json").write_text(json.dumps(results, indent=2, default=float))

cols = ["n_train", "n_test", "whole_design", "baseline_whole_design", "typical_whole_design", "pv_within_tolerance", "baseline_pv",
        "typical_pv", "battery_within_tolerance", "baseline_battery", "typical_battery", "wallbox_precision", "wallbox_recall", "wallbox_f2"]
table = pd.DataFrame({k: v for k, v in results.items() if k != "installers"}).T[cols]
pd.set_option("display.width", 250)
print("installers:", results["installers"])
print(table.round(3).to_string())
