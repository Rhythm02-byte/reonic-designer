"""How close are we to the expert designs on projects the model has not seen?"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import f1_score
from sklearn.model_selection import GroupShuffleSplit, train_test_split

from .baseline import rule_of_thumb
from .engine import Designer
from .schema import INPUT_FIELDS, TARGETS

# A size counts as "matches the expert" if within this relative tolerance (and both agree on include/exclude).
TOLERANCE = {"pv_kwp": 0.20, "battery_kwh": 0.25, "heat_pump_kw": 0.25}


def metrics(pred: pd.DataFrame, truth: pd.DataFrame) -> dict:
    out, all_ok = {}, np.ones(len(truth), dtype=bool)
    for t in TARGETS:
        y, p = truth[t].to_numpy(float), pred[t].to_numpy(float)
        has_y, has_p = y > 0, p > 0
        both = has_y & has_p
        rel = np.abs(p - y) / np.where(y > 0, y, 1)
        ok = np.where(has_y, has_p & (rel <= TOLERANCE[t]), ~has_p)
        all_ok &= ok
        out[t] = {
            "include_accuracy": float((has_y == has_p).mean()),
            "include_f1": float(f1_score(has_y, has_p, zero_division=0)),
            "size_mae": float(np.abs(p - y)[both].mean()) if both.any() else None,
            "size_median_rel_error": float(np.median(rel[both])) if both.any() else None,
            "within_tolerance": float(ok.mean()),
        }
    out["whole_design_within_tolerance"] = float(all_ok.mean())
    return out


def split(df: pd.DataFrame, test_size: float, seed: int, group_col: str | None):
    """Use a group split (e.g. by installer) when available, so we test on genuinely unseen projects."""
    if group_col and group_col in df.columns:
        tr, te = next(GroupShuffleSplit(1, test_size=test_size, random_state=seed).split(df, groups=df[group_col]))
        return df.iloc[tr], df.iloc[te]
    return train_test_split(df, test_size=test_size, random_state=seed)


def run(df: pd.DataFrame, out_dir: str | Path = "reports", test_size: float = 0.2, seed: int = 0,
        group_col: str | None = None) -> dict:
    train, test = split(df, test_size, seed, group_col)
    designer = Designer.train(train)
    ours, base = designer.design_batch(test), rule_of_thumb(test)
    report = {"n_train": len(train), "n_test": len(test),
              "model": metrics(ours, test), "baseline": metrics(base, test)}

    out = Path(out_dir)
    out.mkdir(exist_ok=True)
    (out / "eval.json").write_text(json.dumps(report, indent=2))
    detail = test[[c for c in INPUT_FIELDS if c in test.columns]].copy()
    for t in TARGETS:
        detail[f"{t}_expert"], detail[f"{t}_ours"], detail[f"{t}_baseline"] = test[t], ours[t], base[t]
    detail.to_csv(out / "test_predictions.csv")  # input to the "where do we deviate" analysis
    return report


def print_report(r: dict) -> None:
    print(f"train={r['n_train']}  test={r['n_test']}")
    print(f"{'':14}{'metric':26}{'model':>10}{'baseline':>10}")
    for t in TARGETS:
        for k in ("include_accuracy", "include_f1", "size_median_rel_error", "within_tolerance"):
            m, b = r["model"][t][k], r["baseline"][t][k]
            fmt = lambda x: "  -" if x is None else f"{x:.3f}"
            print(f"{t:14}{k:26}{fmt(m):>10}{fmt(b):>10}")
    print(f"{'whole design within tolerance':40}{r['model']['whole_design_within_tolerance']:>10.3f}"
          f"{r['baseline']['whole_design_within_tolerance']:>10.3f}")
