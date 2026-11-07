"""Tests for the offline hourly simulator (engine.sim)."""
import socket
import time

import numpy as np
import pytest

from engine.sim import recommend_battery, simulate, sweep_battery, sweep_pv
from engine.sim import ev, heatpump, profiles

HOME = {"demandKwh": 4500}
SIZES12 = [0, 1, 2, 3, 4, 5, 6, 8, 10, 12, 15, 20]


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    def boom(*a, **k):
        raise AssertionError("network access in offline simulator")
    monkeypatch.setattr(socket.socket, "connect", boom)
    monkeypatch.setattr(socket, "getaddrinfo", boom)


def _balance(r):
    a = r["audit"]
    lhs = a["pv"] + a["import"]
    rhs = a["load"] + a["export"] + a["curtailed"] + a["charge_ac"] - a["discharge_ac"] + a["standby_kwh"]
    return abs(lhs - rhs) / lhs


@pytest.mark.parametrize("home,system,opts", [
    (HOME, {"pv": {"kwp": 10}, "battery": {"kwh": 8}}, {"feedInCap": False}),
    (HOME, {"pv": {"kwp": 10}, "battery": {"kwh": 8}}, {}),
    ({"demandKwh": 3500, "ev": {"has": True, "kmPerYear": 15000, "smartCharging": True},
      "heating": {"type": "Gas", "fuelKwh": 20000}},
     {"pv": {"kwp": 12, "orientation": "EW"}, "battery": {"kwh": 10}, "wallbox": {"kw": 11}, "heatPump": {"kw": 8}}, {}),
])
def test_energy_conservation_and_soc_bounds(home, system, opts):
    r = simulate(home, system, opts)
    assert _balance(r) < 0.005
    a = r["audit"]
    assert a["soc_hourly_min"] >= -1e-9
    assert a["soc_hourly_max"] <= a["soc_max_usable"] + 1e-9


def test_autarky_monotone_in_battery_size():
    rows = sweep_battery(HOME, {"pv": {"kwp": 8}}, SIZES12)
    aut = [x["autarky"] for x in rows]
    assert all(b >= a - 1e-9 for a, b in zip(aut, aut[1:]))
    sc = [x["selfConsumption"] for x in rows]
    assert all(b >= a - 1e-9 for a, b in zip(sc, sc[1:]))


def test_zero_pv_zero_self_consumption():
    r = simulate(HOME, {"pv": {"kwp": 0}, "battery": {"kwh": 5}})
    assert r["selfConsumption"] == 0 and r["pvYieldKwh"] == 0
    assert r["feedInKwh"] == 0


def test_ev_and_hp_increase_load():
    base = simulate(HOME, {"pv": {"kwp": 8}})
    ev_r = simulate({**HOME, "ev": {"has": True, "kmPerYear": 15000}}, {"pv": {"kwp": 8}, "wallbox": {"kw": 11}})
    hp_r = simulate({**HOME, "heating": {"type": "Gas", "fuelKwh": 20000}}, {"pv": {"kwp": 8}, "heatPump": {"kw": 8}})
    assert ev_r["loadKwh"] > base["loadKwh"] + 1500
    assert hp_r["loadKwh"] > base["loadKwh"] + 3000


def test_ev_modes_energy_and_deadline():
    pv = profiles.pv_profile(8)
    other = profiles.load_profile(4500)
    for mode in ev.MODES:
        e = ev.ev_load(15000, mode, pv, other)
        assert e.sum() == pytest.approx(ev.ev_annual_kwh(15000), rel=1e-6)
        assert e.max() <= 11 + 1e-9
    assert ev.ev_load(15000, "solar", pv, other)[0:0].size == 0
    # solar charging overlaps more with PV than dumb evening charging
    solar = ev.ev_load(15000, "solar", pv, other)
    eve = ev.ev_load(15000, "evening", pv, other)
    assert (np.minimum(solar, pv).sum()) > (np.minimum(eve, pv).sum())


def test_heatpump_scop_and_sizing():
    t = profiles.temperature()
    h = heatpump.hp_electric(t, 18000)
    assert h["scop"] == pytest.approx(3.4, abs=0.01)
    assert h["heat"].sum() == pytest.approx(18000)
    assert heatpump.heat_demand_kwh("oil", litres=2000) == pytest.approx(17000)
    assert heatpump.snap_to_catalog(heatpump.heat_load_kw(18000), [6, 8, 10, 12]) == 10


def test_profiles_sum_and_families():
    for fam in ["H0", "FamilyOfFour", "HomeOfficeOnePerson", "SeniorCouple"]:
        assert profiles.load_profile(4000, fam).sum() == pytest.approx(4000)
    cal = profiles.calendar()
    mid = (cal["hod"] >= 10) & (cal["hod"] < 15)
    assert profiles.load_profile(4000, "HomeOfficeOnePerson")[mid].sum() > profiles.load_profile(4000)[mid].sum()
    ew = profiles.pv_unit_profile("EW").sum()
    s = profiles.pv_unit_profile("S").sum()
    assert 0.7 < ew / s < 0.95


def test_sweep_12_sizes_fast():
    system = {"pv": {"kwp": 10}}
    sweep_battery(HOME, system, SIZES12)  # warm caches
    best = min(_t(lambda: sweep_battery(HOME, system, SIZES12)) for _ in range(3))
    assert best < 0.100, f"{best*1000:.0f} ms"


def _t(fn):
    t = time.perf_counter()
    fn()
    return time.perf_counter() - t


def test_recommend_and_sweep_pv():
    rec = recommend_battery(HOME, {"pv": {"kwp": 10}}, SIZES12)
    assert rec["economic"]["batteryKwh"] <= rec["maxAutarky"]["batteryKwh"] or rec["economic"]["batteryKwh"] == 0
    rows = sweep_pv(HOME, {"pv": {"kwp": 5}, "battery": {"kwh": 5}}, [3, 5, 8, 10])
    assert [round(r["pvKwp"]) for r in rows] == [3, 5, 8, 10]
    assert rows[-1]["pvYieldKwh"] > rows[0]["pvYieldKwh"]


def test_existing_system_incremental():
    home = {**HOME, "existingPv": {"kwp": 6, "builtYear": 2015, "feedInEurKwh": 0.12}}
    r = simulate(home, {"battery": {"kwh": 8}})
    assert r["baseline"]["pvYieldKwh"] > 5000
    assert r["pvYieldKwh"] == pytest.approx(r["baseline"]["pvYieldKwh"])
    assert r["incremental"]["autarkyPts"] > 5
    assert _balance(r) < 0.005


def test_feed_in_cap_curtails():
    r = simulate(HOME, {"pv": {"kwp": 12, "orientation": "S", "tiltDeg": 35}}, {"feedInCap": True})
    r0 = simulate(HOME, {"pv": {"kwp": 12}}, {"feedInCap": False})
    assert r["curtailedKwh"] > 0 and r0["curtailedKwh"] == 0
    assert _balance(r) < 0.005
