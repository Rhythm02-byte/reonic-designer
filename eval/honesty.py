"""Honesty checks: is our score real, how much does it move, and does the engine break its own rules?

    python eval/run.py --honesty        (real data; writes only the "honesty" block of eval/results/latest.json)
    pytest services/engine/tests/test_honesty.py        (the same functions on SYNTHETIC data, no confidential rows)

Ported from the teammate prototype (scripts/leakage_checks.py, repeated_splits.py, fuzz_engine.py), on our engine:
  1. shuffled labels  Train on targets permuted across homes (one permutation for all four targets, inputs unchanged) and
                      score on the true validation labels. A model with no information must fall to the baseline level
                      (B0, the installer-median design); if it kept its score the score would be an artefact (leakage).
                      Setting: train offers <= 2025-09-30, validate 2025-10-01..2025-12-31 (the selection setting).
  2. repeated splits  N random 80/20 splits (default 20 seeds) of the pre-2026 rows (the test split is never read):
                      mean +- sd of whole-design within tolerance, ours vs B0, and the paired difference.
                      Splits share training rows, so the sd understates the sampling uncertainty.
  3. fuzzing          2,000 random / extreme / nonsense homes (+ random planner locks) through the Designer: no exception,
                      deterministic, finite sizes, probabilities in [0, 1], locks returned exactly, and R01-R04 + R07 hold.
Metric: whole design = PV +-20%, battery +-25%, heat pump +-25%, wallbox include/exclude (eval/metrics.py).
"""
from __future__ import annotations

import math
import random
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

sys.path.insert(0, str(Path(__file__).parent))
from metrics import policy_metrics  # noqa: E402

from engine import baseline as bl  # noqa: E402
from engine.models.schemas import Building, Ev, ExistingPv, ExistingStorage, Heating, HomeInputs  # noqa: E402
from engine.policy import rules  # noqa: E402
from engine.policy.designer import Designer, baseline_stats_from  # noqa: E402
from engine.policy.features import TARGETS  # noqa: E402

NAN = float("nan")
SHUFFLE_SEEDS = (0, 1, 2, 3, 4)
SPLIT_SEEDS = tuple(range(20))


# ---- scoring ---------------------------------------------------------------------------------------------------------
def b0_frame(train: pd.DataFrame, test: pd.DataFrame) -> pd.DataFrame:
    """B0 = the installer's median bundle (same definition as the eval baseline), as a target frame for `test`."""
    stats = baseline_stats_from(train)
    rows = []
    for inst in test["installer_id"].astype(str):
        p = bl.median_bundle(stats.get(inst) or stats["all"])
        rows.append((p.kwp, p.battery_kwh, p.hp_kw, 11.0 if p.wallbox else 0.0))
    return pd.DataFrame(rows, columns=["pv_kwp", "battery_kwh", "heat_pump_kw", "wallbox_kw"], index=test.index)


def score_frame(pred: pd.DataFrame, test: pd.DataFrame) -> dict:
    m = policy_metrics(pred.reset_index(drop=True), test[list(TARGETS)].reset_index(drop=True))
    return {"whole": m["wholeDesignWithinTolerance"], "pv": m["pv_kwp"]["withinTolerance"],
            "battery": m["battery_kwh"]["withinTolerance"]}


def score_designer(designer: Designer, train: pd.DataFrame, test: pd.DataFrame) -> dict:
    return {"model": score_frame(designer.design_batch(test), test), "b0": score_frame(b0_frame(train, test), test)}


def _mean_sd(values) -> dict:
    v = np.asarray(list(values), dtype=float)
    return {"mean": float(v.mean()), "sd": float(v.std(ddof=1)) if len(v) > 1 else 0.0, "n": int(len(v))}


def _summ(rows: list[dict], key: str) -> dict:
    return {k: _mean_sd(r[key][k] for r in rows) for k in ("whole", "pv", "battery")}


# ---- 1. shuffled labels ----------------------------------------------------------------------------------------------
def shuffle_labels(df: pd.DataFrame, seed: int) -> pd.DataFrame:
    """Permute the four targets across rows with ONE permutation (designs stay internally coherent, inputs unchanged)."""
    out = df.copy()
    perm = np.random.default_rng(seed).permutation(len(df))
    out[list(TARGETS)] = df[list(TARGETS)].to_numpy()[perm]
    return out


def shuffled_labels(train: pd.DataFrame, test: pd.DataFrame, seeds=SHUFFLE_SEEDS, make=Designer.train) -> dict:
    real = score_designer(make(train), train, test)
    rows = [score_designer(make(shuffle_labels(train, s)), train, test) for s in seeds]  # B0 reference uses the TRUE train labels
    out = {"nTrain": int(len(train)), "nTest": int(len(test)), "seeds": list(seeds),
           "real": {"whole": real["model"]["whole"], "pv": real["model"]["pv"], "battery": real["model"]["battery"]},
           "b0": {k: real["b0"][k] for k in ("whole", "pv", "battery")},
           "shuffled": _summ(rows, "model")}
    out["shuffledWholeMinusB0"] = out["shuffled"]["whole"]["mean"] - out["b0"]["whole"]
    out["realWholeMinusShuffled"] = out["real"]["whole"] - out["shuffled"]["whole"]["mean"]
    return out


# ---- 2. repeated random splits ---------------------------------------------------------------------------------------
def repeated_splits(D: pd.DataFrame, seeds=SPLIT_SEEDS, test_size: float = 0.2, make=Designer.train) -> dict:
    rows = []
    for s in seeds:
        tr, te = train_test_split(D, test_size=test_size, random_state=s)
        rows.append(score_designer(make(tr), tr, te))
    diff = {k: _mean_sd(r["model"][k] - r["b0"][k] for r in rows) for k in ("whole", "pv", "battery")}
    return {"n": int(len(D)), "seeds": list(seeds), "ours": _summ(rows, "model"), "b0": _summ(rows, "b0"),
            "oursMinusB0": diff,
            "splitsOursBeatsB0Whole": int(sum(r["model"]["whole"] > r["b0"]["whole"] for r in rows)), "nSplits": len(rows)}


# ---- 3. fuzzing ------------------------------------------------------------------------------------------------------
CHOICES = {
    "demand_kwh": [None, NAN, 0, 1, 500, 4500, 12000, 1e6, 1e9, -100],
    "price_eur_kwh": [None, NAN, 0, 0.35, 5.0, -1],
    "price_escalation": [None, NAN, 0, 0.03, 1.0],
    "flex_tariff": [None, NAN, True, False],
    "load_family": [None, "H0", "family", "home_office", "senior", "custom", "other", "not_a_profile"],
    "has_ev": [None, NAN, True, False],
    "ev_km": [None, NAN, 0, 12000, 1e7, -5],
    "has_existing_pv": [None, True, False],
    "existing_pv_kwp": [None, NAN, 0, 5, 50, 1e4, -3],
    "existing_pv_trusted": [True, False],
    "has_existing_storage": [None, True, False],
    "existing_storage_kwh": [None, NAN, 0, 10, 1e3],
    "existing_storage_trusted": [True, False],
    "has_existing_wallbox": [None, True, False],
    "heating_type": [None, "Gas", "Oil", "Heatpump", "OtherRenewable", "OtherNonRenewable", "Unknown", "garbage", "HEATPUMP"],
    "heat_demand_kwh": [None, NAN, 0, 15000, 1e7, -1],
    "hp_elec_existing_kwh": [None, NAN, 0, 4000],
    "roof_max_modules": [NAN, NAN, 0, 1, 8, 40, 1000],
}
LOCK_VALUES = (0.0, 3.3, 10.0, 100.0)


def random_row(rng: random.Random, installers) -> dict:
    row = {k: rng.choice(v) for k, v in CHOICES.items()}
    row["installer_id"] = rng.choice([*installers, "unseen-installer", None])
    n = row["roof_max_modules"]
    row["roof_max_kwp"] = n * 0.45 if n == n else NAN
    return row


def random_inputs(rng: random.Random, installers) -> HomeInputs:
    """Extreme but schema-valid HomeInputs (the API path: row_from_inputs -> design)."""
    pick = rng.choice
    pv = pick([None, ExistingPv(kwp=pick([0, 5, 50, 1e4]), trusted=pick([True, False]))])
    st = pick([None, ExistingStorage(kwh=pick([0, 10, 1e3]), trusted=pick([True, False]))])
    return HomeInputs(
        installer_id=pick([*installers, "unseen-installer"]), demand_kwh=pick([0, 1, 500, 4500, 12000, 1e6, 1e9]),
        price_eur_kwh=pick([0.0, 0.35, 5.0]), flex_tariff=pick([None, True, False]),
        ev=Ev(has=pick([True, False]), km_per_year=pick([None, 0, 12000, 1e7])),
        existing_pv=pv, existing_storage=st,
        heating=Heating(type=pick(["Gas", "Oil", "Heatpump", "Unknown"]), heat_demand_kwh=pick([None, 0, 15000, 1e7]),
                        hp_elec_kwh=pick([None, 4000])),
        building=pick([None, Building(roof_max_modules=pick([0, 1, 8, 40, 1000]))]))


def random_locks(rng: random.Random) -> dict:
    return {t: rng.choice(LOCK_VALUES) for t in TARGETS if rng.random() < 0.25}


def _truthy(v) -> bool:
    return v is not None and v == v and bool(v)


def check_design(values: dict, p: dict, intervals: dict, row: dict, locked: dict) -> list[str]:
    """Broken invariants for one design (empty = fine). Components the planner locked are exempt from the rules, never from the lock."""
    out: list[str] = []
    for t, v in values.items():
        if not math.isfinite(v) or v < 0:
            out.append(f"{t} is {v}")
    for t, q in p.items():
        if not (0.0 <= q <= 1.0):
            out.append(f"probability {t} is {q}")
    for t, (lo, mid, hi) in intervals.items():
        if t not in locked and not (-1e-9 <= lo <= mid + 1e-9 <= hi + 2e-9):
            out.append(f"interval {t} not ordered: {lo}, {mid}, {hi}")
    for t, v in locked.items():
        if values[t] != v:
            out.append(f"lock on {t} not respected: asked {v}, got {values[t]}")
    ctx = rules.ctx_from_row(row)
    total_pv = values["pv_kwp"] + ctx["existing_pv_kwp"]
    if "pv_kwp" not in locked:
        if values["pv_kwp"] > rules.PV_MAX_KWP + 1e-9:
            out.append(f"R03 broken: PV {values['pv_kwp']}")
        roof = ctx["roof_max_kwp"]
        if roof is not None and values["pv_kwp"] > roof + 1e-6:
            out.append(f"R07 broken: PV {values['pv_kwp']} on a roof of {roof} kWp")
    if "battery_kwh" not in locked:
        if values["battery_kwh"] > 0 and total_pv <= 0:
            out.append("R02 broken: battery without PV")
        if values["battery_kwh"] > rules.BATTERY_MAX_KWH_PER_KWP * total_pv + 1e-9:
            out.append(f"R04 broken: battery {values['battery_kwh']} for {total_pv} kWp")
    if "heat_pump_kw" not in locked and str(row.get("heating_type") or "") == "Heatpump" and values["heat_pump_kw"] > 0:
        out.append("R01 broken: new heat pump for a home that has one")
    if "wallbox_kw" not in locked and values["wallbox_kw"] > 0 and not _truthy(row.get("has_ev")):
        out.append("wallbox without a known EV")
    return out


def _design(designer: Designer, item, locked: dict):
    """-> (values, probability, intervals, row, n_reasons)."""
    if isinstance(item, HomeInputs):
        from engine.policy.features import row_from_inputs
        row, d = row_from_inputs(item), designer.design(item, locked)
    else:
        row, d = item, designer.design_row(item, locked)
    return d.values, d.probability, d.intervals, row, len(d.reasons)


def fuzz(designer: Designer, n: int = 2000, seed: int = 0) -> dict:
    """n random homes through Designer.design / design_row (alternating the raw-row and the HomeInputs path), each with random
    planner locks. A crash is a finding, not an exception."""
    rng = random.Random(seed)
    installers = designer.installers or ("a",)
    bad: list[dict] = []
    crashes = 0
    for i in range(n):
        item = random_inputs(rng, installers) if i % 2 else random_row(rng, installers)
        locked = random_locks(rng)
        try:
            values, p, iv, row, n_reasons = _design(designer, item, locked)
            problems = check_design(values, p, iv, row, locked)
            if n_reasons == 0:
                problems.append("no explanation")
            if i % 10 == 0 and _design(designer, item, locked)[0] != values:  # determinism on a sample (cost)
                problems.append("not deterministic")
        except Exception as e:  # noqa: BLE001 - the point is to catch anything
            crashes += 1
            problems = [f"crash: {type(e).__name__}: {e}"[:200]]
        if problems:
            bad.append({"i": i, "locked": locked, "problems": problems})
    kinds: dict[str, int] = {}
    for b in bad:
        for pr in b["problems"]:
            k = pr.split(":")[0].split(" for ")[0][:40]
            kinds[k] = kinds.get(k, 0) + 1
    return {"n": n, "seed": seed, "broken": len(bad), "crashes": crashes, "kinds": kinds, "examples": bad[:3],
            "passed": not bad}


def fuzz_batch(designer: Designer, n: int = 2000, seed: int = 0) -> dict:
    """The same invariants through the batch API (design_batch_full), no locks: fast enough for the unit tests."""
    rng = random.Random(seed)
    rows = [random_row(rng, designer.installers or ("a",)) for _ in range(n)]
    df = pd.DataFrame(rows)
    sizes, extra = designer.design_batch_full(df)
    bad = []
    for i, row in enumerate(rows):
        values = {t: float(sizes[t].iat[i]) for t in TARGETS}
        p = {t: float(extra[f"p_{t}"].iat[i]) for t in TARGETS}
        iv = {t: (float(extra[f"lo_{t}"].iat[i]), values[t], float(extra[f"hi_{t}"].iat[i])) for t in TARGETS}
        problems = check_design(values, p, iv, row, {})
        if problems:
            bad.append({"i": i, "problems": problems})
    return {"n": n, "seed": seed, "broken": len(bad), "examples": bad[:3], "passed": not bad}


# ---- driver (real data) ----------------------------------------------------------------------------------------------
def run(R, P, O, D, n_splits: int = len(SPLIT_SEEDS), n_fuzz: int = 2000) -> dict:
    """Real data, served config (config/policy.json). Never reads the 2026 test split."""
    from engine.policy import physics
    physics.load_cache(Path(__file__).resolve().parents[1] / "data" / "processed" / "physics_cache.pkl")
    pre = D[D.when <= R.CUTOFF].reset_index(drop=True)
    train, val = pre[pre.when <= R.TRAIN_END], pre[pre.when > R.TRAIN_END]
    sh = shuffled_labels(train, val)
    print(f"honesty shuffled labels: real whole {100 * sh['real']['whole']:.1f}%  B0 {100 * sh['b0']['whole']:.1f}%  "
          f"shuffled {100 * sh['shuffled']['whole']['mean']:.1f}% +- {100 * sh['shuffled']['whole']['sd']:.1f}", flush=True)
    rs = repeated_splits(pre, SPLIT_SEEDS[:n_splits])
    print(f"honesty repeated splits ({rs['nSplits']}): ours {100 * rs['ours']['whole']['mean']:.1f}% +- {100 * rs['ours']['whole']['sd']:.1f}  "
          f"B0 {100 * rs['b0']['whole']['mean']:.1f}% +- {100 * rs['b0']['whole']['sd']:.1f}", flush=True)
    dz = Designer.train(pre)
    fz = fuzz(dz, n_fuzz)
    print(f"honesty fuzz: {fz['n']} homes, {fz['broken']} broken ({fz['kinds']})", flush=True)
    physics.save_cache(Path(__file__).resolve().parents[1] / "data" / "processed" / "physics_cache.pkl")
    return {"metric": "whole design within tolerance (PV 20%, battery 25%, heat pump 25%, wallbox include)",
            "model": "served config (config/policy.json), trained on the rows of each split",
            "shuffledLabels": {"setting": "train offers <= 2025-09-30, validate 2025-10-01..2025-12-31", **sh},
            "repeatedSplits": {"setting": "random 80/20 of offers <= 2025-12-31 (test split never read)", **rs},
            "fuzz": {"setting": "served composite trained on offers <= 2025-12-31", **fz}}
