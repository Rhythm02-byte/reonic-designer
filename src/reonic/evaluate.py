"""How close are we to the expert designs on projects the model has not seen?"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import f1_score, fbeta_score, precision_score, recall_score
from sklearn.model_selection import GroupShuffleSplit, train_test_split

from .baseline import rule_of_thumb, typical_design
from .engine import Designer
from .schema import INPUT_FIELDS, TARGETS

# A size counts as "matches the expert" if within this relative tolerance (and both agree on include/exclude).
# Wallbox: only include/exclude counts (11 vs 22 kW is a customer choice, not design skill).
TOLERANCE = {"pv_kwp": 0.20, "battery_kwh": 0.25, "heat_pump_kw": 0.25, "wallbox_kw": float("inf")}


def metrics(pred: pd.DataFrame, truth: pd.DataFrame) -> dict:
    out, all_ok = {}, np.ones(len(truth), dtype=bool)
    for t in TARGETS:
        y, p = truth[t].to_numpy(float), pred[t].to_numpy(float)
        known = ~np.isnan(y)  # NaN truth = offered but size unknown: only include/exclude is scored
        has_y, has_p = (y > 0) | ~known, p > 0
        both = has_y & has_p & known
        rel = np.abs(p - np.nan_to_num(y)) / np.where(y > 0, y, 1)
        ok = np.where(has_y, has_p & (~known | (rel <= TOLERANCE[t])), ~has_p)
        all_ok &= ok
        out[t] = {
            "include_accuracy": float((has_y == has_p).mean()),
            "include_precision": float(precision_score(has_y, has_p, zero_division=0)),
            "include_recall": float(recall_score(has_y, has_p, zero_division=0)),
            "include_f1": float(f1_score(has_y, has_p, zero_division=0)),
            # F2 weights recall twice as much as precision: a missed component costs more than an extra one.
            "include_f2": float(fbeta_score(has_y, has_p, beta=2.0, zero_division=0)),
            "size_mae": float(np.abs(p - y)[both].mean()) if both.any() else None,
            "expert_include_rate": float(has_y.mean()),
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
    ours, base, typical = designer.design_batch(test), rule_of_thumb(test), typical_design(train, test)
    report = {"n_train": len(train), "n_test": len(test), "split": group_col or "random",
              "model": metrics(ours, test), "baseline": metrics(base, test), "typical": metrics(typical, test)}
    if "installer_id" in test.columns and test["installer_id"].nunique() > 1:
        report["by_installer"] = {str(k): metrics(ours.loc[g.index], g)["whole_design_within_tolerance"]
                                  for k, g in test.groupby("installer_id")}

    out = Path(out_dir)
    out.mkdir(exist_ok=True)
    (out / "eval.json").write_text(json.dumps(report, indent=2))
    keep = [c for c in ("installer_id", "project_id", "n_options", "pv_source") if c in test.columns]
    detail = test[keep + [c for c in INPUT_FIELDS if c in test.columns]].copy()
    for t in TARGETS:
        detail[f"{t}_expert"], detail[f"{t}_ours"], detail[f"{t}_baseline"] = test[t], ours[t], base[t]
    detail.to_csv(out / "test_predictions.csv")  # input to the "where do we deviate" analysis
    return report


def print_report(r: dict) -> None:
    print(f"train={r['n_train']}  test={r['n_test']}  split={r['split']}")
    print("baseline = naive sizing rule; typical = ignores the home, proposes what most homes got")
    print(f"{'':14}{'metric':26}{'model':>10}{'baseline':>10}{'typical':>10}")
    for t in TARGETS:
        for k in ("expert_include_rate", "include_accuracy", "include_f1", "size_median_rel_error", "within_tolerance"):
            m, b, y = r["model"][t][k], r["baseline"][t][k], r["typical"][t][k]
            fmt = lambda x: "  -" if x is None else f"{x:.3f}"
            print(f"{t:14}{k:26}{fmt(m):>10}{fmt(b):>10}{fmt(y):>10}")
    print()
    print("wallbox include decision (precision, recall, F1, F2 with beta=2):")
    print(f"{'':14}{'metric':26}{'model':>10}{'baseline':>10}")
    for k in ("include_precision", "include_recall", "include_f1", "include_f2"):
        print(f"{'wallbox_kw':14}{k:26}{r['model']['wallbox_kw'][k]:>10.3f}{r['baseline']['wallbox_kw'][k]:>10.3f}")
    print()
    print(f"{'whole design within tolerance':40}{r['model']['whole_design_within_tolerance']:>10.3f}"
          f"{r['baseline']['whole_design_within_tolerance']:>10.3f}{r['typical']['whole_design_within_tolerance']:>10.3f}")
    for k, v in r.get("by_installer", {}).items():
        print(f"  installer {k}: whole design within tolerance {v:.3f}")
