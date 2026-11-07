"""Load Reonic's dataset into canonical columns and build model features."""
import math
from dataclasses import asdict
from pathlib import Path

import numpy as np
import pandas as pd

from . import physics
from .schema import HEATING_TYPES, INPUT_FIELDS, NUMERIC_FIELDS, TARGETS, HomeInputs

# TODO when the dataset arrives: map Reonic's raw column names to canonical names, e.g.
# {"energy_demand_kwh": "annual_consumption_kwh", "pv_size": "pv_kwp"}.
COLUMN_MAP: dict[str, str] = {}

# TODO: map Reonic's heating labels onto HEATING_TYPES, e.g. {"Erdgas": "gas"}.
HEATING_MAP: dict[str, str] = {}


def load(path: str | Path) -> pd.DataFrame:
    p = Path(path)
    if p.suffix == ".parquet":
        df = pd.read_parquet(p)
    elif p.suffix in (".xlsx", ".xls"):
        df = pd.read_excel(p)
    else:
        df = pd.read_csv(p)
    df = df.rename(columns=COLUMN_MAP)
    missing = [t for t in TARGETS if t not in df.columns]
    if missing:
        raise ValueError(f"Target columns {missing} not found. Fill COLUMN_MAP in src/reonic/data.py.")
    for c in INPUT_FIELDS:
        if c not in df.columns:
            df[c] = np.nan
    # Assumption (confirm with Reonic): a blank component size means it was not installed.
    df[list(TARGETS)] = df[list(TARGETS)].apply(pd.to_numeric, errors="coerce").fillna(0.0).clip(lower=0)
    return df


def _bool(v) -> float:
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return np.nan
    if isinstance(v, str):
        return 1.0 if v.strip().lower() in {"1", "true", "yes", "y", "ja"} else 0.0
    return float(bool(v))


def inputs_frame(inputs: HomeInputs | list[HomeInputs]) -> pd.DataFrame:
    rows = inputs if isinstance(inputs, list) else [inputs]
    return pd.DataFrame([asdict(r) for r in rows])


def row_inputs(df: pd.DataFrame) -> list[HomeInputs]:
    return [HomeInputs(**{f: r.get(f) for f in INPUT_FIELDS}) for r in df[list(INPUT_FIELDS)].to_dict("records")]


def features(df: pd.DataFrame) -> pd.DataFrame:
    """Numeric feature matrix. Unknown stays NaN (the gradient-boosting models handle it natively)."""
    X = pd.DataFrame(index=df.index)
    for c in NUMERIC_FIELDS:
        X[c] = pd.to_numeric(df[c], errors="coerce")
    X["has_ev"] = df["has_ev"].map(_bool).astype(float)

    heating = df["heating_type"].astype("string").str.strip().str.lower().replace(HEATING_MAP)
    for h in HEATING_TYPES:
        X[f"heating_{h}"] = (heating == h).astype(float).where(heating.notna())

    # Physics-informed features: what the home will consume, not just what it consumed.
    X["ev_kwh"] = [physics.ev_demand_kwh(e, km) if not np.isnan(e) else np.nan for e, km in zip(X["has_ev"], X["ev_km_per_year"])]
    X["heat_demand_kwh"] = X["heated_area_m2"] * physics.HEAT_DEMAND_KWH_PER_M2
    X["consumption_per_person"] = X["annual_consumption_kwh"] / X["household_size"]
    X["pv_kwp_for_full_demand"] = (X["annual_consumption_kwh"] + X["ev_kwh"].fillna(0)) / physics.SPECIFIC_YIELD_KWH_PER_KWP
    X["roof_max_kwp"] = X["roof_area_m2"] / physics.M2_PER_KWP
    return X
