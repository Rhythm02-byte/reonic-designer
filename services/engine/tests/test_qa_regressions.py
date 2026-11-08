"""QA bug-hunt regressions (Sun 8 Nov). SYNTHETIC inputs only; each test names the bug it pins."""
import math

import pytest
from pydantic import ValidationError

from engine import sim
from engine.design import sim_home, system_from_values
from engine.models.schemas import HomeInputs
from engine.policy import rules
from test_hybrid_api import client, designer, df  # noqa: F401 - shared synthetic fixtures

REQUIRED = ("gridImportKwh", "feedInKwh", "pvYieldKwh", "autarky")


# -- bug 1: a negative roof cap produced a negative PV (and, through R04, a negative battery) -----------------------
def test_negative_roof_modules_is_rejected_by_the_schema():
    with pytest.raises(ValidationError):
        HomeInputs.model_validate({"installerId": "x", "building": {"roofMaxModules": -1}})
    assert HomeInputs.model_validate({"installerId": "x", "building": {"roofMaxModules": 0}}).building.roof_max_modules == 0


def test_design_endpoint_answers_422_for_a_negative_roof(client):
    r = client.post("/design", json={"inputs": {"installerId": "synthB", "building": {"roofMaxModules": -1}}})
    assert r.status_code == 422


@pytest.mark.parametrize("roof_kwp", [-0.45, -10.0])
def test_rules_never_emit_negative_pv_or_battery_even_past_the_schema(roof_kwp):
    ctx = {"roof_max_kwp": roof_kwp, "roof_max_modules": -1}
    pv, _, _ = rules.apply_one("pv_kwp", 8.0, {}, ctx, {})
    assert pv >= 0
    bat, _, _ = rules.apply_one("battery_kwh", 10.0, {"pv_kwp": pv}, ctx, {"battery_kwh": [5.0, 10.0]})
    assert bat >= 0


def test_policy_design_with_negative_roof_values_is_non_negative(designer):  # noqa: F811
    i = HomeInputs.model_construct(**{**HomeInputs.model_validate({"installerId": "synthB", "demandKwh": 6000}).__dict__})
    i.building = HomeInputs.model_validate({"installerId": "x", "building": {"roofMaxModules": 0}}).building
    i.building.roof_max_modules = -1  # bypasses validation, like a caller of the Python API
    res = designer.design(i, {}, 450.0)
    assert all(v >= 0 for v in res.values.values() if not math.isnan(v)), res.values


# -- bug 2: no new PV -> autarky -2e-16 -> recommend_battery's max-autarky min() saw an empty list -> no metrics ----
def test_recommend_battery_without_pv_does_not_raise():
    home = sim_home(HomeInputs.model_validate({"installerId": "x", "demandKwh": 60000, "loadProfile": "G0"}))
    rec = sim.recommend_battery(home, {}, [0, 5, 10])
    assert rec["maxAutarky"]["batteryKwh"] == 0 and rec["economic"]["batteryKwh"] == 0
    assert all(0.0 <= r["autarky"] <= 1.0 and 0.0 <= r["selfConsumption"] <= 1.0 for r in rec["rows"])


@pytest.mark.parametrize("home", [
    {"installerId": "synthB", "demandKwh": 60000, "loadProfile": "G0", "heating": {"type": "Gas"}, "building": {"roofMaxModules": 0}},
    {"installerId": "synthB", "demandKwh": 4000, "building": {"roofMaxModules": 0}},
    {"installerId": "synthA", "demandKwh": 4000, "existingPv": {"kwp": 30}, "building": {"roofMaxModules": 0}},
    {"installerId": "synthB", "demandKwh": 0},
    {"installerId": "nobody", "demandKwh": 200000},
])
def test_design_always_returns_the_core_simulation_metrics(client, home):
    r = client.post("/design", json={"inputs": home})
    assert r.status_code == 200, r.text
    m = r.json()["metrics"]["proposal"]
    assert all(m.get(k) is not None for k in REQUIRED), m


# -- bug 3: kWp was rounded to 2 dp, so modules x moduleWp != kWp for e.g. 415 W modules --------------------------
@pytest.mark.parametrize("wp", [415.0, 435.0, 450.0, 375.5])
@pytest.mark.parametrize("kwp", [3.1, 7.9, 12.34])
def test_pv_kwp_is_exactly_modules_times_module_wp(wp, kwp):
    pv = system_from_values({"pv_kwp": kwp}, wp, "p").pv
    assert pv.kwp == pytest.approx(pv.modules * pv.module_wp / 1000, abs=1e-9)
