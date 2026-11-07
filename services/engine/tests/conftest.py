"""Tiny synthetic CSVs (hand-written, no real data) in the raw Reonic layout."""
import os
from pathlib import Path

import pandas as pd
import pytest

# tests must not depend on the repo's config/policy.json (written by eval --select): use the built-in defaults (hybrid, gate 0.5)
os.environ["ENGINE_POLICY_CONFIG"] = str(Path(__file__).parent / "no-such-policy.json")

SQ_COLS = ["project_id", "customer_contact_id", "request_created_at", "offer_created_at", "first_signed_at", "country",
           "energy_demand_wh", "energy_price_per_wh", "energy_price_increase", "energy_price_with_flexible_tariff",
           "base_price_per_month", "load_profile", "has_ev", "ev_annual_drive_distance_km", "has_solar", "solar_size_kwp",
           "solar_angle", "solar_orientation", "solar_built_year", "has_storage", "storage_size_kwh", "storage_built_year",
           "has_wallbox", "wallbox_charge_speed_kw", "heating_existing_type", "heating_existing_cost_per_year",
           "heating_existing_electricity_demand_kwh", "heating_existing_heating_demand_wh"]
PART_COLS = ["project_id", "option_id", "option_number", "technology", "line_item_function", "component_type", "component_name",
             "component_brand", "quantity", "quantity_units", "module_watt_peak", "inverter_power_kw", "battery_capacity_kwh",
             "wb_charging_speed_kw", "heatpump_nominal_power_kw"]


def _sq(**kw):
    base = dict.fromkeys(SQ_COLS)
    base.update(country="DE", energy_price_increase=0.03, load_profile="H0", has_ev=False, has_solar=False, has_storage=False,
                has_wallbox=False)
    base.update(kw)
    return base


def _part(pid, oid, onum, ctype, name, qty=1, tech="solar", **kw):
    base = dict.fromkeys(PART_COLS)
    base.update(project_id=pid, option_id=oid, option_number=onum, technology=tech, line_item_function="default",
                component_type=ctype, component_name=name, quantity=qty, quantity_units="Item")
    base.update(kw)
    return base


@pytest.fixture(scope="session")
def raw_dir(tmp_path_factory) -> Path:
    root = tmp_path_factory.mktemp("raw") / "inst1"
    root.mkdir()
    sq = pd.DataFrame([
        _sq(project_id="A", customer_contact_id="c1", offer_created_at="2025-03-01 10:00:00.123000", energy_demand_wh=4_500_000,
            energy_price_per_wh=0.00032, has_ev=True, ev_annual_drive_distance_km=12000,
            has_solar=True, solar_size_kwp=5000, solar_built_year=2020,
            has_storage=True, storage_size_kwh=10000, storage_built_year=2025),
        _sq(project_id="B", customer_contact_id="c2", offer_created_at="2025-07-01T07:00:55Z", energy_demand_wh=6_200_000,
            energy_price_per_wh=0.00035),
        _sq(project_id="C", customer_contact_id="c3", offer_created_at="2026-01-15", energy_demand_wh=3_000_000,
            energy_price_per_wh=0.0003, heating_existing_type="Gas", heating_existing_cost_per_year=1.2,
            heating_existing_heating_demand_wh=18_000_000),
        _sq(project_id="D", customer_contact_id="c4", offer_created_at="2026-02-01", energy_demand_wh=5_000_000,
            energy_price_per_wh=0.0003, heating_existing_type="Heatpump", heating_existing_electricity_demand_kwh=4000,
            heating_existing_heating_demand_wh=14_000_000),
    ])
    parts = pd.DataFrame([
        # A: itemised; name beats rounded columns; battery/inverter columns are swapped; AC coupling excluded
        _part("A", "A1", 1, "Module", "PV Module 463W", 20, module_watt_peak=450),
        _part("A", "A1", 1, "ModuleFrameConstruction", "Substructure Concrete Tile Roof", 20),
        _part("A", "A1", 1, "InstallationFee", "DC Install Concrete Roof >30°", 20),
        _part("A", "A1", 1, "BatteryStorage", "Battery 7kWh", 1, tech="ses", inverter_power_kw=7000),
        _part("A", "A1", 1, "BatteryStorage", "AC Coupling Module (Free)", 1, tech="ses", inverter_power_kw=0),
        _part("A", "A1", 1, "Inverter", "Hybrid Inverter 10kW", 1, battery_capacity_kwh=10000),
        _part("A", "A1", 1, "Wallbox", "Wallbox 11kW", 1, tech="wallbox", wb_charging_speed_kw=11000),
        _part("A", "A1", 1, "Other", "Power Optimizer 600W", 20),
        # B: package carries the sizes; option 2 is a bigger battery variant
        _part("B", "B1", 1, "Other", "Complete Package 2 Sigenergy 10.8kWp + 9kWh B", 1),
        _part("B", "B1", 1, "ModuleFrameConstruction", "Substructure Clay Roof", 24),
        _part("B", "B2", 2, "Other", "Complete Package 2 Sigenergy 10.8kWp + 9kWh B", 1),
        _part("B", "B2", 2, "BatteryStorage", "Battery 5kWh Extension", 2, tech="ses", inverter_power_kw=5000),
        _part("B", "B2", 2, "BatteryStorage", "Battery 10kWh", 1, tech="ses", inverter_power_kw=10000),
        # C: no module lines -> substructure count x assumed 450 W; heat pump 12.5 kW (column rounded to 12)
        _part("C", "C1", 1, "ModuleFrameConstruction", "Substructure Flat Roof East/West", 10),
        _part("C", "C1", 1, "Heatpump", "Heat Pump 12.5kW", 1, tech="heatpump", heatpump_nominal_power_kw=12000),
        _part("C", "C1", 1, "HeatingStorage", "Buffer Storage 200L", 1, tech="heatpump"),
        _part("C", "C1", 1, "WarmwaterStorage", "Hot Water Storage 300L", 1, tech="heatpump"),
        # D: battery-only retrofit
        _part("D", "D1", 1, "BatteryStorage", "Battery LFP 10kWh", 1, tech="ses", inverter_power_kw=10000),
    ])[PART_COLS]
    sq[SQ_COLS].to_csv(root / "projects_status_quo.csv", index=False, encoding="latin1")
    parts.to_csv(root / "project_options_parts.csv", index=False, encoding="latin1")
    return root.parent


@pytest.fixture(scope="session")
def processed(raw_dir, tmp_path_factory):
    from engine.etl.normalize import run
    out = tmp_path_factory.mktemp("processed")
    run(raw_dir, out)
    return out
