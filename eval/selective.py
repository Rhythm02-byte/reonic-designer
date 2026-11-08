"""Selective prediction (business view): how often is the WHOLE design right on the homes the model is most sure about?

Served config (config/policy.json), four expanding 2025 time folds (train < quarter q, validate on q). Never reads 2026.
The confidence score is fixed in advance, not tuned: product over parts of the include certainty max(p, 1-p), times
1 / (1 + relative width of the PV p10-p90 range). Homes are ranked by it; we report the whole-design hit rate of the most
confident 25 / 50 / 75 / 100 %, for ours and for the installer's usual design (B0) on the same homes.

    node scripts/py.mjs eval/selective.py          (writes the "selective" block of eval/results/latest.json)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
import run as R  # noqa: E402
from honesty import b0_frame  # noqa: E402
from metrics import whole_hits  # noqa: E402

from engine.policy import physics  # noqa: E402
from engine.policy.designer import Designer  # noqa: E402
from engine.policy.features import TARGETS  # noqa: E402

COVERAGE = (0.25, 0.5, 0.75, 1.0)
QUARTERS = [(pd.Timestamp(f"2025-{m:02d}-01"), pd.Timestamp(f"2025-{m + 3:02d}-01") if m < 10 else pd.Timestamp("2026-01-01"))
            for m in (1, 4, 7, 10)]


def confidence(sizes: pd.DataFrame, extra: pd.DataFrame) -> np.ndarray:
    c = np.ones(len(sizes))
    for t in TARGETS:
        p = extra[f"p_{t}"].to_numpy(float)
        c *= np.maximum(p, 1 - p)
    pv = sizes["pv_kwp"].to_numpy(float)
    width = (extra["hi_pv_kwp"].to_numpy(float) - extra["lo_pv_kwp"].to_numpy(float)) / np.where(pv > 0, pv, 1)
    return c / (1 + np.where(pv > 0, np.nan_to_num(width), 0.0))


def run(D: pd.DataFrame) -> dict:
    pre = D[D.when <= R.CUTOFF]
    assert pre.when.max() <= R.CUTOFF  # the 2026 test is never touched
    conf, ours, b0 = [], [], []
    for start, end in QUARTERS:
        train, val = pre[pre.when < start], pre[(pre.when >= start) & (pre.when < end)]
        if len(train) < 50 or len(val) == 0:
            continue
        sizes, extra = Designer.train(train).design_batch_full(val)
        truth = val[list(TARGETS)]
        conf.append(confidence(sizes, extra))
        ours.append(whole_hits(sizes, truth))
        b0.append(whole_hits(b0_frame(train, val), truth))
        print(f"fold {start.date()}: n={len(val)} whole ours {ours[-1].mean():.3f} B0 {b0[-1].mean():.3f}", flush=True)
    c, o, b = np.concatenate(conf), np.concatenate(ours), np.concatenate(b0)
    order = np.argsort(-c, kind="stable")
    rows = []
    for cov in COVERAGE:
        k = max(1, int(round(cov * len(order))))
        idx = order[:k]
        rows.append({"coverage": cov, "n": int(k), "ours": float(o[idx].mean()), "b0": float(b[idx].mean())})
        print(f"most confident {int(cov * 100):>3}% (n={k}): whole ours {100 * o[idx].mean():.1f}%  B0 {100 * b[idx].mean():.1f}%")
    return {"setting": "served config; 4 expanding 2025 quarter folds; confidence fixed in advance (see eval/selective.py)",
            "nHomes": int(len(c)), "curve": rows}


def main() -> None:
    cache = Path(__file__).resolve().parents[1] / "data" / "processed" / "physics_cache.pkl"
    physics.load_cache(cache)
    _, _, D = R.load(Path("data/processed"))
    res = run(D)
    physics.save_cache(cache)
    out = R.RESULTS / "latest.json"
    latest = json.loads(out.read_text(encoding="utf-8"))
    latest["selective"] = res
    out.write_text(json.dumps(latest, indent=2), encoding="utf-8")
    print("wrote selective block to", out)


if __name__ == "__main__":
    main()
