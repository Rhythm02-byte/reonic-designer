"""Offline hourly physics + economics simulator (PLAN 6.3 S1-S5).

Public API (numpy/pandas only, no network; resources are bundled in ``resources/``):

``simulate(home, system, opts=None) -> dict``
    Metrics of PLAN section 7 (pvYieldKwh, selfConsumption, autarky, gridImportKwh, feedInKwh,
    savingsEurYear, paybackYears, npv20, priceEur) plus fullCyclesPerYear, batteryKwhPerKwp,
    nightLoadKwh, curtailedKwh, hourlyTypicalDays, baseline/incremental (S4), flags, notes.
``sweep_battery(home, system, sizes, opts=None) -> list[dict]``
    One row per battery size (one pass over 8,760 h): the "why this size" curve.
``sweep_pv(home, system, kwp_list, opts=None) -> list[dict]``
    One row per PV size.
``recommend_battery(home, system, sizes, opts=None) -> dict``
    Economic optimum (capped by night load and 150-350 cycles/yr) plus a max-autarky alternative.

Helper modules: ``profiles`` (PV/load/temperature), ``ev``, ``heatpump``, ``battery``, ``economics``.
"""
from . import battery, economics, ev, heatpump, profiles
from .simulate import DEFAULT_SIZES, recommend_battery, simulate, sweep_battery, sweep_pv

__all__ = ["simulate", "sweep_battery", "sweep_pv", "recommend_battery", "DEFAULT_SIZES",
           "profiles", "ev", "heatpump", "battery", "economics"]
