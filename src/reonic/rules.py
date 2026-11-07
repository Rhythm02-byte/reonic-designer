"""Hard constraints applied after the model. Every rule has an ID so explanations and tests can cite it.

Rules never change a value the planner locked; they only flag it.
"""
import numpy as np

from .physics import num as _num
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
        if v > PV_MAX_KWP:
            v = PV_MAX_KWP
            notes.append(f"R03: PV capped at the residential limit of {PV_MAX_KWP:g} kWp.")
        v = round(v, 1)

    elif target == "battery_kwh":
        # Storage-only retrofits are common for homes that already have PV, so count existing PV too.
        pv = max(current.get("pv_kwp", 0.0), 0.0) + max(_num(inputs.existing_pv_kwp) or 0.0, 0.0)  # a negative entry counts as none
        if v > 0 and pv <= 0:
            v = 0.0
            notes.append("R02: no new or existing PV, so no battery.")
        elif v > BATTERY_MAX_KWH_PER_KWP * pv:
            v = BATTERY_MAX_KWH_PER_KWP * pv
            notes.append(f"R04: battery capped at {BATTERY_MAX_KWH_PER_KWP:g} kWh per kWp of PV.")
        if v > 0:
            cap = BATTERY_MAX_KWH_PER_KWP * pv
            v = snap(v, catalog.get(target, []), upper=cap)
            if v > cap + 1e-9:  # no catalogue size fits under the cap (tiny PV): stay under it rather than break R04
                v = float(np.floor(cap * 10) / 10)
                if not any(n.startswith("R04") for n in notes):  # the cap note above already says it
                    notes.append(f"R04: battery limited to {v:g} kWh, below the smallest catalogue size.")

    elif target == "wallbox_kw" and v > 0:
        v = snap(v, catalog.get(target, []) or [11.0, 22.0])

    if locked:
        return float(value), [], [f"Planner override conflicts with {n}" for n in notes]
    return v, notes, []


def common_sizes(sizes: np.ndarray, top: int = 15) -> list[float]:
    """Most frequent installed sizes, i.e. the de-facto product catalog."""
    s = np.round(np.asarray(sizes, dtype=float), 1)
    s = s[s > 0]
    if s.size == 0:
        return []
    vals, counts = np.unique(s, return_counts=True)
    return sorted(float(v) for v in vals[np.argsort(-counts)][:top])
