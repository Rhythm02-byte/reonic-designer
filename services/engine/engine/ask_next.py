"""Ask next: which missing input is worth asking for? (PLAN 6.9, value of information)

For every askable input the planner has not entered, take plausible answers from the installer's training distribution
(demand / roof modules / fossil heat demand: p25, p50, p75; EV, existing PV and storage: yes/no with the observed share),
run the POLICY only (no simulator) once per answer in a single design_batch call, and score the input:

    score = P(design changes) x price swing

P(design changes) = probability mass of the answers whose design differs from today's design: another component set, or at
least one catalog step (battery: the installer's step, heat pump: one size, PV: two modules). Price swing = spread of the
installed price (config/market.json, mid) over the possible answers and the current design. Locked components never count.
The top 3 above MIN_SCORE_EUR are returned; copy is plain English. The distributions are stored in the Designer artifact
(`ask_stats`, built in training; `python -m engine.ask_next --patch` adds them to an existing artifact).
"""
from __future__ import annotations

import time
from typing import Mapping

import numpy as np
import pandas as pd

from engine import baseline as bl
from engine.etl.normalize import DEFAULT_DEMAND_KWH
from engine.models.schemas import AskAnswer, AskImpact, AskNext, Building, ExistingPv, ExistingStorage, HomeInputs
from engine.policy import physics
from engine.policy.features import heat_demand_from_inputs, row_from_inputs
from engine.sim import economics

MAX_ITEMS = 3
MIN_SCORE_EUR = 250.0
MIN_N = 40  # an installer with fewer training rows uses the pooled distributions
PV_STEP_MODULES = 2
FOSSIL_ASK = ("Gas", "Oil")
COMPONENTS = ("pv", "battery", "heatPump", "wallbox")
TARGET = {"pv": "pv_kwp", "battery": "battery_kwh", "heatPump": "heat_pump_kw", "wallbox": "wallbox_kw"}


# ---- distributions (training time) ------------------------------------------------------------------------------
def _q(x: pd.Series, qs=(0.25, 0.5, 0.75)) -> list[float] | None:
    x = pd.to_numeric(x, errors="coerce").dropna()
    return [float(v) for v in np.quantile(x, qs)] if len(x) >= 10 else None


def _share(has: pd.Series) -> float:
    return float(has.fillna(False).astype(bool).mean()) if len(has) else 0.0


def _one(g: pd.DataFrame) -> dict:
    d = pd.to_numeric(g["demand_kwh"], errors="coerce")
    d = d[(d - DEFAULT_DEMAND_KWH).abs() > 1e-6]  # the placeholder is not a real answer
    heat = g[g["heating_type"].isin(FOSSIL_ASK)]["heat_demand_kwh"] if "heating_type" in g and "heat_demand_kwh" in g else pd.Series(dtype=float)
    pv = g["pv_kwp"] if "pv_kwp" in g else pd.Series(dtype=float)
    ev = g["has_ev"].map(lambda v: v is True or v == 1.0) if "has_ev" in g else pd.Series(dtype=bool)
    xpv = g[g["has_existing_pv"].fillna(False).astype(bool)]["existing_pv_kwp"] if "has_existing_pv" in g else pd.Series(dtype=float)
    xst = g[g["has_existing_storage"].fillna(False).astype(bool)]["existing_storage_kwh"] if "has_existing_storage" in g else pd.Series(dtype=float)
    return {"n": int(len(g)), "demand": _q(d), "roofKwp": _q(pv[pv > 0]), "evShare": _share(ev),
            "heatDemand": _q(heat), "existingPvShare": _share(g["has_existing_pv"]) if "has_existing_pv" in g else 0.0,
            "existingPvKwp": _q(xpv, (0.25, 0.75)), "existingStorageShare": _share(g["has_existing_storage"]) if "has_existing_storage" in g else 0.0,
            "existingStorageKwh": _q(xst, (0.5,))}


def stats_from(df: pd.DataFrame) -> dict:
    """Per installer (and pooled under "all"): the input distributions the questions draw their answers from."""
    out = {"all": _one(df)}
    if "installer_id" in df:
        for inst, g in df.groupby(df["installer_id"].astype(str)):
            if len(g) >= MIN_N:
                out[inst] = _one(g)
    return out


# ---- scoring (serve time) ---------------------------------------------------------------------------------------
def _entered(given: Mapping, field: str) -> bool:
    return any(k in given and given[k].source in ("entered", "extracted") for k in {field, field.split(".")[0]})


def _apply(i: HomeInputs, field: str, value) -> HomeInputs:
    j = i.model_copy(deep=True)
    if field == "demandKwh":
        j.demand_kwh = float(value)
    elif field == "building.roofMaxModules":
        j.building = j.building or Building()
        j.building.roof_max_modules = int(value)
    elif field == "ev.has":
        j.ev.has = bool(value)
        if not value:
            j.ev.km_per_year = None
    elif field == "heating.heatDemandKwh":
        j.heating.heat_demand_kwh = float(value)
    elif field == "existingPv.kwp":
        j.existing_pv = ExistingPv(kwp=float(value)) if value else None
    elif field == "existingStorage.kwh":
        j.existing_storage = ExistingStorage(kwh=float(value)) if value else None
    return j


def _distinct(values: list[float], nudge_from: float | None = None) -> list[float]:
    out: list[float] = []
    for v in values:
        if nudge_from is not None and abs(v - nudge_from) < 1e-9:
            v += 100.0  # an answer equal to the tool default would look like "still unanswered"
        if v not in out:
            out.append(v)
    return out


def _round(v: float, to: float) -> float:
    return float(round(v / to) * to)


def _candidates(i: HomeInputs, st: dict, wp: float, locks: set, given: Mapping) -> list[dict]:
    """Askable inputs and their plausible answers: [{field, answers: [(label, value, weight)], ...}]. Skips entered fields."""
    c: list[dict] = []
    # order = priority under the time budget: the roof needs no simulation, a default demand is the headline question,
    # the others each simulate new homes

    def add(field: str, answers: list[tuple[str, float | bool, float]], **extra) -> None:
        if len(answers) >= 2 and not _entered(given, field):
            w = sum(a[2] for a in answers)
            c.append({"field": field, "answers": [(lbl, v, wt / w) for lbl, v, wt in answers], **extra})

    if (i.building is None or i.building.roof_max_modules is None) and st.get("roofKwp") and "pv" not in locks:
        mods = sorted({max(1, round(k * 1000 / wp)) for k in st["roofKwp"]})
        add("building.roofMaxModules", [(f"{m} modules", float(m), 1.0) for m in mods])
    if abs(i.demand_kwh - DEFAULT_DEMAND_KWH) < 1e-6 and st.get("demand"):
        vals = _distinct([max(500.0, _round(v, 100)) for v in st["demand"]], DEFAULT_DEMAND_KWH)
        add("demandKwh", [(f"{v:,.0f} kWh", v, 1.0) for v in vals])
    p_ev = min(max(st.get("evShare", 0.0), 0.02), 0.98)
    add("ev.has", [("Yes", True, p_ev), ("No", False, 1 - p_ev)])
    if i.heating.type in FOSSIL_ASK and heat_demand_from_inputs(i) is None and st.get("heatDemand"):
        add("heating.heatDemandKwh", [(f"{v:,.0f} kWh", v, 1.0) for v in _distinct([max(2000.0, _round(v, 500)) for v in st["heatDemand"]])])
    if i.existing_pv is None and st.get("existingPvKwp"):
        p = min(max(st.get("existingPvShare", 0.0), 0.005), 0.5)
        lo, hi = st["existingPvKwp"]
        answers = [("No", 0.0, 1 - p)]
        for k in _distinct([_round(lo, 0.5), _round(hi, 0.5)]):
            answers.append((f"Yes, about {k:g} kWp", k, p / 2))
        add("existingPv.kwp", answers)
    if i.existing_storage is None and st.get("existingStorageKwh"):
        p = min(max(st.get("existingStorageShare", 0.0), 0.005), 0.5)
        add("existingStorage.kwh", [("No", 0.0, 1 - p), (f"Yes, about {_round(st['existingStorageKwh'][0], 1):g} kWh", _round(st["existingStorageKwh"][0], 1), p)])
    return c


def capex_eur(v: Mapping[str, float]) -> float:
    """Installed price of a design (market.json mid): PV + battery + heat pump + wallbox."""
    pv, bat = float(v.get("pv_kwp") or 0.0), float(v.get("battery_kwh") or 0.0)
    return (float(economics.pv_price_eur(pv)) + float(economics.battery_price_eur(bat))
            + (economics.hp_price_eur() if (v.get("heat_pump_kw") or 0) > 0 else 0.0)
            + (economics.wallbox_price_eur() if (v.get("wallbox_kw") or 0) > 0 else 0.0))


def changed_components(a: Mapping[str, float], b: Mapping[str, float], wp: float, battery_step: float, locks: set) -> list[str]:
    """Components whose presence differs, or whose size differs by at least one catalog step."""
    out = []
    for comp in COMPONENTS:
        if comp in locks:
            continue
        t = TARGET[comp]
        x, y = float(a.get(t) or 0.0), float(b.get(t) or 0.0)
        if (x > 0) != (y > 0):
            out.append(comp)
        elif x > 0:
            if comp == "pv" and abs(x - y) >= PV_STEP_MODULES * wp / 1000 - 1e-9:
                out.append(comp)
            elif comp == "battery" and abs(x - y) >= battery_step - 1e-9:
                out.append(comp)
            elif comp == "heatPump" and abs(bl.HP_SIZES.index(min(bl.HP_SIZES, key=lambda s: abs(s - x))) -
                                            bl.HP_SIZES.index(min(bl.HP_SIZES, key=lambda s: abs(s - y)))) >= 1:
                out.append(comp)
    return out


_QUESTION = {
    "demandKwh": "How much electricity does the home use a year?",
    "building.roofMaxModules": "How many modules fit on the roof?",
    "ev.has": "Is there, or will there be, an electric car?",
    "heating.heatDemandKwh": "How much heat does the home use a year?",
    "existingPv.kwp": "Is there already a solar system on the roof?",
    "existingStorage.kwh": "Is there already a home battery?",
}
_PARTS = {"pv": "PV", "battery": "battery", "heatPump": "heat pump", "wallbox": "wallbox"}


def _why(field: str, st: dict, wp: float, comps: list[str]) -> str:
    rng = lambda q, to=1: f"{_round(q[0], to):,.0f} to {_round(q[-1], to):,.0f}"
    changes = " and ".join(_PARTS[c] for c in comps) or "the design"
    if field == "building.roofMaxModules":
        lo, hi = st["roofKwp"][0], st["roofKwp"][-1]
        return f"PV size for homes like this ranges {lo:.0f}-{hi:.0f} kWp; the roof decides it."
    if field == "demandKwh":
        return f"4,500 kWh is a common tool default. Homes like this use {rng(st['demand'], 100)} kWh, and the size of {changes} follows it."
    if field == "ev.has":
        return f"A car adds a wallbox and about 2,000 kWh of demand. {st.get('evShare', 0):.0%} of this installer's homes have one."
    if field == "heating.heatDemandKwh":
        return f"Heat pump size follows heat demand. Gas and oil homes use {rng(st['heatDemand'], 500)} kWh a year."
    if field == "existingPv.kwp":
        return f"Existing solar changes the new PV and whether a battery is added. {st.get('existingPvShare', 0):.0%} of homes already have some."
    return f"An existing battery changes whether a new one is added. {st.get('existingStorageShare', 0):.0%} of homes already have one."


def ask_next(inputs: HomeInputs, dz, wp: float, locks=(), max_items: int = MAX_ITEMS, budget_ms: float | None = None, executor=None) -> list[AskNext]:
    """Top questions for this home, best first (see module docstring). `dz` is the trained Designer; needs `dz.ask_stats`.
    `budget_ms`: the simulator-backed features of every new answer home cost ~60 ms each, so candidates are warmed in
    priority order and the ones that would exceed the budget are skipped this time (what was warmed stays cached).
    With an `executor` (process pool) all answer homes are simulated in parallel first and the budget is not needed."""
    stats = getattr(dz, "ask_stats", None)
    if not stats:
        return []
    st = stats.get(str(inputs.installer_id)) or stats["all"]
    locks = set(locks)
    cands = _candidates(inputs, st, wp, locks, inputs.provenance)
    if not cands:
        return []
    t0 = time.perf_counter()
    if executor is not None and (dz.feature_cfg or {}).get("physics"):
        physics.warm([row_from_inputs(_apply(inputs, c["field"], v), wp) for c in cands for _, v, _ in c["answers"]], executor)
        budget_ms = None
    if budget_ms is not None:
        kept = []
        for c in cands:
            if kept and (time.perf_counter() - t0) * 1000 > budget_ms:
                break
            dz._X(pd.DataFrame([row_from_inputs(_apply(inputs, c["field"], v), wp) for _, v, _ in c["answers"]]))
            kept.append(c)
        cands = kept
    homes = [inputs] + [_apply(inputs, c["field"], v) for c in cands for _, v, _ in c["answers"]]
    sizes = dz.design_batch(pd.DataFrame([row_from_inputs(h, wp) for h in homes]))
    designs = sizes.to_dict("records")
    bstep = float((dz._stats_for(inputs.installer_id) or {}).get("step", 1.0))
    base, cost0, k = designs[0], capex_eur(designs[0]), 1
    items: list[tuple[float, AskNext]] = []
    for c in cands:
        n = len(c["answers"])
        ds = designs[k:k + n]
        k += n
        comps, p_change, costs = set(), 0.0, [cost0]
        for (_, _, w), d in zip(c["answers"], ds):
            ch = changed_components(base, d, wp, bstep, locks)
            comps.update(ch)
            p_change += w if ch else 0.0
            costs.append(capex_eur({**d, **{TARGET[x]: base[TARGET[x]] for x in locks}}))
        swing = max(costs) - min(costs)
        score = p_change * swing
        if score < MIN_SCORE_EUR:
            continue
        ordered = [x for x in COMPONENTS if x in comps]
        items.append((score, AskNext(
            field=c["field"], question=_QUESTION[c["field"]], why=_why(c["field"], st, wp, ordered),
            impact=AskImpact(components=ordered, price_swing_eur=float(round(swing / 50) * 50)),
            answers=[AskAnswer(label=lbl, value=v) for lbl, v, _ in c["answers"]])))
    items.sort(key=lambda t: -t[0])
    return [a for _, a in items[:max_items]]


def patch_artifact(path=None, processed=None) -> None:
    """Add `ask_stats` to an existing designer artifact from the processed data, leaving the trained models untouched."""
    from engine.design import DEFAULT_DATA_DIR, DEFAULT_MODEL_PATH
    from engine.policy.designer import Designer
    from engine.policy.features import training_frame
    path, processed = path or DEFAULT_MODEL_PATH, processed or DEFAULT_DATA_DIR
    df = training_frame(pd.read_parquet(processed / "projects.parquet"), pd.read_parquet(processed / "options.parquet"))
    dz = Designer.load(path, apply_config=False)
    dz.ask_stats = stats_from(df)
    dz.save(path)
    print(f"ask_stats for {', '.join(dz.ask_stats)} written to {path}")


if __name__ == "__main__":
    import argparse
    from pathlib import Path
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--patch", action="store_true", help="add ask_stats to services/engine/models/designer.joblib")
    ap.add_argument("--data", type=Path, default=None)
    a = ap.parse_args()
    if a.patch:
        patch_artifact(processed=a.data)
