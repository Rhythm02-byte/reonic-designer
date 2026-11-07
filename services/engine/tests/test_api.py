import pytest
from fastapi.testclient import TestClient

from engine.api.main import app, get_store
from engine.design import Store

HOME = {"installerId": "inst1", "demandKwh": 6200, "ev": {"has": True, "kmPerYear": 12000},
        "heating": {"type": "Gas", "heatDemandKwh": 18000}}


@pytest.fixture()
def client(processed):
    app.dependency_overrides[get_store] = lambda: Store(processed)
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200 and r.json()["engineVersion"] == "baseline-0"


def test_design_rules(client):
    r = client.post("/design", json={"inputs": HOME})
    assert r.status_code == 200
    d = r.json()
    assert d["engineVersion"] == "baseline-0"
    assert d["proposal"]["pv"]["kwp"] > 0
    assert d["proposal"]["wallbox"] is not None                  # EV -> wallbox
    assert d["proposal"]["heatPump"]["kw"] in (5, 7, 10, 12)     # gas heating -> snapped HP size
    assert {"p10", "p50", "p90"} <= set(d["confidence"]["pv"])
    assert d["reasons"] and d["metrics"]["proposal"]["pvYieldKwh"] > 0


def test_no_hp_without_fossil_heating_and_no_wallbox_without_ev(client):
    d = client.post("/design", json={"inputs": {"installerId": "inst1", "demandKwh": 4000}}).json()
    assert d["proposal"]["heatPump"] is None and d["proposal"]["wallbox"] is None


def test_lock_keeps_current_component(client):
    current = {"pv": {"modules": 40, "moduleWp": 450, "kwp": 18.0}}
    d = client.post("/design", json={"inputs": HOME, "locks": ["pv"], "current": current}).json()
    assert d["proposal"]["pv"]["kwp"] == 18.0 and d["proposal"]["locks"] == ["pv"]


def test_unknown_installer_falls_back(client):
    d = client.post("/design", json={"inputs": {"installerId": "nope"}}).json()
    assert any(f["code"] == "INSTALLER_UNKNOWN" for f in d["flags"])
