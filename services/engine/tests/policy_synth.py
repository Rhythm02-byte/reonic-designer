"""FAKE data in the engine's canonical training columns, shaped loosely like the real tables (ported from the
teammate prototype's synth.py). Lets tests run without the confidential data. Never report numbers from it."""
import numpy as np
import pandas as pd


def _snap(x: np.ndarray, sizes: list[float]) -> np.ndarray:
    s = np.asarray(sizes)
    return s[np.abs(x[:, None] - s[None, :]).argmin(axis=1)]


def generate(n: int = 1200, seed: int = 0) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    demand = np.clip(rng.lognormal(np.log(4500), 0.35, n), 1500, 15000).round(-2)
    has_ev = rng.random(n) < 0.15
    ev_km = np.where(has_ev & (rng.random(n) < 0.4), rng.choice([10000, 12000, 15000, 25000], n), np.nan)
    known = rng.random(n) < 0.15
    heating = np.where(known, rng.choice(["Heatpump", "Gas", "Oil"], n, p=[0.6, 0.25, 0.15]), "Unknown")
    heat_demand = np.where(np.isin(heating, ["Gas", "Oil"]), rng.normal(15000, 4000, n).clip(3000), np.nan)
    existing_pv = np.where(rng.random(n) < 0.04, rng.choice([4.0, 10.0, 18.9], n), 0.0)

    gets_hp = np.isin(heating, ["Gas", "Oil"]) & (rng.random(n) < 0.6)
    hp_kw = np.where(gets_hp, _snap(np.nan_to_num(heat_demand) / 2000 + rng.normal(0, 1, n), [5.5, 7.5, 10.5, 12.5]), 0.0)
    total = demand + np.where(has_ev, np.nan_to_num(ev_km, nan=12000) * 0.18, 0) + np.where(gets_hp, np.nan_to_num(heat_demand) / 3.2, 0)
    gets_pv = (existing_pv == 0) & (rng.random(n) < 0.85)
    pv = np.where(gets_pv, np.clip(total / 950 * 1.6 * (1 + rng.normal(0, 0.2, n)), 3, 25).round(1), 0.0)
    pv = np.where(gets_pv & (rng.random(n) < 0.05), np.nan, pv)  # offered, size not recoverable
    bat_p = np.where(existing_pv > 0, 0.95, 1 / (1 + np.exp(-((total - 3000) / 1500))))
    gets_bat = rng.random(n) < bat_p
    battery = np.where(gets_bat, _snap(np.nan_to_num(pv, nan=10) + existing_pv + rng.normal(0, 2, n), [5, 7, 10, 14, 15]), 0.0)
    wallbox = np.where(rng.random(n) < np.where(has_ev, 0.6, 0.2), rng.choice([11.0, 22.0], n, p=[0.7, 0.3]), 0.0)

    return pd.DataFrame({
        "installer_id": rng.choice(["synthA", "synthB"], n, p=[0.25, 0.75]), "project_id": [f"s{i}" for i in range(n)],
        "demand_kwh": demand, "price_eur_kwh": rng.choice([0.28, 0.32, 0.35, 0.39, 0.45], n),
        "price_escalation": rng.choice([0.02, 0.03, 0.04, 0.05], n), "flex_tariff": rng.random(n) < 0.1,
        "load_family": rng.choice(["H0", "family", "home_office", "senior"], n, p=[0.85, 0.08, 0.04, 0.03]),
        "has_ev": has_ev, "ev_km": ev_km,
        "has_existing_pv": existing_pv > 0, "existing_pv_kwp": np.where(existing_pv > 0, existing_pv, np.nan),
        "existing_pv_trusted": existing_pv > 0, "has_existing_storage": False, "existing_storage_kwh": np.nan,
        "existing_storage_trusted": False, "has_existing_wallbox": False,
        "heating_type": heating, "heat_demand_kwh": heat_demand, "hp_elec_existing_kwh": np.where(heating == "Heatpump", 4000.0, np.nan),
        "pv_kwp": pv, "battery_kwh": battery, "heat_pump_kw": hp_kw, "wallbox_kw": wallbox,
    })
