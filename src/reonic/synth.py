"""FAKE data in the canonical schema so the pipeline runs before the Reonic dataset arrives.

Never report numbers from this data in the pitch.
"""
import numpy as np
import pandas as pd


def _snap(x: np.ndarray, sizes: list[float]) -> np.ndarray:
    s = np.asarray(sizes)
    return s[np.abs(x[:, None] - s[None, :]).argmin(axis=1)]


def generate(n: int = 3000, seed: int = 0) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    household = rng.integers(1, 6, n)
    consumption = np.clip(1500 + 900 * household + rng.normal(0, 500, n), 1200, None).round()
    heating = rng.choice(["gas", "oil", "heat_pump", "electric", "district"], n, p=[0.45, 0.2, 0.15, 0.05, 0.15])
    has_ev = rng.random(n) < 0.3
    ev_km = np.where(has_ev, np.clip(rng.normal(12000, 4000, n), 3000, None).round(-2), np.nan)
    price = np.clip(rng.normal(0.34, 0.04, n), 0.2, None).round(3)
    feed_in = rng.choice([0.07, 0.08, 0.082], n)
    area = np.clip(rng.normal(140, 40, n), 60, None).round()
    roof = np.clip(rng.normal(60, 20, n), 15, None).round()
    budget = np.clip(rng.normal(32000, 10000, n), 8000, None).round(-2)

    # "Expert" behaviour with noise
    heat_demand = area * 120
    hp_p = np.select([heating == "oil", heating == "gas"], [0.6, 0.35], 0.0)
    gets_hp = rng.random(n) < hp_p
    hp_kw = np.where(gets_hp, _snap(heat_demand / 2000 + rng.normal(0, 0.8, n), [6, 8, 10, 12, 14, 16]), 0.0)
    demand = consumption + np.where(has_ev, np.nan_to_num(ev_km) * 0.18, 0) + np.where(gets_hp, heat_demand / 3.2, 0)
    pv = np.clip(demand / 950 * 0.9 * (1 + rng.normal(0, 0.15, n)), 3, roof / 5.5).round(1)
    battery_p = 1 / (1 + np.exp(-((demand - 4500) / 1500 + (price - 0.3) * 10)))
    gets_bat = rng.random(n) < battery_p
    battery = np.where(gets_bat, _snap(pv * (1 + rng.normal(0, 0.2, n)), [5, 7.5, 10, 12.5, 15, 20]), 0.0)

    df = pd.DataFrame({
        "project_id": np.arange(n), "annual_consumption_kwh": consumption, "household_size": household,
        "heating_type": heating, "has_ev": has_ev, "ev_km_per_year": ev_km,
        "electricity_price_eur_kwh": price, "feed_in_tariff_eur_kwh": feed_in, "budget_eur": budget,
        "roof_area_m2": roof, "heated_area_m2": area,
        "pv_kwp": pv, "battery_kwh": battery, "heat_pump_kw": hp_kw,
    })
    for col in ("roof_area_m2", "heated_area_m2", "budget_eur", "household_size"):  # real data has gaps
        df.loc[rng.random(n) < 0.15, col] = np.nan
    return df
