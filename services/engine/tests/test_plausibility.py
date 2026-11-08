"""Warnings for implausible inputs (engine/plausibility.py). SYNTHETIC data only."""
import pytest
from pydantic import ValidationError
from fastapi.testclient import TestClient

from engine.api.main import app, get_store
from engine.design import Store
from engine.models.schemas import HomeInputs
from engine.plausibility import input_flags
from engine.policy.designer import Designer
from policy_synth import generate


def codes(**kw):
    return {f.code for f in input_flags(HomeInputs.model_validate({"installerId": "x", **kw}))}


def test_plausible_home_gets_no_input_warning():
    assert codes(demandKwh=4200, ev={"has": True, "kmPerYear": 12000}, existingPv={"kwp": 6}, existingStorage={"kwh": 8},
                 building={"roofMaxModules": 30}) == set()


@pytest.mark.parametrize("kw,code", [
    ({"demandKwh": 60}, "INPUT_DEMAND_LOW"),
    ({"demandKwh": 400}, "INPUT_DEMAND_LOW"),
    ({"demandKwh": 80000}, "INPUT_DEMAND_HIGH"),
    ({"ev": {"has": True, "kmPerYear": 0}}, "INPUT_EV_KM"),
    ({"ev": {"has": True, "kmPerYear": 500000}}, "INPUT_EV_KM"),
    ({"existingPv": {"kwp": 80}}, "INPUT_EXISTING_PV"),
    ({"existingPv": {"kwp": 12}, "building": {"roofMaxModules": 10}}, "INPUT_EXISTING_PV_ROOF"),
    ({"existingStorage": {"kwh": 400}}, "INPUT_EXISTING_STORAGE"),
])
def test_implausible_input_is_flagged(kw, code):
    assert code in codes(**kw)


def test_boundaries_and_unknowns_do_not_warn():
    assert codes(demandKwh=500) == set() and codes(demandKwh=50000) == set()
    assert codes(demandKwh=0) == set()                       # 0 means unknown here; UNUSUAL_OMISSION already covers it
    assert codes(ev={"has": False, "kmPerYear": 0}) == set()  # no car, so the distance is irrelevant
    assert codes(ev={"has": True}) == set()                   # distance unknown
    with pytest.raises(ValidationError):  # a negative cap is the schema's problem: it is rejected before any warning
        codes(existingPv={"kwp": 5}, building={"roofMaxModules": -1})


@pytest.fixture()
def client(processed, tmp_path):
    designer = Designer.train(generate(1200, seed=1), config={"mode": "hybrid", "pvGate": 0.5}, synthetic=True)
    path = tmp_path / "designer.joblib"
    designer.save(path)
    store = Store(processed, model_path=path)
    app.dependency_overrides[get_store] = lambda: store
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_design_endpoint_returns_the_warning_and_the_numbers_are_unchanged(client):
    base = {"installerId": "synthB", "demandKwh": 6200}
    flagged = {"installerId": "synthB", "demandKwh": 6200, "existingStorage": {"kwh": 400}}
    a, b = client.post("/design", json={"inputs": base}), client.post("/design", json={"inputs": flagged})
    assert a.status_code == b.status_code == 200
    assert "INPUT_EXISTING_STORAGE" in {f["code"] for f in b.json()["flags"]}
    assert not any(f["code"].startswith("INPUT_") for f in a.json()["flags"])
    assert client.post("/design", json={"inputs": {"installerId": "synthB", "demandKwh": 60}}).json()["flags"] is not None
    low = client.post("/design", json={"inputs": {"installerId": "synthB", "demandKwh": 60}}).json()
    assert "INPUT_DEMAND_LOW" in {f["code"] for f in low["flags"]}


def test_default_demand_is_a_warning_not_a_note():
    from engine.plausibility import default_demand_flag
    f = default_demand_flag(HomeInputs.model_validate({"installerId": "x"}))  # demand left at the 4,500 default
    assert f is not None and f.code == "DEMAND_DEFAULT_LIKE" and f.severity == "warn"
    assert default_demand_flag(HomeInputs.model_validate({"installerId": "x", "demandKwh": 4501})) is None
    entered = HomeInputs.model_validate({"installerId": "x", "demandKwh": 4500, "provenance": {"demandKwh": {"source": "entered"}}})
    assert default_demand_flag(entered) is None  # a bill that really says 4,500 is not a default
