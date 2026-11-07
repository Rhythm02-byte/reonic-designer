"""Simulated homes and designs, to stress-test the model where the real export has gaps.

IMPORTANT: the designs here come from a POLICY WE WRITE (`policy_designs`), not from installers.
So a good score on simulated data only shows the model can learn the policy it was given. It says
nothing about how Reonic's experts decide. Use it for: (1) checking the pipeline recovers a known rule,
(2) measuring how accuracy falls as inputs go missing, (3) testing sizing where the real data has
almost no examples (heat pumps). Never report simulated accuracy as expert accuracy.
"""
import numpy as np
import pandas as pd

from . import physics
from .schema import INPUT_FIELDS, TARGETS

PV_SIZES_STEP = 0.1
BATTERY_SIZES = [5.0, 7.0, 10.0, 14.0, 15.0]
HP_SIZES = [5.5, 7.5, 10.5, 12.5]
WALLBOX_SIZES = [11.0, 22.0]


def _snap(x: np.ndarray, sizes: list[float]) -> np.ndarray:
    s = np.asarray(sizes)
    return s[np.abs(x[:, None] - s[None, :]).argmin(axis=1)]


def sample_inputs(real: pd.DataFrame, n: int, rng: np.random.Generator, hp_share: float = 0.0) -> pd.DataFrame:
    """Bootstrap real homes' inputs, jittered, with an optional share of heat pump homes injected.

    hp_share: fraction of homes made to heat with gas or oil and a known heating demand, so that
    heat pump sizing has examples. The real export is ~0.8% in this group.
    """
    base = real[list(INPUT_FIELDS)].sample(n, replace=True, random_state=int(rng.integers(1 << 31))).reset_index(drop=True)
    base["annual_consumption_kwh"] = (base["annual_consumption_kwh"].fillna(4500) * rng.lognormal(0, 0.12, n)).clip(1000, 20000)
    base["electricity_price_eur_kwh"] = base["electricity_price_eur_kwh"].fillna(0.35)
    base["existing_pv_kwp"] = base["existing_pv_kwp"].fillna(0.0)
    base["existing_battery_kwh"] = base["existing_battery_kwh"].fillna(0.0)
    hp_homes = rng.random(n) < hp_share
    base.loc[hp_homes, "heating_type"] = rng.choice(["gas", "oil"], hp_homes.sum())
    base.loc[hp_homes, "heating_demand_kwh"] = rng.normal(15000, 4000, hp_homes.sum()).clip(4000, 40000)
    return base


def policy_designs(inputs: pd.DataFrame, rng: np.random.Generator, noise: float = 0.15) -> pd.DataFrame:
    """The simulated planner. Explicit, readable rules plus noise. This is the 'truth' the model must recover."""
    n = len(inputs)
    ev_kwh = np.where(inputs["has_ev"].fillna(False).astype(bool), inputs["ev_km_per_year"].fillna(12000) * physics.EV_KWH_PER_KM, 0.0)
    heating = inputs["heating_type"].fillna("unknown").astype(str).str.lower().to_numpy()
    heat_demand = inputs["heating_demand_kwh"].fillna(0).to_numpy()

    # Heat pump: replaces fossil heating when the heat demand is known (rule: size = heat load / full-load hours)
    hp_on = np.isin(heating, ["gas", "oil"]) & (heat_demand > 0) & (rng.random(n) < 0.7)
    hp_elec = np.where(hp_on, heat_demand / physics.HP_SCOP, 0.0)
    hp_kw = np.where(hp_on, _snap(heat_demand / physics.HP_FULL_LOAD_HOURS * np.exp(rng.normal(0, noise, n)), HP_SIZES), 0.0)

    # PV: sized to roughly cover the future demand, skipped if the home already has PV
    demand = inputs["annual_consumption_kwh"].to_numpy() + ev_kwh + hp_elec
    has_pv_already = inputs["existing_pv_kwp"].to_numpy() > 0
    pv_on = ~has_pv_already & (rng.random(n) < 0.9)
    pv_kwp = np.where(pv_on, np.clip(demand / physics.SPECIFIC_YIELD_KWH_PER_KWP * np.exp(rng.normal(0, noise, n)), 3, 25).round(1), 0.0)

    # Battery: more likely with high demand and an expensive tariff; sized to the PV, or added to existing PV
    total_pv = pv_kwp + inputs["existing_pv_kwp"].to_numpy()
    bat_p = 1 / (1 + np.exp(-((demand - 3500) / 1200 + (inputs["electricity_price_eur_kwh"].fillna(0.35).to_numpy() - 0.35) * 8)))
    bat_on = (total_pv > 0) & (rng.random(n) < bat_p)
    bat_kwh = np.where(bat_on, _snap(total_pv * np.exp(rng.normal(0, noise, n)), BATTERY_SIZES), 0.0)

    # Wallbox: almost always with an EV
    wb_on = inputs["has_ev"].fillna(False).astype(bool).to_numpy() & (rng.random(n) < 0.6)
    wb_kw = np.where(wb_on, np.where(rng.random(n) < 0.3, 22.0, 11.0), 0.0)

    return pd.DataFrame({"pv_kwp": pv_kwp, "battery_kwh": bat_kwh, "heat_pump_kw": hp_kw, "wallbox_kw": wb_kw},
                        index=inputs.index)


def simulate(real: pd.DataFrame, n: int = 5000, seed: int = 0, hp_share: float = 0.0, noise: float = 0.15) -> pd.DataFrame:
    """Canonical table (inputs + policy designs) that `Designer.train` and `evaluate.run` accept."""
    rng = np.random.default_rng(seed)
    inputs = sample_inputs(real, n, rng, hp_share)
    targets = policy_designs(inputs, rng, noise)
    out = pd.concat([inputs, targets], axis=1)
    out["installer_id"] = "simulated"
    out["project_id"] = [f"sim{seed}-{i}" for i in range(n)]
    out["pv_source"] = "simulated"
    return out


def mask_inputs(df: pd.DataFrame, rate: float, seed: int = 0) -> pd.DataFrame:
    """Blank a fraction of each input at random: the 'what if the planner knows less' test.
    Targets are never masked."""
    rng = np.random.default_rng(seed)
    out = df.copy()
    for c in INPUT_FIELDS:
        if c in out.columns:
            if out[c].dtype.kind == "b":  # booleans cannot hold a blank: widen to object first
                out[c] = out[c].astype(object)
            blank = rng.random(len(out)) < rate
            out.loc[blank, c] = np.nan if out[c].dtype.kind in "fi" else None
    return out
