"""FAKE data in the canonical schema, shaped like the real export (same fields, similar rates).

Lets tests and teammates without the confidential data run everything. Never report numbers from it.
"""
import numpy as np
import pandas as pd


def _snap(x: np.ndarray, sizes: list[float]) -> np.ndarray:
    s = np.asarray(sizes)
    return s[np.abs(x[:, None] - s[None, :]).argmin(axis=1)]


def generate(n: int = 1600, seed: int = 0) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    consumption = np.clip(rng.lognormal(np.log(4500), 0.35, n), 1500, 15000).round(-2)
    price = rng.choice([0.28, 0.32, 0.35, 0.39, 0.45], n)
    has_ev = rng.random(n) < 0.15
    ev_km = np.where(has_ev & (rng.random(n) < 0.4), rng.choice([10000, 12000, 15000, 25000], n), np.nan)
    profile = rng.choice(["H0", "FamilyOfFour", "SeniorOnePerson", "HomeOfficeOnePerson"], n, p=[0.85, 0.08, 0.04, 0.03])
    known_heating = rng.random(n) < 0.12  # the real export rarely says how the home is heated
    heating = np.where(known_heating, rng.choice(["heat_pump", "gas", "oil"], n, p=[0.8, 0.12, 0.08]), None)
    heat_demand = np.where(known_heating, rng.normal(15000, 4000, n).clip(3000), np.nan)
    existing_pv = np.where(rng.random(n) < 0.03, rng.choice([4.0, 10.0, 18.9], n), 0.0)

    # "Expert" behaviour with noise
    gets_hp = np.isin(heating, ["gas", "oil"]) & (rng.random(n) < 0.6)
    hp_kw = np.where(gets_hp, _snap(np.nan_to_num(heat_demand) / 2000 + rng.normal(0, 1, n), [5.5, 7.5, 10.5, 12.5]), 0.0)
    demand = consumption + np.where(has_ev, np.nan_to_num(ev_km, nan=12000) * 0.18, 0) + np.where(gets_hp, np.nan_to_num(heat_demand) / 3.2, 0)
    gets_pv = (existing_pv == 0) & (rng.random(n) < 0.85)
    pv = np.where(gets_pv, np.clip(demand / 950 * 1.6 * (1 + rng.normal(0, 0.2, n)), 3, 25).round(1), 0.0)
    pv = np.where(gets_pv & (rng.random(n) < 0.05), np.nan, pv)  # offered, size not recoverable
    battery_p = np.where(existing_pv > 0, 0.95, 1 / (1 + np.exp(-((demand - 3000) / 1500))))
    gets_bat = rng.random(n) < battery_p
    battery = np.where(gets_bat, _snap(np.nan_to_num(pv, nan=10) + existing_pv + rng.normal(0, 2, n), [5, 7, 10, 14, 15]), 0.0)
    wallbox = np.where(rng.random(n) < np.where(has_ev, 0.6, 0.2), rng.choice([11.0, 22.0], n, p=[0.7, 0.3]), 0.0)

    return pd.DataFrame({
        "installer_id": rng.choice(["synthA", "synthB"], n, p=[0.25, 0.75]), "project_id": np.arange(n),
        "annual_consumption_kwh": consumption, "electricity_price_eur_kwh": price,
        "energy_price_increase": rng.choice([0.02, 0.03, 0.04, 0.05], n), "has_ev": has_ev, "ev_km_per_year": ev_km,
        "has_flexible_tariff": (rng.random(n) < 0.15).astype(float), "load_profile": profile, "heating_type": heating,
        "heating_demand_kwh": heat_demand, "existing_pv_kwp": existing_pv, "existing_battery_kwh": 0.0,
        "has_existing_wallbox": False, "household_size": np.nan, "heated_area_m2": np.nan,
        "pv_kwp": pv, "battery_kwh": battery, "heat_pump_kw": hp_kw, "wallbox_kw": wallbox,
    })
