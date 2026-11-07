"""Sensitivity of the evaluation to the two unanswered Reonic questions.

    python scripts/sensitivity.py

Question 1: which option was signed (OPTION_CHOICE: first / last).
Question 2: module wattage used where the export gives only a module count (MODULE_WP: 400 / 450 / 500 W).

Same random split and seed for every run, so the differences come from the assumptions, not the split.
Writes reports/sensitivity.json. Synthetic data is never used here.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

from reonic import data, evaluate
from reonic.schema import INPUT_FIELDS, TARGETS

ROOT = Path("data/raw")
OUT = Path("reports/sensitivity")
OUT.mkdir(parents=True, exist_ok=True)


def canonical(df: pd.DataFrame) -> pd.DataFrame:
    """Same finishing steps as data.load() for a raw export, without re-reading the files."""
    for c in INPUT_FIELDS:
        if c not in df.columns:
            df[c] = np.nan
    df[list(TARGETS)] = df[list(TARGETS)].apply(pd.to_numeric, errors="coerce").clip(lower=0)
    return df


results = {}
for choice in ("first", "last"):
    for wp in (400.0, 450.0, 500.0):
        data.MODULE_WP = wp  # option_designs reads the module-level value at call time
        df = canonical(data.load_raw(ROOT, option_choice=choice))
        run_dir = OUT / f"{choice}_{int(wp)}"
        r = evaluate.run(df, out_dir=run_dir)
        m = r["model"]
        results[f"{choice}_{int(wp)}W"] = {
            "option_choice": choice,
            "module_wp": wp,
            "n_test": r["n_test"],
            "whole_design": m["whole_design_within_tolerance"],
            "pv_within_tolerance": m["pv_kwp"]["within_tolerance"],
            "battery_within_tolerance": m["battery_kwh"]["within_tolerance"],
            "baseline_whole_design": r["baseline"]["whole_design_within_tolerance"],
        }
        print(choice, int(wp), {k: round(v, 3) for k, v in results[f"{choice}_{int(wp)}W"].items()
                               if isinstance(v, float)})

data.MODULE_WP = 450.0  # restore the default

summary = {
    "whole_design_range": [min(v["whole_design"] for v in results.values()),
                           max(v["whole_design"] for v in results.values())],
    "pv_within_tolerance_range": [min(v["pv_within_tolerance"] for v in results.values()),
                                  max(v["pv_within_tolerance"] for v in results.values())],
    "runs": results,
}
(Path("reports") / "sensitivity.json").write_text(json.dumps(summary, indent=2, default=float))
print(json.dumps({k: v for k, v in summary.items() if k != "runs"}, indent=2, default=float))
