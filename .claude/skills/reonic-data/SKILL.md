---
name: reonic-data
description: Use when loading, inspecting, or changing Reonic's raw export (data/raw), the expert-design rebuild in src/reonic/data.py, or answering questions about what the data contains. Not needed for model or UI work.
---
# Reonic data

## Layout

`data/raw/<installer_id>/` (gitignored, never commit):

- `projects_status_quo.csv`: one row per home before the offer → **inputs**.
- `project_options_parts.csv`: every line item of every offered option → the **expert design is rebuilt from these**.

Commands: `python -m reonic build` writes `data/projects.csv` for inspection. `python -m reonic eval` runs the evaluation.

## Quirks (already handled in `data.py`; do not undo)

- **Units:** `_kw`, `_kwh`, `_wh` columns hold W and Wh. Divide by 1000. `energy_price_per_wh` × 1000 gives €/kWh.
- **Swapped columns:** battery capacity sits in `inverter_power_kw` on `BatteryStorage` rows, and inverter power in `battery_capacity_kwh` on `Inverter` rows.
- **PV kWp is rebuilt** in this priority order:
  1. `Module` rows (W × qty)
  2. "Complete Package … 10.8kWp + 9kWh" names
  3. module count from per-module lines (`DC Install…`, `Substructure…`, `Roof Mounting…`) × `MODULE_WP` = 450 W (**assumed**)
  4. otherwise NaN (offered, size unknown)
- **Battery:** itemised `BatteryStorage` rows. A package's kWh counts only when the battery isn't itemised, to avoid double counting.
- **Zero consumption:** `energy_demand_wh` = 0 (13 projects, all at `2a8ba8e2`) is loaded as unknown, not as 0 kWh.
- **Options:** projects can have several. `OPTION_CHOICE = "first"` (lowest option_number) until Reonic says which one was signed.

## What the data contains

|                     | `23c108b7` | `2a8ba8e2`     |
| ------------------- | ------------ | ---------------- |
| Projects (usable)   | 336          | 1,257            |
| With >1 option      | 6%           | 22%              |
| PV size recoverable | 99%          | 93%              |
| Period              | 2025         | mid-2024 → 2025 |

- Chosen designs (`OPTION_CHOICE=first`): batteries in about 89%, PV in about 86%, wallbox in 26% (much more likely with an EV). Heat pumps in **13 of 1,593 (0.8%)**. The export has 31 heat pump line items across all options, which is where the earlier 0.3% figure came from. Too few to learn sizing from.
- Storage-only retrofits exist for homes that already have PV.
- Inputs: reliable for demand, price, price increase, EV, load profile, existing PV/battery/wallbox, flexible tariff. Heating type and heating demand about 12%. House size and inhabitants under 1%. Roof area and budget absent.
- The two installers behave differently: PV tracks demand at `2a8ba8e2`; designs look package-driven at `23c108b7`.
- Gaps (share blank in `data/projects.csv`): heating type 88%, heating demand 88%, EV km 96%, household size 100%, heated area 100%, PV size 6%. Consumption, price, EV yes/no, load profile and existing PV/battery are complete.
- Outliers to check before the pitch: consumption 0 or 50,000 kWh, PV up to 99.9 kWp, battery up to 108 kWh. These may be commercial projects or errors. Decide and document, don't silently drop.

## Open questions for Reonic (ask on site, record answers here)

Status after the data checks (`python scripts/data_checks.py` → `reports/data_checks.json`). Data evidence does not replace Reonic's answers.

1. **Which option was signed?** Lowest, highest, or not recoverable? *No data evidence. Sensitivity: whole-design score 12.5–15.7% across both choices (`scripts/sensitivity.py`).*
2. **Module wattage at `2a8ba8e2`**, and is the quantity on DC Install / Substructure lines always the module count? *Sensitivity across 400/450/500 W: PV within tolerance 45–47%, so the conclusion holds. Data evidence: the named modules at 2a8ba8e2 are 'PV Module 475W' (AIKO) and 'PV Module 455W' (Trina). The assumed 450 W is therefore probably low, and 475 W may be closer. Worth asking Reonic.*
3. **Are `inverter_power_kw` and `battery_capacity_kwh` swapped in the export?** *Data evidence supports it: inverter rows' battery_capacity_kwh/1000 matches the kW in the inverter name for 98% of 52 rows. Battery rows match the "+ N kWh" package name for 71% of 77 options, all in folder 23c108b7. The 29% mismatch is not yet explained.*
4. **Do package lines include the battery?** *Data evidence is mixed: 77 of 149 options with a package kWh also have a separate battery row, so the current rule (use the separate row, otherwise the package kWh) is consistent with both readings. Possible double count in those 77 options. Still needs Reonic.*
5. **Does `energy_demand_wh` include an existing EV or heat pump?** *Data evidence supports "no": homes with an EV have median demand 4,000 kWh vs 4,500 kWh without, and heat pump homes 4,000 vs 4,500. If the field included them, those homes would be higher. Unadjusted medians, so weak evidence.*
6. **What do the folder IDs represent?** *Data evidence supports two separate sources: different battery brands (Sigenergy 89% vs Huawei 49% / EcoFlow 40%), different modules (Sunpro 94% vs AIKO 75%), and 0% vs 1.4% existing PV. Still assumed to be installers.*
7. **Realistic time per design today, and offer → signed rate, for the business case.** *No data evidence.*
8. **Is the 4,500 kWh demand a default value?** *Data evidence: 457 of 1,593 projects (29%) show exactly 4,500 kWh, far more than the round value 4,000 kWh (5–7%). Likely a placeholder. Removing them changes the whole-design score from 15.7% to 14.9% (baseline 3.8% → 5.3%), and the model scores them about the same as other homes (18% vs 15%). So the conclusion holds, but 29% of consumption inputs may be placeholders. Ask Reonic whether these are measured, estimated or defaults. See `scripts/default_demand_check.py`.*

**Answers:** _none yet._ When an answer arrives, change the code it affects (`OPTION_CHOICE`, `MODULE_WP`, the swap handling, the demand input), rerun the evaluation and the sensitivity script, and record the before/after in `reonic-evaluate`.

## Checks before you finish a data change

- `pytest -q` passes (loader tests use a hand-made mini export, not the real data).
- `python -m reonic build` runs and prints the PV source counts; no new surprises.
- No file from `data/raw/` or `data/projects.csv` is staged in git.
