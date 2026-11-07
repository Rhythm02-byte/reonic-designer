"""Where and why our designs differ from the experts.

    python scripts/deviation_analysis.py            # tables + reports/deviation_analysis.json
    python scripts/deviation_analysis.py --chart    # also reports/deviation_chart.png (needs the `analysis` extra)

Predictions are out-of-fold: 5-fold cross-validation over all projects, so every project is scored by a model
that never saw it. That gives about 1,600 rows instead of the 319 in a single 80/20 test split, which is too
few to compare home types. Folds are random (not held-out installers); see scripts/unseen_installer.py for that.

A component "agrees" under the same rule as evaluate.py: same include/exclude and, for PV, battery and heat pump,
a size within the tolerance. Real export only (data/raw).
"""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import KFold

from reonic import data
from reonic.engine import Designer
from reonic.evaluate import TOLERANCE
from reonic.schema import INPUT_FIELDS, LABEL, TARGETS

SEED = 0
MIN_GROUP = 40  # smallest group worth reporting a rate for
COMPONENTS = ("pv_kwp", "battery_kwh", "wallbox_kw", "heat_pump_kw")


def canonical(df: pd.DataFrame) -> pd.DataFrame:
    for c in INPUT_FIELDS:
        if c not in df.columns:
            df[c] = np.nan
    df[list(TARGETS)] = df[list(TARGETS)].apply(pd.to_numeric, errors="coerce").clip(lower=0)
    return df


def out_of_fold(full: pd.DataFrame) -> pd.DataFrame:
    pred = pd.DataFrame(index=full.index, columns=list(TARGETS), dtype=float)
    for tr, va in KFold(5, shuffle=True, random_state=SEED).split(full):
        d = Designer.train(full.iloc[tr])
        pred.loc[full.index[va], list(TARGETS)] = d.design_batch(full.iloc[va]).to_numpy()
    return pred


def judge(truth: pd.Series, pred: pd.Series, t: str) -> pd.DataFrame:
    """Per project: agrees?, and what kind of disagreement."""
    y, p = truth.to_numpy(float), pred.to_numpy(float)
    known = ~np.isnan(y)
    has_y, has_p = (y > 0) | ~known, p > 0
    rel = np.abs(p - np.nan_to_num(y)) / np.where(y > 0, y, 1)
    tol = TOLERANCE[t]
    size_ok = ~known | (rel <= tol)
    ok = np.where(has_y, has_p & size_ok, ~has_p)
    kind = np.select(
        [ok, has_y & ~has_p, ~has_y & has_p, has_y & has_p & known & (p < y), has_y & has_p & known & (p > y)],
        ["agrees", "missed (expert had it, we did not)", "extra (we added it, expert did not)", "too small", "too large"], "other")
    return pd.DataFrame({"ok": ok, "kind": kind, "rel_err": np.where(has_y & has_p & known, (p - np.nan_to_num(y)) / np.where(y > 0, y, 1), np.nan)},
                        index=truth.index)


def bands(df: pd.DataFrame) -> pd.DataFrame:
    c = df["annual_consumption_kwh"]
    band = pd.Series("unknown", index=df.index)
    band[c < 3000] = "<3,000 kWh"
    band[(c >= 3000) & (c < 4500)] = "3,000-4,499 kWh"
    band[c == 4500] = "exactly 4,500 kWh"
    band[(c > 4500) & (c < 8000)] = "4,501-7,999 kWh"
    band[c >= 8000] = ">=8,000 kWh"
    ev = df["has_ev"].astype(float).fillna(0).eq(1)
    return pd.DataFrame({
        "installer": df["installer_id"],
        "consumption": band,
        "EV": np.where(ev, "has an EV", "no EV"),
        "existing PV": np.where(df["existing_pv_kwp"].fillna(0) > 0, "has PV", "no PV"),
        "offers per project": np.where(df["n_options"] > 1, "2+ offers", "1 offer"),
        "PV size source": df["pv_source"],
        "heating known": np.where(df["heating_type"].notna(), "heating type known", "heating type unknown"),
    }, index=df.index)


def main(chart: bool) -> None:
    full = canonical(data.load_raw("data/raw"))
    pred = out_of_fold(full)
    judged = {t: judge(full[t], pred[t], t) for t in TARGETS}
    ok = pd.DataFrame({t: judged[t]["ok"] for t in TARGETS})
    whole = ok.all(axis=1)
    groups = bands(full)

    print(f"projects: {len(full)}  (out-of-fold, 5 folds)")
    print("\nOverall agreement with the expert:")
    overall = {t: float(ok[t].mean()) for t in TARGETS}
    overall["whole design"] = float(whole.mean())
    for k, v in overall.items():
        print(f"  {k:<14}{v:6.1%}")

    rows = []
    for dim in groups.columns:
        for val, idx in groups.groupby(dim).groups.items():
            if len(idx) < MIN_GROUP:
                continue
            row = {"dimension": dim, "group": val, "n": len(idx), "whole design agrees": float(whole[idx].mean())}
            for t in COMPONENTS:
                row[f"{t} agrees"] = float(ok.loc[idx, t].mean())
            rows.append(row)
    table = pd.DataFrame(rows)

    pd.set_option("display.width", 220)
    for dim, g in table.groupby("dimension", sort=False):
        print(f"\n== by {dim}")
        print(g.drop(columns="dimension").round(3).to_string(index=False))

    # Biggest patterns: excess misses = how many more misses than the overall rate predicts
    patterns = []
    for _, r in table.iterrows():
        for t in ("pv_kwp", "battery_kwh", "wallbox_kw"):
            miss, base = 1 - r[f"{t} agrees"], 1 - overall[t]
            patterns.append({"component": t, "dimension": r["dimension"], "group": r["group"], "n": int(r["n"]),
                             "miss_rate": miss, "overall_miss_rate": base, "excess_misses": (miss - base) * r["n"]})
    pat = pd.DataFrame(patterns).sort_values("excess_misses", ascending=False)
    print("\nLargest patterns (excess misses over the component's overall rate):")
    print(pat.head(12).round(3).to_string(index=False))

    # What kind of miss, and which direction, per component
    print("\nKinds of disagreement:")
    kinds = {}
    for t in COMPONENTS:
        k = judged[t]["kind"].value_counts()
        kinds[t] = k.to_dict()
        print(f"  {LABEL[t]:<10}", {a: int(b) for a, b in k.items()})
    print("\nSigned size error (ours - expert) / expert, where both included it, by consumption band:")
    err = {}
    for t in ("pv_kwp", "battery_kwh"):
        e = judged[t]["rel_err"].groupby(groups["consumption"]).agg(["count", "median"])
        err[t] = {k: {"n": int(r["count"]), "median_rel_error": float(r["median"])} for k, r in e.iterrows() if r["count"] >= MIN_GROUP}
        print(f"  {LABEL[t]}:", {k: f"{v['median_rel_error']:+.0%} (n={v['n']})" for k, v in err[t].items()})

    ev = evidence(full, ok)
    print("\nEvidence for the three patterns:")
    for k, v in ev.items():
        if not k.startswith("_"):
            print(f"  {k}: {json.dumps(v, default=float)}")

    out = {"n_projects": int(len(full)), "overall_agreement": overall, "breakdown": rows,
           "patterns": pat.head(15).to_dict("records"), "kinds": kinds, "signed_error_by_consumption": err,
           "evidence": {k: v for k, v in ev.items() if not k.startswith("_")}}
    Path("reports").mkdir(exist_ok=True)
    Path("reports/deviation_analysis.json").write_text(json.dumps(out, indent=2, default=float))
    detail = full[["installer_id", "project_id", "annual_consumption_kwh", "has_ev", "existing_pv_kwp", "n_options", "pv_source"]].copy()
    for t in TARGETS:
        detail[f"{t}_expert"], detail[f"{t}_ours"], detail[f"{t}_agrees"] = full[t], pred[t], ok[t]
    detail.to_csv("reports/deviation_oof.csv", index=False)

    if chart:
        make_chart(ev)


def evidence(full: pd.DataFrame, ok: pd.DataFrame) -> dict:
    """The numbers behind the three patterns we write up. Each is a test of an explanation, not an assumption."""
    ev = full["has_ev"].astype(float).fillna(0).eq(1)
    out: dict = {}

    # Pattern 1 (PV): how much does the expert's own PV size vary for near-identical homes?
    near = full[full["annual_consumption_kwh"].between(4000, 5000) & (full["annual_consumption_kwh"] != 4500) & ~ev
                & (full["existing_pv_kwp"].fillna(0) == 0) & (full["pv_kwp"] > 0)]
    spread = {}
    for name, g in list(near.groupby("installer_id")) + [("both", near)]:
        e, med = g["pv_kwp"], g["pv_kwp"].median()
        spread[name] = {"n": int(len(g)), "p10": float(e.quantile(.1)), "p50": float(med), "p90": float(e.quantile(.9)),
                        "share_within_20pct_of_median": float(((e - med).abs() / med <= 0.20).mean()),
                        "model_agrees": float(ok.loc[g.index, "pv_kwp"].mean())}
    out["pv_spread_near_identical_homes"] = spread
    out["_near_pv_values"] = near["pv_kwp"].tolist()

    # Pattern 2 (wallbox): how many wallbox homes does an EV flag explain?
    w = full["wallbox_kw"] > 0
    out["wallbox"] = {"wallbox_homes": int(w.sum()), "share_of_homes_with_wallbox": float(w.mean()),
                      "share_of_homes_with_ev_flag": float(ev.mean()),
                      "share_of_wallbox_homes_with_ev_flag": float(ev[w].mean()),
                      "ev_homes": int(ev.sum()), "ev_homes_with_wallbox": float(w[ev].mean()),
                      "ev_homes_without_wallbox_already_having_one": int((ev & ~w & full["has_existing_wallbox"].astype(float).fillna(0).eq(1)).sum()),
                      "ev_homes_without_wallbox": int((ev & ~w).sum())}

    # Pattern 3 (battery): installer, and the 4,500 kWh placeholder inside each installer
    place = full["annual_consumption_kwh"] == 4500
    rows = {}
    for inst, g in full.groupby("installer_id"):
        for flag, h in g.groupby(place[g.index]):
            rows[f"{inst} | {'demand = 4,500 kWh' if flag else 'other demand'}"] = {
                "n": int(len(h)), "battery_agrees": float(ok.loc[h.index, "battery_kwh"].mean()),
                "pv_agrees": float(ok.loc[h.index, "pv_kwp"].mean()), "wallbox_agrees": float(ok.loc[h.index, "wallbox_kw"].mean())}
    out["battery_by_installer_and_placeholder"] = rows
    sizes = {}
    for inst, g in full[full["battery_kwh"] > 0].groupby("installer_id"):
        vc = g["battery_kwh"].round(1).value_counts(normalize=True)
        sizes[inst] = {"distinct_sizes": int(vc.size), "top3_share": float(vc.head(3).sum()), "top3": [float(k) for k in vc.head(3).index]}
    out["battery_size_concentration"] = sizes

    # Weaker signal: projects with several offers (option choice is a guess)
    multi = full["n_options"] > 1
    out["multiple_offers"] = {"n_multi": int(multi.sum()), "whole_design_multi": float(ok.loc[multi].all(axis=1).mean()),
                              "whole_design_single": float(ok.loc[~multi].all(axis=1).mean())}
    return out


def make_chart(ev: dict, path: str = "reports/deviation_chart.png") -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 3, figsize=(15, 4.6))
    ink, accent, muted = "#1f2937", "#2563eb", "#9ca3af"

    # 1. PV: the experts' own spread
    both = ev["pv_spread_near_identical_homes"]["both"]
    ax = axes[0]
    ax.hist(ev["_near_pv_values"], bins=14, color=muted, edgecolor="white")
    ax.axvspan(both["p50"] * 0.8, both["p50"] * 1.2, color=accent, alpha=0.18)
    ax.axvline(both["p50"], color=accent, lw=2)
    ax.set_title(f"1. PV: experts vary for near-identical homes\n(demand 4,000-5,000 kWh, no EV, no PV, n={both['n']})", fontsize=10, color=ink)
    ax.set_xlabel("expert PV size (kWp)")
    ax.set_ylabel("homes")
    ax.text(0.97, 0.95, f"a single typical size ({both['p50']:.1f} kWp)\nmatches within ±20% for\n{both['share_within_20pct_of_median']:.0%} (shaded)\nour model: {both['model_agrees']:.0%}",
            transform=ax.transAxes, ha="right", va="top", fontsize=9, color=ink)

    # 2. Wallbox: how much an EV flag explains
    wb = ev["wallbox"]
    ax = axes[1]
    vals = [wb["share_of_wallbox_homes_with_ev_flag"], 1 - wb["share_of_wallbox_homes_with_ev_flag"]]
    bars = ax.bar(["wallbox home\nhas an EV flag", "wallbox home\nno EV flag"], vals, color=[accent, muted])
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + 0.02, f"{v:.0%}", ha="center", fontsize=10, color=ink)
    ax.set_ylim(0, 1.05)
    ax.set_title(f"2. Wallbox: the EV rule cannot see most of them\n({wb['wallbox_homes']} homes with a wallbox; only {wb['share_of_homes_with_ev_flag']:.0%} of all homes have an EV flag)",
                 fontsize=10, color=ink)
    ax.set_ylabel("share of wallbox homes")

    # 3. Battery: installer x placeholder demand
    rows = ev["battery_by_installer_and_placeholder"]
    ax = axes[2]
    labels, vals, colors = [], [], []
    for k, r in rows.items():
        inst, kind = k.split(" | ")
        labels.append(f"{inst}\n{'demand = 4,500' if '4,500' in kind else 'other demand'}\nn={r['n']}")
        vals.append(r["battery_agrees"])
        colors.append(muted if "4,500" in kind else accent)
    bars = ax.bar(labels, vals, color=colors)
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + 0.02, f"{v:.0%}", ha="center", fontsize=10, color=ink)
    ax.set_ylim(0, 0.8)
    ax.set_title("3. Battery: placeholder demand hurts at one installer\n(share of homes where we match the expert)", fontsize=10, color=ink)
    ax.tick_params(axis="x", labelsize=8)

    for ax in axes:
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)
    fig.suptitle("Where we disagree with the experts, and why (out-of-fold predictions, 1,593 projects)", fontsize=12, color=ink, y=1.02)
    fig.tight_layout()
    fig.savefig(path, dpi=160, bbox_inches="tight")
    print(f"\nchart: {path}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--chart", action="store_true")
    main(ap.parse_args().chart)
