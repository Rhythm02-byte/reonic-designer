"""Does choosing the size that fits the most plausible expert sizes beat a plain mean prediction?

    python scripts/coverage_sizing.py

Same 5-fold out-of-fold protocol and bootstrap as scripts/repeated_splits.py, comparing sizing="mean" with
sizing="coverage" (quantile models + coverage_size). Everything else is identical. Real export only.
Writes reports/coverage_sizing.json.
"""
import importlib.util
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import KFold

from reonic import data
from reonic.engine import Designer
from reonic.schema import INPUT_FIELDS, TARGETS

_spec = importlib.util.spec_from_file_location("deviation_analysis", Path(__file__).resolve().parent / "deviation_analysis.py")
dev = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(dev)

full = data.load_raw("data/raw")
for c in INPUT_FIELDS:
    if c not in full.columns:
        full[c] = np.nan
full[list(TARGETS)] = full[list(TARGETS)].apply(pd.to_numeric, errors="coerce").clip(lower=0)
full = full.reset_index(drop=True)

ok = {m: pd.DataFrame(index=full.index, columns=list(TARGETS), dtype=bool) for m in ("mean", "coverage")}
secs = {"mean": 0.0, "coverage": 0.0}
for tr, va in KFold(5, shuffle=True, random_state=0).split(full):
    train, val = full.iloc[tr], full.iloc[va]
    for m in ok:
        t0 = time.time()
        d = Designer.train(train, sizing=m)
        pred = d.design_batch(val)
        secs[m] += time.time() - t0
        for t in TARGETS:
            ok[m].loc[val.index, t] = dev.judge(val[t], pred[t], t)["ok"].to_numpy()
arr = {m: {"whole": df.astype(bool).all(axis=1).to_numpy().astype(float),
           "pv": df["pv_kwp"].astype(bool).to_numpy().astype(float),
           "battery": df["battery_kwh"].astype(bool).to_numpy().astype(float)} for m, df in ok.items()}
idx = np.random.default_rng(0).integers(0, len(full), size=(2000, len(full)))
rep = {"n_projects": len(full), "seconds_train_and_predict_5_folds": secs}
for k in ("whole", "pv", "battery"):
    x, y = arr["coverage"][k], arr["mean"][k]
    est = (x[idx] - y[idx]).mean(axis=1)
    rep[k] = {"mean": float(y.mean()), "coverage": float(x.mean()), "gain": float((x - y).mean()),
              "ci_low": float(np.percentile(est, 2.5)), "ci_high": float(np.percentile(est, 97.5))}
Path("reports").mkdir(exist_ok=True)
Path("reports/coverage_sizing.json").write_text(json.dumps(rep, indent=2))
print(f"{len(full)} projects, out-of-fold; time for 5 folds: mean {secs['mean']:.0f}s, coverage {secs['coverage']:.0f}s")
for k in ("whole", "pv", "battery"):
    r = rep[k]
    print(f"{k:8} mean {r['mean']:.1%}  coverage {r['coverage']:.1%}  gain {r['gain']*100:+.1f} points [{r['ci_low']*100:+.1f} to {r['ci_high']*100:+.1f}]")
