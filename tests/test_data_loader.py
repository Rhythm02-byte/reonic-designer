"""The raw-export loader, on a hand-made miniature of Reonic's format (the real data is confidential)."""
import numpy as np
import pandas as pd
import pytest

from reonic import data

SQ_COLS = ["project_id", "offer_created_at", "country", "energy_demand_wh", "energy_price_per_wh", "energy_price_increase",
           "energy_price_with_flexible_tariff", "load_profile", "has_ev", "ev_annual_drive_distance_km", "has_solar",
           "solar_size_kwp", "has_storage", "storage_size_kwh", "has_wallbox", "heating_existing_type",
           "heating_existing_heating_demand_wh", "house_size_sqm", "num_inhabitants"]
PART_COLS = ["project_id", "option_id", "option_number", "technology", "component_type", "component_name", "quantity",
             "quantity_units", "module_watt_peak", "inverter_power_kw", "battery_capacity_kwh", "wb_charging_speed_kw",
             "heatpump_nominal_power_kw"]


def part(pid, oid, num, tech, ctype, name, qty=1.0, units="Item", **vals):
    return {"project_id": pid, "option_id": oid, "option_number": num, "technology": tech, "component_type": ctype,
            "component_name": name, "quantity": qty, "quantity_units": units, **vals}


@pytest.fixture
def raw(tmp_path):
    d = tmp_path / "inst1"
    d.mkdir()
    sq = pd.DataFrame([
        ["p1", "2025-01-01", "Germany", 5_500_000, 0.00039, 0.03, None, "H0", False, None, False, None, False, None, False, "Gas", 15_750_000, None, None],
        ["p2", "2025-01-02", "Germany", 4_000_000, 0.00035, 0.03, 0.0002, "H0", True, 15000, True, 10_000, False, None, False, None, None, None, None],
        ["p3", "2025-01-03", "Germany", 3_000_000, 0.00030, 0.02, None, "H0", False, None, False, None, False, None, False, None, None, None, None],
    ], columns=SQ_COLS)
    parts = pd.DataFrame([
        # p1 option 1: modules 20 x 450 W, battery 10 kWh (capacity sits in inverter_power_kw), heat pump 10.5 kW
        part("p1", "o1", 1, "solar", "Module", "PV Module 450W", 20, module_watt_peak=450),
        part("p1", "o1", 1, "ses", "BatteryStorage", "Battery 10kWh", 1, inverter_power_kw=10_000),
        part("p1", "o1", 1, "heatpump", "Heatpump", "Heat Pump 10.5kW", 1, heatpump_nominal_power_kw=10_500),
        part("p1", "o1", 1, "solar", "ModuleFrameConstruction", "Scaffolding Setup & Removal", 80, units="SquareMeter"),
        # p1 option 2 (should be ignored with OPTION_CHOICE="first")
        part("p1", "o2", 2, "solar", "Module", "PV Module 450W", 30, module_watt_peak=450),
        # p2: storage-only retrofit (home already has PV) + wallbox
        part("p2", "o3", 1, "ses", "BatteryStorage", "Battery 5kWh", 2, inverter_power_kw=5_000),
        part("p2", "o3", 1, "wallbox", "Wallbox", "Wallbox 11kW", 1, wb_charging_speed_kw=11_000),
        # p3: package name gives kWp + kWh, plus a per-module substructure line
        part("p3", "o4", 1, "solar", "Other", "Complete Package 2 Sigenergy 10.8kWp + 9kWh"),
        part("p3", "o4", 1, "solar", "ModuleFrameConstruction", "Substructure 8.8-15kWp", 24),
    ], columns=PART_COLS)
    sq.to_csv(d / "projects_status_quo.csv", index=False)
    parts.to_csv(d / "project_options_parts.csv", index=False)
    return tmp_path


def test_units_inputs_and_targets(raw):
    df = data.load(raw).set_index("project_id")
    p1, p2, p3 = df.loc["p1"], df.loc["p2"], df.loc["p3"]
    assert p1.annual_consumption_kwh == 5500 and p1.electricity_price_eur_kwh == pytest.approx(0.39)
    assert p1.heating_type == "gas" and p1.heating_demand_kwh == 15750
    assert (p1.pv_kwp, p1.battery_kwh, p1.heat_pump_kw, p1.wallbox_kw) == (9.0, 10.0, 10.5, 0.0)
    assert p1.pv_source == "module_rows" and p1.n_options == 2
    assert p2.existing_pv_kwp == 10.0 and p2.has_flexible_tariff == 1.0
    assert (p2.pv_kwp, p2.battery_kwh, p2.wallbox_kw) == (0.0, 10.0, 11.0)
    assert p3.pv_source == "package_name" and p3.pv_kwp == 10.8 and p3.battery_kwh == 9.0
    assert (df.installer_id == "inst1").all()


def test_option_choice_last(raw):
    df = data.load_raw(raw, option_choice="last").set_index("project_id")
    assert df.loc["p1", "pv_kwp"] == 13.5  # 30 x 450 W


def test_module_count_fallback_and_unknown_pv():
    parts = pd.DataFrame([
        part("a", "x", 1, "solar", "AccessoryToModule", "DC Install Clay Tile Roof", 20),
        part("b", "y", 1, "solar", "ServiceFee", "Grid Registration", 1),  # solar offered, size unknowable
    ], columns=PART_COLS)
    o = data.option_designs(parts).set_index("project_id")
    assert o.loc["a", "pv_kwp"] == pytest.approx(20 * data.MODULE_WP / 1000) and o.loc["a", "pv_source"] == "module_count"
    assert np.isnan(o.loc["b", "pv_kwp"]) and o.loc["b", "pv_source"] == "unknown"


def test_zero_consumption_is_unknown_not_zero(raw):
    sq = pd.read_csv(raw / "inst1" / "projects_status_quo.csv")
    sq.loc[sq.project_id == "p3", "energy_demand_wh"] = 0
    sq.to_csv(raw / "inst1" / "projects_status_quo.csv", index=False)
    df = data.load(raw).set_index("project_id")
    assert np.isnan(df.loc["p3", "annual_consumption_kwh"])
    assert df.loc["p1", "annual_consumption_kwh"] == 5500
