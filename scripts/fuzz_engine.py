"""Fuzz the design engine with random and extreme inputs, and check it never breaks its own rules.

    python scripts/fuzz_engine.py            # 2,000 random homes on the real data (synthetic if data/raw is absent)
    python scripts/fuzz_engine.py --n 5000 --seed 7

Why: a crash or a rule violation in front of a judge is worse than a small accuracy gap. Inputs include unknowns,
zero, negative, huge, NaN and nonsense category names, plus random planner overrides.

Invariants checked on every design (components the planner locked are exempt from the rules, never from the lock):
  - no crash, same input gives the same design (deterministic)
  - every size is finite and >= 0; every probability is in [0, 1]
  - a locked value is returned exactly
  - PV <= 30 kWp (R03); no battery without new or existing PV (R02); battery <= 2 kWh per kWp of PV (R04)
  - a home that already heats with a heat pump gets no new one (R01)
  - the wallbox is present if and only if the home has an EV, and uses a catalogue size
  - an explanation is returned, as a list of strings
"""
import argparse
import math
import random
from pathlib import Path

import numpy as np
import pandas as pd

from reonic import data, evaluate, rules, synth
from reonic.engine import Designer
from reonic.schema import HEATING_TYPES, INPUT_FIELDS, LOAD_PROFILES, TARGETS, HomeInputs

NAN = float("nan")
CHOICES = {
    "annual_consumption_kwh": [None, 0, 1, 500, 4500, 12000, 1e6, 1e9, -100, NAN],
    "electricity_price_eur_kwh": [None, 0, 0.35, 5.0, -1, NAN],
    "energy_price_increase": [None, 0, 0.03, 1.0],
    "has_ev": [None, True, False],
    "ev_km_per_year": [None, 0, 12000, 1e7, -5],
    "has_flexible_tariff": [None, True, False],
    "load_profile": [None, *LOAD_PROFILES, "not_a_profile"],
    "heating_type": [None, *HEATING_TYPES, "garbage", "HEAT_PUMP"],
    "heating_demand_kwh": [None, 0, 15000, 1e7],
    "existing_pv_kwp": [None, 0, 5, 50, 1e4],
    "existing_battery_kwh": [None, 0, 10],
    "has_existing_wallbox": [None, True, False],
    "household_size": [None, 3],
    "heated_area_m2": [None, 150],
}
LOCK_VALUES = [0.0, 3.3, 10.0, 100.0]


def random_home(rng: random.Random) -> HomeInputs:
    return HomeInputs(**{f: rng.choice(v) for f, v in CHOICES.items()})


def random_locks(rng: random.Random) -> dict[str, float]:
    return {t: rng.choice(LOCK_VALUES) for t in TARGETS if rng.random() < 0.25}


def check(designer: Designer, inp: HomeInputs, locked: dict[str, float]) -> list[str]:
    """Return a list of broken invariants (empty means fine)."""
    problems: list[str] = []
    try:
        d = designer.design(inp, locked)
        again = designer.design(inp, locked)
    except Exception as e:  # noqa: BLE001 - the point is to catch anything
        return [f"crash: {type(e).__name__}: {e}"]
    values = d.values()
    if values != again.values():
        problems.append("not deterministic")
    for t, v in values.items():
        if not math.isfinite(v) or v < 0:
            problems.append(f"{t} is {v}")
    for t, p in d.probability.items():
        if not (0.0 <= p <= 1.0):
            problems.append(f"probability {t} is {p}")
    for t, v in locked.items():
        if values[t] != v:
            problems.append(f"lock on {t} not respected: asked {v}, got {values[t]}")
    existing_pv = inp.existing_pv_kwp if isinstance(inp.existing_pv_kwp, (int, float)) and math.isfinite(inp.existing_pv_kwp) else 0.0
    if "pv_kwp" not in locked and values["pv_kwp"] > rules.PV_MAX_KWP + 1e-9:
        problems.append(f"R03 broken: PV {values['pv_kwp']}")
    if "battery_kwh" not in locked:
        total_pv = values["pv_kwp"] + max(existing_pv, 0.0)
        if values["battery_kwh"] > 0 and total_pv <= 0:
            problems.append("R02 broken: battery without PV")
        if values["battery_kwh"] > rules.BATTERY_MAX_KWH_PER_KWP * total_pv + 1e-9:
            problems.append(f"R04 broken: battery {values['battery_kwh']} for {total_pv} kWp")
    if "heat_pump_kw" not in locked and str(inp.heating_type or "").lower() == "heat_pump" and values["heat_pump_kw"] > 0:
        problems.append("R01 broken: new heat pump for a home that has one")
    if "wallbox_kw" not in locked:
        has_ev = inp.has_ev is True
        if (values["wallbox_kw"] > 0) != has_ev:
            problems.append(f"wallbox {values['wallbox_kw']} but has_ev={inp.has_ev}")
        allowed = set(designer.catalog.get("wallbox_kw", [])) | {11.0}
        if values["wallbox_kw"] > 0 and values["wallbox_kw"] not in allowed:
            problems.append(f"wallbox size {values['wallbox_kw']} not in catalogue")
    if not d.explanation or not all(isinstance(x, str) for x in d.explanation):
        problems.append("explanation missing or not strings")
    if not all(isinstance(x, str) for x in d.flags + d.rules_applied):
        problems.append("flags or rules not strings")
    return problems


def fuzz(designer: Designer, n: int, seed: int) -> list[dict]:
    rng = random.Random(seed)
    bad = []
    for _ in range(n):
        inp, locked = random_home(rng), random_locks(rng)
        problems = check(designer, inp, locked)
        if problems:
            bad.append({"input": inp, "locked": locked, "problems": problems})
    return bad


def build_designer() -> tuple[Designer, str]:
    if Path("data/raw").is_dir():
        df = data.load("data/raw")
        label = "real export"
    else:
        df, label = synth.generate(1200, seed=1), "synthetic data (data/raw not found)"
    train, _ = evaluate.split(df, 0.2, 0, None)
    return Designer.train(train), label


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=2000)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()
    designer, label = build_designer()
    bad = fuzz(designer, args.n, args.seed)
    print(f"trained on {label}; fuzzed {args.n} random homes (seed {args.seed}): {len(bad)} with a broken invariant")
    kinds: dict[str, int] = {}
    for b in bad:
        for p in b["problems"]:
            kinds[p.split(":")[0].split(" for ")[0][:60]] = kinds.get(p.split(":")[0].split(" for ")[0][:60], 0) + 1
    for k, c in sorted(kinds.items(), key=lambda x: -x[1]):
        print(f"  {c:5}  {k}")
    for b in bad[:5]:
        print("\nexample:", {k: v for k, v in b["input"].__dict__.items() if v is not None}, "| locked:", b["locked"])
        print("   ", b["problems"])
    raise SystemExit(1 if bad else 0)
