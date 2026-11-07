"""Does the suspected default demand value (exactly 4,500 kWh) distort the evaluation?

    python scripts/default_demand_check.py

Three comparisons on the same random split and seed:
  A. all rows (the current headline)
  B. training and test without the rows whose demand is exactly 4,500 kWh
  C. the model trained on all rows, scored separately on default and non-default test rows

Writes reports/default_demand_check.json. Real export only.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

from reonic import data, evaluate
from reonic.engine import Designer
from reonic.schema import INPUT_FIELDS, TARGETS

DEFAULT_KWH = 4500.0
OUT = Path("reports")
(OUT / "default_demand_check").mkdir(parents=True, exist_ok=True)


def canonical(df):
    for c in INPUT_FIELDS:
        if c not in df.columns:
            df[c] = np.nan
    df[list(TARGETS)] = df[list(TARGETS)].apply(pd.to_numeric, errors="coerce").clip(lower=0)
    return df


full = canonical(data.load_raw("data/raw"))
is_default = full["annual_consumption_kwh"].round(3).eq(DEFAULT_KWH)
print(f"rows: {len(full)}, exactly {DEFAULT_KWH:g} kWh: {int(is_default.sum())} ({is_default.mean():.1%})")

result = {"n_rows": int(len(full)), "n_default": int(is_default.sum()), "share_default": float(is_default.mean())}


def summarise(m, r):
    return {"whole_design": m["whole_design_within_tolerance"], "pv": m["pv_kwp"]["within_tolerance"],
            "battery": m["battery_kwh"]["within_tolerance"], "n_test": r["n_test"],
            "baseline_whole_design": r["baseline"]["whole_design_within_tolerance"]}


# A. all rows
r_a = evaluate.run(full, out_dir=OUT / "default_demand_check/all")
result["A_all_rows"] = summarise(r_a["model"], r_a)

# B. drop the default rows everywhere
r_b = evaluate.run(full[~is_default].reset_index(drop=True), out_dir=OUT / "default_demand_check/without_default")
result["B_without_default_rows"] = summarise(r_b["model"], r_b)

# C. score default and non-default test rows separately, with the same split as A
train, test = evaluate.split(full, 0.2, 0, None)
designer = Designer.train(train)
pred = designer.design_batch(test)
mask = test["annual_consumption_kwh"].round(3).eq(DEFAULT_KWH).to_numpy()
for name, sel in (("default_rows", mask), ("other_rows", ~mask)):
    m = evaluate.metrics(pred[sel].reset_index(drop=True), test[sel].reset_index(drop=True))
    result.setdefault("C_scored_separately", {})[name] = {
        "n_test": int(sel.sum()), "whole_design": m["whole_design_within_tolerance"],
        "pv": m["pv_kwp"]["within_tolerance"], "battery": m["battery_kwh"]["within_tolerance"]}

(OUT / "default_demand_check.json").write_text(json.dumps(result, indent=2, default=float))
print(json.dumps(result, indent=2, default=float))
