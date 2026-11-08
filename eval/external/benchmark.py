"""Deterministic public plausibility benchmark. No downloads, private-row exports or fitting.

pnpm x:external
"""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
import os
import platform
import socket
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import wasserstein_distance
from threadpoolctl import threadpool_limits

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from pack.common import ROOT, DATA, quantiles, sha256, write_json


@contextlib.contextmanager
def no_network():
    """Fail closed on Python socket outbound calls during scored computation."""
    original = (socket.socket.connect, socket.socket.connect_ex, socket.create_connection)
    attempted = []
    def deny(*args, **kwargs):
        attempted.append("outbound_socket")
        raise RuntimeError("Outbound networking forbidden in external benchmark")
    socket.socket.connect = socket.socket.connect_ex = socket.create_connection = deny
    try:
        yield attempted
    finally:
        socket.socket.connect, socket.socket.connect_ex, socket.create_connection = original


def sample_homes(n, installers, seed=110701):
    """Anchored coverage; NOT a German joint-population estimator.

    Demand means from Stromspiegel table, all multipliers/quotas analyst coverage.
    Heating/EV/persons balanced, rather than unsupported independent population priors.
    """
    from engine.models.schemas import HomeInputs
    rng = np.random.Generator(np.random.PCG64(seed))
    means = [1800, 2700, 3500, 3800, 4500]
    heating = ["Gas", "Oil", "Heatpump", "OtherRenewable", "OtherNonRenewable", "Unknown"]
    homes = []
    for i in range(n):
        people = i % 5 + 1
        demand = round(means[people - 1] * rng.uniform(.6, 1.6))
        heat = heating[(i // 5) % 6]
        ev = (i // 30) % 2 == 1
        homes.append(HomeInputs.model_validate({
            "installerId": installers[i % len(installers)], "demandKwh": demand, "persons": people,
            "ev": {"has": ev, "kmPerYear": int(rng.uniform(5000, 25000)) if ev else None},
            "heating": {"type": heat, "heatDemandKwh": int(rng.uniform(8000, 30000))},
            "priceEurKwh": .32, "provenance": {"demandKwh": {"source": "entered", "confidence": 1}},
        }))
    return homes


def contextual_scores(sizes, summary, requested_year=2026, reference_year=2024):
    positive = sizes.pv_kwp.gt(0)
    cohort = summary["pv_by_year"].get(str(reference_year))
    if not cohort or not cohort["n"]:
        raise ValueError("Required reference PV cohort unavailable")
    pv = sizes.loc[positive, "pv_kwp"].to_numpy()
    linked = summary["linkage"]["by_pv_commissioning_year"].get(str(reference_year), {})
    ref_ratio = linked.get("usable_ratio_quantile_sketch_1001", [])
    joint = positive & sizes.battery_kwh.gt(0)
    ratio_nominal = (sizes.loc[joint, "battery_kwh"] / sizes.loc[joint, "pv_kwp"]).to_numpy()
    # Engine dispatch's usable fraction is an assumption, NOT a product conversion fact.
    ratio_usable_scenario = ratio_nominal * .92
    return {
        "same_year_2026": {"status": "blocked", "reason": "Pinned MaStR snapshot is 2025-02-09; no 2026 cohort"},
        "historical_reference": {"year": reference_year, "requested_year": requested_year,
            "scope": "Historical context only; snapshot/population mismatch, no 2026 accuracy claim",
            "pv_cohort_n": cohort["n"], "pv_p5_kwp": cohort["p5"], "pv_p95_kwp": cohort["p95"],
            "generated_n": len(sizes), "positive_pv_n": len(pv), "zero_pv_n": int((~positive).sum()),
            "positive_pv_inside_p5_p95_n": int(((pv >= cohort["p5"]) & (pv <= cohort["p95"])).sum()),
            "positive_pv_inside_p5_p95_share": float(((pv >= cohort["p5"]) & (pv <= cohort["p95"])).mean()) if len(pv) else None,
            "generated_pv_kwp": quantiles(pv), "generated_nominal_battery_kwh_per_kwp": quantiles(ratio_nominal),
            "registered_colocated_ratio_n": linked.get("linked_colocated_n", 0),
            "wasserstein_to_1001_quantile_sketch": {
                "status": "scenario_only" if len(ref_ratio) and len(ratio_nominal) else "blocked",
                "usable_fraction_assumption": .92,
                "distance_kwh_per_kwp": float(wasserstein_distance(ratio_usable_scenario, ref_ratio)) if len(ref_ratio) and len(ratio_nominal) else None,
                "caveat": "Approximate empirical W1 against equally weighted quantile sketch. Registry usable kWh vs engine nominal kWh converted with dispatch assumption 0.92; registered co-location is not proven electrical coupling."}}}


def engine_tree_sha256():
    h = hashlib.sha256()
    for path in sorted((ROOT / "services/engine/engine").rglob("*.py")):
        h.update(path.relative_to(ROOT).as_posix().encode())
        h.update(path.read_bytes())
    return h.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--n", type=int, default=240)
    parser.add_argument("--sampler", choices=["public-marginals", "balanced-coverage"], default="public-marginals")
    parser.add_argument("--skip-stress", action="store_true", help="Development only; marks stress blocked")
    args = parser.parse_args()
    if args.n < 1:
        parser.error("--n must be positive")
    os.environ["OFFLINE"] = "1"
    os.environ["OMP_NUM_THREADS"] = "1"
    os.environ["MKL_NUM_THREADS"] = "1"
    required = [DATA / "mastr_summary.json", DATA / "profiles/measured.npz", DATA / "profiles/metadata.json",
                DATA / "profile_calibration.json", DATA / "german_priors.json", DATA / "sources.json"]
    for path in required:
        if not path.exists():
            raise SystemExit(f"Missing public cache: {path.name}. See data/external/README.md. No live fallback.")
    frozen_public_hashes = {p.relative_to(ROOT).as_posix(): sha256(p) for p in required}
    from engine.policy.designer import Designer
    from engine.policy.features import row_from_inputs
    model = ROOT / "services/engine/models/designer.joblib"
    if not model.exists():
        raise SystemExit("Missing local designer artifact; ask Engine owner. Benchmark never trains it.")
    config_path = Path(os.environ.get("ENGINE_POLICY_CONFIG") or ROOT / "services/engine/config/policy.json").resolve()
    frozen_model_hash, frozen_config_hash = sha256(model), sha256(config_path)
    frozen_source_hash = engine_tree_sha256()
    with no_network() as attempted, threadpool_limits(limits=1):
        d = Designer.load(model)
        installers = d.installers or ("external-unseen",)
        if args.sampler == "public-marginals":
            from pack.public_priors import sample_public_homes
            homes, sampler_manifest = sample_public_homes(args.n, installers)
        else:
            homes = sample_homes(args.n, installers)
            sampler_manifest = {"mode": "balanced_coverage", "source_anchor": "https://www.stromspiegel.de/stromverbrauch-verstehen/stromverbrauch-im-haushalt/",
                "accessed_at": "2026-11-08", "demand_means_1_to_5_persons_kwh": [1800, 2700, 3500, 3800, 4500],
                "analyst_coverage": "Uniform demand multiplier [0.6,1.6], balanced persons/heating/EV/installer; EV km5000-25000; useful heat8000-30000; price .32. No measured German joint-population distribution."}
        print(f"Scoring {args.n} homes: {args.sampler}; no fitting or network", flush=True)
        frame = pd.DataFrame([row_from_inputs(h) for h in homes])
        sizes = d.design_batch(frame)
        repeat = d.design_batch(frame)
        replay = bool(np.array_equal(sizes.to_numpy(), repeat.to_numpy(), equal_nan=True))
        if not np.isfinite(sizes.to_numpy()).all():
            raise ValueError("Nonfinite predicted capacity")
        summary = json.loads((DATA / "mastr_summary.json").read_text(encoding="utf-8"))
        context = contextual_scores(sizes, summary)
        if args.skip_stress:
            stress = {"status": "blocked", "reason": "--skip-stress requested"}
        else:
            from stress import run_stress
            from engine.design import Store, design
            store = Store(ROOT / "data/processed", model)
            print("Running 720 DEV stress requests plus replay and 24 full-response probes", flush=True)
            stress = run_stress(d, full_response=lambda request: design(request, store))
    # Keep volatile timing outside the deterministic scored aggregate.
    timing = stress.pop("policy_latency_ms", None)
    if timing is not None:
        write_json(HERE / "run_timings.json", {"policy_latency_ms": timing, "hardware": platform.machine(),
                   "note": "Descriptive current-run timing; intentionally excluded from deterministic results.json"})
    if sha256(model) != frozen_model_hash or sha256(config_path) != frozen_config_hash or engine_tree_sha256() != frozen_source_hash:
        raise SystemExit("Model/config/source changed during benchmark; retain prior report and rerun after owner freezes artifact")
    if {p.relative_to(ROOT).as_posix(): sha256(p) for p in required} != frozen_public_hashes:
        raise SystemExit("Scored public caches changed during benchmark; rerun with frozen evidence")
    results = {
        "schema_version": 1, "as_of": "2026-11-08", "offline": True,
        "purpose": "Public cohort plausibility and structural robustness, NOT expert accuracy",
        "seed": 110701, "prng": "numpy.PCG64", "runtime": {"python": platform.python_version(), "numpy": np.__version__, "pandas": pd.__version__},
        "receipt": {"model_sha256": frozen_model_hash, "policy_sha256": frozen_config_hash,
                    "engine_python_tree_sha256": frozen_source_hash, "benchmark_sha256": sha256(Path(__file__)),
                    "public_cache_sha256": frozen_public_hashes,
                    "repeated_batch_identical": replay, "outbound_socket_attempts": len(attempted),
                    "volatile_fields": "policy latency separated into run_timings.json; no clock time in scored aggregates",
                    "network_guard_scope": "Python sockets during computation only; not a system firewall"},
        "sampler": {**sampler_manifest, "population_weighted_metric": "blocked: no verified joint distribution of adopter households"},
        "plausibility": context, "stress": stress,
        "measured_profile_calibration": json.loads((DATA / "profile_calibration.json").read_text(encoding="utf-8")),
    }
    write_json(HERE / "results.json", results)
    print(json.dumps({"offline": True, "n": args.n, "replay_identical": replay,
                      "outbound_attempts": len(attempted), "plausibility": context,
                      "stress_status": stress.get("status"), "stress_hard_failure_count": stress.get("hard_failure_count"),
                      "results": "eval/external/results.json"}, indent=2))
    if not replay or attempted or stress.get("network_attempts", 0):
        raise SystemExit("Offline/replay gate failed")


if __name__ == "__main__":
    main()
