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
- **Options:** projects can have several. `OPTION_CHOICE = "first"` (lowest option_number) until Reonic says which one was signed.

## What the data contains

| | `23c108b7` | `2a8ba8e2` |
|---|---|---|
| Projects (usable) | 336 | 1,257 |
| With >1 option | 6% | 22% |
| PV size recoverable | 99% | 93% |
| Period | 2025 | mid-2024 → 2025 |

- Expert designs: batteries in about 89%, PV in about 86%, wallbox in 26% (much more likely with an EV). Heat pumps in 0.3% (31 rows), so heat pump sizing can't be learned.
- Storage-only retrofits exist for homes that already have PV.
- Inputs: reliable for demand, price, price increase, EV, load profile, existing PV/battery/wallbox, flexible tariff. Heating type and heating demand about 12%. House size and inhabitants under 1%. Roof area and budget absent.
- The two installers behave differently: PV tracks demand at `2a8ba8e2`; designs look package-driven at `23c108b7`.
- Outliers to check before the pitch: consumption 0 or 50,000 kWh, PV up to 99.9 kWp, battery up to 108 kWh. These may be commercial projects or errors. Decide and document, don't silently drop.

## Open questions for Reonic (ask on site, record answers here)

1. Which option was signed? Lowest, highest, or not recoverable?
2. Module wattage at `2a8ba8e2`, and is the quantity on DC Install / Substructure lines always the module count?
3. Are `inverter_power_kw` and `battery_capacity_kwh` really swapped in the export?
4. Do package lines include the battery, or can a separate battery come on top?
5. Does `energy_demand_wh` include an existing EV or heat pump?
6. What do the folder IDs represent? (We assume installers.)
7. Realistic time per design today, and offer → signed rate, for the business case.

**Answers:** _none yet._ When an answer arrives, change the code it affects (`OPTION_CHOICE`, `MODULE_WP`, the swap handling), rerun the evaluation, and record the before/after in `reonic-evaluate`.

## Checks before you finish a data change

- `pytest -q` passes (loader tests use a hand-made mini export, not the real data).
- `python -m reonic build` runs and prints the PV source counts; no new surprises.
- No file from `data/raw/` or `data/projects.csv` is staged in git.
