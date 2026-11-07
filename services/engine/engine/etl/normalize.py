"""ETL: raw Reonic CSVs -> unit-fixed projects/options tables + per-installer catalogs.

Only this module reads raw CSVs. Downstream code uses kWh, kW, kWp and EUR/kWh.

    python -m engine.etl.normalize --raw dataset --out data/processed
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd

DEFAULT_MODULE_WP = 450.0
DEFAULT_DEMAND_KWH = 4500.0
FOSSIL_HEATING = {"Gas", "Oil", "OtherNonRenewable"}

ROOF_TYPES = [
    "concrete_tile", "clay_tile", "flat", "flat_ew", "metal", "bitumen",
    "slate", "beaver_tail", "trapezoid", "standing_seam", "other", "unknown",
]

_NUM = r"(\d+(?:[.,]\d+)?)"
RE_PACKAGE = re.compile(_NUM + r"\s*kWp\s*\+\s*" + _NUM + r"\s*kWh", re.I)
RE_KWH = re.compile(_NUM + r"\s*kWh", re.I)
RE_KW = re.compile(_NUM + r"\s*kW(?![hp])", re.I)
RE_WP = re.compile(r"(\d{3})\s*Wp?\b")
RE_PITCH = re.compile(r"([<>])\s*(\d{2})")


def _f(s: str) -> float:
    return float(s.replace(",", "."))


def parse_package(name: str) -> tuple[float, float] | None:
    m = RE_PACKAGE.search(name or "")
    return (_f(m.group(1)), _f(m.group(2))) if m else None


def parse_kwh(name: str) -> float | None:
    m = RE_KWH.search(name or "")
    return _f(m.group(1)) if m else None


def parse_kw(name: str) -> float | None:
    m = RE_KW.search(name or "")
    return _f(m.group(1)) if m else None


def parse_wp(name: str) -> float | None:
    m = RE_WP.search(name or "")
    return float(m.group(1)) if m else None


def parse_roof(names: list[str]) -> tuple[str, str | None]:
    """Roof type + pitch hint from mounting lines (Substructure / DC Install / Roof Mounting)."""
    mount = [n for n in names if re.match(r"(substructure|dc install|roof mounting|sl rack)", n, re.I)]
    text = " | ".join(mount).lower()
    pitch = None
    m = RE_PITCH.search(" ".join(mount))
    if m:
        pitch = {("<", "15"): "lt15", ("<", "30"): "lt30", (">", "30"): "gt30"}.get((m.group(1), m.group(2)))
    if not text:
        return "unknown", pitch
    rules = [
        ("flat_ew", r"east/west|east-west"),
        ("flat", r"flat|ballast"),
        ("beaver_tail", r"beaver"),
        ("slate", r"slate"),
        ("bitumen", r"bitumen"),
        ("standing_seam", r"standing seam"),
        ("trapezoid", r"trapez"),
        ("metal", r"metal"),
        ("concrete_tile", r"concrete"),
        ("clay_tile", r"clay"),
    ]
    for roof, pat in rules:
        if re.search(pat, text):
            return roof, pitch
    return ("other" if re.search(r"cross-lay|rack|pitched|facade", text) else "unknown"), pitch


def _read(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, encoding="latin1")


def _load_profile_family(lp) -> str:
    s = str(lp or "")
    if s == "H0":
        return "H0"
    for key, fam in (("Family", "family"), ("Home", "home_office"), ("Senior", "senior"), ("Custom", "custom")):
        if key in s:
            return fam
    return "other"


def _bool(sq: pd.DataFrame, col: str) -> pd.Series:
    if col not in sq:
        return pd.Series(False, index=sq.index)
    return sq[col].fillna(False).astype(bool)


def build_projects(sq: pd.DataFrame, installer_id: str, parts_projects: set) -> pd.DataFrame:
    """One row per project with unit-fixed inputs and data-quality flags."""
    nat = pd.Series(pd.NaT, index=sq.index)
    nan = pd.Series(np.nan, index=sq.index)
    dt = lambda c: pd.to_datetime(sq[c], format="mixed", errors="coerce", utc=True).dt.tz_localize(None) if c in sq else nat
    num = lambda c: pd.to_numeric(sq[c], errors="coerce") if c in sq else nan
    req, off, sig = dt("request_created_at"), dt("offer_created_at"), dt("first_signed_at")
    ref_year = off.dt.year.fillna(req.dt.year).fillna(sig.dt.year)

    p = pd.DataFrame({"project_id": sq["project_id"], "installer_id": installer_id})
    p["customer_id"] = sq.get("customer_contact_id")
    p["request_at"], p["offer_at"], p["signed_at"] = req, off, sig
    p["ref_year"] = ref_year
    p["country"] = sq.get("country")
    p["has_parts"] = p.project_id.isin(parts_projects)

    p["demand_kwh"] = num("energy_demand_wh") / 1000.0
    p["demand_is_default"] = (p.demand_kwh - DEFAULT_DEMAND_KWH).abs() < 1e-6
    p["demand_round500"] = (p.demand_kwh % 500 == 0) & p.demand_kwh.notna()
    p["price_eur_kwh"] = num("energy_price_per_wh") * 1000.0
    p["price_escalation"] = num("energy_price_increase")
    p["flex_tariff"] = num("energy_price_with_flexible_tariff").notna()
    p["base_price_month"] = num("base_price_per_month")
    p["load_profile"] = sq.get("load_profile")
    p["load_family"] = p.load_profile.map(_load_profile_family)

    p["has_ev"] = _bool(sq, "has_ev")
    p["ev_km"] = num("ev_annual_drive_distance_km")

    # Existing PV / storage: trusted only if built before the offer year
    # (otherwise the planned system was probably typed into the status quo).
    pv_year, st_year = num("solar_built_year"), num("storage_built_year")
    has_pv, has_st = _bool(sq, "has_solar"), _bool(sq, "has_storage")
    p["has_existing_pv"] = has_pv
    p["existing_pv_kwp"] = num("solar_size_kwp") / 1000.0
    p["existing_pv_built_year"] = pv_year
    p["existing_pv_trusted"] = has_pv & pv_year.notna() & (pv_year < ref_year)
    p["existing_pv_ambiguous"] = has_pv & ~p.existing_pv_trusted
    p["existing_pv_tilt"] = num("solar_angle")
    p["existing_pv_orientation"] = sq["solar_orientation"] if "solar_orientation" in sq else None
    p["has_existing_storage"] = has_st
    p["existing_storage_kwh"] = num("storage_size_kwh") / 1000.0
    p["existing_storage_built_year"] = st_year
    p["existing_storage_trusted"] = has_st & st_year.notna() & (st_year < ref_year)
    p["existing_storage_ambiguous"] = has_st & ~p.existing_storage_trusted
    p["has_existing_wallbox"] = _bool(sq, "has_wallbox")
    p["existing_wallbox_kw"] = num("wallbox_charge_speed_kw") / 1000.0

    htype = sq["heating_existing_type"].fillna("Unknown") if "heating_existing_type" in sq else pd.Series("Unknown", index=sq.index)
    p["heating_type"] = htype
    p["heating_fossil"] = htype.isin(FOSSIL_HEATING)
    cost = num("heating_existing_cost_per_year")
    p["heating_cost_is_unit_price"] = cost.notna() & (cost < 10)  # 0.76-1.53 are unit prices, not annual costs
    p["heating_cost_eur_year"] = cost.where(~p.heating_cost_is_unit_price)
    p["heating_cost_increase"] = num("heating_existing_cost_increase_per_year")
    p["heat_demand_kwh"] = num("heating_existing_heating_demand_wh") / 1000.0
    p["hp_elec_existing_kwh"] = num("heating_existing_electricity_demand_kwh").where(htype == "Heatpump")
    # existing-HP heat demand is derived (= 3.5 x electricity): one signal, never two features
    p["heat_demand_is_derived"] = (htype == "Heatpump") & p.heat_demand_kwh.notna()

    p["house_sqm"] = num("house_size_sqm")
    p["house_built_year"] = num("house_built_year")
    p["num_inhabitants"] = num("num_inhabitants")
    return p


def _first_valid(*vals):
    for v in vals:
        if v is not None and not (isinstance(v, float) and np.isnan(v)):
            return v
    return None


def build_option(g: pd.DataFrame) -> dict:
    names = g.component_name.fillna("").tolist()
    ctype = g.component_type
    qty = g.quantity.fillna(1)
    r: dict = {}

    # --- PV size
    mod = g[ctype == "Module"]
    wp_vals = [_first_valid(parse_wp(n), w) for n, w in zip(mod.component_name.fillna(""), mod.module_watt_peak)]
    wp_vals = [w for w in wp_vals if w]
    sub = g[(ctype == "ModuleFrameConstruction")
            & g.component_name.str.contains(r"substructure|roof mounting", case=False, na=False)
            & ~g.component_name.str.contains(r"ballast|end caps|additional module|plate", case=False, na=False)]
    dc = g[g.component_name.str.startswith("DC Install", na=False)]
    pkg = [p for p in map(parse_package, names) if p]

    n_mod, src = np.nan, "none"
    if len(mod):
        n_mod, src = float(qty[mod.index].sum()), "modules"
    elif len(sub):
        n_mod, src = float(qty[sub.index].sum()), "substructure"
    elif len(dc):
        n_mod, src = float(qty[dc.index].sum()), "dc_install"
    wp_assumed = not wp_vals
    wp = float(np.median(wp_vals)) if wp_vals else DEFAULT_MODULE_WP
    if pkg:
        kwp, src = pkg[0][0], "package"
        if np.isnan(n_mod):
            n_mod = float(round(kwp * 1000 / wp))
    elif not np.isnan(n_mod):
        kwp = n_mod * wp / 1000.0
    else:
        kwp = 0.0
    r.update(n_modules=n_mod, module_wp=wp, module_wp_assumed=bool(wp_assumed), kwp=kwp, kwp_source=src, has_pv=kwp > 0)
    # any line of the solar technology: with kwp == 0 this means "PV offered, size not recoverable" (target NaN in the policy)
    r["has_solar_tech"] = bool((g.technology == "solar").any()) if "technology" in g else False

    # --- battery: capacity from the NAME first; column inverter_power_kw holds Wh (swapped); exclude AC coupling
    bat = g[(ctype == "BatteryStorage") & ~g.component_name.str.contains("coupling", case=False, na=False)]
    kwh = 0.0
    for i, row in bat.iterrows():
        c = parse_kwh(row.component_name)
        if c is None and pd.notna(row.inverter_power_kw):
            c = row.inverter_power_kw / 1000.0
        kwh += (c or 0.0) * qty[i]
    if kwh == 0 and pkg:
        kwh = pkg[0][1]
    r["battery_kwh"] = float(kwh)
    r["has_battery"] = kwh > 0

    # --- inverter: power from NAME; column battery_capacity_kwh holds W (swapped)
    inv = g[ctype == "Inverter"]
    ik = [_first_valid(parse_kw(n), w / 1000.0 if pd.notna(w) else None) for n, w in zip(inv.component_name.fillna(""), inv.battery_capacity_kwh)]
    ik = [x for x in ik if x]
    r["inverter_kw"] = float(max(ik)) if ik else np.nan

    # --- wallbox / heat pump
    wb = g[ctype == "Wallbox"]
    wk = [_first_valid(parse_kw(n), w / 1000.0 if pd.notna(w) else None) for n, w in zip(wb.component_name.fillna(""), wb.wb_charging_speed_kw)]
    wk = [x for x in wk if x]
    r["has_wallbox"] = len(wb) > 0
    r["wallbox_kw"] = float(max(wk)) if wk else np.nan
    hp = g[ctype == "Heatpump"]
    hk = [_first_valid(parse_kw(n), w / 1000.0 if pd.notna(w) else None) for n, w in zip(hp.component_name.fillna(""), hp.heatpump_nominal_power_kw)]
    hk = [x for x in hk if x]
    r["hp_kw"] = float(max(hk)) if hk else 0.0
    r["has_heatpump"] = len(hp) > 0
    r["has_buffer"] = bool((ctype == "HeatingStorage").any())
    r["has_dhw_tank"] = bool((ctype == "WarmwaterStorage").any())

    # --- hidden signals from part names
    roof, pitch = parse_roof(names)
    low = " | ".join(names).lower()
    r.update(
        roof_type=roof, pitch_hint=pitch,
        has_optimizers="optimizer" in low,
        has_backup=bool(re.search(r"emergency|transfer switch|eps box|backup", low)),
        has_meter_cabinet="meter cabinet" in low,
        n_lines=len(g),
    )
    return r


def build_options(parts: pd.DataFrame, installer_id: str) -> pd.DataFrame:
    rows = []
    for (pid, oid, onum), g in parts.groupby(["project_id", "option_id", "option_number"], sort=False):
        rows.append({"project_id": pid, "option_id": oid, "option_number": onum, "installer_id": installer_id, **build_option(g)})
    o = pd.DataFrame(rows)
    o = o.sort_values(["project_id", "option_number"], kind="stable").reset_index(drop=True)
    o["is_primary"] = ~o.duplicated("project_id")  # lowest option_number per project
    return o


def build_catalog(parts: pd.DataFrame, opts: pd.DataFrame, installer_id: str) -> dict:
    n_opt = len(opts)
    keyed = parts.assign(_opt=parts.project_id.astype(str) + "/" + parts.option_id.astype(str))

    def products(ctype: str, size_fn):
        d = keyed[keyed.component_type == ctype]
        if ctype == "BatteryStorage":
            d = d[~d.component_name.str.contains("coupling", case=False, na=False)]
        out = []
        for name, g in d.groupby("component_name"):
            f = g.iloc[0]
            out.append({
                "name": name, "brand": None if pd.isna(f.component_brand) else f.component_brand,
                "size": size_fn(f), "count": int(g._opt.nunique()), "share": round(g._opt.nunique() / n_opt, 4),
            })
        return sorted(out, key=lambda x: -x["count"])

    kwh_of = lambda r: _first_valid(parse_kwh(r.component_name), r.inverter_power_kw / 1000 if pd.notna(r.inverter_power_kw) else None)
    kw_of = lambda r: _first_valid(parse_kw(r.component_name), r.wb_charging_speed_kw / 1000 if pd.notna(r.wb_charging_speed_kw) else None)
    inv_of = lambda r: _first_valid(parse_kw(r.component_name), r.battery_capacity_kwh / 1000 if pd.notna(r.battery_capacity_kwh) else None)
    hp_of = lambda r: _first_valid(parse_kw(r.component_name), r.heatpump_nominal_power_kw / 1000 if pd.notna(r.heatpump_nominal_power_kw) else None)
    pkgs = (keyed[keyed.component_name.map(lambda n: parse_package(n) is not None)]
            .groupby("component_name")._opt.nunique().sort_values(ascending=False))

    skip_types = {"Module", "BatteryStorage", "Wallbox", "Heatpump", "Inverter"}
    services = []
    for name, g in keyed[~keyed.component_type.isin(skip_types)].groupby("component_name"):
        share = g._opt.nunique() / n_opt
        if share < 0.3:
            continue
        f = g.iloc[0]
        services.append({
            "componentName": name, "componentType": f.component_type, "technology": f.technology,
            "lineItemFunction": f.line_item_function,
            "componentBrand": None if pd.isna(f.component_brand) else f.component_brand,
            "quantityUnits": None if pd.isna(f.quantity_units) else f.quantity_units,
            "medianQuantity": float(g.quantity.median()), "share": round(float(share), 4),
        })
    services.sort(key=lambda x: -x["share"])

    prim = opts[opts.is_primary]
    bsizes = prim.loc[prim.battery_kwh > 0, "battery_kwh"].round(1).value_counts()
    return {
        "installerId": installer_id, "nProjects": int(opts.project_id.nunique()), "nOptions": n_opt,
        "batteryAttachRate": round(float(prim.has_battery.mean()), 4),
        "wallboxAttachRate": round(float(prim.has_wallbox.mean()), 4),
        "heatPumpAttachRate": round(float(prim.has_heatpump.mean()), 4),
        "medianKwp": float(prim.loc[prim.has_pv, "kwp"].median()),
        "medianBatteryKwh": float(prim.loc[prim.has_battery, "battery_kwh"].median()) if prim.has_battery.any() else 0.0,
        "batterySizesKwh": {str(k): int(v) for k, v in bsizes.items()},
        "moduleWp": {str(int(k)): int(v) for k, v in opts.loc[~opts.module_wp_assumed, "module_wp"].value_counts().items()},
        "batteries": products("BatteryStorage", kwh_of),
        "wallboxes": products("Wallbox", kw_of),
        "heatPumps": products("Heatpump", hp_of),
        "inverters": products("Inverter", inv_of),
        "packages": [{"name": k, "kwp": parse_package(k)[0], "kwh": parse_package(k)[1], "count": int(v)} for k, v in pkgs.items()],
        "roofTypes": {k: int(v) for k, v in opts.roof_type.value_counts().items()},
        "services": services,
    }


def run(raw: Path, out: Path) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    projects, options = [], []
    for d in sorted(p for p in raw.iterdir() if p.is_dir()):
        sq_path, parts_path = d / "projects_status_quo.csv", d / "project_options_parts.csv"
        if not (sq_path.exists() and parts_path.exists()):
            continue
        sq, parts = _read(sq_path), _read(parts_path)
        opts = build_options(parts, d.name)
        projects.append(build_projects(sq, d.name, set(parts.project_id)))
        options.append(opts)
        cat = build_catalog(parts, opts, d.name)
        (out / f"catalog_{d.name}.json").write_text(json.dumps(cat, indent=2, default=float), encoding="utf-8")
    P, O = pd.concat(projects, ignore_index=True), pd.concat(options, ignore_index=True)
    P.to_parquet(out / "projects.parquet", index=False)
    O.to_parquet(out / "options.parquet", index=False)
    return {"projects": len(P), "options": len(O)}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--raw", default="dataset", type=Path)
    ap.add_argument("--out", default="data/processed", type=Path)
    a = ap.parse_args()
    print(run(a.raw, a.out))


if __name__ == "__main__":
    main()
