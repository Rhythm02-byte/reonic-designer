from reonic import physics, rules
from reonic.schema import HomeInputs

CAT = {"battery_kwh": [5.0, 10.0, 15.0], "heat_pump_kw": [8.0, 12.0], "pv_kwp": [], "wallbox_kw": [11.0, 22.0]}


def test_battery_raises_self_consumption_and_stays_bounded():
    no_bat = physics.self_consumption_ratio(5000, 8000, 0)
    with_bat = physics.self_consumption_ratio(5000, 8000, 10)
    assert 0 < no_bat < with_bat <= 0.95


def test_no_ev_means_no_ev_demand():
    assert physics.ev_demand_kwh(False, 20000) == 0
    assert physics.ev_demand_kwh(True, None) == physics.DEFAULT_EV_KM * physics.EV_KWH_PER_KM


def test_r01_existing_heat_pump():
    v, notes, _ = rules.apply_one("heat_pump_kw", 10, {}, HomeInputs(heating_type="heat_pump"), CAT)
    assert v == 0 and notes[0].startswith("R01")


def test_r02_no_battery_without_pv():
    v, notes, _ = rules.apply_one("battery_kwh", 10, {"pv_kwp": 0}, HomeInputs(), CAT)
    assert v == 0 and notes[0].startswith("R02")


def test_r02_battery_allowed_for_existing_pv():
    v, notes, _ = rules.apply_one("battery_kwh", 10, {"pv_kwp": 0}, HomeInputs(existing_pv_kwp=8), CAT)
    assert v == 10.0 and notes == []


def test_r03_residential_pv_cap():
    v, notes, _ = rules.apply_one("pv_kwp", 45, {}, HomeInputs(), CAT)
    assert v == rules.PV_MAX_KWP and notes[0].startswith("R03")


def test_wallbox_snaps_to_catalog():
    assert rules.apply_one("wallbox_kw", 14, {}, HomeInputs(), CAT)[0] == 11.0


def test_r04_battery_ratio_and_snap():
    v, notes, _ = rules.apply_one("battery_kwh", 30, {"pv_kwp": 6}, HomeInputs(), CAT)
    assert v == 10.0 and notes[0].startswith("R04")


def test_locked_value_is_kept_but_flagged():
    v, notes, flags = rules.apply_one("battery_kwh", 10, {"pv_kwp": 0}, HomeInputs(), CAT, locked=True)
    assert v == 10 and notes == [] and "R02" in flags[0]


def test_common_sizes_picks_frequent_values():
    assert rules.common_sizes([10, 10, 10, 7.5, 7.5, 5, 0], top=2) == [7.5, 10.0]
