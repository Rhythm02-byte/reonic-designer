"""Two references the model has to be compared with.

rule_of_thumb: a naive sizing rule. Easy to beat, so beating it alone proves little.
typical_design: ignores the home entirely and proposes what most homes got, at the median size. This is the fair
"no information" reference: a model trained on shuffled answers lands close to it (scripts/leakage_checks.py).
"""
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


def typical_design(train: pd.DataFrame, test: pd.DataFrame) -> pd.DataFrame:
    """Each component that most training homes got, at its median size. Wallbox: the same EV rule the model uses."""
    out = pd.DataFrame(index=test.index, columns=["pv_kwp", "battery_kwh", "heat_pump_kw", "wallbox_kw"], dtype=float)
    for t in ("pv_kwp", "battery_kwh", "heat_pump_kw"):
        included = (train[t] > 0) | train[t].isna()  # NaN = offered, size unknown
        out[t] = float(train.loc[train[t] > 0, t].median()) if included.mean() > 0.5 else 0.0
    out["wallbox_kw"] = np.where(test["has_ev"].astype(float).fillna(0) == 1, 11.0, 0.0)
    return out
