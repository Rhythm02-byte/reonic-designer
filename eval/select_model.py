"""Honest model selection: everything is chosen on the VALIDATION window (train offers <= 2025-09-30, validate
2025-10-01..2025-12-31); the 2026 test split is read only in `test_phase`, once, after the config is frozen.

  1. M1 upgrades, greedy, kept only if validation EMS improves: (a) physics features (simulator economic kWp / battery),
     (b) installer-specific PV prior (median kWp by demand bucket, out-of-fold for training rows), (c) regularisation grid.
  2. Composite: per component (heat pump, PV, battery, wallbox, in chain order) choose the best source among
     B0, B0c, H1, M1 (and SIM for the battery) by that component's validation within-tolerance, tie-break EMS.
  2b. Opt-in sizing options on the chosen composite (ported from the teammate prototype): coverage sizing (PV / battery size =
      the value within tolerance of the most plausible expert sizes, from nine quantile models), the full installer battery
      catalog (instead of the 15 most common sizes) and a 0.5 neighbour blend, singly and combined. Adopted only if the
      validation whole-design score improves and EMS drops by at most 1 point; otherwise the config stays as it was.
  3. Conformal calibration of the p10-p90 size intervals (CQR residual widening) on the validation split, target 80%.
  4. Refit on train+validation, score 2026 once for B0 / B0c / B1 / M1 / M1+ / composite, write policy.json and the block.

    python eval/select_model.py --validate-only      (development: never touches the test split)
    python eval/run.py --data dataset --offline --select      (full run, writes eval/results/latest.json)
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))

from engine.policy import physics  # noqa: E402
from engine.policy.designer import CONFIG_PATH, Designer  # noqa: E402
from engine.policy.features import TARGETS  # noqa: E402

CACHE = Path(__file__).resolve().parents[1] / "data" / "processed" / "physics_cache.pkl"
GATES = (0.3, 0.4, 0.5, 0.6)
REG_GRID = ({"maxDepth": 3, "minLeaf": 20}, {"maxDepth": 3, "minLeaf": 40}, {"maxDepth": 2, "minLeaf": 40},
            {"maxDepth": 4, "minLeaf": 30, "l2": 1.0})
COMPONENTS = (("heatPump", "heat_pump_kw", "heatPump", ("B0", "B0c", "H1", "M1")),
              ("pv", "pv_kwp", "pv", ("B0", "B0c", "H1", "M1")),          # H1 has no PV rule: skipped below
              ("battery", "battery_kwh", "battery", ("B0", "B0c", "H1", "M1", "SIM")),
              ("wallbox", "wallbox_kw", "wallbox", ("B0", "B0c", "H1", "M1")))
EMPTY = {"mode": "learned", "pvGate": 0.5, "sources": {}, "conformal": {}, "sizing": {}}
BOTH = ["pv", "battery"]
# (name, sizing config). "none" is the reference; every other row is scored against it on validation only.
SIZING_CANDIDATES = (
    ("none (current)", {}),
    ("battery catalog = all installed sizes", {"batteryCatalogTop": 0}),
    ("coverage sizing PV", {"coverage": ["pv"]}),
    ("coverage sizing battery", {"coverage": ["battery"]}),
    ("coverage sizing PV + battery", {"coverage": BOTH}),
    ("coverage PV + battery (catalog candidates)", {"coverage": BOTH, "coverageCandidates": "catalog"}),
    ("neighbour blend 0.5", {"blend": 0.5}),
    ("catalog + coverage", {"batteryCatalogTop": 0, "coverage": BOTH}),
    ("catalog + coverage (catalog candidates)", {"batteryCatalogTop": 0, "coverage": BOTH, "coverageCandidates": "catalog"}),
    ("catalog + blend", {"batteryCatalogTop": 0, "blend": 0.5}),
    ("coverage + blend", {"coverage": BOTH, "blend": 0.5}),
    ("catalog + coverage + blend", {"batteryCatalogTop": 0, "coverage": BOTH, "blend": 0.5}),
)
MAX_EMS_LOSS = 1.0


def _train(df, features, model, mode="learned", sizing=None):
    return Designer.train(df, config={**EMPTY, "mode": mode, "features": features, "model": model, "sizing": sizing or {}})


def _train_sizing(sizing: dict) -> dict:
    """What must exist at training time for a decision-time sizing config: only the quantile models for coverage sizing."""
    return {"coverage": sizing["coverage"]} if sizing.get("coverage") else {}


def choose_sizing(rows: list[dict]) -> dict:
    """First row is the reference. Adopt the candidate with the best validation whole-design (ties: EMS) among those that beat
    the reference whole-design and lose at most MAX_EMS_LOSS EMS points; none qualifies -> keep the reference."""
    ref = rows[0]
    ok = [r for r in rows[1:] if r["wholeDesign"] > ref["wholeDesign"] + 1e-9 and r["ems"] >= ref["ems"] - MAX_EMS_LOSS]
    return max(ok, key=lambda r: (round(r["wholeDesign"], 9), round(r["ems"], 9))) if ok else ref


def _rank(sc):
    return (round(sc["ems"], 9), round(sc["wholeDesign"], 9))


def _eval(R, jobs, O, dz, fn, name="V"):
    R.VARIANTS[name] = fn
    r = R.run_split(jobs, O, models=(name,), designer=dz)
    return r, R.scores(r, name)


# ---- phases ---------------------------------------------------------------------------------------------------------
def validate_phase(R, P, O, D) -> dict:
    physics.load_cache(CACHE)
    jobs = R.splits_validation(P, O, D)
    train = pd.concat([j.train for j in jobs])
    log: list[dict] = []

    # 1. M1 upgrades -------------------------------------------------------------------------------------------------
    def m1_candidate(name, features, model):
        dz = _train(train, features, model)
        best = None
        for g in GATES:
            _, sc = _eval(R, jobs, O, dz, lambda d, g=g: d.with_config("learned", g, conformal={}))
            if best is None or _rank(sc) > _rank(best):
                best = {**sc, "pvGate": g}
        rec = {"stage": "M1", "name": name, "features": features, "model": model, **best}
        log.append(rec)
        print(f"M1 {name:<34} gate {best['pvGate']}  val EMS {best['ems']:.2f}  whole {100 * best['wholeDesign']:.1f}%  "
              f"PV {100 * best['pv']:.1f}%  bat {100 * best['battery']:.1f}%", flush=True)
        return rec, dz

    cur, cur_dz = m1_candidate("base (installer-one-hot features)", {}, {})
    base = cur
    for name, feats, model in (("+physics features", {"physics": True}, {}), ("+installer PV prior", {"installerPrior": True}, {})):
        rec, dz = m1_candidate(name, {**cur["features"], **feats}, cur["model"])
        if _rank(rec) > _rank(cur):
            cur, cur_dz = rec, dz
    best_reg = None
    for reg in REG_GRID:
        rec, dz = m1_candidate(f"+regularisation {reg}", cur["features"], reg)
        if best_reg is None or _rank(rec) > _rank(best_reg[0]):
            best_reg = (rec, dz)
    if _rank(best_reg[0]) > _rank(cur):
        cur, cur_dz = best_reg
    m1 = {"features": cur["features"], "model": cur["model"], "pvGate": cur["pvGate"], "name": cur["name"]}
    print(f"-> M1+ = {cur['name']}  features {cur['features']} model {cur['model']} gate {cur['pvGate']}", flush=True)
    physics.save_cache(CACHE)

    # 2. composite, component by component ---------------------------------------------------------------------------
    sources = {"pv": "M1", "battery": "M1", "heatPump": "M1", "wallbox": "M1"}
    gate = m1["pvGate"]
    comp_log: dict[str, list] = {}
    for comp, tgt, key, cands in COMPONENTS:
        rows = []
        options = [(s, gate) for s in cands if not (comp == "pv" and s == "H1")]
        if comp == "pv":
            options = [(s, gate) for s in ("B0", "B0c")] + [("M1", g) for g in GATES]
        for src, g in options:
            srcs = {**sources, comp: src}
            _, sc = _eval(R, jobs, O, cur_dz, lambda d, srcs=srcs, g=g: d.with_config("composite", g, srcs, conformal={}), "C1")
            rows.append({"source": src, **({"pvGate": g} if comp == "pv" else {}), "componentWithinTolerance": sc[key],
                         "ems": sc["ems"], "wholeDesign": sc["wholeDesign"]})
        top = rows[0]
        for r in rows[1:]:  # strict improvement only: ties keep the earlier (simpler) source
            if (r["componentWithinTolerance"], round(r["ems"], 9)) > (top["componentWithinTolerance"], round(top["ems"], 9)):
                top = r
        sources[comp] = top["source"]
        if comp == "pv":
            gate = top.get("pvGate", gate)
        comp_log[comp] = rows
        print(f"component {comp:<9} -> {top['source']}" + (f"@{gate}" if comp == "pv" else "") +
              "   " + ", ".join(f"{r['source']}{'@' + str(r['pvGate']) if 'pvGate' in r else ''} {100 * r['componentWithinTolerance']:.1f}%"
                                for r in rows), flush=True)
    comp_fn = lambda d, c=None: d.with_config("composite", gate, sources, conformal=c or {})
    _, comp_sc = _eval(R, jobs, O, cur_dz, comp_fn, "C1")
    print(f"composite validation: EMS {comp_sc['ems']:.2f} whole {100 * comp_sc['wholeDesign']:.1f}% PV {100 * comp_sc['pv']:.1f}% "
          f"bat {100 * comp_sc['battery']:.1f}%", flush=True)
    physics.save_cache(CACHE)

    # 2b. sizing options on the chosen composite ---------------------------------------------------------------------
    cov_dz = _train(train, m1["features"], m1["model"], sizing={"coverage": BOTH})  # same models + the quantile spread
    sizing_rows = []
    for name, sz in SIZING_CANDIDATES:
        _, sc = _eval(R, jobs, O, cov_dz, lambda d, sz=sz: comp_fn(d).with_config(sizing=sz), "C2")
        sizing_rows.append({"name": name, "sizing": sz, **sc})
        print(f"sizing {name:<44} val EMS {sc['ems']:.2f}  whole {100 * sc['wholeDesign']:.1f}%  PV {100 * sc['pv']:.1f}%  "
              f"bat {100 * sc['battery']:.1f}%", flush=True)
    pick = choose_sizing(sizing_rows)
    sizing = pick["sizing"]
    print(f"-> sizing = {pick['name']}  {sizing}", flush=True)
    cur_dz = cov_dz if sizing.get("coverage") else cur_dz
    physics.save_cache(CACHE)

    # 3. conformal ---------------------------------------------------------------------------------------------------
    dz_c = comp_fn(cur_dz).with_config(sizing=sizing)
    lo, hi, y = [], [], []
    for j in jobs:
        _, extra = dz_c.design_batch_full(j.test)
        lo.append(extra[[f"lo_{t}" for t in TARGETS]].set_axis(list(TARGETS), axis=1))
        hi.append(extra[[f"hi_{t}" for t in TARGETS]].set_axis(list(TARGETS), axis=1))
        y.append(j.test[list(TARGETS)].reset_index(drop=True).set_axis(extra.index))
    lo, hi, y = pd.concat(lo), pd.concat(hi), pd.concat(y)
    conformal, cov = {}, {}
    for t in ("pv_kwp", "battery_kwh"):
        m = y[t].notna() & (y[t] > 0)
        yy, l, h = y.loc[m, t].to_numpy(), lo.loc[m, t].to_numpy(), hi.loc[m, t].to_numpy()
        s = np.maximum(l - yy, yy - h)
        n = len(s)
        level = min(1.0, math.ceil((n + 1) * 0.8) / n)
        q = float(np.quantile(s, level, method="higher"))
        conformal[t] = round(q, 3)
        cov[t] = {"n": int(n), "before": float(((yy >= l) & (yy <= h)).mean()),
                  "afterInSample": float(((yy >= l - q) & (yy <= h + q)).mean())}
    print(f"conformal widening (kWp / kWh): {conformal}  validation coverage {cov}", flush=True)

    comp_sc = {k: pick[k] for k in ("ems", "wholeDesign", "pv", "battery", "heatPump", "wallbox")}
    return {"m1": m1, "sources": sources, "pvGate": gate, "conformal": conformal, "sizing": sizing,
            "sizingCandidates": sizing_rows, "validationCoverage": cov,
            "m1Candidates": log, "componentCandidates": comp_log,
            "compositeValidation": comp_sc, "nTrain": {j.inst: int(len(j.train)) for j in jobs},
            "nValidation": int(sum(len(j.test) for j in jobs)), "baseM1": base}


def test_phase(R, P, O, D, v: dict) -> dict:
    """Refit on train+validation (<= 2025-12-31) and score 2026 ONCE with the frozen config. Nothing here feeds back."""
    jobs = R.splits_temporal(P, O, D)
    train = pd.concat([j.train for j in jobs])
    m1, base = v["m1"], v["baseM1"]
    dz_orig = _train(train, {}, {})
    dz_plus = _train(train, m1["features"], m1["model"], sizing=_train_sizing(v["sizing"]))
    comp = lambda d, c, sz=v["sizing"]: d.with_config("composite", v["pvGate"], v["sources"], conformal=c, sizing=sz)
    R.VARIANTS.update({
        "M1": lambda d: d.with_config("learned", base["pvGate"], conformal={}),
        "M1+": lambda d: d.with_config("learned", m1["pvGate"], conformal={}, sizing={}),
        "C0raw": lambda d: comp(d, {}, {}),
        "C1raw": lambda d: comp(d, {}),
        "C1": lambda d: comp(d, v["conformal"]),
    })
    r1 = R.run_split(jobs, O, models=("B0", "B0c", "B1", "M1"), designer=dz_orig)
    r2 = R.run_split(jobs, O, models=("M1+", "C0raw", "C1raw", "C1"), designer=dz_plus)
    table, cov = {}, {}
    for r, names in ((r1, ("B0", "B0c", "B1", "M1")), (r2, ("M1+", "C0raw", "C1raw", "C1"))):
        for m in names:
            table[m] = R.scores(r, m)
            pol = r["baselines"][m]["overall"]["policy"]
            cov[m] = {t: pol[t].get("p10p90Coverage") for t in ("pv_kwp", "battery_kwh", "heat_pump_kw")}
    table["composite"] = table.pop("C1")
    table["composite (no conformal)"] = table.pop("C1raw")
    cov["composite"], cov["composite (no conformal)"] = cov.pop("C1"), cov.pop("C1raw")
    table["composite (previous sizing, no conformal)"] = table.pop("C0raw")
    cov["composite (previous sizing, no conformal)"] = cov.pop("C0raw")
    physics.save_cache(CACHE)
    return {"table": table, "coverage": cov, "nTest": int(r1["nTest"]), "nTrain": r1["nTrain"]}


def run(R, P, O, D) -> dict:
    v = validate_phase(R, P, O, D)
    cfg = {"mode": "composite", "pvGate": v["pvGate"], "sources": v["sources"], "features": v["m1"]["features"],
           "model": v["m1"]["model"], "conformal": v["conformal"], "sizing": v["sizing"]}
    meta = {"chosen": "composite", "selectedOn": "validation 2025-10-01..2025-12-31 (train <= 2025-09-30)",
            "criterion": "per component: validation within-tolerance, tie-break validation EMS",
            "validationScores": v["compositeValidation"], "generatedAt": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps({**cfg, **meta}, indent=2) + "\n", encoding="utf-8")
    print(f"select  -> composite written to {CONFIG_PATH}", flush=True)
    t = test_phase(R, P, O, D, v)  # the only read of the 2026 split
    return {"trainWindow": "offers <= 2025-09-30", "validationWindow": "2025-10-01..2025-12-31", "testWindow": "2026",
            "nTrain": v["nTrain"], "nValidation": v["nValidation"], "criterion": meta["criterion"],
            "validation": {"m1Candidates": v["m1Candidates"], "componentCandidates": v["componentCandidates"],
                           "sizingCandidates": v["sizingCandidates"], "sizing": v["sizing"],
                           "composite": v["compositeValidation"], "coverage": v["validationCoverage"]},
            "bestGate": {"M1": v["m1"]["pvGate"], "H1": v["baseM1"]["pvGate"]},
            "chosen": {"model": "composite", "pvGate": v["pvGate"], "config": cfg},
            "test": t["table"], "testCoverage": t["coverage"], "nTest": t["nTest"], "nTrainTest": t["nTrain"],
            "testNote": "refit on train+validation (offers <= 2025-12-31); 2026 scored once with the frozen validation-chosen config. "
                        "M1 = original features, gate from validation; M1+ = validated feature/regularisation upgrades."}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--validate-only", action="store_true", required=True)
    ap.add_argument("--processed", default="data/processed", type=Path)
    a = ap.parse_args()
    import run as R  # noqa: E402
    P, O, D = R.load(a.processed)
    v = validate_phase(R, P, O, D)
    out = Path(__file__).parent / "results" / "selection_validation.json"
    out.write_text(json.dumps(v, indent=2, default=float), encoding="utf-8")
    print("wrote", out)
