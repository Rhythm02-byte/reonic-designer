"""Deterministic physics and economics.

These are rough defaults for German single-family homes. They give the model physically
meaningful features and feed the explanation; they never make the design decision alone.
TODO: calibrate every constant with the Reonic experts on site.
"""
import math

SPECIFIC_YIELD_KWH_PER_KWP = 950.0  # annual PV yield per kWp
M2_PER_KWP = 5.5  # roof area needed per kWp
EV_KWH_PER_KM = 0.18
DEFAULT_EV_KM = 12_000
HEAT_DEMAND_KWH_PER_M2 = 120.0  # space heating + hot water, older building stock
HP_SCOP = 3.2  # seasonal coefficient of performance
HP_FULL_LOAD_HOURS = 2_000
DEFAULT_PRICE_EUR_KWH = 0.35
DEFAULT_FEED_IN_EUR_KWH = 0.08
CAPEX = {"pv_per_kwp": 1_300, "battery_per_kwh": 650, "hp_fixed": 12_000, "hp_per_kw": 800}


def num(x) -> float | None:
    """None/NaN -> None, everything else -> float."""
    if x is None:
        return None
    try:
        f = float(x)
    except (TypeError, ValueError):
        return None
    return None if math.isnan(f) else f


def ev_demand_kwh(has_ev, km=None) -> float:
    if not has_ev or num(has_ev) == 0:
        return 0.0
    return (num(km) or DEFAULT_EV_KM) * EV_KWH_PER_KM


def heat_demand_kwh(heated_area_m2) -> float | None:
    a = num(heated_area_m2)
    return None if a is None else a * HEAT_DEMAND_KWH_PER_M2


def heat_pump_electricity_kwh(heat_demand: float) -> float:
    return heat_demand / HP_SCOP


def heat_pump_kw_for(heat_demand: float) -> float:
    return heat_demand / HP_FULL_LOAD_HOURS


def pv_yield_kwh(kwp: float) -> float:
    return kwp * SPECIFIC_YIELD_KWH_PER_KWP


def self_consumption_ratio(consumption_kwh: float, generation_kwh: float, battery_kwh: float = 0.0) -> float:
    """Share of PV generation used on site. Simple empirical curve; replace with a proper model if time allows."""
    if generation_kwh <= 0 or consumption_kwh <= 0:
        return 0.0
    base = 0.3 * (consumption_kwh / generation_kwh) ** 0.6
    battery_per_mwh = battery_kwh / (consumption_kwh / 1000)
    uplift = 0.35 * (1 - math.exp(-battery_per_mwh / 1.5))
    return max(0.0, min(base + uplift, 0.95, consumption_kwh / generation_kwh))


def capex_eur(pv_kwp: float, battery_kwh: float, heat_pump_kw: float) -> float:
    hp = CAPEX["hp_fixed"] + CAPEX["hp_per_kw"] * heat_pump_kw if heat_pump_kw > 0 else 0.0
    return CAPEX["pv_per_kwp"] * pv_kwp + CAPEX["battery_per_kwh"] * battery_kwh + hp


def annual_pv_savings_eur(consumption_kwh, pv_kwp, battery_kwh, price=None, feed_in=None) -> float:
    """Bill savings from PV + battery only (heat pump fuel savings not modelled yet)."""
    price = num(price) or DEFAULT_PRICE_EUR_KWH
    feed_in = num(feed_in) or DEFAULT_FEED_IN_EUR_KWH
    gen = pv_yield_kwh(pv_kwp)
    sc = self_consumption_ratio(consumption_kwh, gen, battery_kwh)
    return gen * sc * price + gen * (1 - sc) * feed_in
