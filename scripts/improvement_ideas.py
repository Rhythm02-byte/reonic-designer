"""Test each improvement idea the same way: 5-fold out-of-fold, bootstrap gain over the current model.

    python scripts/improvement_ideas.py                # all ideas
    python scripts/improvement_ideas.py coverage tune  # a subset (names below)

Ideas can be combined with "+" (e.g. coverage+nb_blend). All compared with the current model, sizing="mean"):
  coverage      size chosen to fit the most plausible expert sizes (scripts/coverage_sizing.py)
  ph_weight     rows with the 4,500 kWh placeholder demand count 30% in training
  ph_drop       placeholder rows dropped from training (weight 0)
  ph_flag       an "is placeholder" feature added
  installer     installer added as a feature (only helps installers seen in training)
  nosnap        battery sizes not snapped to the catalogue of common sizes
  nb_engine     the same blend done inside the engine (before rules R03/R04 and catalogue snapping): the version to ship
  nb_blend(_hi) size (after the rules, experiment only) = half (75%) neighbours, rest the model, half the median size of the 25 most similar past homes
  tune_a/tune_b regularised / shorter gradient-boosting settings
Also reports each idea on placeholder rows and on the other rows. Tuning variants were chosen after looking at these
same folds, so treat their gains as optimistic. Real export only. Writes reports/improvement_ideas.json.
"""
import importlib.util
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import KFold

from reonic import data, engine, rules
from reonic.engine import ALL_SIZES, LEGACY, Designer
from reonic.schema import INPUT_FIELDS, TARGETS

_spec = importlib.util.spec_from_file_location("deviation_analysis", Path(__file__).resolve().parent / "deviation_analysis.py")
dev = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(dev)

PLACEHOLDER = 4500.0
base_features = engine.features


def is_ph(df):
    return (pd.to_numeric(df["annual_consumption_kwh"], errors="coerce") == PLACEHOLDER).to_numpy()


def with_flag(df):
    X = base_features(df)
    X["is_placeholder"] = is_ph(df).astype(float)
    return X


def with_installer(df):
    X = base_features(df)
    X["installer_is_first"] = (df["installer_id"] == sorted(FULL_INSTALLERS)[0]).astype(float)  # two installers: one 0/1 flag
    return X


def run_variant(name, train, val):
    """`name` may combine ideas with "+", e.g. "coverage+nb_blend". nb_blend_hi gives the neighbours 75% of the weight."""
    engine.features = base_features
    kw, blend, nosnap, snap_top = dict(LEGACY, coverage_for=ALL_SIZES), 0.0, False, None  # base = the old default
    for part in name.split("+"):
        if part == "coverage":
            kw["sizing"] = "coverage"  # all three sizes
        elif part == "ph_weight":
            kw["sample_weight"] = np.where(is_ph(train), 0.3, 1.0)
        elif part == "ph_drop":
            kw["sample_weight"] = np.where(is_ph(train), 0.0, 1.0)
        elif part == "ph_flag":
            engine.features = with_flag
        elif part == "installer":
            engine.features = with_installer
        elif part == "tune_a":
            kw["params"] = dict(max_leaf_nodes=15, min_samples_leaf=40, l2_regularization=1.0)
        elif part == "tune_b":
            kw["params"] = dict(max_iter=100, learning_rate=0.05, max_depth=4, min_samples_leaf=30)
        elif part == "snap40":  # snap batteries to the 40 most common sizes instead of 15
            snap_top = 40
        elif part == "nosnap":  # keep battery sizes as predicted (0.1 kWh) instead of snapping to the 15 most common sizes
            nosnap = True
        elif part == "nb_engine":  # the proper version: blend inside the engine, before rules and snapping
            kw["blend"] = 0.5
        elif part == "nb_blend":
            blend = 0.5
        elif part == "nb_blend_hi":
            blend = 0.75
    d = Designer.train(train, **kw)
    if snap_top:
        d.catalog["battery_kwh"] = rules.common_sizes(train["battery_kwh"].to_numpy(float), top=snap_top)
    if nosnap:
        d.catalog["battery_kwh"] = []
    pred = d.design_batch(val)
    if blend:
        nbs = d.neighbours.query(base_features(val))
        for t in ("pv_kwp", "battery_kwh"):
            med = np.array([n[t][n[t] > 0].median() if (n[t] > 0).any() else np.nan for n in nbs])
            pred[t] = np.where((pred[t] > 0) & ~np.isnan(med), (1 - blend) * pred[t].to_numpy() + blend * med, pred[t])
    engine.features = base_features
    return pred


full = data.load_raw("data/raw")
for c in INPUT_FIELDS:
    if c not in full.columns:
        full[c] = np.nan
full[list(TARGETS)] = full[list(TARGETS)].apply(pd.to_numeric, errors="coerce").clip(lower=0)
full = full.reset_index(drop=True)
FULL_INSTALLERS = set(full["installer_id"].dropna())

names = ["base"] + (sys.argv[1:] or ["coverage", "ph_weight", "ph_drop", "ph_flag", "installer", "nb_blend", "tune_a", "tune_b"])
ok = {n: pd.DataFrame(index=full.index, columns=list(TARGETS), dtype=bool) for n in names}
secs = dict.fromkeys(names, 0.0)
for tr, va in KFold(5, shuffle=True, random_state=0).split(full):
    train, val = full.iloc[tr], full.iloc[va]
    for n in names:
        t0 = time.time()
        pred = run_variant(n, train, val)
        secs[n] += time.time() - t0
        for t in TARGETS:
            ok[n].loc[val.index, t] = dev.judge(val[t], pred[t], t)["ok"].to_numpy()
    print("fold done", flush=True)

idx = np.random.default_rng(0).integers(0, len(full), size=(2000, len(full)))
ph = is_ph(full)
arr = {n: {"whole": df.astype(bool).all(axis=1).to_numpy().astype(float), "pv": df["pv_kwp"].astype(bool).to_numpy().astype(float),
           "battery": df["battery_kwh"].astype(bool).to_numpy().astype(float)} for n, df in ok.items()}
rep = {"n_projects": len(full), "placeholder_rows": int(ph.sum()), "seconds": secs, "ideas": {}}
for n in names:
    r = {}
    for k in ("whole", "pv", "battery"):
        x, y = arr[n][k], arr["base"][k]
        est = (x[idx] - y[idx]).mean(axis=1)
        r[k] = {"score": float(x.mean()), "gain": float((x - y).mean()), "ci_low": float(np.percentile(est, 2.5)), "ci_high": float(np.percentile(est, 97.5))}
    r["whole_on_placeholder_rows"] = float(arr[n]["whole"][ph].mean())
    r["whole_on_other_rows"] = float(arr[n]["whole"][~ph].mean())
    rep["ideas"][n] = r
Path("reports").mkdir(exist_ok=True)
Path("reports/improvement_ideas.json").write_text(json.dumps(rep, indent=2))
print(f"{len(full)} projects ({int(ph.sum())} with placeholder demand); gain over current model, points [95% interval]")
print(f"{'idea':11}{'whole':>8}{'gain':>8}{'  interval':>16}{'PV gain':>9}{'bat gain':>9}{'ph rows':>9}{'others':>8}{'secs':>6}")
for n in names:
    r = rep["ideas"][n]
    w = r["whole"]
    print(f"{n:11}{w['score']:8.1%}{w['gain']*100:+8.1f}  [{w['ci_low']*100:+5.1f},{w['ci_high']*100:+5.1f}]{r['pv']['gain']*100:+9.1f}{r['battery']['gain']*100:+9.1f}"
          f"{r['whole_on_placeholder_rows']:9.1%}{r['whole_on_other_rows']:8.1%}{secs[n]:6.0f}")
