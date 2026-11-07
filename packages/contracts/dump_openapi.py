"""Dump the engine's OpenAPI schema and a /design example fixture (synthetic home, no raw data).

    services/engine/.venv/Scripts/python packages/contracts/dump_openapi.py
"""
import json
from pathlib import Path

from fastapi.testclient import TestClient

from engine.api.main import app

HERE = Path(__file__).parent
SYNTHETIC_HOME = {
    "installerId": "2a8ba8e2", "demandKwh": 5200, "priceEurKwh": 0.34, "priceEscalation": 0.03,
    "ev": {"has": True, "kmPerYear": 14000},
    "heating": {"type": "Gas", "heatDemandKwh": 18000},
    "building": {"roofType": "concrete_tile"},
}


def main() -> None:
    (HERE / "openapi.json").write_text(json.dumps(app.openapi(), indent=2) + "\n", encoding="utf-8")
    (HERE / "fixtures").mkdir(exist_ok=True)
    body = {"inputs": SYNTHETIC_HOME}
    res = TestClient(app).post("/design", json=body).json()
    res["latencyMs"] = 1.0  # stable fixture
    (HERE / "fixtures" / "design-request.example.json").write_text(json.dumps(body, indent=2) + "\n", encoding="utf-8")
    (HERE / "fixtures" / "design-response.example.json").write_text(json.dumps(res, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
