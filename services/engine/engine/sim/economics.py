"""20-year economics (S5) and capex from ``config/market.json``.

Annual flows are simulated for year 1 and for the last year (PV and battery degraded) and
interpolated linearly in between. Price escalation applies to retail electricity and fuel.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

import numpy as np

CONFIG_PATH = Path(__file__).resolve().parents[2] / "config" / "market.json"


@lru_cache(maxsize=1)
def load_market(path: str | None = None) -> dict:
    """Load config/market.json (cached). Contains as_of, sources, ranges low/mid/high and rules."""
    return json.loads(Path(path or CONFIG_PATH).read_text(encoding="utf-8"))


def pv_price_eur(kwp, level: str = "mid", market: dict | None = None):
    """Installed PV price (EUR) for ``kwp`` (scalar or array): size-dependent EUR/kWp, interpolated."""
    m = (market or load_market())["pv_eur_per_kwp_installed"]
    k = np.asarray(kwp, float)
    per = np.interp(k, m["anchors_kwp"], m[level])
    return np.where(k > 0, per * k, 0.0)


def battery_price_eur(kwh, level: str = "mid", market: dict | None = None):
    """Installed battery price (EUR) = kWh x EUR/kWh (flat across sizes)."""
    return np.asarray(kwh, float) * (market or load_market())["battery_eur_per_kwh_installed"][level]


def hp_price_eur(level: str = "mid", market: dict | None = None) -> float:
    """Installed air-water heat pump price (EUR), before subsidy."""
    return float((market or load_market())["heatpump_air_water_installed_eur"][level])


def wallbox_price_eur(level: str = "mid", market: dict | None = None) -> float:
    """Installed 11 kW wallbox price (EUR)."""
    return float((market or load_market())["wallbox_11kw_installed_eur"][level])


def kfw_subsidy_eur(hp_price: float, market: dict | None = None) -> float:
    """KfW 458 base grant (30% of eligible cost, capped eligible cost)."""
    k = (market or load_market())["kfw_458"]
    return k["base_rate"] * min(hp_price, k["eligible_cost_cap_eur_first_unit"])


def project(*, imp0, exp0, imp1_first, exp1_first, imp1_last, exp1_last, price: float,
            escalation: float, fit0, fit1, fuel0_year1: float = 0.0, fuel1_year1: float = 0.0,
            fuel_escalation: float = 0.03, invest, om_year, inverter_repl, years: int = 20,
            discount: float = 0.03, inverter_year: int = 13) -> dict:
    """Cash-flow model. All flow/invest inputs may be scalars or (B,) arrays (one per variant).

    cost_t = import_t * price_t - export_t * feed-in_t + fuel_t, for the baseline (0) and the new
    system (1). savings_t = cost0_t - cost1_t; cash_t = savings_t - O&M - inverter replacement.
    ``fit0``/``fit1`` are scalars, (years,) or (years, B) arrays. Returns dict with savings_year1, npv, payback
    (years, NaN if > 40), cash (years, B), om etc.
    """
    t = np.arange(years)[:, None]  # 0..years-1
    w = t / max(years - 1, 1)
    def lerp(a, b):
        a, b = np.atleast_1d(np.asarray(a, float)), np.atleast_1d(np.asarray(b, float))
        return a[None, :] + w * (b - a)[None, :]
    p_t = price * (1 + escalation) ** t
    f_t = (1 + fuel_escalation) ** t
    def fit_arr(x):
        x = np.asarray(x, float)
        return np.full((years, 1), float(x)) if x.ndim == 0 else (x.reshape(-1, 1) if x.ndim == 1 else x)
    fit0, fit1 = fit_arr(fit0), fit_arr(fit1)
    imp0, exp0 = np.atleast_1d(np.asarray(imp0, float))[None, :], np.atleast_1d(np.asarray(exp0, float))[None, :]
    cost0 = imp0 * p_t - exp0 * fit0 + fuel0_year1 * f_t
    cost1 = lerp(imp1_first, imp1_last) * p_t - lerp(exp1_first, exp1_last) * fit1 + fuel1_year1 * f_t
    savings = cost0 - cost1
    B = savings.shape[1]
    om = np.broadcast_to(np.atleast_1d(np.asarray(om_year, float))[None, :], (years, B))
    cash = savings - om
    if 1 <= inverter_year <= years:
        cash = cash.copy()
        cash[inverter_year - 1] -= np.atleast_1d(np.asarray(inverter_repl, float))
    inv = np.broadcast_to(np.atleast_1d(np.asarray(invest, float)), (B,))
    disc = (1 + discount) ** -(np.arange(1, years + 1)[:, None])
    npv = (cash * disc).sum(0) - inv
    cum = -inv[None, :] + np.cumsum(cash, axis=0)
    payback = np.full(B, np.nan)
    last = cash[-1]
    for j in range(B):
        hit = np.nonzero(cum[:, j] >= 0)[0]
        if len(hit):
            i = hit[0]
            prev = cum[i - 1, j] if i > 0 else -inv[j]
            payback[j] = i + (-prev) / (cum[i, j] - prev) if cum[i, j] != prev else float(i)
        elif last[j] > 0:
            extra = -cum[-1, j] / last[j]
            payback[j] = years + extra if years + extra <= 40 else np.nan
        if inv[j] <= 0 and cash[:, j].sum() >= 0:
            payback[j] = 0.0
    return {"savings_year1": savings[0], "npv": npv, "payback": payback, "cash": cash,
            "om_year": om[0], "savings": savings}
