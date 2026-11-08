"""German public-marginal scenario, not an adopter joint distribution.

All source facts, mappings and analyst assumptions are in german_priors.json.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

PRIORS_PATH = Path(__file__).resolve().parents[3] / "data/external/german_priors.json"


def sample_public_homes(n, installers, seed=110701):
    from engine.models.schemas import HomeInputs
    priors = json.loads(PRIORS_PATH.read_text(encoding="utf-8"))
    rng = np.random.Generator(np.random.PCG64(seed))
    people_weights = np.asarray(priors["household_size"]["percent_1_2_3_4_5plus"]) / 100
    heating_weights = np.asarray(priors["heating"]["percent_gas_oil_wood_ambientgroup_other"]) / 100
    heating_types = ["Gas", "Oil", "OtherRenewable", "Heatpump", "Unknown"]
    anchors = priors["household_demand_without_electric_dhw_kwh"]
    homes, counts = [], {"persons_topcoded_5": {str(i): 0 for i in range(1, 6)},
                         "heating_mapping": {k: 0 for k in heating_types}, "plug_in_vehicle_yes": 0}
    for i in range(n):
        people = int(rng.choice(np.arange(1, 6), p=people_weights))
        heating = heating_types[int(rng.choice(np.arange(5), p=heating_weights))]
        ev = bool(rng.random() < priors["plug_in_vehicle"]["EVS_2023_household_percent"] / 100)
        demand = round(anchors[people - 1] * rng.uniform(.6, 1.6))
        home = HomeInputs.model_validate({"installerId": installers[i % len(installers)],
            "persons": people, "demandKwh": demand,
            "ev": {"has": ev, "kmPerYear": int(rng.uniform(5000, 25000)) if ev else None},
            "heating": {"type": heating, "heatDemandKwh": int(rng.uniform(8000, 30000)) if heating != "Unknown" else None},
            "priceEurKwh": .32, "provenance": {"demandKwh": {"source": "entered", "confidence": 1}}})
        homes.append(home)
        counts["persons_topcoded_5"][str(people)] += 1
        counts["heating_mapping"][heating] += 1
        counts["plug_in_vehicle_yes"] += int(ev)
    return homes, {"mode": "independent_public_marginal_scenario", "realized_counts": counts,
                   "source_manifest": "data/external/german_priors.json",
                   "interpretation": priors["interpretation"], "assumptions": priors["analyst_assumptions"]}
