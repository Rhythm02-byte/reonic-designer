"""The checks left after scripts/improvement_ideas.py. Run one or all:

    python scripts/remaining_tests.py confirm | curve | nested | installer     (no argument = all four)

confirm    The best setting (coverage sizing + 40 battery sizes) against the current model on folds it was NOT chosen on
           (fold seeds 1-3; the search used seed 0). If the gain holds here, it is not a selection artefact.
curve      Score against the share of training data used (20-100%): would more data help?
nested     Tuning done honestly: the settings are picked by an inner cross-validation inside each training fold,
           then scored on the untouched fold.
installer  One model per installer (trained on that installer's projects only) against the pooled model, same rows.

All: out-of-fold, 1,593 real projects, bootstrap 95% interval on the gain. Writes reports/remaining_tests.json.
"""
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import KFold

from reonic import data
from reonic.baseline import typical_design
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
BEST = dict(sizing="coverage", battery_catalog_top=40)
rng = np.random.default_rng(0)
IDX = rng.integers(0, len(full), size=(2000, len(full)))


def score(pred: pd.DataFrame, val: pd.DataFrame) -> dict[str, np.ndarray]:
    ok = pd.DataFrame({t: dev.judge(val[t], pred[t], t)["ok"].to_numpy() for t in TARGETS}, index=val.index)
    return {"whole": ok.all(axis=1).to_numpy(float), "pv": ok["pv_kwp"].to_numpy(float), "battery": ok["battery_kwh"].to_numpy(float)}


def collect(parts: list[tuple[np.ndarray, dict]]) -> dict[str, np.ndarray]:
    """Stitch per-fold scores back into one array in project order."""
    out = {k: np.full(len(full), np.nan) for k in ("whole", "pv", "battery")}
    for rows, s in parts:
        for k in out:
            out[k][rows] = s[k]
    return out


def gain(a: np.ndarray, b: np.ndarray) -> dict:
    est = (a[IDX] - b[IDX]).mean(axis=1)
    return {"a": float(a.mean()), "b": float(b.mean()), "gain": float((a - b).mean()),
            "ci_low": float(np.percentile(est, 2.5)), "ci_high": float(np.percentile(est, 97.5))}


def line(label: str, g: dict) -> str:
    return f"  {label:10} {g['b']:6.1%} -> {g['a']:6.1%}   {g['gain']*100:+5.1f} points [{g['ci_low']*100:+5.1f} to {g['ci_high']*100:+5.1f}]"


def confirm() -> dict:
    res, per_seed = {}, []
    base_all, best_all, typ_all = [], [], []
    for seed in (1, 2, 3):
        pb, pt, pf = [], [], []
        for tr, va in KFold(5, shuffle=True, random_state=seed).split(full):
            train, val = full.iloc[tr], full.iloc[va]
            pb.append((va, score(Designer.train(train).design_batch(val), val)))
            pf.append((va, score(Designer.train(train, **BEST).design_batch(val), val)))
            pt.append((va, score(typical_design(train, val), val)))
        base_all.append(collect(pb)); best_all.append(collect(pf)); typ_all.append(collect(pt))
        g = gain(best_all[-1]["whole"], base_all[-1]["whole"])
        per_seed.append(g["gain"])
        print(f"  fold seed {seed}: current {g['b']:.1%}, best {g['a']:.1%}, gain {g['gain']*100:+.1f}", flush=True)
    avg = lambda L, k: np.mean([x[k] for x in L], axis=0)  # per-project mean over the three fold seeds
    for k in ("whole", "pv", "battery"):
        res[k] = gain(avg(best_all, k), avg(base_all, k))
    res["whole_vs_typical"] = gain(avg(best_all, "whole"), avg(typ_all, "whole"))
    res["per_seed_gain"] = per_seed
    print("CONFIRM: best setting vs current model, fold seeds 1-3 (not used for choosing it)")
    for k in ("whole", "pv", "battery"):
        print(line(k, res[k]))
    print(line("vs typical", res["whole_vs_typical"]).replace(res["whole_vs_typical"]["b"].__format__("6.1%"), f"{res['whole_vs_typical']['b']:6.1%}"), "(typical design -> best)")
    return res


def curve() -> dict:
    res = {}
    print("LEARNING CURVE: share of the training folds used -> whole design (current / best / typical), PV (current), battery (current)")
    for frac in (0.2, 0.4, 0.6, 0.8, 1.0):
        pb, pf, pt = [], [], []
        for tr, va in KFold(5, shuffle=True, random_state=1).split(full):
            sub = np.random.default_rng(7).choice(tr, size=int(len(tr) * frac), replace=False)
            train, val = full.iloc[sub], full.iloc[va]
            pb.append((va, score(Designer.train(train).design_batch(val), val)))
            pf.append((va, score(Designer.train(train, **BEST).design_batch(val), val)))
            pt.append((va, score(typical_design(train, val), val)))
        b, f, t = collect(pb), collect(pf), collect(pt)
        res[str(frac)] = {"n_train": int(len(tr) * frac), "current": {k: float(b[k].mean()) for k in b}, "best": {k: float(f[k].mean()) for k in f},
                          "typical_whole": float(t["whole"].mean())}
        print(f"  {frac:4.0%} (n={int(len(tr)*frac):4}): whole {b['whole'].mean():.1%} / {f['whole'].mean():.1%} / {t['whole'].mean():.1%}   "
              f"PV {b['pv'].mean():.1%}   battery {b['battery'].mean():.1%}", flush=True)
    return res


GRID = [{}, dict(max_iter=100, learning_rate=0.05, max_depth=4, min_samples_leaf=30), dict(max_leaf_nodes=15, min_samples_leaf=40, l2_regularization=1.0),
        dict(max_iter=150, learning_rate=0.05, max_depth=3, min_samples_leaf=20), dict(max_iter=80, learning_rate=0.1, max_leaf_nodes=8, min_samples_leaf=50),
        dict(max_iter=200, learning_rate=0.03, max_depth=5, min_samples_leaf=30, l2_regularization=2.0)]


def nested() -> dict:
    parts_b, parts_n, chosen = [], [], []
    for tr, va in KFold(5, shuffle=True, random_state=1).split(full):
        train, val = full.iloc[tr], full.iloc[va]
        inner = []
        for p in GRID:
            sc = []
            for itr, iva in KFold(3, shuffle=True, random_state=2).split(train):
                a, b = train.iloc[itr], train.iloc[iva]
                sc.append(score(Designer.train(a, params=p).design_batch(b), b)["whole"].mean())
            inner.append(np.mean(sc))
        k = int(np.argmax(inner))
        chosen.append(k)
        parts_b.append((va, score(Designer.train(train).design_batch(val), val)))
        parts_n.append((va, score(Designer.train(train, params=GRID[k]).design_batch(val), val)))
        print(f"  outer fold: inner CV picked setting {k} (inner scores {[round(x, 3) for x in inner]})", flush=True)
    b, n = collect(parts_b), collect(parts_n)
    res = {"chosen_settings": chosen, **{k: gain(n[k], b[k]) for k in ("whole", "pv", "battery")}}
    print("NESTED TUNING: settings picked inside each training fold, scored on the untouched fold (0 = defaults)")
    for k in ("whole", "pv", "battery"):
        print(line(k, res[k]))
    return res


def installer() -> dict:
    res = {}
    pooled, per = [], []
    for tr, va in KFold(5, shuffle=True, random_state=1).split(full):
        train, val = full.iloc[tr], full.iloc[va]
        pooled.append((va, score(Designer.train(train).design_batch(val), val)))
        out = []
        for inst in sorted(full.installer_id.unique()):
            t_i, v_i = train[train.installer_id == inst], val[val.installer_id == inst]
            out.append((np.where(full.index.isin(v_i.index))[0], score(Designer.train(t_i).design_batch(v_i), v_i)))
        per.append(out)
    P = collect(pooled)
    S = {k: np.full(len(full), np.nan) for k in ("whole", "pv", "battery")}
    for fold in per:
        for rows, s in fold:
            for k in S:
                S[k][rows] = s[k]
    print("PER-INSTALLER MODELS vs one pooled model (same rows)")
    for k in ("whole", "pv", "battery"):
        res[k] = gain(S[k], P[k])
        print(line(k, res[k]))
    for inst in sorted(full.installer_id.unique()):
        m = (full.installer_id == inst).to_numpy()
        res[f"whole_{inst[:8]}"] = {"n": int(m.sum()), "pooled": float(P["whole"][m].mean()), "per_installer": float(S["whole"][m].mean())}
        print(f"  installer {inst[:8]} (n={int(m.sum())}): pooled {P['whole'][m].mean():.1%}, own model {S['whole'][m].mean():.1%}")
    return res


if __name__ == "__main__":
    todo = sys.argv[1:] or ["confirm", "curve", "nested", "installer"]
    path = Path("reports/remaining_tests.json")
    report = json.loads(path.read_text()) if path.exists() else {}
    for name in todo:
        report[name] = {"confirm": confirm, "curve": curve, "nested": nested, "installer": installer}[name]()
        Path("reports").mkdir(exist_ok=True)
        path.write_text(json.dumps(report, indent=2, default=float))
        print()
