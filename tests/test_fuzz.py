"""Fuzzing the design engine (full 2,000-home run on the real data: scripts/fuzz_engine.py)."""
import importlib.util
import math
from pathlib import Path

import pytest

from reonic import synth
from reonic.engine import Designer
from reonic.schema import Design, HomeInputs

_spec = importlib.util.spec_from_file_location("fuzz_engine", Path(__file__).resolve().parents[1] / "scripts" / "fuzz_engine.py")
fz = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(fz)

NAN = float("nan")


@pytest.fixture(scope="module")
def designer():
    return Designer.train(synth.generate(1200, seed=1))


def test_random_and_extreme_homes_break_no_invariant(designer):
    bad = fz.fuzz(designer, n=40, seed=1)
    assert not bad, bad[:2]


@pytest.mark.parametrize("home", [
    HomeInputs(),  # everything unknown
    HomeInputs(annual_consumption_kwh=1e9, existing_pv_kwp=1e4, has_ev=True, ev_km_per_year=1e7),
    HomeInputs(annual_consumption_kwh=-100, electricity_price_eur_kwh=-1, ev_km_per_year=-5, has_ev=True),
    HomeInputs(annual_consumption_kwh=NAN, electricity_price_eur_kwh=NAN, heating_demand_kwh=0),
    HomeInputs(heating_type="garbage", load_profile="not_a_profile", has_ev=False),
    HomeInputs(heating_type="HEAT_PUMP", heating_demand_kwh=1e7, existing_pv_kwp=0),
])
def test_corner_homes_give_a_finite_valid_design(designer, home):
    assert fz.check(designer, home, {}) == []
    d = designer.design(home)
    assert all(math.isfinite(v) and v >= 0 for v in d.values().values())


def test_every_component_can_be_locked_at_extreme_values(designer):
    home = HomeInputs(annual_consumption_kwh=5000, has_ev=True)
    for locks in ({"pv_kwp": 100.0}, {"battery_kwh": 100.0}, {"heat_pump_kw": 100.0}, {"wallbox_kw": 100.0},
                  {"pv_kwp": 0.0, "battery_kwh": 10.0}):
        assert fz.check(designer, home, locks) == [], locks


class _Stub:
    """A designer that returns a fixed (possibly wrong) design, to prove the checker can fail."""
    catalog = {"wallbox_kw": [11.0, 22.0]}

    def __init__(self, **sizes):
        self.sizes = {"pv_kwp": 0.0, "battery_kwh": 0.0, "heat_pump_kw": 0.0, "wallbox_kw": 0.0, **sizes}

    def design(self, inp, locked=None):
        return Design(**self.sizes, probability={k: 0.5 for k in self.sizes}, explanation=["x"], rules_applied=[], flags=[])


@pytest.mark.parametrize("sizes, home, expected", [
    ({"battery_kwh": 5.0}, HomeInputs(), "R02"),  # battery without any PV
    ({"pv_kwp": 40.0}, HomeInputs(), "R03"),  # above the residential cap
    ({"pv_kwp": 2.0, "battery_kwh": 20.0}, HomeInputs(), "R04"),  # battery above 2 kWh per kWp
    ({"heat_pump_kw": 8.0}, HomeInputs(heating_type="heat_pump"), "R01"),  # new heat pump for a home that has one
    ({"wallbox_kw": 11.0}, HomeInputs(has_ev=False), "wallbox"),  # wallbox without an EV
    ({"wallbox_kw": 7.0}, HomeInputs(has_ev=True), "catalogue"),  # size not in the catalogue
    ({"pv_kwp": -1.0}, HomeInputs(), "is -1.0"),  # negative size
])
def test_the_checker_flags_broken_designs(sizes, home, expected):
    problems = fz.check(_Stub(**sizes), home, {})
    assert any(expected in p for p in problems), problems


def test_the_checker_flags_a_broken_lock_and_a_crash():
    assert any("lock on pv_kwp" in p for p in fz.check(_Stub(pv_kwp=5.0), HomeInputs(), {"pv_kwp": 9.0}))

    class _Crashes:
        catalog = {}

        def design(self, *a, **k):
            raise ValueError("boom")

    assert fz.check(_Crashes(), HomeInputs(), {})[0].startswith("crash: ValueError")
