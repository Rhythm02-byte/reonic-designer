"""Heat pump model (S2): heat demand from fuel, hourly heat from temperature, COP(T), rod, sizing.

Assumptions (PLAN 6.3 S2): gas condensing 0.95, old gas 0.80, oil 0.85 (oil litres x 10 kWh);
heating limit 15 degC (UNSOURCED, research table); domestic hot water 18% flat; seasonal COP
(rod included) normalised to 3.4 (Fraunhofer ISE field test, air-water mean SPF 3.4);
heat load = demand / full-load hours (2,000 h default).
"""
from __future__ import annotations

import numpy as np

EFFICIENCY = {"gas": 0.95, "gas_old": 0.80, "oil": 0.85}
OIL_KWH_PER_LITRE = 10.0


def heat_demand_kwh(fuel: str = "gas", fuel_kwh: float | None = None, litres: float | None = None,
                    old_boiler: bool = False, efficiency: float | None = None) -> float:
    """Useful heat (kWh/yr) = fuel kWh x boiler efficiency. Oil: pass ``litres`` (x10 kWh/l)."""
    if fuel.lower().startswith("oil"):
        key = "oil"
    else:
        key = "gas_old" if old_boiler else "gas"
    kwh = fuel_kwh if fuel_kwh is not None else (litres or 0.0) * OIL_KWH_PER_LITRE
    return float(kwh) * (efficiency if efficiency is not None else EFFICIENCY[key])


def heat_load_kw(demand_kwh: float, full_load_hours: float = 2000.0) -> float:
    """Design heat load in kW = annual heat demand / full-load hours."""
    return float(demand_kwh) / float(full_load_hours)


def snap_to_catalog(kw: float, sizes, tolerance: float = 0.05) -> float:
    """Smallest catalog size >= kw*(1-tolerance); the largest size if none is big enough."""
    s = sorted(float(x) for x in sizes)
    for x in s:
        if x >= kw * (1.0 - tolerance):
            return x
    return s[-1]


def hourly_heat(temp: np.ndarray, demand_kwh: float, dhw_share: float = 0.18,
                heating_limit: float = 15.0) -> np.ndarray:
    """Hourly heat (kWh): space heating ~ heating degree hours below ``heating_limit``; DHW flat."""
    hdh = np.clip(heating_limit - temp, 0.0, None)
    space = (1.0 - dhw_share) * demand_kwh * hdh / hdh.sum()
    return space + dhw_share * demand_kwh / len(temp)


def cop_curve(temp: np.ndarray, scale: float = 1.0) -> np.ndarray:
    """Air-water COP(T) = scale * (3.0 + 0.075*T), clipped to [1.8, 5.5] (shape only; see hp_electric)."""
    return np.clip(scale * (3.0 + 0.075 * temp), 1.8, 5.5)


def hp_electric(temp: np.ndarray, demand_kwh: float, scop: float = 3.4, dhw_share: float = 0.18,
                heating_limit: float = 15.0, bivalence_c: float = -7.0, rod_share_cold: float = 0.5,
                hp_thermal_kw: float | None = None) -> dict:
    """Hourly HP electricity (kWh) for a heat demand.

    Below ``bivalence_c`` the rod supplies ``rod_share_cold`` of the heat (COP 1); heat above
    ``hp_thermal_kw`` (if given) is also rod. The COP curve is scaled so the whole-year
    heat / electricity (rod included) equals ``scop``. Returns dict(elec, heat, cop, rod_elec, scop).
    """
    heat = hourly_heat(temp, demand_kwh, dhw_share, heating_limit)
    rod = np.where(temp < bivalence_c, heat * rod_share_cold, 0.0)
    hp_heat = heat - rod
    if hp_thermal_kw is not None:
        over = np.clip(hp_heat - hp_thermal_kw, 0.0, None)
        rod = rod + over
        hp_heat = hp_heat - over
    raw = cop_curve(temp)
    denom = heat.sum() / scop - rod.sum()
    if denom <= 0:
        raise ValueError("rod share too large for the requested SCOP")
    scale = float((hp_heat / raw).sum() / denom)
    cop = np.clip(raw * scale, 1.5, 6.0)
    elec = hp_heat / cop + rod
    return {"elec": elec, "heat": heat, "cop": cop, "rod_elec": rod, "scop": float(heat.sum() / elec.sum())}
