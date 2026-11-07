"""Hard constraints applied after the model. Every rule has an ID so explanations, flags and tests can cite it.

R01 home already heats with a heat pump -> no new one
R02 no new or existing PV -> no battery
R03 PV <= 30 kWp (residential ceiling)
R07 PV <= the modules the roof fits (building.roofMaxModules; only when known)
R04 battery <= 2.0 kWh per kWp of PV (new + existing), hard cap
R05 amber flag: usable battery > 1.5 kWh per kWp (HTW Berlin storage guidance; usable = 90% of nominal). Never changes a value.

Locked (planner) values are only flagged, never changed: a violated R01-R04 becomes a red flag.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping

import numpy as np

PV_MAX_KWP = 30.0
BATTERY_MAX_KWH_PER_KWP = 2.0
USABLE_FRACTION = 0.9
R05_USABLE_KWH_PER_KWP = 1.5


@dataclass(frozen=True)
class Hit:
    id: str
    target: str
    text: str
    severity: str = "amber"  # "amber" | "red"
    evidence: dict = field(default_factory=dict)


def _num(x) -> float | None:
    try:
        f = float(x)
    except (TypeError, ValueError):
        return None
    return None if np.isnan(f) else f


def ctx_from_row(row: Mapping) -> dict:
    """Rule context from a canonical input row. Existing PV counts even when 'ambiguous' (lenient: storage retrofits)."""
    pv = _num(row.get("existing_pv_kwp")) or 0.0 if row.get("has_existing_pv") else 0.0
    return {"heating_type": row.get("heating_type"), "existing_pv_kwp": pv,
            "roof_max_kwp": _num(row.get("roof_max_kwp")), "roof_max_modules": _num(row.get("roof_max_modules"))}


def snap(value: float, catalog: list[float], upper: float | None = None) -> float:
    """Snap to the nearest size installers actually use (learned from the data)."""
    options = [c for c in catalog if upper is None or c <= upper + 1e-9] or catalog
    if not options:
        return round(value, 1)
    return float(min(options, key=lambda c: abs(c - value)))


def common_sizes(sizes, top: int | None = 15) -> list[float]:
    """Most frequent installed sizes, i.e. the de-facto product catalog (`top` None = every installed size)."""
    s = np.round(np.asarray(sizes, dtype=float), 1)
    s = s[s > 0]
    if s.size == 0:
        return []
    vals, counts = np.unique(s, return_counts=True)
    return sorted(float(v) for v in vals[np.argsort(-counts)][:top])  # top None = all


def apply_one(target: str, value: float, current: dict[str, float], ctx: Mapping, catalog: dict[str, list[float]],
              locked: bool = False) -> tuple[float, list[Hit], list[Hit]]:
    """Returns (value, applied rules, flags). `current` holds the components already decided upstream."""
    applied: list[Hit] = []
    flags: list[Hit] = []
    if value is None or np.isnan(value):  # unknown size stays unknown
        return float("nan"), applied, flags
    v = max(0.0, float(value)) if not locked else float(value)

    if target == "heat_pump_kw":
        if str(ctx.get("heating_type") or "") == "Heatpump" and v > 0:
            applied.append(Hit("R01", target, "R01: the home already heats with a heat pump, so no new one.", "red",
                               {"existing_heat_pump": True}))
            v = 0.0
        elif v > 0 and not locked:
            v = snap(v, catalog.get(target, []))

    elif target == "pv_kwp":
        if v > PV_MAX_KWP:
            applied.append(Hit("R03", target, f"R03: PV capped at the residential limit of {PV_MAX_KWP:g} kWp.", "red",
                               {"limit_kwp": PV_MAX_KWP, "requested_kwp": round(v, 2)}))
            v = PV_MAX_KWP
        roof = _num(ctx.get("roof_max_kwp"))
        if roof is not None and v > roof + 1e-9:
            n = _num(ctx.get("roof_max_modules"))
            what = f"the {n:g} modules the roof fits" if n is not None else f"the roof limit of {roof:g} kWp"
            applied.append(Hit("R07", target, f"R07: PV limited to {what}.", "red",
                               {"roof_max_kwp": round(roof, 2), "requested_kwp": round(v, 2)}))
            v = roof
        if not locked:
            v = round(v, 1)

    elif target == "battery_kwh":
        pv = current.get("pv_kwp", 0.0) + (_num(ctx.get("existing_pv_kwp")) or 0.0)
        pv = 0.0 if np.isnan(pv) else pv  # new PV of unknown size: only existing PV is certain
        cap = BATTERY_MAX_KWH_PER_KWP * pv
        if v > 0 and pv <= 0:
            applied.append(Hit("R02", target, "R02: no new or existing PV, so no battery.", "red", {"pv_kwp": 0.0}))
            v = 0.0
        elif v > cap:
            applied.append(Hit("R04", target, f"R04: battery capped at {BATTERY_MAX_KWH_PER_KWP:g} kWh per kWp of PV.", "red",
                               {"max_kwh_per_kwp": BATTERY_MAX_KWH_PER_KWP, "pv_kwp": round(pv, 2), "cap_kwh": round(cap, 2)}))
            v = cap
        if v > 0 and not locked:
            v = snap(v, catalog.get(target, []), upper=cap)

    elif target == "wallbox_kw" and v > 0 and not locked:
        v = snap(v, catalog.get(target, []) or [11.0, 22.0])

    if locked:
        out = float(value)
        flags = [Hit(h.id, h.target, f"Planner override conflicts with {h.text}", "red", h.evidence) for h in applied]
        applied = []
        v = out

    if target == "battery_kwh" and v > 0:
        pv = current.get("pv_kwp", 0.0) + (_num(ctx.get("existing_pv_kwp")) or 0.0)
        pv = 0.0 if np.isnan(pv) else pv
        if pv > 0 and USABLE_FRACTION * v > R05_USABLE_KWH_PER_KWP * pv:
            ratio = USABLE_FRACTION * v / pv
            flags.append(Hit("R05", target,
                             f"R05: usable battery {USABLE_FRACTION * v:.1f} kWh is {ratio:.2f} kWh per kWp of PV, above the "
                             f"{R05_USABLE_KWH_PER_KWP:g} kWh/kWp guidance; extra storage rarely pays back.", "amber",
                             {"usable_kwh_per_kwp": round(ratio, 2), "guidance_kwh_per_kwp": R05_USABLE_KWH_PER_KWP,
                              "pv_kwp": round(pv, 2)}))
    return v, applied, flags


def audit(values: Mapping[str, float], ctx: Mapping, catalog: dict[str, list[float]]) -> list[Hit]:
    """Check a complete design (e.g. the planner's) against R01-R05; nothing is changed."""
    current: dict[str, float] = {}
    out: list[Hit] = []
    for t in ("heat_pump_kw", "pv_kwp", "battery_kwh", "wallbox_kw"):
        v = float(values.get(t, 0.0) or 0.0)
        _, _, flags = apply_one(t, v, current, ctx, catalog, locked=True)
        out += flags
        current[t] = v
    return out
