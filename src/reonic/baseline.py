"""Naive rule-of-thumb designer. The model must beat this, or it is not worth showing."""
import numpy as np
import pandas as pd

from . import physics
from .data import features


def rule_of_thumb(df: pd.DataFrame) -> pd.DataFrame:
    X = features(df)
    demand = X["future_demand_kwh"].fillna(X["future_demand_kwh"].median())
    pv = (demand / physics.SPECIFIC_YIELD_KWH_PER_KWP).clip(3, 15).round(1)  # 1 kWp per 1,000 kWh
    battery = np.where(demand > 3500, pv.round(), 0.0)
    fossil = (X["heating_oil"] == 1) | (X["heating_gas"] == 1)
    hp = np.where(fossil & X["heat_demand_kwh"].notna(), (X["heat_demand_kwh"] / physics.HP_FULL_LOAD_HOURS).round(), 0.0)
    wallbox = np.where(X["has_ev"] == 1, 11.0, 0.0)
    return pd.DataFrame({"pv_kwp": pv, "battery_kwh": battery, "heat_pump_kw": hp, "wallbox_kw": wallbox}, index=df.index)
