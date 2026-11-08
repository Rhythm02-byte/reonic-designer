"""Deterministic intake-only DEV stress suite. No expert labels or population claims.

720 requests = 240 ordinary + 120 observation + 120 boundary + 120 pairs.
The full contract/HTTP/deployment is NOT certified by the policy adapter.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from contextlib import contextmanager
from copy import deepcopy
from dataclasses import asdict
import hashlib
import itertools
import json
import os
from pathlib import Path
import platform
import socket
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "services/engine"))
os.environ["OFFLINE"] = "1"

import numpy as np
from pydantic import ValidationError
from threadpoolctl import threadpool_limits
from engine.models.schemas import DesignRequest
from engine.policy.designer import Designer
from engine.policy import physics
from engine.sim.battery import BatteryParams, flows

SPEC = "spec-v1-dev-20261108"
AS_OF = "2026-11-07"
SEED = 110701
HEATING = ("Gas", "Oil", "Heatpump", "OtherRenewable", "OtherNonRenewable", "Unknown")
TARGETS = ("pv_kwp", "battery_kwh", "heat_pump_kw", "wallbox_kw")
LOCK_TARGET = {"pv": "pv_kwp", "battery": "battery_kwh", "heatPump": "heat_pump_kw", "wallbox": "wallbox_kw"}
ANCHORS = ((1800, 2700, 3500, 3800, 4500), (2100, 3200, 4100, 4700, 6000))
REVIEW_CODES = {
    "placeholder": {"DEMAND_DEFAULT_LIKE"}, "default_minimal": {"DEMAND_DEFAULT_LIKE"},
    "untrusted_pv": {"EXISTING_PV_AMBIGUOUS"}, "unseen_installer": {"INSTALLER_UNKNOWN"},
    "locked_roof_conflict": {"R07", "R03"}, "locked_hp_conflict": {"R01"},
    # Empty mappings are explicit instrumentation/semantic gaps, never arbitrary prose matching.
    "extreme": set(), "domain": set(), "contradiction": set(), "missing": set(),
    "cost_only": set(), "storage_only": set(), "future_build": set(),
}


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def rng_for(family, base_id, seed=SEED):
    sub_seed = int.from_bytes(hashlib.sha256(f"{SPEC}|{seed}|{family}|{base_id}".encode()).digest()[:8], "big")
    return np.random.Generator(np.random.PCG64(sub_seed))


def set_path(obj, path, value, remove=False):
    keys = path.split(".")
    cur = obj
    for key in keys[:-1]:
        cur = cur.setdefault(key, {})
    if remove:
        cur.pop(keys[-1], None)
    else:
        cur[keys[-1]] = value


def ordinary_inputs(index, base_id, seed=SEED):
    """Balanced factors, source-anchor demand times analyst coverage; never output-conditioned."""
    r = rng_for("ordinary", base_id, seed)
    persons, dhw = index % 5 + 1, (index // 5) % 2
    heating, ev_state = HEATING[index % 6], (index // 6) % 3
    assets, roof_band = (index // 18) % 4, index % 5
    trusted = bool((index // 4) % 2)
    sqm = round(r.uniform(70, 250), 1)
    band = ((30, 70), (70, 140), (140, 250))[(index // 7) % 3]
    useful_heat = round(sqm * r.uniform(*band))
    h = {"type": heating, "heatDemandKwh": useful_heat}
    latent = {"demand_boundary": "appliance_dhw_excluding_ev_hp", "electric_dhw": bool(dhw),
        "renovated": bool(index % 2), "asset_category": assets, "roof_band": roof_band,
        "ev_state": ("absent", "current", "planned")[ev_state], "heat_intensity_band": list(band)}
    if heating in ("Gas", "Oil", "OtherNonRenewable"):
        efficiency = float(r.uniform(.65, .95))
        h.update(fuelKwh=round(useful_heat / efficiency), plannedSwitch=bool(index % 2))
        latent["boiler_efficiency"] = efficiency
    if heating == "Heatpump":
        spf = float(r.uniform(2, 5))
        h["hpElecKwh"] = round(useful_heat / spf)
        latent["seasonal_performance"] = spf
    ev = {"has": ev_state == 1, "smartCharging": bool(index % 2)}
    if ev_state:
        ev.update(kmPerYear=round(r.uniform(0, 30000)))
        latent.update(ev_efficiency=float(r.uniform(.12, .30)), ev_home_share=float(r.uniform(0, 1)))
        if ev_state == 2:
            ev["plannedYear"] = 2027
    cap = (None, 0, int(r.integers(4, 13)), int(r.integers(13, 31)), int(r.integers(31, 61)))[roof_band]
    building = {"sqm": sqm, "builtYear": (1930, 1975, 1995, 2015, 2025)[index % 5],
        "roofType": ("clay_tile", "flat", "flat_ew", "metal")[index % 4],
        "orientation": ("south", "east-west")[index % 2]}
    if cap is not None:
        building["roofMaxModules"] = cap
    demand = round(ANCHORS[dhw][persons - 1] * r.uniform(.6, 1.6))
    price_range = ((.15, .25), (.25, .40), (.40, .60))[(index // 3) % 3]
    inp = {"installerId": ("known_0", "known_1", "unseen_external")[(index // 6 + index // 18) % 3],
        "persons": persons, "demandKwh": demand, "priceEurKwh": round(r.uniform(*price_range), 4),
        "priceEscalation": (0, .03, .08)[index % 3], "flexTariff": bool(index % 2),
        "loadProfile": ("H0", "FamilyOfFour", "HomeOffice", "Senior")[index % 4],
        "heating": h, "ev": ev, "building": building,
        "location": dict(zip(("lat", "lon"), ((48.137, 11.576), (52.520, 13.405), (53.551, 9.994))[index % 3])),
        "provenance": {"demandKwh": {"source": "entered", "confidence": 1}}}
    if assets in (1, 2):
        inp["existingPv"] = {"kwp": round(r.uniform(2, 25), 1), "trusted": trusted}
    if assets in (2, 3):
        inp["existingStorage"] = {"kwh": round(r.uniform(2, 25), 1), "trusted": trusted}
    if index % 4 == 0:
        inp["existingWallbox"] = {"kw": (11, 22)[index % 2]}
    return inp, latent


def case_record(case_id, pool, inp, latent=None, action="accept", reason=None, pair=None, current=None, locks=None):
    request = {"inputs": inp, "locks": locks or []}
    if current is not None:
        request["current"] = current
    return {"spec_version": SPEC, "case_id": case_id, "base_id": pair["id"] if pair else case_id,
        "split": "dev", "pool": pool, "request": request, "latent": latent or {},
        "expectation": {"action": action, "reason": reason}, "pair": pair,
        "evidence_ids": ["S1", "A-coverage"], "request_sha256": digest(request)}


def generate_cases(seed=SEED):
    cases = []
    for i in range(240):
        cid = f"dev-ordinary-{i:04d}"
        inp, latent = ordinary_inputs(i, cid, seed)
        cases.append(case_record(cid, "ordinary", inp, latent))
    for i in range(120):
        cid = f"dev-observation-{i:04d}"
        inp, latent = ordinary_inputs(i, cid, seed)
        subtype = i // 30
        reason = "missing"
        if subtype == 0:
            removed = ("persons", "building", "heating.heatDemandKwh", "location", "ev")[i % 5]
            set_path(inp, removed, None, remove=True)
            latent["observed_mask"] = {removed: False}
        elif subtype == 1:
            inp["ev"] = {"has": True}
            inp["heating"] = {"type": "Gas"}
            inp["existingPv"] = {"kwp": 6, "trusted": False}
            latent["observed_mask"] = {"ev.kmPerYear": False, "heating.fuelKwh": False}
        elif subtype == 2:
            inp["demandKwh"] = 4500
            source = ("entered", "installer_default", "national_default")[i % 3]
            inp["provenance"] = {"demandKwh": {"source": source, "confidence": 1}}
            reason = "placeholder" if source != "entered" else None
        else:
            inp = {"installerId": "known_0"}
            reason = "default_minimal"
        latent["observation_family"] = ("independent_mask", "conditional_mask", "placeholder_provenance", "all_defaults")[subtype]
        cases.append(case_record(cid, "observation", inp, latent, "review" if reason else "accept", reason))
    malformed = [
        ("installerId", None, "remove"), ("demandKwh", None, "set"), ("demandKwh", "many", "set"),
        ("ev.has", None, "set"), ("heating.type", "Nuclear", "set"), ("building.roofType", "banana", "set"),
        ("provenance.demandKwh.confidence", 1.1, "set"), ("provenance.demandKwh.confidence", -.1, "set"),
        ("persons", [], "set"), ("ev", [], "set"), ("building.roofMaxModules", "many", "set"),
        ("priceEurKwh", None, "set"), ("priceEscalation", "many", "set"),
        ("location.lat", {}, "set"), ("existingPv.kwp", "many", "set"), ("existingStorage.kwh", None, "set"),
        ("heating.hpElecKwh", "many", "set"), ("heating.fuelKwh", "many", "set"),
        ("existingWallbox.kw", [], "set"), ("building", 17, "set")]
    extremes = [
        ("demandKwh", v) for v in (0, .001, 200000, 4500000, -1)] + [
        ("ev.kmPerYear", v) for v in (-1, 0, .001, 100000)] + [
        ("building.roofMaxModules", v) for v in (-1, 0, 1, 100000)] + [
        ("existingPv.kwp", v) for v in (-1, .005, 5000)] + [
        ("existingStorage.kwh", v) for v in (-1, .005, 5000)] + [
        ("heating.heatDemandKwh", v) for v in (-1, 0, .001, 10000000)] + [
        ("heating.hpElecKwh", v) for v in (-1, .001, 4000000)] + [
        ("priceEurKwh", v) for v in (-.1, 0, .001, 32)] + [
        ("priceEscalation", v) for v in (-2, 0, 10)] + [
        ("location.lat", v) for v in (-100, 100)] + [
        ("building.builtYear", 2099), ("persons", -1), ("heating.fuelKwh", -1),
        ("basePriceMonth", -1), ("existingWallbox.kw", -11)]
    assert len(extremes) == 40
    for i in range(120):
        cid = f"dev-boundary-{i:04d}"
        inp, latent = ordinary_inputs(i, cid, seed)
        family, action, reason, locks, current = i // 40, "review", "extreme", [], None
        if family == 0:
            path, value, operation = malformed[i % len(malformed)]
            set_path(inp, path, value, remove=operation == "remove")
            action, reason = "reject", "schema"
        elif family == 1:
            path, value = extremes[i - 40]
            set_path(inp, path, value)
            latent["corruption"] = {"field": path, "value": value, "kind": "finite_extreme_or_unit_probe"}
        else:
            subtype = i % 10
            reason = "contradiction"
            if subtype == 0:
                inp["ev"] = {"has": False, "kmPerYear": 20000}
            elif subtype == 1:
                inp["heating"] = {"type": "Heatpump", "fuelKwh": 20000, "hpElecKwh": 0, "heatDemandKwh": 0}
            elif subtype == 2:
                inp["heating"] = {"type": "Gas", "fuelKwh": 1000, "heatDemandKwh": 20000}
            elif subtype == 3:
                inp["existingPv"] = {"kwp": 5000, "trusted": False}
                reason = "untrusted_pv"
            elif subtype == 4:
                inp.pop("existingPv", None)
                inp["existingStorage"] = {"kwh": 10, "trusted": False}
                reason = "storage_only"
            elif subtype == 5:
                inp["installerId"] = "unseen_external"
                reason = "unseen_installer"
            elif subtype == 6:
                inp["heating"] = {"type": "Gas", "costEurYear": 1200}
                reason = "cost_only"
            elif subtype == 7:
                inp["building"]["roofMaxModules"] = 4
                current = {"pv": {"modules": 200, "moduleWp": 450, "kwp": 90}}
                locks, reason = ["pv"], "locked_roof_conflict"
            elif subtype == 8:
                inp["heating"] = {"type": "Heatpump", "hpElecKwh": 4000}
                current, locks, reason = {"heatPump": {"kw": 10}}, ["heatPump"], "locked_hp_conflict"
            else:
                locks, action, reason = ["unknownComponent"], "reject", "schema"
        latent["boundary_family"] = ("schema", "finite_extreme", "contradiction")[family]
        cases.append(case_record(cid, "boundary", inp, latent, action, reason, current=current, locks=locks))
    pair_types = ("roof_shrink", "demand_up", "ev_present", "lock_preserve", "key_order", "ignored_extra")
    for i in range(120):
        pair_id, kind = f"dev-pair-{i:04d}", pair_types[i % len(pair_types)]
        inp, latent = ordinary_inputs(i + 240, pair_id, seed)
        inp["installerId"] = "known_0"
        inp["building"]["roofMaxModules"] = 40
        inp["heating"] = {"type": "Gas", "heatDemandKwh": 18000}
        inp["ev"] = {"has": False}
        inp.pop("existingWallbox", None)
        changed, other = [], deepcopy(inp)
        current, locks = None, []
        if kind == "roof_shrink":
            other["building"]["roofMaxModules"] = 4
            changed = ["building.roofMaxModules"]
        elif kind == "demand_up":
            other["demandKwh"] = inp["demandKwh"] + 3000
            changed = ["demandKwh"]
        elif kind == "ev_present":
            other["ev"] = {"has": True, "kmPerYear": 12000}
            changed = ["ev"]
        elif kind == "lock_preserve":
            current = {"pv": {"modules": 20, "moduleWp": 450, "kwp": 9}, "battery": {"kwh": 5}}
            locks = ["pv", "battery", "heatPump", "wallbox"]
            other["demandKwh"] = inp["demandKwh"] + 3000
            changed = ["demandKwh"]
        elif kind == "key_order":
            other = dict(reversed(list(inp.items())))
        else:
            other["unusedSyntheticProbe"] = "ignored_by_contract"
            changed = ["unusedSyntheticProbe"]
        for role, observed in (("a", inp), ("b", other)):
            pair = {"id": pair_id, "kind": kind, "role": role, "changed_paths": changed,
                "preconditions": "same installer/catalog/config; no fitting; explicit roof; fixed non-HP heating"}
            cases.append(case_record(f"{pair_id}-{role}", "metamorphic", observed, latent,
                current=current, locks=locks, pair=pair))
    assert len(cases) == 720
    return cases


@contextmanager
def no_network():
    original_connect, original_create = socket.socket.connect, socket.create_connection
    attempts = []
    def deny(*args, **kwargs):
        attempts.append("outbound_attempt")
        raise RuntimeError("Network disabled by external stress harness")
    socket.socket.connect = deny
    socket.create_connection = deny
    try:
        yield attempts
    finally:
        socket.socket.connect, socket.create_connection = original_connect, original_create


def structural_checks(inputs, values, locks, catalog, flag_codes):
    """Independent algebraic checks; does not call policy.rules or optimizer."""
    out = {"finite_nonnegative": all(np.isfinite(v) and v >= 0 for v in values.values())}
    roof = inputs.building.roof_max_modules if inputs.building else None
    if roof is not None and roof >= 0 and "pv_kwp" not in locks:
        out["roof_cap"] = values["pv_kwp"] <= roof * .45 + 1e-9
    if inputs.heating.type == "Heatpump" and "heat_pump_kw" not in locks:
        out["existing_hp_gate"] = values["heat_pump_kw"] == 0
    elif inputs.heating.type not in ("Gas", "Oil", "OtherNonRenewable", "Heatpump") and "heat_pump_kw" not in locks:
        out["nonfossil_hp_gate"] = values["heat_pump_kw"] == 0
    # Exclude explicitly conflicted locks from feasibility; they require an explicit relevant conflict.
    for target, expected in locks.items():
        conflict = (target == "pv_kwp" and roof is not None and expected > roof * .45) or (target == "heat_pump_kw" and inputs.heating.type == "Heatpump" and expected > 0)
        out[f"lock_conflict_surfaced_{target}" if conflict else f"locks_preserved_{target}"] = (bool(flag_codes & {"R01", "R03", "R07"}) if conflict else abs(values[target] - expected) < 1e-9)
    existing_pv = max(0, inputs.existing_pv.kwp) if inputs.existing_pv else 0
    if "battery_kwh" not in locks and values["pv_kwp"] + existing_pv <= 0:
        out["no_battery_without_pv_policy"] = values["battery_kwh"] == 0
    for target in ("battery_kwh", "heat_pump_kw"):
        if target not in locks and values[target] > 0 and catalog.get(target):
            out[f"catalog_{target}"] = any(abs(values[target] - size) < 1e-6 for size in catalog[target])
    if inputs.existing_wallbox is not None and "wallbox_kw" not in locks:
        out["no_duplicate_wallbox"] = values["wallbox_kw"] == 0
    return out


def toy_physics():
    scenarios = {
        "zero": (np.zeros(24), np.zeros(24)), "constant_load": (np.zeros(24), np.ones(24)),
        "pv_only": (np.ones(24), np.zeros(24)), "day_night": (np.r_[np.ones(12), np.zeros(12)], np.r_[np.zeros(12), np.ones(12)]),
        "impulse": (np.r_[4., np.zeros(23)], np.r_[np.zeros(23), 1.]),
    }
    checks, failures = Counter(), []
    for name, (pv, load) in scenarios.items():
        for nominal, params, mode in ((0., BatteryParams(standby_kw=0), "no_battery"),
                (3., BatteryParams(usable=1, eta_charge=1, eta_discharge=1, standby_kw=0), "lossless"),
                (3., BatteryParams(), "lossy")):
            res = flows(pv, load, nominal, p=params, hourly=True)
            h = res["hourly"]
            ch, dis, soc = (h[k][:, 0] for k in ("charge", "discharge", "soc"))
            standby = params.standby_kw if nominal else 0
            balance = pv + h["import"][:, 0] + dis - load - h["export"][:, 0] - ch - h["curtailed"][:, 0] - standby
            ledger = np.diff(np.r_[0., soc]) - params.eta_charge * ch + dis / params.eta_discharge
            observed = {"ac_balance": np.max(np.abs(balance)) < 1e-6 * max(1, float(pv.sum() + load.sum())),
                "soc_ledger": np.max(np.abs(ledger)) < 1e-6,
                "soc_bounds": bool(np.all(soc >= -1e-9) and np.all(soc <= nominal * params.usable + 1e-9)),
                "ratio_bounds": all(0 <= float(res[k][0]) <= 1 for k in ("self_consumption", "autarky"))}
            if not nominal:
                observed["no_battery_exact_import"] = np.isclose(res["import_kwh"][0], np.maximum(load - pv, 0).sum())
                observed["no_battery_exact_export"] = np.isclose(res["export"][0], np.maximum(pv - load, 0).sum())
            for rule, passed in observed.items():
                checks[f"{rule}_{'pass' if passed else 'fail'}"] += 1
                if not passed:
                    failures.append({"case_id": f"toy-{name}-{mode}", "rule": rule})
    return {"scenarios": 15, "counts": dict(checks), "failures": failures,
        "boundary": "AC hourly kWh; standby supplied separately from grid; SoC ledger excludes grid standby; empty initial SoC",
        "scope": "hand-computable 24h traces, not full API annual conservation"}


def coverage(cases):
    ordinary = [c for c in cases if c["pool"] == "ordinary"]
    factors = {
        "heating": [c["request"]["inputs"]["heating"]["type"] for c in ordinary],
        "ev": [c["latent"]["ev_state"] for c in ordinary],
        "assets": [str(c["latent"]["asset_category"]) for c in ordinary],
        "roof": [str(c["latent"]["roof_band"]) for c in ordinary],
        "installer": [c["request"]["inputs"]["installerId"] for c in ordinary],
    }
    counts = {k: dict(Counter(v)) for k, v in factors.items()}
    expected = {"heating": 6, "ev": 3, "assets": 4, "roof": 5, "installer": 3}
    for factor, minimum in (("heating", 30), ("ev", 60), ("assets", 40), ("roof", 30)):
        assert len(counts[factor]) == expected[factor] and min(counts[factor].values()) >= minimum
    pairwise = {}
    for a, b in itertools.combinations(factors, 2):
        present = len(set(zip(factors[a], factors[b])))
        pairwise[f"{a}*{b}"] = {"present": present, "required_cartesian": expected[a] * expected[b]}
    trust = Counter()
    for c in ordinary:
        for asset in ("existingPv", "existingStorage"):
            if asset in c["request"]["inputs"]:
                trust[str(c["request"]["inputs"][asset]["trusted"])] += 1
    assert min(trust.values()) >= 30
    return {"pool_requests": dict(Counter(c["pool"] for c in cases)), "ordinary_segments": counts,
        "asset_trust_occurrences": dict(trust), "pairwise": pairwise,
        "population_representative": False, "empirical_enabled": False}


def run_stress(designer, *, full_response=None, seed=SEED):
    """Run all policy cases; optionally callable full_response(DesignRequest) for 24 selected probes.

    No private identifiers, neighbour rows, reasons/evidence or row-level designs are returned.
    """
    cases = generate_cases(seed)
    report = {"spec_version": SPEC, "split": "dev", "seed": seed, "as_of": AS_OF,
        "scope": "policy structural + Pydantic schema; representative full-response checks only when adapter supplied",
        "coverage": coverage(cases), "case_sha256": digest(cases), "prng": "numpy.PCG64 with SHA256 sub-seeds",
        "runtime": {"python": platform.python_version(), "numpy": np.__version__},
        "generator_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "catalog_sha256": digest(designer.catalog),
        "contract_sha256": hashlib.sha256((ROOT / "packages/contracts/openapi.json").read_bytes()).hexdigest(),
        "review_semantic_mapping": {k: sorted(v) for k, v in REVIEW_CODES.items()},
        "final_suite": "NOT RUN: evaluator-controlled hidden seed and disjoint public profiles required",
        "blocked_coverage": ["HTTP status/invalid JSON transport, including raw NaN/Infinity tokens", "full annual API conservation beyond toy seam",
            "manufacturer compatibility and catalogue product IDs", "complete numeric-field domain Cartesian boundary coverage",
            "full BOM/VAT conventions", "household billing-boundary disclosure (no contract field)",
            "public-profile empirical resampling and held-out profile years", "production deployment network isolation",
            "same underlying base replayed over every installer (balanced combinations only)"]}
    rules = defaultdict(lambda: {"eligible": 0, "pass": 0, "fail": 0, "blocked": 0, "not_applicable": 0, "case_ids": []})
    failures, latencies, outputs, accepted, review_rows = [], [], {}, 0, []
    by_pool = defaultdict(Counter)
    def record(rule, status, cid):
        rules[rule]["eligible"] += 1
        rules[rule][status] += 1
        if status in ("fail", "blocked"):
            rules[rule]["case_ids"].append(cid)
        if status == "fail":
            failures.append({"case_id": cid, "rule": rule})
    with no_network() as attempts, threadpool_limits(limits=1):
        for case in cases:
            cid, pool = case["case_id"], case["pool"]
            payload = deepcopy(case["request"])
            token = payload["inputs"].get("installerId")
            if token in ("known_0", "known_1"):
                payload["inputs"]["installerId"] = designer.installers[min(int(token[-1]), len(designer.installers) - 1)] if designer.installers else "unseen_external"
            expectation = case["expectation"]
            try:
                request = DesignRequest.model_validate(payload)
            except ValidationError:
                good = expectation["action"] == "reject" or expectation["action"] == "review"
                record("schema_expected_action", "pass" if good else "fail", cid)
                by_pool[pool]["schema_rejected"] += 1
                continue
            if expectation["action"] == "reject":
                record("schema_expected_action", "fail", cid)
                by_pool[pool]["unexpected_schema_accept"] += 1
                continue
            current = request.current
            locks = {}
            for comp in request.locks:
                item = getattr(current, {"heatPump": "heat_pump"}.get(comp, comp)) if current else None
                attr = {"pv": "kwp", "battery": "kwh", "heatPump": "kw", "wallbox": "kw"}[comp]
                locks[LOCK_TARGET[comp]] = getattr(item, attr) if item else 0.
            t0 = time.perf_counter()
            try:
                result = designer.design(request.inputs, locks, module_wp=450)
                latencies.append((time.perf_counter() - t0) * 1000)
                values = result.values
                flags = {flag.code for flag in result.flags}
                outputs[cid] = values
                accepted += 1
                by_pool[pool]["policy_returned"] += 1
                for rule, good in structural_checks(request.inputs, values, locks, designer.catalog, flags).items():
                    record(rule, "pass" if good else "fail", cid)
                if expectation["action"] == "review":
                    reason = expectation["reason"]
                    relevant = REVIEW_CODES.get(reason, set())
                    # Endpoint-only disclosure flags cannot be evaluated from PolicyDesign.
                    endpoint_only = reason in ("placeholder", "default_minimal", "unseen_installer", "untrusted_pv")
                    status = "blocked" if endpoint_only else ("pass" if relevant & flags else "fail")
                    record("relevant_review_warning", status, cid)
                    review_rows.append((cid, reason, status))
                # Replay same request: compare numeric policy output; never serialize neighbour evidence.
                again = designer.design(request.inputs, locks, module_wp=450)
                record("offline_replay", "pass" if canonical(values) == canonical(again.values) else "fail", cid)
            except Exception as exc:
                # Never store exception text: upstream errors may contain project identifiers or frame values.
                record("controlled_policy_execution", "fail", cid)
                by_pool[pool]["policy_exception"] += 1
                failures[-1]["exception_type"] = type(exc).__name__
        paired = defaultdict(dict)
        for case in cases:
            if case["pair"]:
                paired[case["pair"]["id"]][case["pair"]["role"]] = case
        for pair_id, members in paired.items():
            a, b = members["a"], members["b"]
            if a["case_id"] not in outputs or b["case_id"] not in outputs:
                record("metamorphic_execution", "fail", pair_id)
                continue
            va, vb, kind = outputs[a["case_id"]], outputs[b["case_id"]], a["pair"]["kind"]
            if kind in ("key_order", "ignored_extra", "lock_preserve"):
                good = canonical(va) == canonical(vb)
            elif kind == "roof_shrink":
                good = vb["pv_kwp"] <= 4 * .45 + 1e-9
            elif kind == "ev_present":
                good = vb["wallbox_kw"] >= va["wallbox_kw"]
            else:
                good = vb["pv_kwp"] >= va["pv_kwp"]
            # Product monotonicity is a diagnostic, never a physics theorem/hard gate.
            record("diagnostic_demand_monotonic" if kind == "demand_up" else f"pair_{kind}", "pass" if good else "fail", pair_id)
        report["toy_physics"] = toy_physics()
        if full_response is not None:
            report["full_response_subset"] = check_full_responses(cases, designer, full_response)
        report["network_attempts"] = len(attempts)
        record("outbound_network_disabled", "pass" if not attempts else "fail", "suite")
    report.update(requests=len(cases), policy_accepted=accepted, rules=dict(rules), failures=failures,
        by_pool={k: dict(v) for k, v in by_pool.items()},
        policy_latency_ms={"p50": float(np.percentile(latencies, 50)), "p95": float(np.percentile(latencies, 95))} if latencies else None,
        review={"predeclared_cases": sum(c["expectation"]["action"] == "review" for c in cases),
            "policy_pass": sum(s == "pass" for _, _, s in review_rows),
            "policy_fail": sum(s == "fail" for _, _, s in review_rows),
            "policy_blocked": sum(s == "blocked" for _, _, s in review_rows),
            "false_review_rate": None, "false_review_rate_blocked_reason": "PolicyDesign omits endpoint intake review signals"})
    hard_failures = [f for f in failures if f["rule"] != "diagnostic_demand_monotonic"]
    report["hard_failure_count"] = len(hard_failures)
    full_failures = report.get("full_response_subset", {}).get("failures", [])
    report["status"] = "FAIL_WITH_BLOCKED_COVERAGE" if hard_failures or report["toy_physics"]["failures"] or full_failures else "INCOMPLETE_BLOCKED_COVERAGE"
    return report


def check_full_responses(cases, designer, callback):
    """24 preselected synthetic cases: ordinary 0..5, observation 60..65/90..95, boundary80..85."""
    selected = [c for c in cases if c["case_id"] in {
        *(f"dev-ordinary-{i:04d}" for i in range(6)),
        *(f"dev-observation-{i:04d}" for i in range(60, 66)),
        *(f"dev-observation-{i:04d}" for i in range(90, 96)),
        *(f"dev-boundary-{i:04d}" for i in range(80, 86))}]
    counts, failures = Counter(), []
    for case in selected:
        payload = deepcopy(case["request"])
        token = payload["inputs"].get("installerId")
        if token in ("known_0", "known_1"):
            payload["inputs"]["installerId"] = designer.installers[min(int(token[-1]), len(designer.installers)-1)] if designer.installers else "unseen_external"
        request = DesignRequest.model_validate(payload)
        try:
            response = callback(request)
            for design in (response.proposal, *response.alternatives):
                counts["designs"] += 1
                pv = design.pv
                checks = {"pv_module_identity": not pv or (pv.modules > 0 and isinstance(pv.modules, int) and abs(pv.kwp-pv.modules*pv.module_wp/1000) <= max(1e-6, 1e-6*pv.kwp)),
                    "response_sizes_finite": all(v is None or np.isfinite(v) and v >= 0 for v in (pv.kwp if pv else None, design.battery.kwh if design.battery else None, design.heat_pump.kw if design.heat_pump else None, design.wallbox.kw if design.wallbox else None))}
                if pv and request.inputs.building and request.inputs.building.roof_max_modules is not None:
                    checks["response_roof_modules"] = pv.modules <= request.inputs.building.roof_max_modules
                for rule, good in checks.items():
                    counts[f"{rule}_{'pass' if good else 'fail'}"] += 1
                    if not good:
                        failures.append({"case_id": case["case_id"], "rule": rule})
                # Missing metrics must not silently disappear from the checked denominator.
                metric = response.metrics.get(design.id)
                pv_present = bool(design.pv or request.inputs.existing_pv)
                required = ["grid_import_kwh", "feed_in_kwh", "pv_yield_kwh"]
                if request.inputs.demand_kwh > 0:
                    required.append("autarky")
                if pv_present:
                    required.append("self_consumption")
                for name in required:
                    value = getattr(metric, name) if metric is not None else None
                    good = value is not None and np.isfinite(value)
                    counts[f"required_metric_present_{'pass' if good else 'fail'}"] += 1
                    if not good:
                        counts[f"missing_{name}"] += 1
                        failures.append({"case_id": case["case_id"], "rule": f"missing_required_{name}"})
            for metrics in response.metrics.values():
                for name in ("self_consumption", "autarky"):
                    v = getattr(metrics, name)
                    if v is not None:
                        good = np.isfinite(v) and 0 <= v <= 1
                        counts[f"metric_bounds_{'pass' if good else 'fail'}"] += 1
                        if not good:
                            failures.append({"case_id": case["case_id"], "rule": f"{name}_bounds"})
            reason = case["expectation"]["reason"]
            if case["expectation"]["action"] == "review":
                relevant = REVIEW_CODES.get(reason, set())
                good = bool({f.code for f in response.flags} & relevant)
                counts[f"review_{'pass' if good else 'fail'}"] += 1
                if not good:
                    failures.append({"case_id": case["case_id"], "rule": "full_response_review"})
            counts["returned"] += 1
        except Exception as exc:
            counts["exceptions"] += 1
            failures.append({"case_id": case["case_id"], "rule": "full_response_exception", "exception_type": type(exc).__name__})
    return {"n": len(selected), "counts": dict(counts), "failures": failures,
        "note": "direct engine.design.design call; HTTP behavior/BOM tax semantics not certified"}


def write_suite(directory, seed=SEED):
    directory.mkdir(parents=True, exist_ok=True)
    cases = generate_cases(seed)
    blob = "\n".join(canonical(case) for case in cases) + "\n"
    path = directory / "stress_cases_dev.jsonl"
    path.write_text(blob, encoding="utf-8")
    manifest = {"spec_version": SPEC, "split": "dev", "seed": seed, "as_of": AS_OF,
        "cases": len(cases), "case_file_sha256": hashlib.sha256(blob.encode()).hexdigest(),
        "generator_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "prng": "numpy.PCG64", "numpy": np.__version__, "coverage": coverage(cases),
        "evidence": [{"id": "S1", "kind": "source_anchor", "publisher": "Stromspiegel/co2online",
            "url": "https://www.stromspiegel.de/stromverbrauch-verstehen/stromverbrauch-im-haushalt/",
            "accessed_at": "2026-11-08", "release": "undated current SFH table", "license": "UNVERIFIED; numeric reference facts only",
            "artifact_sha256": None, "local_artifact_id": None, "verified_status": "landing_or_table_verified",
            "units": "annual household kWh; with/without electric hot water; excludes EV/HP additions in harness",
            "note": "2-person SFH table 2700 conflicts with intro prose 3500; table chosen explicitly"},
            {"id": "A-coverage", "kind": "analyst_coverage", "source": "research/external/TASK2-SYNTHETIC-TEST-SPEC.md",
            "note": "All quotas/ranges/scenario efficiencies/locations/roof limits/tariffs/perturbations are coverage assumptions, not population probabilities"}],
        "units": {"demandKwh": "kWh/year", "heatDemandKwh": "thermal kWh/year", "hpElecKwh": "electrical kWh/year", "existingPv.kwp": "kWp", "existingStorage.kwh": "kWh", "priceEurKwh": "EUR/kWh", "priceEscalation": "fraction/year"},
        "empirical_enabled": False, "final_suite_status": "blocked pending independent evaluator seed/profile allocation"}
    (directory / "stress_manifest.json").write_text(json.dumps(manifest, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    return manifest


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=Path(__file__).with_name("stress_results.json"))
    parser.add_argument("--full-response", action="store_true")
    args = parser.parse_args()
    manifest = write_suite(args.out.parent)
    model = ROOT / "services/engine/models/designer.joblib"
    config_path = ROOT / "services/engine/config/policy.json"
    start_hashes = {"model": hashlib.sha256(model.read_bytes()).hexdigest(),
        "config": hashlib.sha256(config_path.read_bytes()).hexdigest()}
    physics.load_cache(ROOT / "data/processed/physics_cache.pkl")
    designer = Designer.load(model)
    callback = None
    if args.full_response:
        from engine.design import Store, design
        store = Store(ROOT / "data/processed", model)
        callback = lambda request: design(request, store)
    report = run_stress(designer, full_response=callback)
    report["manifest_sha256"] = digest(manifest)
    end_hashes = {"model": hashlib.sha256(model.read_bytes()).hexdigest(),
        "config": hashlib.sha256(config_path.read_bytes()).hexdigest()}
    report["model_sha256"] = start_hashes["model"]
    report["policy_config_sha256"] = start_hashes["config"]
    report["artifact_consistency"] = {"start_sha256": start_hashes, "end_sha256": end_hashes,
        "unchanged": start_hashes == end_hashes}
    if start_hashes != end_hashes:
        report["status"] = "INVALID_ARTIFACT_CHANGED_DURING_RUN"
    args.out.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("status", "requests", "policy_accepted", "hard_failure_count", "review", "network_attempts", "toy_physics")}, indent=2))


if __name__ == "__main__":
    main()
