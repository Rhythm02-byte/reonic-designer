# External DEV stress handoff

2026-11-08, Europe/Berlin. No commits or engine changes. This is a **failed, incomplete development suite**, not a release certification or an expert-accuracy result.

Commands:

```text
node scripts/py.mjs -m pytest -q eval/external/ceiling eval/external/pack/test_stress.py
node scripts/py.mjs eval/external/stress.py --full-response
```

Combined unit verification: **11 passed**. `run_stress(designer)` is callable by the external benchmark; it returns aggregates and synthetic case IDs, never neighbours, private row IDs or private feature rows.

The generator freezes 720 intake-only requests before evaluation: 240 ordinary, 120 missing/default, 120 boundary/contradiction, and 120 metamorphic pairs (240 requests). Cases use PCG64 with SHA-256 family sub-seeds and `as_of=2026-11-07`. All ordinary quotas pass, with all ten Cartesian factor-pair matrices covered. Analyst coverage is explicitly separate from Stromspiegel household demand anchors; the manifest cites URL/access date and records the table/prose discrepancy. It does not estimate German prevalence. There are no synthetic target labels.

## Final DEV receipt

Canonical report: `eval/external/stress_results.json` (same frozen run also in `stress_final_dev_results.json`; canonical copy adds consistency/coverage caveats). Cases and manifest are `stress_cases_dev.jsonl` / `stress_manifest.json`.

- 720 requests; **44 expected schema rejections**, **676 policy returns**; no policy crashes or uncontrolled schema outcomes in this scoped adapter.
- **1/676 nonnegative-capacity failure**: synthetic `dev-boundary-0049` supplies `building.roofMaxModules=-1`. The schema accepts it and policy can return negative PV. It should reject or explicitly request review with a bounded draft.
- **186 predeclared review cases**: policy identifies 8 using frozen relevant codes, misses 120, and 58 are blocked in the policy adapter because their intake-disclosure codes are added by the full endpoint. Do not call these 120 physical violations. `hard_failure_count=121` combines the one negative-capacity defect with the missing-review checks.
- All **676 replay comparisons** pass; **0 attempted outbound connections** under the in-process block. This is not proof of deployment network isolation.
- Of 120 metamorphic pairs: **119 pass**, **1 demand→PV nondecrease diagnostic fails**. Demand monotonicity is a product expectation, not a physical theorem. All 100 other pairs pass (roof shrink, EV addition, valid locks, key order, ignored extras).
- **15/15 toy simulations** pass hourly AC balance, SoC ledger, SoC bounds and ratio checks; all five no-battery scenarios also match closed-form import/export. These are 24-hour test-seam trajectories, not full-year API conservation.
- Preselected **24 actual full engine responses** contain 70 proposal/alternative designs: **39/70 fail strict module identity**, while all 70 have finite nonnegative displayed capacities and all 26 eligible roof-module checks pass. The identity problem is consistent with `system_from_values` rounding kWp to two decimals when modules × moduleWp requires three. Relevant full-response review warnings pass 12/16; four remain missing.
- The original subset counted **136 non-null ratio metrics** in bounds, but did not certify missing required metrics. A separate `stress_metric_availability.json` follow-up adds explicit availability failures after observing that gap: **339/347 required metric fields present, 8 missing** (grid import, feed-in, PV yield and autarky each absent twice). It confirms identical start/end model/config SHA and zero network attempts. The engine logs `recommend_battery: min() iterable argument is empty`; `attach_metrics` catches it, so returned design JSON alone must not be taken as proof that simulation metrics exist.

## Reproducibility limits

The final DEV worker loaded the artifact after another owner retrained it at **04:01:54**. Its observed model mtime remained 04:01:54 through run completion around 04:11; config mtime stayed 2026-11-07 22:16:14. **Start SHA was not captured in that run**, so its artifact consistency is explicitly mtime-only. The CLI now records model/config SHA before load and after execution and invalidates changed artifacts. The metric-availability follow-up also records start/end SHA.

The earlier exploratory 03:58–04:04 run is retained as `stress_results_dev_initial.json` with initial cases/manifest. Another owner's artifact retrain occurred during it, so its end SHA does not identify the originally loaded model. Its counts are **not** a controlled before/after comparison. The development generator initially failed a roof-band quota assertion before evaluation; that was repaired. Installer/heating coverage and per-lock/network bookkeeping were then improved before the final DEV run. No model or policy was changed or fitted to failures. No evaluator-controlled final synthetic suite has been run.

Blocked scope: HTTP status and raw malformed JSON/NaN/Infinity handling; exhaustive numeric-domain probes; manufacturer/product compatibility; full BOM/VAT semantics; all annual API trajectories; billing-boundary disclosure; public-profile holdout allocation; same-base replay over every installer; false-review rate with a dedicated workflow review state. All are explicit in the result, so there is no “all stress checks passed” claim.

Owner requests: Engine should reject negative roof/domain values, preserve module arithmetic precision, handle empty/NaN autarky candidate sets without dropping metrics, and add explicit relevant domain/conflict/uncertainty warnings. Eval should retain the failing DEV receipt, agree scope/semantics, and hold an independent new seed/profile split after fixes. Future runs must stay offline and separate from expert-match evaluation.
