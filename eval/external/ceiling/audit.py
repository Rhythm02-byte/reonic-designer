"""Aggregate-only collision bounds and frozen scoring sensitivity; never selects a model.

Run: node scripts/py.mjs eval/external/ceiling/audit.py
Uses only canonical ETL parquet, never reads raw exports. Defaults exclude 2026.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT / "services/engine"), str(ROOT / "eval")]
os.environ["OFFLINE"] = "1"

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from threadpoolctl import threadpool_limits

import run as evaluation
from metrics import TARGETS, TOLERANCE, policy_metrics, pred_frame
from engine.policy.designer import Designer, load_config
from engine.policy import physics
from engine.policy.features import INPUT_COLS, features


def whole_hits(pred, truth, module_mode="relative"):
    """Same inclusion/unknown convention as policy_metrics; two frozen PV alternatives."""
    p, y = np.asarray(pred, float), np.asarray(truth, float)
    ok = np.ones(len(y), dtype=bool)
    for j, target in enumerate(TARGETS):
        known = ~np.isnan(y[:, j])
        has_y, has_p = (y[:, j] > 0) | ~known, p[:, j] > 0
        if target == "wallbox_kw":
            size_ok = np.ones(len(y), dtype=bool)
        else:
            atol = TOLERANCE[target] * np.nan_to_num(y[:, j])
            if target == "pv_kwp" and module_mode == "one_module_only":
                atol = np.full(len(y), 0.45)
            if target == "pv_kwp" and module_mode == "relative_or_one_module":
                atol = np.maximum(atol, 0.45)
            size_ok = ~known | (np.abs(p[:, j] - y[:, j]) <= atol)
        ok &= np.where(has_y, has_p & size_ok, ~has_p)
    return ok


def maximum_tolerance_overlap(truth):
    """Exact max number of targets matched by ONE arbitrary nonnegative prediction.

    Each observed label gives a Cartesian product of intervals of acceptable predictions.
    A maximum overlap exists at a lower interval endpoint (or zero/tiny positive for
    absent/unknown-only labels). Intersect unique membership bitsets per dimension.
    This relaxes catalogue/rules, so it is an optimistic empirical upper bound.
    """
    y = np.asarray(truth, dtype=float)
    n = len(y)
    if n <= 1:
        return n
    by_dimension = []
    for j, target in enumerate(TARGETS):
        col = y[:, j]
        if target == "wallbox_kw":
            candidates = [0.0, 1.0]
        else:
            candidates = [0.0, np.nextafter(0.0, 1.0)]
            candidates.extend(col[(col > 0) & np.isfinite(col)] * (1 - TOLERANCE[target]))
        masks = set()
        for value in candidates:
            known, positive = ~np.isnan(col), col > 0
            if target == "wallbox_kw":
                good = ((positive | ~known) == (value > 0))
            else:
                good = np.where(positive | ~known,
                    (value > 0) & (~known | (np.abs(value - col) <= TOLERANCE[target] * col + 1e-10)), value == 0)
            mask = sum(1 << int(i) for i in np.flatnonzero(good))
            if mask:
                masks.add(mask)
        # A subset can never outperform its superset in later intersections.
        ordered = sorted(masks, key=int.bit_count, reverse=True)
        maximal = []
        for mask in ordered:
            if not any(mask & other == mask for other in maximal):
                maximal.append(mask)
        by_dimension.append(maximal)
    states = {(1 << n) - 1}
    for masks in sorted(by_dimension, key=len):
        states = {s & m for s in states for m in masks if s & m}
    return max(map(int.bit_count, states), default=0)


def collision_summary(X, Y):
    # Internal grouping only: neither keys, row ids, labels nor memberships are saved.
    groups = X.groupby(list(X.columns), dropna=False, sort=False).indices.values()
    best = duplicate_best = duplicate_n = duplicate_groups = singleton_n = 0
    largest = 0
    for indices in groups:
        count = len(indices)
        largest = max(largest, count)
        matched = maximum_tolerance_overlap(Y.iloc[indices])
        best += matched
        if count > 1:
            duplicate_groups += 1
            duplicate_n += count
            duplicate_best += matched
        else:
            singleton_n += 1
    return {"n": len(X), "groups": singleton_n + duplicate_groups,
        "singleton_rows": singleton_n, "duplicate_groups": duplicate_groups,
        "duplicate_rows": duplicate_n, "largest_group": largest,
        "maximum_empirical_matched": best, "empirical_upper_bound": best / len(X),
        "duplicate_subset_upper_bound": duplicate_best / duplicate_n if duplicate_n else None,
        "minimum_unavoidable_empirical_errors": len(X) - best}


def option_targets(options):
    """Mirror training_frame's documented presence/unknown-size convention for ANY option."""
    has_solar = options.has_solar_tech if "has_solar_tech" in options else False
    return pd.DataFrame({
        "pv_kwp": np.where(options.has_pv, options.kwp, np.where(has_solar, np.nan, 0.0)),
        "battery_kwh": np.where(options.has_battery, options.battery_kwh, 0.0),
        "heat_pump_kw": np.where(options.has_heatpump, np.where(options.hp_kw > 0, options.hp_kw, np.nan), 0.0),
        "wallbox_kw": np.where(options.has_wallbox, np.where(options.wallbox_kw.notna() & (options.wallbox_kw > 0), options.wallbox_kw, 11.0), 0.0),
    }, index=options.index)


def score_options(pred, test, options):
    ids = list(test.project_id)
    pp = pred.set_axis(ids)
    options = options[options.project_id.isin(ids)]
    op = pp.loc[list(options.project_id)].to_numpy()
    yy = option_targets(options).to_numpy()
    hits = pd.Series(whole_hits(op, yy), index=options.project_id).groupby(level=0).any()
    return float(hits.reindex(ids, fill_value=False).mean())


def score_one(pred, test, options):
    y = test[list(TARGETS)]
    strict = whole_hits(pred, y)
    # Assert checker has the production semantics, within floating endpoint precision.
    assert abs(float(strict.mean()) - policy_metrics(pred, y)["wholeDesignWithinTolerance"]) < 1e-9
    return {"primary_relative": float(strict.mean()),
        "primary_relative_or_one_module": float(whole_hits(pred, y, "relative_or_one_module").mean()),
        "primary_one_module_only": float(whole_hits(pred, y, "one_module_only").mean()),
        "any_option_relative": score_options(pred, test, options),
        "pv_relative": policy_metrics(pred, y)["pv_kwp"]["withinTolerance"]}


def score_split(P, O, D, train, test):
    jobs = evaluation.jobs_by_installer(P, O, D, train, test, min_train=20, min_test=5)
    if not jobs:
        return {"n_train": len(train), "n_test": 0, "status": "insufficient_data"}
    train = pd.concat([j.train for j in jobs])
    designer = Designer.train(train)
    collected = {"ours": [], "B0": []}
    tests = []
    for job in jobs:
        collected["ours"].append(designer.design_batch(job.test).reset_index(drop=True))
        p, _, _ = evaluation.predict("B0", job, job.test, None)
        collected["B0"].append(pred_frame(p, list(job.test.project_id)).reset_index(drop=True))
        tests.append(job.test)
    test = pd.concat(tests).reset_index(drop=True)
    scores = {name: score_one(pd.concat(preds).reset_index(drop=True), test, O) for name, preds in collected.items()}
    return {"n_train": len(train), "n_test": len(test), "models": scores,
        "ours_minus_B0": {key: scores["ours"][key] - scores["B0"][key] for key in scores["ours"]}}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=Path(__file__).with_name("results.json"))
    parser.add_argument("--random-splits", type=int, default=20)
    args = parser.parse_args()
    physics.load_cache(ROOT / "data/processed/physics_cache.pkl")
    P, O, D = evaluation.load(ROOT / "data/processed")
    # No 2026 labels or inputs are scored, grouped or used for configuration choices.
    D = D[D.when <= evaluation.CUTOFF].copy().reset_index(drop=True)
    O = O[O.project_id.isin(D.project_id)].copy()
    P = P[P.project_id.isin(D.project_id)].copy()
    X = features(D, tuple(sorted(D.installer_id.astype(str).unique())))
    served_X = features(D, tuple(sorted(D.installer_id.astype(str).unique())), physics=bool(load_config().get("features", {}).get("physics")))
    raw_cols = [c for c in INPUT_COLS if c in D]
    # Additional physically/pre-offer interpretable ETL fields; never IDs or offer/signed dates.
    # Existing-asset status can still be contaminated by planned-system entry; verify provenance
    # before using any new field for fitting. This is a representation-bound diagnostic only.
    extra_cols = ["base_price_month", "load_profile", "existing_pv_built_year", "existing_pv_tilt",
        "existing_pv_orientation", "existing_storage_built_year", "existing_wallbox_kw",
        "heating_cost_eur_year", "heating_cost_increase", "house_sqm", "house_built_year", "num_inhabitants"]
    extra_cols = [c for c in extra_cols if c in D]
    coarse = pd.DataFrame({"installer": D.installer_id, "demand_500_bin": np.floor(D.demand_kwh / 500),
        "has_ev": D.has_ev, "heating_type": D.heating_type})
    report = {"scope": "canonical projects with parts, offer date <=2025-12-31; no 2026 analysis",
        "kind": "research_diagnostic_not_model_selection", "offline": True,
        "interpretation": "Exact collisions bound this finite empirical sample for functions of the specified representation only; not a population Bayes ceiling. Singleton memorization makes bounds optimistic. Coarse grouping is not an upper bound for full-input models.",
        "pv_module_tolerance_assumption_kwp": 0.45,
        "hashes": {"script": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "policy_config": hashlib.sha256((ROOT / "services/engine/config/policy.json").read_bytes()).hexdigest()},
        "collisions": {"canonical_input_columns": collision_summary(D[raw_cols], D[list(TARGETS)]),
            "expanded_pre_offer_ETL_inputs": collision_summary(D[raw_cols + extra_cols], D[list(TARGETS)]),
            "model_base_features": collision_summary(X, D[list(TARGETS)]),
            "served_features_without_redundant_installer_prior": collision_summary(served_X, D[list(TARGETS)]),
            "coarse_diagnostic_only": collision_summary(coarse, D[list(TARGETS)])}}
    report["additional_pre_offer_field_nonmissing"] = {c: int(D[c].notna().sum()) for c in extra_cols}
    report["additional_field_caveat"] = "Physical field interpretation does not establish capture timestamp; existing assets can contain planned-system information. Do not adopt without pre-offer availability/provenance audit. Identifiers, customer keys, offer/signature dates and output-derived flags are excluded."
    print("collision analysis complete", flush=True)
    report["quarters"] = {}
    for quarter in range(1, 5):
        start = pd.Timestamp(f"2025-{(quarter - 1) * 3 + 1:02d}-01")
        end = start + pd.offsets.QuarterBegin(startingMonth=1)
        report["quarters"][f"2025Q{quarter}"] = score_split(P, O, D, D[D.when < start], D[(D.when >= start) & (D.when < end)])
        print(f"quarter {quarter} complete", flush=True)
    report["random_splits"] = []
    for seed in range(args.random_splits):
        train, test = train_test_split(D, test_size=0.2, random_state=seed)
        report["random_splits"].append({"seed": seed, **score_split(P, O, D, train, test)})
        print(f"random seed {seed} complete", flush=True)
    if report["random_splits"]:
        report["random_gap_summary"] = {key: {"mean": float(np.mean([r["ours_minus_B0"][key] for r in report["random_splits"]])),
            "sd": float(np.std([r["ours_minus_B0"][key] for r in report["random_splits"]], ddof=1)) if args.random_splits > 1 else None}
            for key in report["random_splits"][0]["ours_minus_B0"]}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({"out": str(args.out), "collisions": report["collisions"], "quarters": report["quarters"],
        "random_gap_summary": report.get("random_gap_summary")}, indent=2, allow_nan=False))


if __name__ == "__main__":
    with threadpool_limits(limits=1):
        main()
