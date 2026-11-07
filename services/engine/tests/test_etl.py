import json

import pandas as pd
import pytest

from engine.etl.normalize import parse_kw, parse_kwh, parse_package, parse_roof


@pytest.fixture(scope="module")
def tables(processed):
    P = pd.read_parquet(processed / "projects.parquet").set_index("project_id")
    O = pd.read_parquet(processed / "options.parquet")
    return P, O


def opt(O, oid):
    return O[O.option_id == oid].iloc[0]


def test_unit_fixes(tables):
    P, _ = tables
    a = P.loc["A"]
    assert a.demand_kwh == 4500 and a.demand_is_default and a.demand_round500
    assert a.price_eur_kwh == pytest.approx(0.32)
    assert a.existing_pv_kwp == 5.0 and a.existing_storage_kwh == 10.0
    assert P.loc["B"].demand_kwh == 6200 and not P.loc["B"].demand_is_default


def test_trusted_existing_rule(tables):
    P, _ = tables
    assert P.loc["A"].existing_pv_trusted and not P.loc["A"].existing_pv_ambiguous      # built 2020 < 2025
    assert not P.loc["A"].existing_storage_trusted and P.loc["A"].existing_storage_ambiguous  # built 2025 == offer year
    assert not P.loc["B"].existing_pv_trusted


def test_mixed_date_formats(tables):
    P, _ = tables
    assert P.offer_at.notna().all()


def test_heating_fields(tables):
    P, _ = tables
    c = P.loc["C"]
    assert c.heating_fossil and c.heat_demand_kwh == 18000
    assert c.heating_cost_is_unit_price and pd.isna(c.heating_cost_eur_year)
    d = P.loc["D"]
    assert not d.heating_fossil and d.hp_elec_existing_kwh == 4000 and d.heat_demand_is_derived


def test_name_beats_column_and_swapped_columns(tables):
    _, O = tables
    a = opt(O, "A1")
    assert a.n_modules == 20 and a.module_wp == 463 and not a.module_wp_assumed
    assert a.kwp == pytest.approx(9.26) and a.kwp_source == "modules"
    assert a.battery_kwh == 7.0            # swapped column, AC coupling excluded
    assert a.inverter_kw == 10.0           # swapped column
    assert a.has_wallbox and a.wallbox_kw == 11.0
    assert a.has_optimizers and not a.has_backup


def test_package_parsing(tables):
    _, O = tables
    b1, b2 = opt(O, "B1"), opt(O, "B2")
    assert b1.kwp == 10.8 and b1.kwp_source == "package" and b1.battery_kwh == 9.0
    assert b2.battery_kwh == 20.0          # 2 x 5 kWh extension + 10 kWh
    assert b1.is_primary and not b2.is_primary


def test_substructure_count_and_assumed_wp(tables):
    _, O = tables
    c = opt(O, "C1")
    assert c.kwp_source == "substructure" and c.module_wp == 450 and c.module_wp_assumed
    assert c.kwp == pytest.approx(4.5)
    assert c.hp_kw == 12.5 and c.has_buffer and c.has_dhw_tank and not c.has_battery


def test_battery_only_option_has_no_pv(tables):
    _, O = tables
    d = opt(O, "D1")
    assert not d.has_pv and d.kwp == 0 and d.battery_kwh == 10.0


def test_roof_parsing():
    assert parse_roof(["Substructure Concrete Tile Roof"]) == ("concrete_tile", None)
    assert parse_roof(["DC Install Clay Roof <30°"]) == ("clay_tile", "lt30")
    assert parse_roof(["DC Install Concrete Roof >30°"]) == ("concrete_tile", "gt30")
    assert parse_roof(["Substructure Flat Roof East/West"])[0] == "flat_ew"
    assert parse_roof(["Substructure Flat Roof Ballast"])[0] == "flat"
    assert parse_roof(["Substructure Standing Seam B"])[0] == "standing_seam"
    assert parse_roof(["Substructure Beaver Tail Tile"])[0] == "beaver_tail"
    assert parse_roof(["Substructure 8.8-15kWp"])[0] == "unknown"
    assert parse_roof(["Battery 7kWh"])[0] == "unknown"


def test_name_parsers():
    assert parse_package("Complete Package 2 Sigenergy 10.8kWp + 9kWh B") == (10.8, 9.0)
    assert parse_kwh("EcoFlow | 10,2 kWh | Power Ocean") == 10.2
    assert parse_kw("Heat Pump 12.5kW 400V") == 12.5
    assert parse_kw("Roof 10.8kWp") is None


def test_catalog_written(processed):
    cat = json.loads((processed / "catalog_inst1.json").read_text())
    assert cat["nOptions"] == 5 and cat["packages"][0]["kwp"] == 10.8
    assert any(b["size"] == 7.0 for b in cat["batteries"])
