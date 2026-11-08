"""Canonical training frame and feature matrix, built only from OUR ETL tables (projects + options).

Unknown stays NaN: the gradient-boosting models handle missing values natively.
Targets: a component that was not offered has size 0; NaN = offered but size unknown.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from engine.etl.normalize import DEFAULT_DEMAND_KWH, _load_profile_family
from engine.models.schemas import HomeInputs

TARGETS = ("pv_kwp", "battery_kwh", "heat_pump_kw", "wallbox_kw")
HEATING = ("Gas", "Oil", "Heatpump", "OtherRenewable", "OtherNonRenewable", "Unknown")
FAMILIES = ("H0", "family", "home_office", "senior", "custom", "other")

EV_KWH_PER_KM = 0.18
DEFAULT_EV_KM = 12_000.0
SPECIFIC_YIELD_KWH_PER_KWP = 950.0
DEFAULT_WALLBOX_KW = 11.0

# Raw (maskable) input columns of the canonical frame. Everything else is derived in features().
INPUT_COLS = (
    "installer_id", "demand_kwh", "price_eur_kwh", "price_escalation", "flex_tariff", "load_family",
    "has_ev", "ev_km", "has_existing_pv", "existing_pv_kwp", "existing_pv_trusted",
    "has_existing_storage", "existing_storage_kwh", "existing_storage_trusted", "has_existing_wallbox",
    "heating_type", "heat_demand_kwh", "hp_elec_existing_kwh",
)
MASKABLE = tuple(c for c in INPUT_COLS if c not in ("installer_id", "existing_pv_trusted", "existing_storage_trusted"))


def training_frame(P: pd.DataFrame, O: pd.DataFrame) -> pd.DataFrame:
    """One row per project that has parts: project inputs + the primary option's design as targets."""
    P = P[P.has_parts].copy()
    P["when"] = P.offer_at.fillna(P.request_at).fillna(P.signed_at)
    o = O[O.is_primary].set_index("project_id")
    o = o.assign(has_solar_tech=o["has_solar_tech"] if "has_solar_tech" in o else False)  # older ETL tables lack it
    o = o[["kwp", "battery_kwh", "hp_kw", "wallbox_kw", "has_pv", "has_battery", "has_heatpump", "has_wallbox", "has_solar_tech"]]
    o.columns = ["_kwp", "_bat", "_hp", "_wb", "_hpv", "_hbat", "_hhp", "_hwb", "_sol"]
    df = P.join(o, on="project_id", how="inner")
    # PV: size if recovered; NaN if the option has solar lines but no recoverable size ("offered, size unknown"); else 0
    df["pv_kwp"] = np.where(df._hpv, df._kwp, np.where(df._sol.astype(bool), np.nan, 0.0))
    df["battery_kwh"] = np.where(df._hbat, df._bat, 0.0)
    df["heat_pump_kw"] = np.where(df._hhp, np.where(df._hp > 0, df._hp, np.nan), 0.0)  # NaN = offered, size unknown
    df["wallbox_kw"] = np.where(df._hwb, np.where(df._wb.notna() & (df._wb > 0), df._wb, DEFAULT_WALLBOX_KW), 0.0)
    return df.drop(columns=[c for c in df.columns if c.startswith("_")]).reset_index(drop=True)


def targets(df: pd.DataFrame) -> pd.DataFrame:
    return df[list(TARGETS)].astype(float)


def _num(df: pd.DataFrame, c: str) -> pd.Series:
    return pd.to_numeric(df[c], errors="coerce") if c in df else pd.Series(np.nan, index=df.index)


def _b(df: pd.DataFrame, c: str) -> pd.Series:
    """Boolean-ish column -> 1.0 / 0.0 / NaN (unknown)."""
    if c not in df:
        return pd.Series(np.nan, index=df.index)
    return df[c].map(lambda v: np.nan if v is None or v is pd.NA or (isinstance(v, float) and np.isnan(v)) else float(bool(v))).astype(float)


def _trusted(has: pd.Series, trusted: pd.Series, value: pd.Series) -> pd.Series:
    """Existing PV/storage size counts only when trusted: 0 when there is none, NaN when ambiguous or unknown."""
    out = pd.Series(np.nan, index=has.index)
    out[has == 0] = 0.0
    ok = (has == 1) & (trusted == 1)
    out[ok] = value[ok].fillna(0.0)
    return out


def features(df: pd.DataFrame, installers: tuple[str, ...] | list[str] = (), physics: bool = False, prior=None,
             prior_values: pd.Series | None = None) -> pd.DataFrame:
    """Feature matrix. Optional upgrades (validated in eval/selection.py): `physics` adds the simulator's economic-optimum
    kWp / battery for the home; `prior` (a physics.PvPrior) or explicit `prior_values` (out-of-fold, for training rows) adds
    the installer's median kWp for this demand bucket."""
    X = _base_features(df, installers)
    if physics:
        from engine.policy import physics as ph
        X = pd.concat([X, ph.physics_features(df)], axis=1)
    if prior_values is not None:
        X["inst_pv_prior_kwp"] = prior_values.reindex(df.index).astype(float)
    elif prior is not None:
        X["inst_pv_prior_kwp"] = prior.transform(df).astype(float)
    return X.astype(float)


def _base_features(df: pd.DataFrame, installers: tuple[str, ...] | list[str] = ()) -> pd.DataFrame:
    # Columns are collected in a dict and assembled once: a DataFrame.__setitem__ per column costs ~0.4 ms each, which
    # dominated single-home /design calls (~40 columns, called several times per request).
    X: dict[str, pd.Series] = {}
    d = _num(df, "demand_kwh")
    X["demand_kwh"] = d
    X["demand_is_default"] = ((d - DEFAULT_DEMAND_KWH).abs() < 1e-6).astype(float).where(d.notna())
    X["demand_round500"] = ((d % 500) == 0).astype(float).where(d.notna())
    X["price_eur_kwh"] = _num(df, "price_eur_kwh")
    X["price_escalation"] = _num(df, "price_escalation")
    X["flex_tariff"] = _b(df, "flex_tariff")
    ev = _b(df, "has_ev")
    km = _num(df, "ev_km")
    X["has_ev"], X["ev_km"] = ev, km
    X["ev_kwh"] = pd.Series(np.where(ev == 1, km.fillna(DEFAULT_EV_KM) * EV_KWH_PER_KM, 0.0), index=df.index).where(ev.notna())
    X["existing_pv_kwp"] = _trusted(_b(df, "has_existing_pv"), _b(df, "existing_pv_trusted"), _num(df, "existing_pv_kwp"))
    X["existing_storage_kwh"] = _trusted(_b(df, "has_existing_storage"), _b(df, "existing_storage_trusted"), _num(df, "existing_storage_kwh"))
    X["has_existing_wallbox"] = _b(df, "has_existing_wallbox")

    htype = df["heating_type"].astype("object") if "heating_type" in df else pd.Series(None, index=df.index, dtype="object")
    known = htype.notna()
    for h in HEATING:
        X[f"heating_{h}"] = (htype == h).astype(float).where(known)
    fam = df["load_family"].astype("object") if "load_family" in df else pd.Series(None, index=df.index, dtype="object")
    for f in FAMILIES:
        X[f"profile_{f}"] = (fam == f).astype(float).where(fam.notna())
    # existing-HP heat demand is derived from its electricity (x3.5): keep one signal, not two
    X["heat_demand_kwh"] = _num(df, "heat_demand_kwh").where(htype != "Heatpump")
    X["hp_elec_existing_kwh"] = _num(df, "hp_elec_existing_kwh")

    X["future_demand_kwh"] = d + X["ev_kwh"].fillna(0)
    X["pv_kwp_for_full_demand"] = X["future_demand_kwh"] / SPECIFIC_YIELD_KWH_PER_KWP
    inst = df["installer_id"].astype("object") if "installer_id" in df else pd.Series(None, index=df.index, dtype="object")
    for i in installers:
        X[f"installer_{i}"] = (inst == i).astype(float)  # all zeros = unseen installer
    return pd.DataFrame(X, index=df.index).astype(float)


def heat_demand_from_inputs(i: HomeInputs) -> float | None:
    h = i.heating
    heat = h.heat_demand_kwh
    if heat is None and h.fuel_kwh:
        heat = h.fuel_kwh * 0.9
    if heat is None and h.cost_eur_year and h.type == "Gas":
        heat = h.cost_eur_year / 0.122
    return heat


def row_from_inputs(i: HomeInputs, module_wp: float = 450.0) -> dict:
    """API HomeInputs -> one canonical input row. Unknown stays NaN; existing PV/storage keep their trust flag.
    `building.roofMaxModules` becomes a hard PV cap (roof_max_kwp, via the installer's module Wp); not a model feature."""
    n = np.nan
    h = i.heating
    pv, st = i.existing_pv, i.existing_storage
    heat = heat_demand_from_inputs(i)
    roof = i.building.roof_max_modules if i.building else None
    return {
        "roof_max_modules": float(roof) if roof is not None else n,
        "roof_max_kwp": roof * module_wp / 1000.0 if roof is not None else n,
        "installer_id": i.installer_id, "demand_kwh": i.demand_kwh, "price_eur_kwh": i.price_eur_kwh,
        "price_escalation": i.price_escalation, "flex_tariff": i.flex_tariff if i.flex_tariff is not None else n,
        "load_family": _load_profile_family(i.load_profile),
        "has_ev": i.ev.has, "ev_km": i.ev.km_per_year if i.ev.km_per_year is not None else n,
        "has_existing_pv": pv is not None, "existing_pv_kwp": pv.kwp if pv else n, "existing_pv_trusted": bool(pv and pv.trusted),
        "has_existing_storage": st is not None, "existing_storage_kwh": st.kwh if st else n,
        "existing_storage_trusted": bool(st and st.trusted),
        "has_existing_wallbox": i.existing_wallbox is not None,
        "heating_type": h.type, "heat_demand_kwh": heat if heat is not None else n,
        "hp_elec_existing_kwh": (h.hp_elec_kwh if h.hp_elec_kwh is not None else n) if h.type == "Heatpump" else n,
    }


def mask_inputs(df: pd.DataFrame, rate: float, seed: int = 0) -> pd.DataFrame:
    """Blank a fraction of each input at random: the 'what if the planner knows less' test. Targets are never masked."""
    rng = np.random.default_rng(seed)
    out = df.copy()
    for c in MASKABLE:
        if c not in out:
            continue
        blank = rng.random(len(out)) < rate
        if out[c].dtype.kind == "f":
            out.loc[blank, c] = np.nan
        else:
            out[c] = out[c].astype(object)
            out.loc[blank, c] = None
    return out
