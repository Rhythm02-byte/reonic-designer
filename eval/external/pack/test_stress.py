import importlib.util
from pathlib import Path

import numpy as np

spec = importlib.util.spec_from_file_location("external_stress", Path(__file__).parents[1] / "stress.py")
stress = importlib.util.module_from_spec(spec)
spec.loader.exec_module(stress)


def test_counts_quotas_replay_and_no_design_labels():
    cases = stress.generate_cases()
    assert len(cases) == 720
    assert stress.digest(cases) == stress.digest(stress.generate_cases())
    assert stress.digest(cases) != stress.digest(stress.generate_cases(110702))
    assert stress.coverage(cases)["pool_requests"] == {"ordinary": 240, "observation": 120, "boundary": 120, "metamorphic": 240}
    assert all("expected_design" not in c and "targets" not in c for c in cases)
    assert len({c["case_id"] for c in cases}) == 720
    assert all(c["request_sha256"] == stress.digest(c["request"]) for c in cases)
    assert all(v["present"] == v["required_cartesian"] for v in stress.coverage(cases)["pairwise"].values())


def test_pair_members_are_grouped_and_frozen_before_run():
    cases = stress.generate_cases()
    pairs = [c for c in cases if c["pair"]]
    assert len({c["base_id"] for c in pairs}) == 120
    assert all(c["base_id"] == c["pair"]["id"] for c in pairs)


def test_independent_check_detects_physical_and_lock_errors():
    request = stress.DesignRequest.model_validate({"inputs": {"installerId": "synthetic", "heating": {"type": "Heatpump"}, "building": {"roofMaxModules": 1}}})
    values = {"pv_kwp": 4., "battery_kwh": 10., "heat_pump_kw": 5., "wallbox_kw": 0.}
    checks = stress.structural_checks(request.inputs, values, {}, {}, set())
    assert not checks["roof_cap"]
    assert not checks["existing_hp_gate"]
    assert checks["finite_nonnegative"]
    values["pv_kwp"] = np.nan
    assert not stress.structural_checks(request.inputs, values, {}, {}, set())["finite_nonnegative"]


def test_each_lock_has_its_own_verdict():
    request = stress.DesignRequest.model_validate({"inputs": {"installerId": "synthetic"}})
    values = {"pv_kwp": 8., "battery_kwh": 5., "heat_pump_kw": 0., "wallbox_kw": 0.}
    checks = stress.structural_checks(request.inputs, values, {"pv_kwp": 9., "battery_kwh": 5.}, {}, set())
    assert not checks["locks_preserved_pv_kwp"]
    assert checks["locks_preserved_battery_kwh"]


def test_toy_accounting_uses_hourly_ledger_and_closed_form_no_battery():
    report = stress.toy_physics()
    assert report["scenarios"] == 15
    assert not report["failures"]
    assert report["counts"]["soc_ledger_pass"] == 15


def test_network_is_blocked_and_restored():
    original = stress.socket.socket.connect
    with stress.no_network() as attempts:
        try:
            stress.socket.create_connection(("example.invalid", 80))
        except RuntimeError:
            pass
        assert len(attempts) == 1
    assert stress.socket.socket.connect is original


def test_missing_metrics_are_failures_not_excluded_bounds():
    from types import SimpleNamespace as NS
    case = stress.generate_cases()[0]
    response = NS(proposal=NS(id="proposal", pv=None, battery=None, heat_pump=None, wallbox=None),
        alternatives=[], metrics={}, flags=[])
    result = stress.check_full_responses([case], NS(installers=("synthetic",)), lambda req: response)
    assert result["counts"]["missing_grid_import_kwh"] == 1
    assert result["counts"]["missing_autarky"] == 1
    assert result["counts"]["required_metric_present_fail"] == 4
