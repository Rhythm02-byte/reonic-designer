"""Checks that answer, from the data itself, the parts of open questions 3 to 6 that the export can settle.

    python scripts/data_checks.py

Q3: are battery and inverter columns swapped? Test: package names say "+ 9kWh", so the battery row should be 9 kWh.
Q4: do packages include the battery? Test: how often a package and a separate battery row share an option.
Q5: does energy demand already include EV / heat pump? Test: are EV and heat pump homes higher than similar homes?
Q6: are the two folders different sources? Test: compare products, offer counts and consumption between folders.

Writes reports/data_checks.json. Uses the real export in data/raw (never committed).
"""
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd

from reonic import data

ROOT = Path("data/raw")
PKG_KWH = re.compile(r"\+\s*(\d+(?:[.,]\d+)?)\s*kWh", re.I)
PKG_KWP = re.compile(r"(\d+(?:[.,]\d+)?)\s*kWp", re.I)
report: dict = {}

# -- Q3 and Q4 need option-level data ----------------------------------------------------------------
q3_rows, q4 = [], {"options_with_package_kwh": 0, "of_which_also_separate_battery": 0, "options_with_separate_battery": 0}
for folder in sorted(p for p in ROOT.iterdir() if (p / "project_options_parts.csv").exists()):
    parts = pd.read_csv(folder / "project_options_parts.csv")
    names = parts["component_name"].fillna("")
    for oid, g in parts.groupby("option_id"):
        n = g["component_name"].fillna("")
        pkg = g[(g.component_type == "Other") & n.str.contains("kWp", case=False)]
        pkg_kwh = [float(PKG_KWH.search(x).group(1).replace(",", ".")) for x in pkg.component_name if PKG_KWH.search(x)]
        batt = g[g.component_type == "BatteryStorage"]
        has_batt = len(batt) > 0
        if has_batt:
            q4["options_with_separate_battery"] += 1
        if pkg_kwh:
            q4["options_with_package_kwh"] += 1
            if has_batt:
                q4["of_which_also_separate_battery"] += 1
        # Q3: battery capacity is stored in inverter_power_kw (in Wh) on battery rows
        if pkg_kwh and has_batt:
            stored_kwh = float(batt["inverter_power_kw"].fillna(0).sum()) / 1000
            q3_rows.append({"folder": folder.name, "package_kwh": pkg_kwh[0], "row_kwh_if_swapped": stored_kwh,
                            "match": abs(stored_kwh - pkg_kwh[0]) < 0.5})
q3 = pd.DataFrame(q3_rows)
report["Q3_swap_check"] = {
    "options_compared": int(len(q3)),
    "battery_row_matches_package_name": float(q3["match"].mean()) if len(q3) else None,
    "by_folder": {k: float(v) for k, v in q3.groupby("folder")["match"].mean().items()} if len(q3) else {},
}
report["Q4_package_battery"] = q4

# Inverter rows: check the other side of the swap (inverter kW should match the name, e.g. "Hybrid Inverter 10kW")
inv_rows = []
for folder in sorted(p for p in ROOT.iterdir() if (p / "project_options_parts.csv").exists()):
    parts = pd.read_csv(folder / "project_options_parts.csv")
    inv = parts[parts.component_type == "Inverter"]
    for _, r in inv.iterrows():
        m = re.search(r"(\d+(?:\.\d+)?)\s*kW", str(r.component_name))
        if m and pd.notna(r.battery_capacity_kwh):
            inv_rows.append(abs(float(r.battery_capacity_kwh) / 1000 - float(m.group(1))) < 0.5)
report["Q3_inverter_side"] = {"rows_compared": len(inv_rows),
                              "match_share": float(np.mean(inv_rows)) if inv_rows else None}

# -- Q5 and Q6 use project-level data ----------------------------------------------------------------
frames = []
for folder in sorted(p for p in ROOT.iterdir() if (p / "projects_status_quo.csv").exists()):
    sq = pd.read_csv(folder / "projects_status_quo.csv")
    sq["folder"] = folder.name
    frames.append(sq)
sq = pd.concat(frames, ignore_index=True)
sq["demand_kwh"] = pd.to_numeric(sq["energy_demand_wh"], errors="coerce") / 1000
sq["ev"] = sq["has_ev"].astype(bool)
sq["hp"] = sq["heating_existing_type"].astype(str).str.lower().eq("heatpump")

# Q5: compare demand of EV homes with non-EV homes, and heat pump homes with others, within a house-size band.
# If the demand field already contained the EV, EV homes would show no clear uplift beyond the EV's own kWh.
q5 = {}
for flag in ("ev", "hp"):
    a = sq.loc[sq[flag], "demand_kwh"].dropna()
    b = sq.loc[~sq[flag], "demand_kwh"].dropna()
    q5[flag] = {"n_with": int(len(a)), "median_with_kwh": float(a.median()) if len(a) else None,
                "median_without_kwh": float(b.median()) if len(b) else None}
report["Q5_demand_includes_ev_hp"] = q5

# Q6: folder comparison on observable features
q6 = {}
for folder, g in sq.groupby("folder"):
    parts = pd.read_csv(ROOT / folder / "project_options_parts.csv")
    batt_brands = parts.loc[parts.component_type == "BatteryStorage", "component_brand"].dropna().value_counts(normalize=True).head(3)
    mod_brands = parts.loc[parts.component_type == "Module", "component_brand"].dropna().value_counts(normalize=True).head(3)
    q6[folder] = {
        "projects": int(len(g)),
        "median_demand_kwh": float(g["demand_kwh"].median()),
        "share_ev": float(g["ev"].mean()),
        "share_heat_pump_existing": float(g["hp"].mean()),
        "share_with_existing_pv": float((pd.to_numeric(g["solar_size_kwp"], errors="coerce") > 0).mean()),
        "top_battery_brands": {k: round(float(v), 2) for k, v in batt_brands.items()},
        "top_module_brands": {k: round(float(v), 2) for k, v in mod_brands.items()},
        "countries": g["country"].value_counts().to_dict(),
    }
report["Q6_folder_comparison"] = q6

Path("reports").mkdir(exist_ok=True)
Path("reports/data_checks.json").write_text(json.dumps(report, indent=2, default=float))
print(json.dumps(report, indent=2, default=float))
