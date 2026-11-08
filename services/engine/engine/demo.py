"""Read-only endpoints for the demo UI: /meta (form + catalogs), /eval/summary (offline backtest) and /holdout (real past
homes with the expert's design next to ours, from the temporal TEST split, model trained on the train split only)."""
from __future__ import annotations

import json
import os
import threading
from pathlib import Path
from typing import Callable

import numpy as np
import pandas as pd

from engine import baseline as bl
from engine import sim
from engine.models.schemas import (
    EvalModelScores, EvalSummary, HoldoutResponse, HoldoutRow, HoldoutSystem, HomeInputs, MetaField, MetaResponse, MetaTarget,
)
from engine.policy.designer import Designer

REPO_ROOT = Path(__file__).resolve().parents[3]
EVAL_RESULTS = REPO_ROOT / "eval" / "results" / "latest.json"
HOLDOUT_CUTOFF = pd.Timestamp("2025-12-31 23:59:59.999")  # same cutoff as the eval's temporal split (train+validation | test)
TOLERANCES = {"pv": 0.2, "battery": 0.25, "heatPump": 0.25}  # relative size error that still counts as an expert match
HEATING = ["Gas", "Oil", "Heatpump", "OtherRenewable", "OtherNonRenewable", "Unknown"]
LOAD_PROFILES = ["H0", "FamilyOfFour", "HomeOffice", "Senior", "Custom"]
ROOFS = ["concrete_tile", "clay_tile", "flat", "flat_ew", "metal", "bitumen", "slate", "beaver_tail", "trapezoid",
         "standing_seam", "other", "unknown"]

FIELDS = [
    MetaField(name="demandKwh", kind="number", label="Electricity demand", unit="kWh/yr"),
    MetaField(name="priceEurKwh", kind="number", label="Electricity price", unit="EUR/kWh"),
    MetaField(name="loadProfile", kind="choice", choices=LOAD_PROFILES, label="Load profile"),
    MetaField(name="persons", kind="number", label="Persons in the home"),
    MetaField(name="homeOffice", kind="bool", label="Works from home"),
    MetaField(name="flexTariff", kind="bool", label="Flexible tariff"),
    MetaField(name="ev.has", kind="bool", label="Electric vehicle"),
    MetaField(name="ev.kmPerYear", kind="number", label="EV driving distance", unit="km/yr"),
    MetaField(name="existingPv.kwp", kind="number", label="Existing PV", unit="kWp"),
    MetaField(name="existingStorage.kwh", kind="number", label="Existing battery", unit="kWh"),
    MetaField(name="heating.type", kind="choice", choices=HEATING, label="Current heating"),
    MetaField(name="heating.heatDemandKwh", kind="number", label="Heat demand", unit="kWh/yr"),
    MetaField(name="heating.fuelKwh", kind="number", label="Fuel use", unit="kWh/yr"),
    MetaField(name="building.sqm", kind="number", label="Living area", unit="m2"),
    MetaField(name="building.builtYear", kind="number", label="Year built"),
    MetaField(name="building.roofMaxModules", kind="number", label="Roof fits about", unit="modules"),
    MetaField(name="building.roofType", kind="choice", choices=ROOFS, label="Roof type"),
]

DEFAULT_CATALOG = {
    "pv_kwp": [round(3.0 + 0.9 * k, 1) for k in range(0, 31)],  # ~2 modules apart, 3-30 kWp
    "battery_kwh": [float(x) for x in sim.DEFAULT_SIZES if x > 0],
    "heat_pump_kw": list(bl.HP_SIZES),
    "wallbox_kw": [11.0, 22.0],
}
TARGET_META = (("pvKwp", "pv_kwp", "PV", "kWp"), ("batteryKwh", "battery_kwh", "Battery", "kWh"),
               ("heatPumpKw", "heat_pump_kw", "Heat pump", "kW"), ("wallboxKw", "wallbox_kw", "Wallbox", "kW"))


def meta(designer: Designer | None, installers: list[str], synthetic: bool, engine_version: str) -> MetaResponse:
    cat = designer.catalog if designer is not None else {}
    targets = [MetaTarget(name=n, label=label, unit=unit,  # type: ignore[arg-type]
                          catalog=sorted({float(x) for x in (cat.get(t) or DEFAULT_CATALOG[t]) if x > 0}))
               for n, t, label, unit in TARGET_META]
    return MetaResponse(fields=FIELDS, targets=targets, installers=installers, synthetic=synthetic, engine_version=engine_version)


# ---- /eval/summary ------------------------------------------------------------------------------------------------
def _scores(o: dict) -> EvalModelScores:
    p = o["overall"]["policy"]
    return EvalModelScores(ems=o["overall"]["expertMatchPrimary"], whole_design=p["wholeDesignWithinTolerance"],
                           pv=p["pv_kwp"]["withinTolerance"], battery=p["battery_kwh"]["withinTolerance"],
                           heat_pump=p["heat_pump_kw"]["withinTolerance"], wallbox=p["wallbox_kw"]["withinTolerance"])


def eval_summary(path: Path | None = None) -> EvalSummary | None:
    """Compact view of eval/results/latest.json (None when there are no results yet or the file is unreadable)."""
    p = Path(path or os.environ.get("ENGINE_EVAL_RESULTS") or EVAL_RESULTS)
    if not p.exists():
        return None
    try:
        r = json.loads(p.read_text(encoding="utf-8"))
        t = r["splits"]["temporal"]
        models = {m: _scores(v) for m, v in t["baselines"].items() if m in ("B0", "B0c", "B1", "M1", "H1")}
    except (ValueError, KeyError, TypeError):
        return None
    sel = r.get("selection")
    chosen = (sel or {}).get("chosen", {}).get("model")
    served = (r.get("served") or {}).get("test")  # `pnpm eval`: baselines + the SERVED config on the 2026 test (the pitch numbers)
    if served:
        models = {("ours" if m == "ours" else m): EvalModelScores(
            ems=s.get("ems"), whole_design=s.get("wholeDesign"), pv=s.get("pv"), battery=s.get("battery"),
            heat_pump=s.get("heatPump"), wallbox=s.get("wallbox")) for m, s in served["models"].items()}
        return EvalSummary(split="temporal", n_test=int(served["n"]), chosen="ours", models=models, selection=sel,
                           generated_at=r.get("generatedAt"), tolerances=TOLERANCES)
    if chosen is None:
        learned = {m: s.ems or 0 for m, s in models.items() if m in ("M1", "H1")}
        chosen = max(learned, key=learned.get) if learned else next(iter(models), "")
    return EvalSummary(split="temporal", n_test=int(t["nTest"]), chosen=chosen, models=models, selection=sel,
                       generated_at=r.get("generatedAt"), tolerances=TOLERANCES)


# ---- /holdout -----------------------------------------------------------------------------------------------------
FAMILY_TO_PROFILE = {"H0": "H0", "family": "FamilyOfFour", "home_office": "HomeOffice", "senior": "Senior", "custom": "Custom",
                     "other": "Other"}


def _f(x) -> float | None:
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    return None if np.isnan(v) else v


def _flag(x) -> bool | None:
    if x is None or x is pd.NA or (isinstance(x, float) and np.isnan(x)):
        return None
    return bool(x)


def inputs_from_row(row: dict) -> HomeInputs:
    """Canonical frame row -> API HomeInputs (inverse of features.row_from_inputs, as far as the API can express it)."""
    d: dict = {"installerId": str(row["installer_id"])}
    for key, col in (("demandKwh", "demand_kwh"), ("priceEurKwh", "price_eur_kwh"), ("priceEscalation", "price_escalation")):
        if _f(row.get(col)) is not None:
            d[key] = _f(row[col])
    fam = row.get("load_family")
    if isinstance(fam, str):
        d["loadProfile"] = FAMILY_TO_PROFILE.get(fam, "Other")
    if _flag(row.get("flex_tariff")) is not None:
        d["flexTariff"] = _flag(row["flex_tariff"])
    d["ev"] = {"has": bool(_flag(row.get("has_ev"))), **({"kmPerYear": _f(row["ev_km"])} if _f(row.get("ev_km")) is not None else {})}
    if _flag(row.get("has_existing_pv")):
        d["existingPv"] = {"kwp": _f(row.get("existing_pv_kwp")) or 0.0, "trusted": bool(_flag(row.get("existing_pv_trusted")))}
    if _flag(row.get("has_existing_storage")):
        d["existingStorage"] = {"kwh": _f(row.get("existing_storage_kwh")) or 0.0, "trusted": bool(_flag(row.get("existing_storage_trusted")))}
    if _flag(row.get("has_existing_wallbox")):
        d["existingWallbox"] = {"kw": 11.0}
    h = {"type": row.get("heating_type") if row.get("heating_type") in HEATING else "Unknown"}
    if _f(row.get("heat_demand_kwh")) is not None:
        h["heatDemandKwh"] = _f(row["heat_demand_kwh"])
    if h["type"] == "Heatpump" and _f(row.get("hp_elec_existing_kwh")) is not None:
        h["hpElecKwh"] = _f(row["hp_elec_existing_kwh"])
    d["heating"] = h
    return HomeInputs.model_validate(d)


def pick_diverse(T: pd.DataFrame, n: int, seed: int = 0) -> list[int]:
    """Row positions of `n` test homes covering the interesting segments (battery / no battery, EV, heat pump, no PV,
    existing PV) round-robin, so every segment shows up before any repeats. Deterministic."""
    rng = np.random.default_rng(seed)
    T = T.reset_index(drop=True)
    bat, pv, hp = T["battery_kwh"].fillna(0), T["pv_kwp"], T["heat_pump_kw"]
    cats = [bat > 0, bat <= 0, T["has_ev"].fillna(False).astype(bool), hp.gt(0),
            pv.eq(0), T["has_existing_pv"].fillna(False).astype(bool)]
    cats = [c.to_numpy() for c in cats if c.any()]
    chosen: list[int] = []
    while len(chosen) < min(n, len(T)):
        before = len(chosen)
        for c in cats:
            pool = [i for i in np.flatnonzero(c) if i not in chosen]
            if pool and len(chosen) < n:
                chosen.append(int(rng.choice(pool)))
        if len(chosen) == before:  # no segment has candidates left
            rest = [i for i in range(len(T)) if i not in chosen]
            chosen += [int(i) for i in rng.permutation(rest)[: n - len(chosen)]]
    return chosen


class HoldoutService:
    """Trains one designer on offers <= cutoff (train + validation; never on the test rows) and serves rows of the later offers."""

    def __init__(self, D: pd.DataFrame, wp_for: Callable[[str], float] = lambda inst: 450.0, designer: Designer | None = None,
                 cutoff: pd.Timestamp = HOLDOUT_CUTOFF, synthetic: bool = False):
        self.D, self.wp_for, self.cutoff, self.synthetic = D, wp_for, cutoff, synthetic
        self._designer = designer
        self._cache: dict[int, HoldoutResponse] = {}

    @property
    def designer(self) -> Designer:
        if self._designer is None:
            self._designer = Designer.train(self.D[self.D["when"] <= self.cutoff], synthetic=self.synthetic)
        return self._designer

    def warm(self, n: int = 12) -> None:
        """Train the designer and fill the row cache (about 7 s); call from a background thread at startup."""
        if self.has_test():
            self.rows(n)

    def has_test(self) -> bool:
        return bool((self.D["when"] > self.cutoff).any())

    def rows(self, n: int = 12) -> HoldoutResponse:
        from engine.design import system_from_values  # local: design imports this package's siblings

        n = max(1, min(int(n), 50))
        if n not in self._cache:
            T = self.D[self.D["when"] > self.cutoff].reset_index(drop=True)
            out = []
            for pos in pick_diverse(T, n):
                row = T.iloc[pos].to_dict()
                inputs = inputs_from_row(row)
                res = self.designer.design(inputs)
                ours = system_from_values(res.values, self.wp_for(inputs.installer_id), "ours")
                out.append(HoldoutRow(
                    project_id=str(row["project_id"]), installer_id=inputs.installer_id, inputs=inputs,
                    expert=HoldoutSystem(pv_kwp=_f(row["pv_kwp"]), battery_kwh=_f(row["battery_kwh"]),
                                         heat_pump_kw=_f(row["heat_pump_kw"]), wallbox_kw=_f(row["wallbox_kw"])),
                    ours=HoldoutSystem(pv_kwp=ours.pv.kwp if ours.pv else 0.0, battery_kwh=ours.battery.kwh if ours.battery else 0.0,
                                       heat_pump_kw=ours.heat_pump.kw if ours.heat_pump else 0.0,
                                       wallbox_kw=ours.wallbox.kw if ours.wallbox else 0.0)))
            self._cache[n] = HoldoutResponse(rows=out)
        return self._cache[n]


def warm_in_background(svc: HoldoutService | None, n: int = 12) -> threading.Thread | None:
    """Start `svc.warm(n)` in a daemon thread so the first /holdout call is instant. Never raises."""
    if svc is None:
        return None

    def run() -> None:
        try:
            svc.warm(n)
        except Exception:  # noqa: BLE001 - warming is an optimisation only
            import logging
            logging.getLogger("engine.demo").exception("holdout warm-up failed")

    t = threading.Thread(target=run, name="holdout-warm", daemon=True)
    t.start()
    return t
