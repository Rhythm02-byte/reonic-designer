"""Naive rule-of-thumb designer. The model must beat this, or it is not worth showing."""
import numpy as np
import pandas as pd

from . import physics
from .data import features


def rule_of_thumb(df: pd.DataFrame) -> pd.DataFrame:
    X = features(df)
    demand = X["annual_consumption_kwh"].fillna(X["annual_consumption_kwh"].median()) + X["ev_kwh"].fillna(0)
    pv = (demand / physics.SPECIFIC_YIELD_KWH_PER_KWP).clip(3, 15).round(1)
    battery = np.where(demand > 3500, pv.round(), 0.0)
    fossil = (X["heating_oil"] == 1) | (X["heating_gas"] == 1)
    hp = np.where(fossil & X["heat_demand_kwh"].notna(),
                  (X["heat_demand_kwh"] / physics.HP_FULL_LOAD_HOURS).round(), 0.0)
    return pd.DataFrame({"pv_kwp": pv, "battery_kwh": battery, "heat_pump_kw": hp}, index=df.index)
