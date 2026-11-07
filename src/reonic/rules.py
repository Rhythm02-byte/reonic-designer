"""Hard constraints applied after the model. Every rule has an ID so explanations and tests can cite it.

Rules never change a value the planner locked; they only flag it.
"""
import numpy as np

from . import physics
from .schema import HomeInputs

PV_MAX_KWP = 30.0  # residential ceiling
BATTERY_MAX_KWH_PER_KWP = 2.0


def snap(value: float, catalog: list[float], upper: float | None = None) -> float:
    """Snap to the nearest size installers actually use (learned from the data)."""
    options = [c for c in catalog if upper is None or c <= upper + 1e-9] or catalog
    if not options:
        return round(value, 1)
    return float(min(options, key=lambda c: abs(c - value)))


def apply_one(target: str, value: float, current: dict[str, float], inputs: HomeInputs,
              catalog: dict[str, list[float]], locked: bool = False) -> tuple[float, list[str], list[str]]:
    """Returns (value, rule notes, flags). `current` holds the components already decided upstream."""
    v = max(0.0, float(value))
    notes: list[str] = []

    if target == "heat_pump_kw":
        if str(inputs.heating_type or "").lower() == "heat_pump" and v > 0:
            v = 0.0
            notes.append("R01: the home already heats with a heat pump, so no new one.")
        elif v > 0:
            v = snap(v, catalog.get(target, []))

    elif target == "pv_kwp":
        if v > 0:
            cap = PV_MAX_KWP
            roof = physics.num(inputs.roof_area_m2)
            if roof is not None:
                cap = min(cap, roof / physics.M2_PER_KWP)
            if v > cap:
                v = cap
                notes.append(f"R03: PV capped at {cap:.1f} kWp (roof area / residential limit).")
            v = round(v, 1)

    elif target == "battery_kwh":
        pv = current.get("pv_kwp", 0.0)
        if v > 0 and pv <= 0:
            v = 0.0
            notes.append("R02: no PV, so no battery.")
        elif v > BATTERY_MAX_KWH_PER_KWP * pv:
            v = BATTERY_MAX_KWH_PER_KWP * pv
            notes.append(f"R04: battery capped at {BATTERY_MAX_KWH_PER_KWP:g} kWh per kWp of PV.")
        if v > 0:
            v = snap(v, catalog.get(target, []), upper=BATTERY_MAX_KWH_PER_KWP * pv)

    if locked:
        return float(value), [], [f"Planner override conflicts with {n}" for n in notes]
    return v, notes, []


def budget_flags(values: dict[str, float], inputs: HomeInputs) -> list[str]:
    budget = physics.num(inputs.budget_eur)
    if budget is None:
        return []
    cost = physics.capex_eur(values["pv_kwp"], values["battery_kwh"], values["heat_pump_kw"])
    if cost > budget * 1.1:
        return [f"R06: estimated cost €{cost:,.0f} is above the budget of €{budget:,.0f}."]
    return []


def common_sizes(sizes: np.ndarray, top: int = 15) -> list[float]:
    """Most frequent installed sizes, i.e. the de-facto product catalog."""
    s = np.round(np.asarray(sizes, dtype=float), 1)
    s = s[s > 0]
    if s.size == 0:
        return []
    vals, counts = np.unique(s, return_counts=True)
    return sorted(float(v) for v in vals[np.argsort(-counts)][:top])
