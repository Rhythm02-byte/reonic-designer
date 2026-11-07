"""Turn Reonic's export into one row per project: canonical inputs + the expert design (targets).

Raw layout (one folder per installer):
    data/raw/<installer_id>/projects_status_quo.csv    the home before the offer  -> inputs
    data/raw/<installer_id>/project_options_parts.csv  line items of every option -> targets

Quirks of the export, handled here (see CONTEXT.md §7):
  * "_kw"/"_kwh"/"_wh" columns hold W / Wh, so divide by 1000.
  * inverter_power_kw and battery_capacity_kwh are swapped: battery capacity sits in
    inverter_power_kw on BatteryStorage rows.
  * PV size is rarely explicit; it's rebuilt from module rows, "…kWp" package names or module counts.
  * Projects can have several options and the signed one is not marked (OPTION_CHOICE).
"""
import math
import re
from dataclasses import asdict
from pathlib import Path

import numpy as np
import pandas as pd

from . import physics
from .schema import (BOOL_FIELDS, HEATING_TYPES, INPUT_FIELDS, LOAD_PROFILES, NUMERIC_FIELDS, TARGETS,
                     HomeInputs)

# Which option counts as the expert design. Pending Reonic's answer (THI-2): "first" = lowest option_number.
OPTION_CHOICE = "first"
# Assumed module power where the export only gives a module count (installer 2a8ba8e2). Pending THI-2.
MODULE_WP = 450.0

HEATING_MAP = {"gas": "gas", "oil": "oil", "heatpump": "heat_pump", "electric": "electric", "district": "district",
               "otherrenewable": "other", "othernonrenewable": "other"}
_PER_MODULE = re.compile(r"^(DC Install|Substructure|Roof Mounting)", re.I)
_PKG_KWP = re.compile(r"(\d+(?:[.,]\d+)?)\s*kWp\s*\+?", re.I)
_PKG_KWH = re.compile(r"\+\s*(\d+(?:[.,]\d+)?)\s*kWh", re.I)


# -- raw export -> one row per project ---------------------------------------------------------------
def _num(s: pd.Series) -> pd.Series:
    return pd.to_numeric(s, errors="coerce")


def _first_float(pattern: re.Pattern, text) -> float:
    m = pattern.search(text) if isinstance(text, str) else None
    return float(m.group(1).replace(",", ".")) if m else np.nan


def option_designs(parts: pd.DataFrame) -> pd.DataFrame:
    """One row per option with pv_kwp, battery_kwh, heat_pump_kw, wallbox_kw and where the PV number came from."""
    p = parts.copy()
    q = _num(p["quantity"]).fillna(1.0)
    ctype, name = p["component_type"].fillna(""), p["component_name"].fillna("")
    units = p["quantity_units"].fillna("Item")

    p["bat_kwh"] = np.where(ctype.eq("BatteryStorage"), _num(p["inverter_power_kw"]).fillna(0) * q / 1000, 0.0)  # swapped column
    p["hp_kw"] = np.where(ctype.eq("Heatpump"), _num(p["heatpump_nominal_power_kw"]).fillna(0) * q / 1000, 0.0)
    p["wb_kw"] = np.where(ctype.eq("Wallbox"), _num(p["wb_charging_speed_kw"]).fillna(11000) / 1000, 0.0)
    p["mod_kwp"] = np.where(ctype.eq("Module"), _num(p["module_watt_peak"]).fillna(0) * q / 1000, 0.0)
    is_pkg = ctype.eq("Other") & name.str.contains("kWp", case=False)
    p["pkg_kwp"] = np.where(is_pkg, name.map(lambda s: _first_float(_PKG_KWP, s)), np.nan)
    p["pkg_kwh"] = np.where(is_pkg, name.map(lambda s: _first_float(_PKG_KWH, s)), np.nan)
    per_module = name.str.match(_PER_MODULE) & ~name.str.contains("Ballast", case=False) & units.eq("Item") & (q > 2)
    p["n_modules"] = np.where(per_module, q, np.nan)
    p["is_solar"] = p["technology"].eq("solar")

    o = p.groupby(["project_id", "option_id", "option_number"], dropna=False).agg(
        bat_kwh=("bat_kwh", "sum"), heat_pump_kw=("hp_kw", "sum"), wallbox_kw=("wb_kw", "max"),
        mod_kwp=("mod_kwp", "sum"), pkg_kwp=("pkg_kwp", "max"), pkg_kwh=("pkg_kwh", "max"),
        n_modules=("n_modules", "max"), has_solar=("is_solar", "any"),
    ).reset_index()

    # PV: explicit module rows > package name > module count x assumed wattage > unknown (NaN)
    from_count = o["n_modules"] * MODULE_WP / 1000
    o["pv_kwp"] = np.select([o["mod_kwp"] > 0, o["pkg_kwp"] > 0, from_count > 0, ~o["has_solar"]],
                            [o["mod_kwp"], o["pkg_kwp"], from_count, 0.0], np.nan)
    o["pv_source"] = np.select([o["mod_kwp"] > 0, o["pkg_kwp"] > 0, from_count > 0, ~o["has_solar"]],
                               ["module_rows", "package_name", "module_count", "no_pv"], "unknown")
    # Battery: itemised rows; a package's battery only counts when it is not itemised (avoids double counting)
    o["battery_kwh"] = np.where(o["bat_kwh"] > 0, o["bat_kwh"], o["pkg_kwh"].fillna(0))
    o["pv_kwp"] = o["pv_kwp"].round(2)
    o["battery_kwh"] = o["battery_kwh"].round(2)
    return o[["project_id", "option_id", "option_number", *TARGETS, "pv_source"]]


def status_quo_inputs(sq: pd.DataFrame) -> pd.DataFrame:
    """Canonical inputs from projects_status_quo.csv (units fixed)."""
    b = lambda c: sq[c].map(_bool)
    heating = sq["heating_existing_type"].astype("string").str.strip().str.lower().map(HEATING_MAP)
    return pd.DataFrame({
        "project_id": sq["project_id"],
        # A home cannot use 0 kWh a year. 13 projects (0.8%) carry 0, so treat it as unknown, not as a measurement.
        "annual_consumption_kwh": (_num(sq["energy_demand_wh"]) / 1000).where(lambda s: s > 0),
        "electricity_price_eur_kwh": _num(sq["energy_price_per_wh"]) * 1000,
        "energy_price_increase": _num(sq["energy_price_increase"]),
        "has_ev": b("has_ev"),
        "ev_km_per_year": _num(sq["ev_annual_drive_distance_km"]),
        "has_flexible_tariff": sq["energy_price_with_flexible_tariff"].notna().astype(float),
        "load_profile": sq["load_profile"],
        "heating_type": heating,
        "heating_demand_kwh": _num(sq["heating_existing_heating_demand_wh"]) / 1000,
        "existing_pv_kwp": np.where(b("has_solar") == 1, _num(sq["solar_size_kwp"]) / 1000, 0.0),
        "existing_battery_kwh": np.where(b("has_storage") == 1, _num(sq["storage_size_kwh"]) / 1000, 0.0),
        "has_existing_wallbox": b("has_wallbox"),
        "household_size": _num(sq["num_inhabitants"]),
        "heated_area_m2": _num(sq["house_size_sqm"]),
        "country": sq["country"],
        "offer_created_at": pd.to_datetime(sq["offer_created_at"], errors="coerce"),
    })


def load_raw(root: str | Path, option_choice: str = OPTION_CHOICE) -> pd.DataFrame:
    frames = []
    for d in sorted(p for p in Path(root).iterdir() if (p / "projects_status_quo.csv").exists()):
        sq = status_quo_inputs(pd.read_csv(d / "projects_status_quo.csv"))
        opts = option_designs(pd.read_csv(d / "project_options_parts.csv"))
        n_opts = opts.groupby("project_id").size().rename("n_options")
        chosen = opts.sort_values("option_number", ascending=(option_choice == "first")).drop_duplicates("project_id")
        df = sq.merge(chosen, on="project_id", how="inner").join(n_opts, on="project_id")
        df.insert(0, "installer_id", d.name)
        frames.append(df)
    if not frames:
        raise FileNotFoundError(f"No <installer>/projects_status_quo.csv folders under {root}")
    return pd.concat(frames, ignore_index=True)


# -- entry point used everywhere ---------------------------------------------------------------------
def load(path: str | Path) -> pd.DataFrame:
    """A folder = Reonic raw export; a file = an already-canonical table (e.g. synthetic data)."""
    p = Path(path)
    if p.is_dir():
        df = load_raw(p)
    elif p.suffix == ".parquet":
        df = pd.read_parquet(p)
    else:
        df = pd.read_csv(p)
    missing = [t for t in TARGETS if t not in df.columns]
    if missing:
        raise ValueError(f"Target columns {missing} not found in {path}.")
    for c in INPUT_FIELDS:
        if c not in df.columns:
            df[c] = np.nan
    df[list(TARGETS)] = df[list(TARGETS)].apply(pd.to_numeric, errors="coerce").clip(lower=0)
    return df


def default_data_path() -> str:
    return "data/raw" if Path("data/raw").is_dir() else "data/synthetic.csv"


# -- features ---------------------------------------------------------------------------------------
def _bool(v) -> float:
    if v is None or (isinstance(v, float) and math.isnan(v)) or v is pd.NA:
        return np.nan
    if isinstance(v, str):
        return 1.0 if v.strip().lower() in {"1", "true", "yes", "y", "ja"} else 0.0
    return float(bool(v))


def inputs_frame(inputs: HomeInputs | list[HomeInputs]) -> pd.DataFrame:
    rows = inputs if isinstance(inputs, list) else [inputs]
    return pd.DataFrame([asdict(r) for r in rows])


def row_inputs(df: pd.DataFrame) -> list[HomeInputs]:
    recs = df[list(INPUT_FIELDS)].astype(object).where(df[list(INPUT_FIELDS)].notna(), None).to_dict("records")
    return [HomeInputs(**r) for r in recs]


def features(df: pd.DataFrame) -> pd.DataFrame:
    """Numeric feature matrix. Unknown stays NaN (the gradient-boosting models handle it natively)."""
    X = pd.DataFrame(index=df.index)
    for c in NUMERIC_FIELDS:
        X[c] = pd.to_numeric(df[c], errors="coerce")
    for c in BOOL_FIELDS:
        X[c] = df[c].map(_bool).astype(float)

    heating = df["heating_type"].astype("string").str.strip().str.lower()
    for h in HEATING_TYPES:
        X[f"heating_{h}"] = (heating == h).astype(float).where(heating.notna())
    profile = df["load_profile"].astype("string")
    for lp in LOAD_PROFILES:
        X[f"profile_{lp}"] = (profile == lp).astype(float).where(profile.notna())

    # Physics-informed features: what the home will consume, not just what it consumed.
    ev = [physics.ev_demand_kwh(e, km) if not np.isnan(e) else np.nan for e, km in zip(X["has_ev"], X["ev_km_per_year"])]
    X["ev_kwh"] = ev
    X["heat_demand_kwh"] = X["heating_demand_kwh"].fillna(X["heated_area_m2"] * physics.HEAT_DEMAND_KWH_PER_M2)
    X["future_demand_kwh"] = X["annual_consumption_kwh"] + X["ev_kwh"].fillna(0)
    X["pv_kwp_for_full_demand"] = X["future_demand_kwh"] / physics.SPECIFIC_YIELD_KWH_PER_KWP
    return X
