import math

import pytest

from reonic import api, synth
from reonic.engine import Designer


@pytest.fixture(scope="module", autouse=True)
def designer():
    d = Designer.train(synth.generate(600, seed=2))
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(api, "designer", lambda: d)
        yield d


@pytest.mark.parametrize("body", [
    {"inputs": {"roof_area_m2": 40}},  # unknown field
    {"inputs": {"annual_consumption_kwh": -1}},
    {"inputs": {"annual_consumption_kwh": math.inf}},
    {"inputs": {"annual_consumption_kwh": "5000"}},
    {"inputs": {"has_ev": 1}},
    {"inputs": {"heating_type": "coal"}},
    {"inputs": {}, "locked": {"budget": 1}},
    {"inputs": {}, "locked": {"pv_kwp": True}},
])
def test_bad_input_is_rejected(body):
    with pytest.raises(ValueError):
        api.design(body)


def test_alternative_flips_a_component_and_replans_downstream():
    out = api.design({"inputs": {"annual_consumption_kwh": 6000, "existing_pv_kwp": 0, "has_ev": None}})
    assert out["economics"]["cost_eur"] > 0
    if out["values"]["pv_kwp"] > 0:
        alt = out["alternatives"]["pv_kwp"]
        assert alt["value"] == 0 and alt["values"]["battery_kwh"] == 0  # R02 downstream of the flip


def test_locked_component_has_no_alternative():
    out = api.design({"inputs": {"annual_consumption_kwh": 6000}, "locked": {"pv_kwp": 8}})
    assert out["values"]["pv_kwp"] == 8 and "pv_kwp" not in out["alternatives"]


def test_unknown_consumption_gives_no_savings_estimate():
    out = api.design({"inputs": {}})
    assert out["economics"]["savings_eur"] is None and out["economics"]["payback_years"] is None


def test_validate_needs_all_components():
    with pytest.raises(ValueError):
        api.validate({"inputs": {}, "values": {"pv_kwp": 8}})
    out = api.validate({"inputs": {"annual_consumption_kwh": 4000},
                        "values": {"pv_kwp": 8, "battery_kwh": 30, "heat_pump_kw": 0, "wallbox_kw": 11}})
    assert out["flags"]  # 30 kWh on 8 kWp breaks R04
