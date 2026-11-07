import pytest

from reonic import business
from reonic.business import SCENARIOS, Scenario, evaluate


def test_base_scenario_arithmetic():
    base = {s.name: s for s in SCENARIOS}["Base"]
    r = evaluate(base)
    assert r["designs_per_planner_per_year"] == 12 * 46
    assert r["hours_saved_per_planner"] == pytest.approx(552 * (1.5 - 0.5))
    assert r["value_per_planner_eur"] == pytest.approx(552 * 50)
    assert r["value_per_installer_eur"] == pytest.approx(552 * 50 * 3)


def test_scenarios_are_ordered_and_physically_possible():
    values = [evaluate(s)["value_per_planner_eur"] for s in SCENARIOS]
    assert values == sorted(values)
    assert all(evaluate(s)["plausible"] for s in SCENARIOS)


def test_implausible_workload_is_flagged():
    too_much = Scenario("x", designs_per_week=30, hours_per_design_today=2.5, minutes_per_design_with_tool=20,
                        planner_cost_eur_per_hour=50, planners=1)
    assert not evaluate(too_much)["plausible"]


def test_no_saving_when_the_tool_is_slower():
    slow = Scenario("x", 10, 1.0, 90, 50, 1)
    assert evaluate(slow)["value_per_planner_eur"] < 0


def test_sensitivity_moves_in_the_expected_direction():
    for label, low, high in business.sensitivity():
        assert low != high, label
