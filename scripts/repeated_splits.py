"""How much do our numbers move, and against which reference are they honest?

    python scripts/repeated_splits.py

Part A: 30 random 80/20 splits (seeds 0-29). For each, the model, the rule-of-thumb baseline, and a TYPICAL-DESIGN
        baseline that ignores the inputs: the median size of each component that most homes get, plus the wallbox
        rule. The typical design is the fair "no information" reference: the shuffled-label check in
        scripts/leakage_checks.py showed that a model trained on scrambled answers already lands close to it.
Part B: bootstrap over the 1,593 projects using out-of-fold predictions, giving a 95% interval for the model's
        whole-design score and for its gap to each baseline.

Splits share training data, so their spread understates sampling uncertainty; part B is the better interval.
Real export only. Writes reports/repeated_splits.json.
"""
import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import KFold, train_test_split

from reonic import data, evaluate
from reonic.baseline import rule_of_thumb, typical_design
from reonic.engine import Designer
from reonic.schema import INPUT_FIELDS, TARGETS

_spec = importlib.util.spec_from_file_location("deviation_analysis", Path(__file__).resolve().parent / "deviation_analysis.py")
dev = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(dev)

N_SPLITS, N_BOOT = 30, 2000


def canonical(df: pd.DataFrame) -> pd.DataFrame:
    for c in INPUT_FIELDS:
        if c not in df.columns:
            df[c] = np.nan
    df[list(TARGETS)] = df[list(TARGETS)].apply(pd.to_numeric, errors="coerce").clip(lower=0)
    return df


def whole(pred: pd.DataFrame, truth: pd.DataFrame) -> dict:
    m = evaluate.metrics(pred.reset_index(drop=True), truth.reset_index(drop=True))
    return {"whole": m["whole_design_within_tolerance"], "pv": m["pv_kwp"]["within_tolerance"], "battery": m["battery_kwh"]["within_tolerance"]}


def spread(values) -> dict:
    v = np.asarray(values, dtype=float)
    return {"mean": float(v.mean()), "sd": float(v.std(ddof=1)), "p2_5": float(np.percentile(v, 2.5)), "p97_5": float(np.percentile(v, 97.5)),
            "min": float(v.min()), "max": float(v.max())}


full = canonical(data.load_raw("data/raw")).reset_index(drop=True)
report: dict = {"n_projects": int(len(full))}

# ---- Part A: 30 random splits ----------------------------------------------------------------------
rows = []
for seed in range(N_SPLITS):
    tr, te = train_test_split(full, test_size=0.2, random_state=seed)
    d = Designer.train(tr)
    rows.append({"model": whole(d.design_batch(te), te), "rule": whole(rule_of_thumb(te), te), "typical": whole(typical_design(tr, te), te)})
a = {}
for metric in ("whole", "pv", "battery"):
    for who in ("model", "rule", "typical"):
        a[f"{who}_{metric}"] = spread([r[who][metric] for r in rows])
    a[f"model_minus_typical_{metric}"] = spread([r["model"][metric] - r["typical"][metric] for r in rows])
    a[f"model_minus_rule_{metric}"] = spread([r["model"][metric] - r["rule"][metric] for r in rows])
a["splits_where_model_beats_typical_on_whole_design"] = int(sum(r["model"]["whole"] > r["typical"]["whole"] for r in rows))
report["A_thirty_splits"] = a

# ---- Part B: bootstrap on out-of-fold predictions --------------------------------------------------
ok = {"model": pd.DataFrame(index=full.index, columns=list(TARGETS), dtype=bool),
      "rule": pd.DataFrame(index=full.index, columns=list(TARGETS), dtype=bool),
      "typical": pd.DataFrame(index=full.index, columns=list(TARGETS), dtype=bool)}
for tr, va in KFold(5, shuffle=True, random_state=0).split(full):
    train, val = full.iloc[tr], full.iloc[va]
    preds = {"model": Designer.train(train).design_batch(val), "rule": rule_of_thumb(val), "typical": typical_design(train, val)}
    for who, p in preds.items():
        for t in TARGETS:
            ok[who].loc[val.index, t] = dev.judge(val[t], p[t], t)["ok"].to_numpy()
success = {who: df.astype(bool).all(axis=1).to_numpy().astype(float) for who, df in ok.items()}
pv_ok = {who: df["pv_kwp"].astype(bool).to_numpy().astype(float) for who, df in ok.items()}
bat_ok = {who: df["battery_kwh"].astype(bool).to_numpy().astype(float) for who, df in ok.items()}

rng = np.random.default_rng(0)
idx = rng.integers(0, len(full), size=(N_BOOT, len(full)))


def boot(x, y=None):
    est = x[idx].mean(axis=1) if y is None else (x[idx] - y[idx]).mean(axis=1)
    return {"point": float((x if y is None else x - y).mean()), "ci_low": float(np.percentile(est, 2.5)), "ci_high": float(np.percentile(est, 97.5))}


b = {}
for name, arr in (("whole", success), ("pv", pv_ok), ("battery", bat_ok)):
    b[f"{name}_model"] = boot(arr["model"])
    b[f"{name}_typical"] = boot(arr["typical"])
    b[f"{name}_rule"] = boot(arr["rule"])
    b[f"{name}_model_minus_typical"] = boot(arr["model"], arr["typical"])
    b[f"{name}_model_minus_rule"] = boot(arr["model"], arr["rule"])
report["B_bootstrap_out_of_fold"] = b

Path("reports").mkdir(exist_ok=True)
Path("reports/repeated_splits.json").write_text(json.dumps(report, indent=2, default=float))

p = lambda x: f"{x:5.1%}"
print(f"projects: {report['n_projects']}\n")
print(f"A. {N_SPLITS} random 80/20 splits: mean (sd) [2.5%-97.5% across splits]")
for metric, label in (("whole", "Whole design"), ("pv", "PV within tolerance"), ("battery", "Battery within tolerance")):
    print(f"  {label}")
    for who, nm in (("model", "our model"), ("typical", "typical design"), ("rule", "rule of thumb")):
        s = a[f"{who}_{metric}"]
        print(f"    {nm:15} {p(s['mean'])} ({s['sd']*100:.1f})  [{p(s['p2_5'])} - {p(s['p97_5'])}]")
    g = a[f"model_minus_typical_{metric}"]
    print(f"    model minus typical design: {g['mean']*100:+.1f} points [{g['p2_5']*100:+.1f} to {g['p97_5']*100:+.1f}]")
print(f"  splits where the model beats the typical design on whole design: {a['splits_where_model_beats_typical_on_whole_design']} of {N_SPLITS}")
print(f"\nB. Bootstrap over {len(full)} projects ({N_BOOT} resamples), out-of-fold predictions: estimate [95% interval]")
for metric, label in (("whole", "Whole design"), ("pv", "PV"), ("battery", "Battery")):
    print(f"  {label}")
    for who, nm in (("model", "our model"), ("typical", "typical design"), ("rule", "rule of thumb")):
        s = b[f"{metric}_{who}"]
        print(f"    {nm:15} {p(s['point'])}  [{p(s['ci_low'])} - {p(s['ci_high'])}]")
    for who, nm in (("typical", "typical design"), ("rule", "rule of thumb")):
        s = b[f"{metric}_model_minus_{who}"]
        print(f"    model minus {nm}: {s['point']*100:+.1f} points [{s['ci_low']*100:+.1f} to {s['ci_high']*100:+.1f}]")
