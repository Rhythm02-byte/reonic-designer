"""baseline-0 design service: installer-median bundle conditioned on simple rules (no simulation, no learning yet)."""
from __future__ import annotations

import json
import logging
import os
import time
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

from engine import baseline as bl
from engine import sim
from engine.models.schemas import (
    BatteryDesign, BatteryPoint, BomLine, Curves, DesignRequest, DesignResponse, Flag, HeatPumpDesign, HomeInputs,
    Interval, Metrics, Physics, Provenance, PvDesign, PvPoint, ReasonCode, SimulateRequest, SystemDesign, ValidateRequest,
    ValidateResponse, WallboxDesign,
)
from engine.ask_next import ask_next
from engine.plausibility import input_flags
from engine.etl.normalize import DEFAULT_DEMAND_KWH
from engine.policy import rules
from engine.policy.designer import hit_to_flag
from engine.policy.features import row_from_inputs

BASELINE_VERSION = "baseline-0"
POLICY_VERSION = "policy-1"
ENGINE_VERSION = BASELINE_VERSION  # app title; the live version is Store.engine_version
DEFAULT_DATA_DIR = Path(__file__).resolve().parents[3] / "data" / "processed"
DEFAULT_MODEL_PATH = Path(__file__).resolve().parents[1] / "models" / "designer.joblib"
PV_YIELD_KWH_PER_KWP = 950.0  # crude reference-site yield; no simulation in baseline-0


class Store:
    """Per-installer stats + catalogs from data/processed (falls back to built-in aggregates)."""

    def __init__(self, data_dir: Path | None = None, model_path: Path | None = None):
        self.dir = Path(data_dir or os.environ.get("ENGINE_DATA_DIR") or DEFAULT_DATA_DIR)
        # the trained policy is picked up from the default location only when no explicit data dir is given
        if model_path is None and data_dir is None:
            model_path = Path(os.environ.get("ENGINE_MODEL_PATH") or DEFAULT_MODEL_PATH)
        self.designer = None
        if model_path is not None and Path(model_path).exists():
            from engine.policy.designer import Designer
            self.designer = Designer.load(model_path)
        self.stats: dict[str, bl.Stats] = {}
        self.catalogs: dict[str, dict] = {}
        pp, op = self.dir / "projects.parquet", self.dir / "options.parquet"
        if pp.exists() and op.exists():
            P, O = pd.read_parquet(pp), pd.read_parquet(op)
            J = O[O.is_primary].merge(P, on=["project_id", "installer_id"])
            for inst, g in J.groupby("installer_id"):
                self.stats[inst] = bl.fit_stats(g, inst)
            self.stats["all"] = bl.fit_stats(J, "all")
        for f in self.dir.glob("catalog_*.json"):
            self.catalogs[f.stem.removeprefix("catalog_")] = json.loads(f.read_text(encoding="utf-8"))

    @property
    def synthetic(self) -> bool:
        """True when the engine runs on synthetic / fallback data rather than the real dataset."""
        return os.environ.get("ENGINE_SYNTHETIC") == "1" or self.designer is None or bool(getattr(self.designer, "synthetic", False))

    @property
    def installers(self) -> list[str]:
        if self.designer is not None and self.designer.installers:
            return list(self.designer.installers)
        return sorted(k for k in self.stats if k != "all")

    @property
    def engine_version(self) -> str:
        return POLICY_VERSION if self.designer is not None else BASELINE_VERSION

    def get(self, installer_id: str) -> tuple[bl.Stats, bool]:
        if installer_id in self.stats:
            return self.stats[installer_id], True
        return self.stats.get("all", bl.FALLBACK), False


def input_provenance(i: HomeInputs) -> dict[str, Provenance]:
    """Where each key input of the design comes from, keyed by dotted camelCase path ('ev.has', 'heating.type').

    entered = the caller marked it in `inputs.provenance`; derived = the engine estimated it from other inputs;
    national_default = nothing says the user typed it (4,500 kWh demand is flagged as looking like a tool default)."""
    given = i.provenance
    out: dict[str, Provenance] = {}

    def put(key: str, derived: bool = False, confidence: float = 0.6) -> None:
        if key in given:
            out[key] = given[key]
        elif derived:
            out[key] = Provenance(source="derived", confidence=0.5)
        else:
            out[key] = Provenance(source="national_default", confidence=confidence)

    put("demandKwh", confidence=0.3 if abs(i.demand_kwh - DEFAULT_DEMAND_KWH) < 1e-6 else 0.6)
    put("persons")
    put("loadProfile")
    put("priceEurKwh")
    put("heating.type")
    put("ev.has")
    if i.ev.has:
        put("ev.kmPerYear", derived=i.ev.km_per_year is None)
    if i.building and i.building.roof_max_modules is not None:
        put("building.roofMaxModules")
    h = i.heating
    if h.heat_demand_kwh is not None or h.fuel_kwh or h.cost_eur_year:
        put("heating.heatDemandKwh", derived=h.heat_demand_kwh is None)
    return out


def home_mapping(i: HomeInputs) -> dict:
    h = i.heating
    heat = h.heat_demand_kwh
    if heat is None and h.fuel_kwh:
        heat = h.fuel_kwh * 0.9
    if heat is None and h.cost_eur_year and h.type == "Gas":
        heat = h.cost_eur_year / 0.122
    return {"demand_kwh": i.demand_kwh, "has_ev": i.ev.has, "heating_type": h.type, "heat_demand_kwh": heat,
            "has_existing_wallbox": i.existing_wallbox is not None}


def _bom(cat: dict | None, d: SystemDesign) -> list[BomLine]:
    if not cat:
        return []
    out: list[BomLine] = []

    def nearest(prods: list[dict], size: float) -> dict | None:
        prods = [p for p in prods if p.get("size")]
        return min(prods, key=lambda p: (abs(p["size"] - size), -p["count"])) if prods else None

    if d.pv is not None and d.pv.modules:
        out.append(BomLine(technology="pv", component_type="Module", component_name=f"PV module {d.pv.module_wp:g} Wp",
                           quantity=d.pv.modules, quantity_units="pcs"))
        inv = nearest(cat.get("inverters") or [], d.pv.kwp)  # inverter AC size ~ array kWp: the installer's closest model
        if inv:
            out.append(BomLine(technology="pv", component_type="Inverter", component_name=inv["name"], component_brand=inv["brand"]))
    for key, comp, tech, ctype in (("battery", d.battery, "ses", "BatteryStorage"),
                                   ("wallbox", d.wallbox, "wallbox", "Wallbox"),
                                   ("heatpump", d.heat_pump, "heatpump", "Heatpump")):
        if comp is None:
            continue
        prods = cat["batteries"] if key == "battery" else cat["wallboxes"] if key == "wallbox" else cat["heatPumps"]
        size = comp.kwh if key == "battery" else comp.kw
        p = nearest(prods, size)
        if p:
            out.append(BomLine(technology=tech, component_type=ctype, component_name=p["name"], component_brand=p["brand"]))
    for s in cat["services"]:
        if s["share"] >= 0.8:
            out.append(BomLine(technology=s["technology"], line_item_function=s["lineItemFunction"], component_type=s["componentType"],
                               component_name=s["componentName"], component_brand=s["componentBrand"],
                               quantity=s["medianQuantity"], quantity_units=s["quantityUnits"]))
    return out


def _to_design(pred: bl.Pred, wp: float, id_: str, label: str | None = None, roof_modules: int | None = None) -> SystemDesign:
    modules = max(1, round(pred.kwp * 1000 / wp))
    if roof_modules is not None:
        modules = max(1, min(modules, roof_modules))  # the roof is a hard cap
    return SystemDesign(
        id=id_, label=label,
        pv=PvDesign(modules=modules, module_wp=wp, kwp=round(modules * wp / 1000, 2)),
        battery=BatteryDesign(kwh=pred.battery_kwh) if pred.battery_kwh > 0 else None,
        wallbox=WallboxDesign(kw=11.0) if pred.wallbox else None,
        heat_pump=HeatPumpDesign(kw=pred.hp_kw) if pred.hp_kw > 0 else None,
    )


def _apply_locks(d: SystemDesign, req: DesignRequest) -> SystemDesign:
    if not req.current:
        return d
    for lock in req.locks:
        attr = {"pv": "pv", "battery": "battery", "heatPump": "heat_pump", "wallbox": "wallbox"}[lock]
        setattr(d, attr, getattr(req.current, attr))
    d.locks = list(req.locks)
    return d


log = logging.getLogger("engine.design")
_POOL = ThreadPoolExecutor(max_workers=2, thread_name_prefix="sim")  # numpy releases the GIL: sweeps and the proposal run overlap
PHYSICS_POOL = None  # process pool for the simulator-backed features of "Ask next" answer homes (set by the API lifespan)
ASK_BUDGET_MS = 150.0  # simulator-backed features of the answer homes; see ask_next()
_ASK_POOL = ThreadPoolExecutor(max_workers=1, thread_name_prefix="ask")
ORIENTATIONS = {"S", "E", "W", "EW"}


def start_physics_pool(workers: int | None = None):
    """Spawn (and warm) the worker processes; ENGINE_PHYS_WORKERS=0 disables. Never raises: no pool = in-process with a budget."""
    global PHYSICS_POOL
    n = int(os.environ.get("ENGINE_PHYS_WORKERS", "4")) if workers is None else workers
    if n <= 0 or PHYSICS_POOL is not None:
        return PHYSICS_POOL
    try:
        from concurrent.futures import ProcessPoolExecutor
        from engine.policy import physics
        PHYSICS_POOL = ProcessPoolExecutor(max_workers=n)
        for f in [PHYSICS_POOL.submit(physics._physics_one, {"demand_kwh": 3000.0 + k}) for k in range(n)]:
            f.result(timeout=60)
    except Exception:  # noqa: BLE001
        log.exception("physics pool unavailable")
        PHYSICS_POOL = None
    return PHYSICS_POOL


def sim_home(i: HomeInputs) -> dict:
    """HomeInputs -> the simulator's home dict (same camelCase keys; a free-text orientation the simulator cannot read is dropped)."""
    h = i.model_dump(by_alias=True, exclude_none=True, exclude={"provenance"})
    b = h.get("building")
    if b and str(b.get("orientation", "")).strip().upper() not in ORIENTATIONS:
        b.pop("orientation", None)
    return h


def sim_system(d: SystemDesign) -> dict:
    out: dict = {}
    if d.pv and d.pv.kwp > 0:
        out["pv"] = {"kwp": d.pv.kwp}
    if d.battery and d.battery.kwh > 0:
        out["battery"] = {"kwh": d.battery.kwh}
    if d.wallbox:
        out["wallbox"] = {"kw": d.wallbox.kw}
    if d.heat_pump:
        out["heatPump"] = {"kw": d.heat_pump.kw}
    return out


def _key(x) -> str:
    return json.dumps(x, sort_keys=True, separators=(",", ":"))


@lru_cache(maxsize=512)
def _simulate_cached(home_key: str, sys_key: str) -> dict:
    return sim.simulate(json.loads(home_key), json.loads(sys_key))


@lru_cache(maxsize=512)
def _sweeps_cached(home_key: str, sys_key: str, sizes: tuple, kwps: tuple) -> tuple[dict, list]:
    home, system = json.loads(home_key), json.loads(sys_key)
    rec = sim.recommend_battery(home, system, list(sizes))
    return rec, (sim.sweep_pv(home, system, list(kwps)) if kwps else [])


def _metrics(r: dict, night: float | None = None, typical: bool = False) -> Metrics:
    return Metrics(
        pv_yield_kwh=r["pvYieldKwh"], self_consumption=r["selfConsumption"], autarky=r["autarky"],
        grid_import_kwh=r["gridImportKwh"], feed_in_kwh=r["feedInKwh"], savings_eur_year=r["savingsEurYear"],
        payback_years=r["paybackYears"], npv20=r["npv20"], price_eur=r["priceEur"],
        full_cycles_per_year=r["fullCyclesPerYear"], night_load_kwh=r.get("nightLoadKwh", night),
        hourly_typical_days=r.get("hourlyTypicalDays") if typical else None)


def simulate_metrics(home: HomeInputs, system: SystemDesign) -> Metrics:
    return _metrics(_simulate_cached(_key(sim_home(home)), _key(sim_system(system))), typical=True)


def _pv_kwps(d: SystemDesign, points: int = 7) -> tuple[float, ...]:
    """Proposed kWp +-40% in whole modules (at most `points` values, the proposal always included)."""
    if not d.pv or d.pv.modules <= 0:
        return ()
    m, wp = d.pv.modules, d.pv.module_wp
    lo, hi = max(1, round(0.6 * m)), max(round(1.4 * m), m + 1)
    mods = sorted({int(x) for x in np.linspace(lo, hi, min(points, hi - lo + 1)).round()} | {m})
    return tuple(round(k * wp / 1000, 3) for k in mods)


def _bat_variant(base: SystemDesign, kwh: float, id_: str, label: str) -> SystemDesign:
    d = base.model_copy(deep=True)
    d.id, d.label, d.locks = id_, label, []
    d.battery = BatteryDesign(kwh=kwh) if kwh > 0 else None
    return d


def attach_metrics(response: DesignResponse, home: HomeInputs, battery_sizes=None, locks=(),
                   replace_alternatives: bool = True) -> None:
    """Fill `response.metrics`, `curves` and `physics` from the hourly simulator (engine/sim).

    One battery sweep over the installer's sizes + 0 (+ every battery in the response) yields the economic optimum, the
    max-independence variant, the 'why this size' curve and the metrics of every battery variant; one PV sweep gives
    the kWp curve. With `replace_alternatives` the alternatives become: without battery, economic battery, max
    independence (battery variants are skipped when the battery is locked). Amber flag R06 when the proposed battery is
    >= 2 sizes above the economic optimum. Results are cached by input hash; a simulator failure never breaks /design."""
    try:
        _attach_metrics(response, home, battery_sizes, locks, replace_alternatives)
    except Exception:  # noqa: BLE001 - physics is an add-on to the policy
        log.exception("attach_metrics failed")
        if not response.metrics:
            for d in [response.proposal, *response.alternatives]:
                response.metrics[d.id] = Metrics(pv_yield_kwh=round(d.pv.kwp * PV_YIELD_KWH_PER_KWP) if d.pv else None)


def _attach_metrics(response, home, battery_sizes, locks, replace_alternatives) -> None:
    prop = response.proposal
    pb = prop.battery.kwh if prop.battery else 0.0
    steps = sorted({0.0, *(float(x) for x in (battery_sizes or sim.DEFAULT_SIZES) if x >= 0)})
    sizes = tuple(sorted({*steps, pb, *(a.battery.kwh for a in response.alternatives if a.battery)}))
    home_k, sys_k = _key(sim_home(home)), _key(sim_system(prop))
    typical = _POOL.submit(_simulate_cached, home_k, sys_k)
    rec, pv_rows = _sweeps_cached(home_k, sys_k, sizes, _pv_kwps(prop))
    by_kwh = {round(r["batteryKwh"], 3): r for r in rec["rows"]}
    night = rec["nightLoadKwh"]

    response.metrics[prop.id] = _metrics(typical.result(), night, typical=True)
    eco, mx = rec["economic"]["batteryKwh"], rec["maxAutarky"]["batteryKwh"]

    if replace_alternatives:
        alts: list[SystemDesign] = []
        taken = {pb}
        if "battery" not in locks:
            for kwh, label in ((0.0, "Without battery"), (eco, "Economic battery"), (mx, "Max independence")):
                if kwh in taken or (kwh == 0 and label != "Without battery"):
                    continue
                taken.add(kwh)
                alts.append(_bat_variant(prop, kwh, f"alt-{len(alts) + 1}", label))
        response.alternatives = alts
    for a in response.alternatives:
        row = by_kwh.get(round(a.battery.kwh if a.battery else 0.0, 3))
        if row is not None:
            response.metrics[a.id] = _metrics(row, night)

    response.curves = Curves(
        battery=[BatteryPoint(kwh=r["batteryKwh"], autarky=r["autarky"], self_consumption=r["selfConsumption"],
                              savings_eur_year=r["savingsEurYear"], payback_years=r["paybackYears"], npv20=r["npv20"],
                              full_cycles_per_year=r["fullCyclesPerYear"]) for r in rec["rows"]],
        pv=[PvPoint(kwp=r["pvKwp"], autarky=r["autarky"], self_consumption=r["selfConsumption"],
                    savings_eur_year=r["savingsEurYear"], payback_years=r["paybackYears"], npv20=r["npv20"],
                    pv_yield_kwh=r["pvYieldKwh"]) for r in pv_rows])
    response.physics = Physics(economic_kwh=eco, max_autarky_kwh=mx, night_load_kwh=night)

    ladder = sorted({*steps, eco, pb})
    n_above = ladder.index(pb) - ladder.index(eco)
    if pb > 0 and n_above >= 2 and round(pb, 3) in by_kwh:
        a, e = by_kwh[round(pb, 3)], by_kwh[round(eco, 3)]
        d_aut, d_sav, d_npv = (a["autarky"] - e["autarky"]) * 100, a["savingsEurYear"] - e["savingsEurYear"], a["npv20"] - e["npv20"]
        what = f"the economic optimum ({eco:g} kWh)" if eco > 0 else "no battery (no size pays back within the guard rails)"
        response.flags.append(Flag(
            severity="warn", code="R06", component="battery",
            message=(f"R06: the proposed {pb:g} kWh battery is {n_above} sizes above {what}. The extra storage adds "
                     f"{d_aut:+.1f} pp autarky and {d_sav:+,.0f} EUR/yr savings, but changes the 20-year NPV by {d_npv:+,.0f} EUR.")))


def design(req: DesignRequest, store: Store) -> DesignResponse:
    if store.designer is not None:
        return design_policy(req, store)
    t0 = time.perf_counter()
    i = req.inputs
    stats, known = store.get(i.installer_id)
    cat = store.catalogs.get(i.installer_id)
    home = home_mapping(i)
    k = bl.demand_bucket(i.demand_kwh)
    pred = bl.conditioned(stats, home)
    wps = {float(k): v for k, v in (cat or {}).get("moduleWp", {}).items()}
    wp = max(wps, key=wps.get) if wps and sum(wps.values()) >= 30 else stats.module_wp  # few module lines -> assume 450 W

    roof = i.building.roof_max_modules if i.building else None
    proposal = _apply_locks(_to_design(pred, wp, "proposal", "Recommended", roof), req)
    alts: list[SystemDesign] = []
    sizes = stats.battery_sizes
    if pred.battery_kwh > 0 and pred.battery_kwh in sizes:
        idx = sizes.index(pred.battery_kwh)
        for j, label in ((idx - 1, "Smaller battery"), (idx + 1, "Larger battery")):
            if 0 <= j < len(sizes) and "battery" not in req.locks:
                alts.append(_to_design(bl.Pred(pred.kwp, sizes[j], pred.wallbox, pred.hp_kw), wp, f"alt-{len(alts) + 1}", label, roof))
    metrics = {d.id: Metrics(pv_yield_kwh=round(d.pv.kwp * PV_YIELD_KWH_PER_KWP) if d.pv else None) for d in [proposal, *alts]}

    kq, bq = bl._pick(stats.kwp, k), bl._pick(stats.battery, k)
    conf = {"pv": Interval(p10=kq[0], p50=kq[1], p90=kq[2], prob_included=1.0),
            "battery": Interval(p10=bq[0], p50=bq[1], p90=bq[2], prob_included=bl._pick(stats.battery_share, k)),
            "wallbox": Interval(p10=11, p50=11, p90=11, prob_included=0.55 if i.ev.has else stats.wallbox_share * 0.5)}
    reasons = [ReasonCode(code="PV_DEMAND_BUCKET", component="pv", value=proposal.pv.kwp if proposal.pv else None,
                          evidence={"demand_kwh": i.demand_kwh, "bucket": k, "installer_median_kwp": kq[1]})]
    if proposal.battery:
        reasons.append(ReasonCode(code="BATTERY_INSTALLER_MEDIAN", component="battery", value=proposal.battery.kwh,
                                  evidence={"bucket": k, "installer_attach_rate": round(bl._pick(stats.battery_share, k), 2)}))
    if proposal.wallbox:
        reasons.append(ReasonCode(code="WALLBOX_EV", component="wallbox", value=11.0, evidence={"has_ev": True}))
    if proposal.heat_pump:
        reasons.append(ReasonCode(code="HP_HEAT_DEMAND", component="heatPump", value=proposal.heat_pump.kw,
                                  evidence={"heat_demand_kwh": home["heat_demand_kwh"], "full_load_hours": bl.HP_FULL_LOAD_HOURS}))
    flags: list[Flag] = []
    if abs(i.demand_kwh - 4500) < 1e-6:
        flags.append(Flag(severity="info", code="DEMAND_DEFAULT_LIKE", message="4,500 kWh is a common tool default; confirm the real consumption."))
    if not known:
        flags.append(Flag(severity="warn", code="INSTALLER_UNKNOWN", message="No history for this installer; using pooled statistics."))
    if i.existing_pv and not i.existing_pv.trusted:
        flags.append(Flag(severity="warn", code="EXISTING_PV_AMBIGUOUS", component="pv", message="Existing PV was built in or after the offer year; it may be the planned system."))
    flags.extend(input_flags(i))  # ours: implausible inputs (engine/plausibility.py)

    resp = DesignResponse(
        proposal=proposal, alternatives=alts, metrics=metrics, confidence=conf, reasons=reasons, flags=flags,
        bom=_bom(cat, proposal), provenance=input_provenance(i),
        engine_version=BASELINE_VERSION, latency_ms=0.0,
    )
    attach_metrics(resp, i, stats.battery_sizes, req.locks, replace_alternatives=False)
    resp.latency_ms = round((time.perf_counter() - t0) * 1000, 2)
    return resp


# ---- learned policy (policy-1) ---------------------------------------------------------------------------------

_LOCK_TARGET = {"pv": "pv_kwp", "battery": "battery_kwh", "heatPump": "heat_pump_kw", "wallbox": "wallbox_kw"}


def _module_wp(store: Store, installer_id: str) -> float:
    cat = store.catalogs.get(installer_id)
    wps = {float(k): v for k, v in (cat or {}).get("moduleWp", {}).items()}
    if wps and sum(wps.values()) >= 30:
        return max(wps, key=wps.get)
    return 450.0  # few module lines -> assume 450 W


def system_from_values(values: dict[str, float], wp: float, id_: str, label: str | None = None) -> SystemDesign:
    kwp = values.get("pv_kwp", 0.0)
    modules = max(1, round(kwp * 1000 / wp)) if kwp > 0 else 0
    return SystemDesign(
        id=id_, label=label,
        pv=PvDesign(modules=modules, module_wp=wp, kwp=round(modules * wp / 1000, 2)) if kwp > 0 else None,
        battery=BatteryDesign(kwh=round(values["battery_kwh"], 2)) if values.get("battery_kwh", 0) > 0 else None,
        wallbox=WallboxDesign(kw=values["wallbox_kw"]) if values.get("wallbox_kw", 0) > 0 else None,
        heat_pump=HeatPumpDesign(kw=values["heat_pump_kw"]) if values.get("heat_pump_kw", 0) > 0 else None,
    )


def values_from_system(d: SystemDesign | None) -> dict[str, float]:
    d = d or SystemDesign()
    return {"pv_kwp": d.pv.kwp if d.pv else 0.0, "battery_kwh": d.battery.kwh if d.battery else 0.0,
            "heat_pump_kw": d.heat_pump.kw if d.heat_pump else 0.0, "wallbox_kw": d.wallbox.kw if d.wallbox else 0.0}


def design_policy(req: DesignRequest, store: Store) -> DesignResponse:
    """Trained designer: component chain + rules + explanations. A lock keeps that component's value from `req.current`
    (a locked component absent from `current` means 'none')."""
    t0 = time.perf_counter()
    i, dz = req.inputs, store.designer
    cur = values_from_system(req.current)
    locked = {_LOCK_TARGET[c]: cur[_LOCK_TARGET[c]] for c in req.locks}
    wp = _module_wp(store, i.installer_id)
    res = dz.design(i, locked, wp)

    proposal = system_from_values(res.values, wp, "proposal", "Recommended")
    if "pv" in req.locks and req.current and req.current.pv:
        proposal.pv = req.current.pv  # keep the planner's exact module choice
    proposal.locks = list(req.locks)
    resp = DesignResponse(
        proposal=proposal, alternatives=[], confidence=res.confidence(), reasons=res.reasons, flags=list(res.flags),
        bom=_bom(store.catalogs.get(i.installer_id), proposal),
        provenance=input_provenance(i),
        engine_version=POLICY_VERSION, latency_ms=0.0)
    if abs(i.demand_kwh - DEFAULT_DEMAND_KWH) < 1e-6:
        resp.flags.append(Flag(severity="info", code="DEMAND_DEFAULT_LIKE", message="4,500 kWh is a common tool default; confirm the real consumption."))
    if i.installer_id not in dz.installers:
        resp.flags.append(Flag(severity="warn", code="INSTALLER_UNKNOWN", message="No history for this installer; the policy falls back to pooled behaviour."))
    if i.existing_pv and not i.existing_pv.trusted:
        resp.flags.append(Flag(severity="warn", code="EXISTING_PV_AMBIGUOUS", component="pv", message="Existing PV was built in or after the offer year; it may be the planned system."))
    resp.flags.extend(input_flags(i))  # ours: implausible inputs (engine/plausibility.py)
    st = dz._stats_for(i.installer_id)
    # value of information: policy only, one batch; runs beside the simulator sweeps and never breaks /design
    asking = _ASK_POOL.submit(ask_next, i, dz, wp, req.locks, budget_ms=ASK_BUDGET_MS, executor=PHYSICS_POOL)
    attach_metrics(resp, i, (st or {}).get("sizes") or list(sim.DEFAULT_SIZES), req.locks)
    try:
        resp.ask_next = asking.result()
    except Exception:  # noqa: BLE001
        log.exception("ask_next failed")
    resp.latency_ms = round((time.perf_counter() - t0) * 1000, 2)
    return resp


def validate(req: ValidateRequest, store: Store) -> ValidateResponse:
    """Planner's own system -> hard-rule flags (R01-R05) + how it compares with similar past homes."""
    values = values_from_system(req.system)
    if store.designer is None:  # no trained model: rules only
        row = row_from_inputs(req.inputs)
        flags = [hit_to_flag(h) for h in rules.audit(values, rules.ctx_from_row(row), {})]
        return ValidateResponse(flags=flags, metrics=_safe_metrics(req.inputs, req.system), engine_version=store.engine_version)
    v = store.designer.validate(req.inputs, values, _module_wp(store, req.inputs.installer_id))
    return ValidateResponse(flags=v.flags, percentiles=v.percentiles, similar_share=v.similar_share,
                            n_similar=v.n_similar, metrics=_safe_metrics(req.inputs, req.system), engine_version=store.engine_version)


def _safe_metrics(home: HomeInputs, system: SystemDesign) -> Metrics | None:
    try:
        return simulate_metrics(home, system)
    except Exception:  # noqa: BLE001 - physics must never break validation
        log.exception("simulation failed")
        return None


def simulate(req: SimulateRequest) -> Metrics:
    """Homeowner variant switching: simulator only, no policy."""
    return simulate_metrics(req.inputs, req.system)
