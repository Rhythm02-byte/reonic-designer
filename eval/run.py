"""Offline, deterministic backtest of the baselines and the learned policy against expert designs.

    python eval/run.py --data dataset --offline [--sensitivity] [--robustness]
    python eval/run.py --oracle        ("Ask next" oracle experiment only: see eval/oracle.py; updates latest.json["oracle"])
    python eval/run.py --honesty       (shuffled labels, 20 repeated splits, engine fuzz: see eval/honesty.py; updates latest.json["honesty"])

Models: B0 installer median bundle, B0c conditioned median (what /design serves without a trained model),
B1 rule of thumb, M1 learned policy chain (engine.policy, mode "learned"), H1 hybrid (engine.policy, mode "hybrid": the
engine's own policy; this file only calls it), always trained on the TRAIN split only.
Splits:
  temporal            train offers <= 2025-12-31, test after (baselines per installer, M1 pooled with installer one-hot)
  random80_20         random 80/20, seed 0 (comparable to the teammate prototype's recorded 13.5% whole-design)
  loio_test_<id>      leave-one-installer-out, one entry per direction (train on the other installer, test on <id>)
--select       model selection WITHOUT touching the test split (eval/select_model.py): train offers <= 2025-09-30, validate
               2025-10-01..2025-12-31; M1 feature upgrades, per-component source choice (composite), conformal intervals, all on
               validation only; writes services/engine/config/policy.json, then refits on train+validation (<= 2025-12-31)
               and scores 2026 ONCE
--sensitivity  option choice (first/last) x module Wp (400/450/475/500), random split, M1 vs B0c
--robustness   blank 0/20/40/60% of the test inputs at random (3 seeds), whole-design curve
Never tune on the test split.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

sys.path.insert(0, str(Path(__file__).parent))
from metrics import evaluate, policy_metrics, pred_frame  # noqa: E402

from engine import baseline as bl  # noqa: E402
from engine.etl import normalize  # noqa: E402
from engine.policy.designer import CONFIG_PATH, Designer, load_config  # noqa: E402
from engine.policy.features import TARGETS, mask_inputs, training_frame  # noqa: E402

CUTOFF = pd.Timestamp("2025-12-31 23:59:59.999")          # end of validation = start of test (2026)
TRAIN_END = pd.Timestamp("2025-09-30 23:59:59.999")       # selection setting: train <= here, validate until CUTOFF
GATES = (0.3, 0.4, 0.5, 0.6)
BASELINES = {
    "B0": lambda s, h: bl.median_bundle(s),
    "B0c": bl.conditioned,
    "B1": bl.rule_of_thumb,
}
MODELS = ("B0", "B0c", "B1", "M1", "H1")
DEFAULT_GATES = {"M1": 0.5, "H1": load_config()["pvGate"]}
RESULTS = Path(__file__).parent / "results"
NO_SIZING = {"sizing": {}}  # plain M1 / H1 runs never use the opt-in sizing options (no quantile models trained, no blend)
VARIANTS: dict = {}  # model name -> fn(trained Designer) -> Designer with a decision config (used by select_model.py)


@dataclass
class Job:
    inst: str
    train: pd.DataFrame
    test: pd.DataFrame
    stats: bl.Stats


def load(processed: Path) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """-> (projects with parts, options, canonical frame D = inputs + primary-option targets)."""
    P, O = pd.read_parquet(processed / "projects.parquet"), pd.read_parquet(processed / "options.parquet")
    D = training_frame(P, O)
    P = P[P.has_parts].copy()
    return P, O, D


def fit_stats(P: pd.DataFrame, O: pd.DataFrame, ids, installer: str | None) -> bl.Stats:
    prim = O[O.is_primary].merge(P[P.project_id.isin(set(ids))], on=["project_id", "installer_id"])
    return bl.fit_stats(prim if installer is None else prim[prim.installer_id == installer], installer or "pooled")


def jobs_by_installer(P, O, D, train: pd.DataFrame, test: pd.DataFrame, min_train=0, min_test=1) -> list[Job]:
    out = []
    for inst in sorted(D.installer_id.unique()):
        tr, te = train[train.installer_id == inst], test[test.installer_id == inst]
        if len(tr) >= max(min_train, 1) and len(te) >= min_test:
            out.append(Job(inst, tr, te, fit_stats(P, O, tr.project_id, inst)))
    return out


def splits_temporal(P, O, D):
    return jobs_by_installer(P, O, D, D[D.when <= CUTOFF], D[D.when > CUTOFF], min_train=20, min_test=5)


def splits_validation(P, O, D):
    """Selection setting: train offers <= 2025-09-30, validate 2025-10-01..2025-12-31. The test split is not read."""
    return jobs_by_installer(P, O, D, D[D.when <= TRAIN_END], D[(D.when > TRAIN_END) & (D.when <= CUTOFF)], min_train=20, min_test=5)


def splits_random(P, O, D):
    train, test = train_test_split(D, test_size=0.2, random_state=0)
    return jobs_by_installer(P, O, D, train, test)


def splits_loio(P, O, D):
    out = {}
    for held in sorted(D.installer_id.unique()):
        rest = D[D.installer_id != held]
        out[f"loio_test_{held}"] = [Job(held, rest, D[D.installer_id == held], fit_stats(P, O, rest.project_id, None))]
    return out


def home_of(row: dict) -> dict:
    """Baseline home mapping; masked (NaN) booleans count as 'no', a missing demand as the tool default."""
    h = dict(row)
    for k in ("has_ev", "has_existing_wallbox"):
        v = h.get(k)
        h[k] = False if v is None or (isinstance(v, float) and np.isnan(v)) else bool(v)
    if h.get("demand_kwh") is None or pd.isna(h["demand_kwh"]):
        h["demand_kwh"] = normalize.DEFAULT_DEMAND_KWH
    return h


def predict(model: str, job: Job, test: pd.DataFrame, designer: Designer | None, gates: dict | None = None):
    """-> (project_id -> Pred, per-row ms, DataFrame of p10/p90 columns or None).
    M1 / H1 are the engine's Designer in mode learned / hybrid (single source of truth: engine/policy/designer.py)."""
    ids = list(test.project_id)
    if model in ("M1", "H1") or model in VARIANTS:
        if model in VARIANTS:
            dz = VARIANTS[model](designer)
        else:  # plain M1 / H1 are scored without the composite's conformal widening
            g = {**DEFAULT_GATES, **(gates or {})}[model]
            dz = designer.with_config("hybrid" if model == "H1" else "learned", g, conformal={}, sizing={})
        t = time.perf_counter()
        sizes, extra = dz.design_batch_full(test)
        ms = (time.perf_counter() - t) * 1000 / max(len(test), 1)
        preds = {pid: bl.Pred(r.pv_kwp if r.pv_kwp == r.pv_kwp else 0.0, r.battery_kwh, r.wallbox_kw > 0, r.heat_pump_kw)
                 for pid, r in zip(ids, sizes.itertuples())}
        return preds, [ms] * len(test), extra.set_axis(ids)
    fn, preds, times = BASELINES[model], {}, []
    for pid, row in zip(ids, test.to_dict("records")):
        t = time.perf_counter()
        preds[pid] = fn(job.stats, home_of(row))
        times.append((time.perf_counter() - t) * 1000)
    return preds, times, None


def run_split(jobs: list[Job], O: pd.DataFrame, models=MODELS, pooled=True, transform=None, designer: Designer | None = None,
              gates: dict | None = None) -> dict:
    """pooled=True: one M1 trained on the union of the jobs' train sets (temporal/random). False: one per job (LOIO)."""
    learned = any(m in models for m in ("M1", "H1")) or any(m in VARIANTS for m in models)
    shared = designer or (Designer.train(pd.concat([j.train for j in jobs]), config=NO_SIZING) if learned and pooled else None)
    res = {"nTest": int(sum(len(j.test) for j in jobs)), "nTrain": {}, "baselines": {}, "pvGate": {m: (gates or {}).get(m, DEFAULT_GATES[m]) for m in models if m in DEFAULT_GATES}}
    designers = {j.inst: shared or (Designer.train(j.train, config=NO_SIZING) if learned else None) for j in jobs}
    res["nTrain"] = {j.inst: int(len(j.train)) for j in jobs} if not pooled else {"pooled": int(sum(len(j.train) for j in jobs))}
    for m in models:
        per, A = {}, {"preds": {}, "steps": {}, "times": [], "pred": [], "truth": [], "extra": [], "tests": []}
        for j in jobs:
            test = j.test if transform is None else transform(j.test)
            preds, times, extra = predict(m, j, test, designers[j.inst], gates)
            steps = {pid: j.stats.battery_step for pid in preds}
            ids = list(test.project_id)
            truth = j.test.set_index("project_id").loc[ids, list(TARGETS)]
            pf = pred_frame(preds, ids)
            lo = hi = None
            if extra is not None:
                lo, hi = (extra[[f"{k}_{t}" for t in TARGETS]].set_axis(list(TARGETS), axis=1) for k in ("lo", "hi"))
            per[j.inst] = {**evaluate(test, O[O.project_id.isin(ids)], preds, steps, times),
                           "policy": policy_metrics(pf, truth, lo, hi)}
            A["preds"] |= preds; A["steps"] |= steps; A["times"] += times
            A["pred"].append(pf); A["truth"].append(truth); A["tests"].append(test)
            if extra is not None:
                A["extra"].append((lo, hi))
        test_all = pd.concat(A["tests"])
        lo = pd.concat([a for a, _ in A["extra"]]) if A["extra"] else None
        hi = pd.concat([b for _, b in A["extra"]]) if A["extra"] else None
        overall = {**evaluate(test_all, O[O.project_id.isin(test_all.project_id)], A["preds"], A["steps"], A["times"]),
                   "policy": policy_metrics(pd.concat(A["pred"]), pd.concat(A["truth"]), lo, hi)}
        res["baselines"][m] = {"overall": overall, "byInstaller": per}
    return res


# ---- model selection (validation only) -------------------------------------------------------------------------------
def scores(r: dict, model: str) -> dict:
    o = r["baselines"][model]["overall"]
    p = o["policy"]
    return {"ems": o["expertMatchPrimary"], "wholeDesign": p["wholeDesignWithinTolerance"], "pv": p["pv_kwp"]["withinTolerance"],
            "battery": p["battery_kwh"]["withinTolerance"], "heatPump": p["heat_pump_kw"]["withinTolerance"],
            "wallbox": p["wallbox_kw"]["withinTolerance"]}


def select(P, O, D) -> dict:
    """Model selection on the VALIDATION window only, then one refit + one test scoring: see eval/select_model.py.
    Writes the chosen config to config/policy.json and returns the 'selection' block (validation table, chosen config, test, coverage)."""
    import select_model
    return select_model.run(sys.modules[__name__], P, O, D)


# ---- sensitivity & robustness -----------------------------------------------------------------------------------------
def brief(r: dict, model: str) -> dict:
    o = r["baselines"][model]["overall"]
    p = o["policy"]
    return {"expertMatchPrimary": o["expertMatchPrimary"], "wholeDesign": p["wholeDesignWithinTolerance"],
            "pvWithinTolerance": p["pv_kwp"]["withinTolerance"], "batteryWithinTolerance": p["battery_kwh"]["withinTolerance"]}


def sensitivity(raw: Path) -> dict:
    """Option choice x module wattage (Wp is only assumed where the export gives no module name). Random 80/20, seed 0."""
    out, orig = {}, normalize.DEFAULT_MODULE_WP
    try:
        for wp in (400.0, 450.0, 475.0, 500.0):
            normalize.DEFAULT_MODULE_WP = wp
            with tempfile.TemporaryDirectory() as tmp:
                normalize.run(raw, Path(tmp))
                P0, O0 = pd.read_parquet(Path(tmp) / "projects.parquet"), pd.read_parquet(Path(tmp) / "options.parquet")
            for choice in ("first", "last"):
                O = O0.sort_values(["project_id", "option_number"], kind="stable").reset_index(drop=True)
                O["is_primary"] = ~O.duplicated("project_id", keep="first" if choice == "first" else "last")
                D = training_frame(P0, O)
                P = P0[P0.has_parts].copy()
                r = run_split(splits_random(P, O, D), O, models=("B0c", "M1"))
                out[f"{choice}_{int(wp)}W"] = {"optionChoice": choice, "moduleWp": wp, "nTest": r["nTest"],
                                               "M1": brief(r, "M1"), "B0c": brief(r, "B0c")}
                print(f"sensitivity {choice:<5} {int(wp)} W  M1 whole-design {out[f'{choice}_{int(wp)}W']['M1']['wholeDesign']:.3f}")
    finally:
        normalize.DEFAULT_MODULE_WP = orig
    wd = [v["M1"]["wholeDesign"] for v in out.values()]
    return {"split": "random80_20", "wholeDesignRangeM1": [min(wd), max(wd)], "runs": out}


def robustness(P, O, D, rates=(0.0, 0.2, 0.4, 0.6), seeds=(0, 1, 2)) -> dict:
    """M1 (trained on clean train rows) and baselines on test rows with a share of every input blanked."""
    jobs = splits_random(P, O, D)
    shared = Designer.train(pd.concat([j.train for j in jobs]), config=NO_SIZING)
    curve: dict = {}
    for rate in rates:
        runs = []
        for seed in seeds if rate > 0 else (0,):
            r = run_split(jobs, O, models=("B0", "B0c", "M1"), transform=lambda t, s=seed, q=rate: mask_inputs(t, q, s), pooled=True, designer=shared)
            runs.append({m: brief(r, m) for m in ("B0", "B0c", "M1")})
        curve[f"{int(rate * 100)}"] = {m: {k: float(np.mean([x[m][k] for x in runs])) for k in runs[0][m]} for m in runs[0]}
        print(f"robustness blank {int(rate * 100):>2}%  M1 whole-design {curve[f'{int(rate * 100)}']['M1']['wholeDesign']:.3f}")
    return {"split": "random80_20", "seeds": list(seeds), "blankRate": curve}


# ---- driver -----------------------------------------------------------------------------------------------------------
def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="dataset", type=Path, help="raw dataset dir (<installer>/*.csv)")
    ap.add_argument("--processed", default="data/processed", type=Path)
    ap.add_argument("--offline", action="store_true", help="no network/LLM calls (always true for baselines and M1)")
    ap.add_argument("--select", action="store_true", help="choose M1/H1 and the PV gate on the validation split, write config/policy.json")
    ap.add_argument("--sensitivity", action="store_true", help="option choice x module Wp grid (slow)")
    ap.add_argument("--robustness", action="store_true", help="blank 0/20/40/60%% of the inputs (slow)")
    ap.add_argument("--oracle", action="store_true", help="value of answering one question: unknown vs answered (test split, scored once; writes only the oracle block)")
    ap.add_argument("--honesty", action="store_true", help="shuffled-label leakage check, 20 repeated random splits, 2,000-home engine fuzz "
                                                           "(eval/honesty.py; never reads the test split; writes only the honesty block)")
    ap.add_argument("--out", default=RESULTS, type=Path)
    a = ap.parse_args()
    os.environ["OFFLINE"] = "1" if a.offline else os.environ.get("OFFLINE", "")

    if a.honesty:
        import honesty
        res = honesty.run(sys.modules[__name__], *load(a.processed))
        latest = json.loads((a.out / "latest.json").read_text(encoding="utf-8"))
        latest["honesty"] = res
        (a.out / "latest.json").write_text(json.dumps(latest, indent=2), encoding="utf-8")
        print("wrote honesty block to", a.out / "latest.json")
        return

    if a.oracle:
        import oracle
        from engine.policy import physics
        physics.load_cache(Path(__file__).resolve().parents[1] / "data" / "processed" / "physics_cache.pkl")
        res = oracle.run(sys.modules[__name__], *load(a.processed))
        latest = json.loads((a.out / "latest.json").read_text(encoding="utf-8"))
        latest["oracle"] = res
        (a.out / "latest.json").write_text(json.dumps(latest, indent=2), encoding="utf-8")
        print("wrote oracle block to", a.out / "latest.json")
        return

    normalize.run(a.data, a.processed)
    P, O, D = load(a.processed)
    installers = sorted(D.installer_id.unique())

    selection, gates = None, None
    if a.select:
        selection = select(P, O, D)
        gates = selection["bestGate"]  # each learned model scored with ITS validation-best gate
    splits = {"temporal": run_split(splits_temporal(P, O, D), O, gates=gates),
              "random80_20": run_split(splits_random(P, O, D), O, gates=gates)}
    for name, jobs in splits_loio(P, O, D).items():
        splits[name] = run_split(jobs, O, pooled=False, gates=gates)
    best = max(splits["temporal"]["baselines"].items(), key=lambda kv: kv[1]["overall"]["expertMatchPrimary"])
    m1 = splits["temporal"]["baselines"]["M1"]["overall"]
    result = {
        "generatedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"), "offline": a.offline,
        "cutoff": "2025-12-31", "installers": installers, "nProjects": int(len(D)),
        "headline": {"split": "temporal", "baseline": best[0], "expertMatchScore": best[1]["overall"]["expertMatchPrimary"],
                     "expertMatchScoreAnyOption": best[1]["overall"]["expertMatchAny"],
                     "nTestProjects": splits["temporal"]["nTest"], "runtimeMsP50": best[1]["overall"]["runtimeMs"]["p50"],
                     "m1ExpertMatchScore": m1["expertMatchPrimary"],
                     "m1WholeDesign": m1["policy"]["wholeDesignWithinTolerance"]},
        "splits": splits,
    }
    if selection is not None:
        result["selection"] = selection
    prev = {}
    if (a.out / "latest.json").exists():
        try:
            prev = json.loads((a.out / "latest.json").read_text(encoding="utf-8"))
        except ValueError:
            pass
    if a.sensitivity:
        result["sensitivity"] = sensitivity(a.data)
    elif "sensitivity" in prev:
        result["sensitivity"] = prev["sensitivity"]  # carried over from an earlier --sensitivity run
    for k in ("oracle", "honesty"):  # blocks written by their own flags: a plain / --select run must not drop them
        if k in prev:
            result[k] = prev[k]
    if a.robustness:
        result["robustness"] = robustness(P, O, D)
    elif "robustness" in prev:
        result["robustness"] = prev["robustness"]

    a.out.mkdir(parents=True, exist_ok=True)
    text = json.dumps(result, indent=2)
    (a.out / "latest.json").write_text(text, encoding="utf-8")
    (a.out / f"{datetime.now().strftime('%Y%m%d-%H%M%S')}.json").write_text(text, encoding="utf-8")
    print_table(result)


def print_table(r: dict) -> None:
    f = lambda v, d=1: "-" if v is None else f"{v:.{d}f}"
    pc = lambda v: "-" if v is None else f"{100 * v:.1f}"
    if "selection" in r:
        sel = r["selection"]
        print(f"\nselection (validation {sel['validationWindow']}, n={sel['nValidation']}): M1 candidates, EMS / whole-design %")
        for v in sel["validation"]["m1Candidates"]:
            print(f"  {v['name'][:44]:<44} {f(v['ems'], 2):>6} / {pc(v['wholeDesign'])}")
        print(f"chosen: {sel['chosen']['model']} {json.dumps(sel['chosen']['config'])}")
        print(f"test (2026, n={sel['nTest']}, scored once): EMS / whole / PV / battery %")
        for m, v in sel["test"].items():
            print(f"  {m:<26} {f(v['ems'], 2):>6} / {pc(v['wholeDesign'])} / {pc(v['pv'])} / {pc(v['battery'])}")
        print("test p10-p90 coverage % (PV / battery):", {m: [pc(c['pv_kwp']), pc(c['battery_kwh'])] for m, c in sel["testCoverage"].items()})
    print(f"\n{'split':<24}{'model':<5}{'n':>5}{'EMS':>6}{'EMSany':>7}{'whole%':>7}{'PV%':>6}{'bat%':>6}{'hp%':>6}{'F1bat':>6}{'F1wb':>5}"
          f"{'F2wb':>5}{'kWpMAE':>7}{'batMAE':>7}{'cov PV':>7}{'cov bat':>8}{'ms':>7}")
    for sname, s in r["splits"].items():
        for b, v in s["baselines"].items():
            o, p = v["overall"], v["overall"]["policy"]
            cov = lambda t: pc(p[t].get("p10p90Coverage"))
            print(f"{sname[:23]:<24}{b:<5}{o['nProjects']:>5}{f(o['expertMatchPrimary']):>6}{f(o['expertMatchAny']):>7}"
                  f"{pc(p['wholeDesignWithinTolerance']):>7}{pc(p['pv_kwp']['withinTolerance']):>6}{pc(p['battery_kwh']['withinTolerance']):>6}"
                  f"{pc(p['heat_pump_kw']['withinTolerance']):>6}{f(p['battery_kwh']['includeF1'], 2):>6}{f(p['wallbox_kw']['includeF1'], 2):>5}"
                  f"{f(p['wallbox_kw']['includeF2'], 2):>5}{f(p['pv_kwp']['sizeMae'], 2):>7}{f(p['battery_kwh']['sizeMae'], 2):>7}"
                  f"{cov('pv_kwp'):>7}{cov('battery_kwh'):>8}{f(o['runtimeMs']['p50'], 3):>7}")
    if "sensitivity" in r:
        print("\nsensitivity (random 80/20): option x Wp -> M1 whole-design % / EMS ; B0c whole-design %")
        for k, v in r["sensitivity"]["runs"].items():
            print(f"  {k:<12} M1 {pc(v['M1']['wholeDesign'])} / {f(v['M1']['expertMatchPrimary'])}   B0c {pc(v['B0c']['wholeDesign'])}")
    if "robustness" in r:
        print("\nrobustness (share of inputs blanked) -> whole-design %: M1 | B0c | B0")
        for k, v in r["robustness"]["blankRate"].items():
            print(f"  {k:>3}%  {pc(v['M1']['wholeDesign'])} | {pc(v['B0c']['wholeDesign'])} | {pc(v['B0']['wholeDesign'])}   (EMS M1 {f(v['M1']['expertMatchPrimary'])})")


if __name__ == "__main__":
    main()
