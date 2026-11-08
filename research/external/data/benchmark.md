# Offline plausibility benchmark — 2026-11-08

Run **`pnpm x:external`**. Final default run completed offline with the saved local model, unchanged start/end model/config/engine-source/public-cache hashes and zero attempted Python socket connections. `eval/external/results.json` is the aggregate receipt; volatile policy timing is separate in `run_timings.json`. No model fitting or new 2026 expert-match scoring occurs. The checker completes even when it finds engine failures; process exit 0 is not a stress release pass.

## Contextual plausibility

The default generates 240 homes from verified German public marginals (household size 2024, EVS plug-in ownership 2023, dwelling heat 2022) plus Stromspiegel SFH demand anchors. Mixed-year independence, mapping the broad ambient-heat group to a Heatpump proxy, 5+→5 topcoding, demand spread, EV km/useful-heat volumes and tariff are explicit assumptions in `data/external/german_priors.json`. It is **not a measured joint distribution of German PV adopters**.

Reference: 535,307 registered 2024 household-use building/roof/facade PV units, 1–30 gross kWp, active/operating Germany, snapshot 2025-02-09. Public source/units/filters/hashes: [pack README](../../../data/external/README.md), [MaStR extraction](mastr.md). All sources accessed 2026-11-08.

| Check | Observed result | Interpretation |
|---|---|---|
| Proposed positive PV within 2024 p5–p95 (4.00–19.86 kWp) | 234/234(100.0%);6/240 propose no PV | Contextual range check, not expert accuracy; zero-PV denominator kept separate |
| Proposed positive PV median | 8.90 kWp | This source-marginal scenario only |
| Proposed nominal battery/PV median | 0.8654kWh/ kWp | Nominal capacity is not registry usable capacity |
| Approximate ratio Wasserstein | 0.2183kWh/ kWp | Engine nominal×0.92 **scenario** versus 2024 co-location usable-ratio 1001-midpoint quantile sketch; no significance or pass threshold |
| Real 2026 reference | BLOCKED | Snapshot predates 2026; do not substitute historical results silently |
| National battery attach rate | BLOCKED | Registry co-location/missingness is not unbiased household attachment |

The separately retained balanced coverage run, `eval/external/results_balanced_coverage.json`, has 239/239 positive PV sizes in the same historical range and ratio distance 0.2070. Different scenario populations are not an improvement comparison. Its complete stress dictionary is **identical** to the default run, providing an additional replay of the frozen suite under the same artifact/code. Both runs have zero network attempts; the final public-marginal batch itself also replayed identically.

## Actual DEV stress result: FAIL_WITH_BLOCKED_COVERAGE

720 intake-only requests:240 ordinary+120 missing/default+120 boundary+120 pairs(240 requests).44 expected schema rejects,676 policy returns. No synthetic expert labels.15 toy energy ledgers and 676 policy replays pass; all ordinary factor-pair coverage quotas pass. This is a development suite; hidden evaluator seed/profile allocation remains a request.

| Distinct check | Result |
|---|---|
| Finite/nonnegative policy capacities | 1/676 fails: negative roof cap yields negative PV (`dev-boundary-0049`) |
| Relevant policy review warnings | 8 pass, 120 miss, 58 adapter-blocked of 186 predeclared review cases; these are not 120 physical defects |
| Metamorphic pairs | 119/120 pass; one demand-monotonic **diagnostic** fails; all 100 non-demand pairs pass |
| Full-response arithmetic | 39/70 strict modules×moduleWp identities fail, consistent with two-decimal serialization; not 39 impossible systems |
| Full-response capacity/roof | 70/70 finite/nonnegative;26 eligible module roof checks pass |
| Required full-response metric availability | 339/347 present; 8 missing (grid import/feed-in/PV yield/autarky twice each) |
| Full-response relevant warnings | 12/16 pass, 4 missing |

`hard_failure_count=121` combines the single nonnegative-capacity failure with 120 missing-review checks; preserve that breakdown. The engine logs a caught `recommend_battery` empty-candidate exception for two selected cases; design JSON can return while simulation metrics are unavailable. HTTP malformed transport, full BOM/VAT/compatibility, all annual API trajectories, dedicated review state/false-review rate and independent final seed/profile scope remain explicitly blocked. See [detailed scoped handoff](../../creative/ceiling/STRESS.md), cases/manifest and result JSON.

## Review and three testable improvements

1. **Engine/Eval:** narrow bounded-input/output, module precision and simulation-availability fixes; retain this failing DEV receipt, add targeted independent fixtures, rerun unchanged DEV, then allocate a new hidden evaluator seed. Do not tune the model or relax tolerances to hide failures.
2. **Engine:** test the shipped measured household/HP/EV profiles on fixed systems, keeping annual energies and demand boundaries explicit. In the 9 kWp/5 kWh scenario, the paired WPuQ household+HP median autarky change is about −0.07 pp with a wide selected-cohort range; the single measured EV shape changes household+EV median by +8.17 pp. These are sensitivity cases, not universal corrections or actual savings validation. [Profiles report](profiles.md).
3. **Engine/Eval:** test a weak, cohort-qualified usable-battery/PV prior only under the registered pre-2026 folds, after product usable/nominal semantics are resolved. Keep public typicality separate from expert imitation. Refresh MaStR for real 2026 and investigate the documented direct solar-reference field before stronger pairing claims.

Validation: **18 external unit tests pass**; web lint/typecheck pass. `pnpm test` has 108 engine passes and 3 timing failures; targeted retry also fails all 3 (warm/cold design and 12-size battery sweep). No cause is attributed on this shared busy machine and no timing limit was changed. Files remain uncommitted; no raw downloads or confidential rows are staged. Other owners' concurrent edits were preserved.
