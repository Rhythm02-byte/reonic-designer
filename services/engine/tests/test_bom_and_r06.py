"""Jury-review engine bugs: a bill of materials must not mix makers (inverter vs battery), and R06 must not warn when
the larger battery earns the better 20-year NPV. SYNTHETIC data only."""
from engine.design import _bom
from engine.models.schemas import BatteryDesign, PvDesign, SystemDesign


def cat(inverters, batteries):
    return {"inverters": inverters, "batteries": batteries, "wallboxes": [], "heatPumps": [], "services": [], "moduleWp": {}}


def prod(brand, name, size, count=10):
    return {"brand": brand, "name": name, "size": size, "count": count}


def brands(lines):
    return {l.component_type: l.component_brand for l in lines if l.component_brand}


def system(kwp=8.0, kwh=10.0):
    return SystemDesign(pv=PvDesign(modules=round(kwp * 1000 / 450), module_wp=450, kwp=kwp), battery=BatteryDesign(kwh=kwh))


def test_inverter_follows_the_battery_brand_when_the_size_is_close():
    c = cat([prod("Sigenergy", "Sig 8 kW", 8.0), prod("EcoFlow", "Eco 7 kW", 7.6)],
            [prod("EcoFlow", "Eco 10 kWh", 10.0)])
    b = brands(_bom(c, system(kwp=8.0, kwh=10.0)))
    assert b["Inverter"] == b["BatteryStorage"] == "EcoFlow"  # nearest inverter alone would be the Sigenergy 8 kW


def test_a_far_off_same_brand_inverter_is_not_forced():
    c = cat([prod("Sigenergy", "Sig 8 kW", 8.0), prod("EcoFlow", "Eco 3 kW", 3.0)], [prod("EcoFlow", "Eco 10 kWh", 10.0)])
    assert brands(_bom(c, system()))["Inverter"] == "Sigenergy"  # an undersized inverter is worse than a mixed list


def test_no_battery_keeps_the_nearest_inverter():
    c = cat([prod("Sigenergy", "Sig 8 kW", 8.0), prod("EcoFlow", "Eco 7 kW", 7.6)], [prod("EcoFlow", "Eco 10 kWh", 10.0)])
    s = SystemDesign(pv=PvDesign(modules=18, module_wp=450, kwp=8.1))
    assert brands(_bom(c, s))["Inverter"] == "Sigenergy"


def _rows(npv_big):
    row = lambda aut, sav, npv: {"autarky": aut, "savingsEurYear": sav, "npv20": npv}
    return {5.0: row(0.50, 400.0, 3000.0), 10.0: row(0.60, 450.0, 3100.0), 15.0: row(0.65, 480.0, npv_big)}


STEPS = (0.0, 5.0, 10.0, 15.0)


def test_r06_warns_when_the_larger_battery_costs_npv():
    from engine.design import _r06
    f = _r06(15.0, 5.0, STEPS, _rows(2500.0))
    assert f is not None and f.code == "R06" and f.severity == "warn" and "-500 EUR" in f.message


def test_r06_is_silent_when_the_larger_battery_earns_more_npv():
    from engine.design import _r06
    assert _r06(15.0, 5.0, STEPS, _rows(3500.0)) is None


def test_r06_is_silent_below_two_sizes_above_the_economic_one():
    from engine.design import _r06
    assert _r06(10.0, 5.0, STEPS, _rows(100.0)) is None
