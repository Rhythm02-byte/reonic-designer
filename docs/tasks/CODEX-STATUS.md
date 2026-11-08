# Codex night shift status

- 2026-11-08 03:45 CET: Started on clean branch `next`; board read, no active claims. Plan in CODEX-PLAN.md. Public download discovery first; parallel agents assigned ceiling, diverse generation and hard criticism. No commits authorized.
- 2026-11-08 03:57 CET: A raw public downloads complete (~1.2 GB); MaStR extraction and measured profile calibration running. C complete (no 2026 rescore): exact-input empirical oracle bound ~62%, not a demonstrated 25% ceiling. B has 200 candidates, logged debate and tournament; integration next. Initial parser issues (ZIP memory materialization, weather ns vs feed seconds) corrected before extraction results.
- 2026-11-08 04:00 CET: B full draft integrated in research/creative/blindspots.md with parent judge review, top25/top5/wildcards, 200 raw ideas and 435 logged pair comparisons. A extracted 1,985,451 household-use rooftop PV units; storage SSE-to-SEE mapping via legacy SpeMastrNummer field recovered 1,641,534 lithium units and 860,408 conservative location/operator links. 57 calibrated measured profiles retained; negative reconstructed OPSD household boundary excluded.
- 2026-11-08 04:05 CET: Public adapter/linker tests pass; Zenodo payload size+MD5 verified and 21 source artifacts have local SHA-256. Full DEV stress identifies negative roof-cap/negative capacity and full-response module-rounding failures; owner notified, no engine fix outside scope. pnpm test is running. x:external smoke replay identical with zero outbound attempts; final full benchmark pending stress handoff.

- 2026-11-08 04:13 CET: C expanded available-input audit lifts empirical oracle only from62.22% to62.30%; most omitted occupancy/building fields are recorded in6/1,268 development rows. No universal ceiling or hidden-model win inferred.16 external tests and web lint/typecheck passed. Full pnpm test:108 pass,3 timing failures under parallel load; targeted retry in progress. Final pnpm x:external now includes720 stress requests and24 direct full-response probes, with start/end model/config/source hashes.

- 2026-11-08 04:14 CET: Targeted retry confirms all3 timing tests still fail (warm design p95~943ms, cold~1389ms, sweep~162ms). Other concurrent work remains, so no cause attributed; no threshold weakened. Root pnpm test is NOT passing. External tests16/16, web lint/typecheck pass. Final benchmark still running; no further model experiments or test scoring planned.

- 2026-11-08 04:25 CET: Full offline balanced benchmark finished:239/239 positive PV proposals within historical2024 p5–p95, approximate usable-ratio W1=0.207.720-case DEV stress reproduced FAIL_WITH_BLOCKED_COVERAGE with artifact/config/source unchanged and zero outbound attempts. Preserved results_balanced_coverage.json; replacing default intake sampling with verified Destatis marginal scenario (mixed-year/independence/proxy assumptions explicit), then final rerun.

- 2026-11-08 04:32 CET: Scope/size audit clean for our deliverables: all under5MB, raw/public downloads ignored, nothing staged. Board/AGENTS update requests prompt Markdown commits, but this task explicitly forbids all commits; files stay uncommitted for Claude. Other owners have concurrent changes outside our paths, preserved.18 external tests pass after final sampler integration; web lint/typecheck already passed.

## Final report — 2026-11-08 04:39 CET

All three workstreams delivered, uncommitted for Claude; no private rows exported or new UI.

**Top five, after measured-evidence review:** (1) repair bounded-output/simulation-availability defects; (2) correct unsupported pitch claims; (3) rehearse existing Ask next; (4) retain offline replay receipts; (5) distinguish genuine 4500 kWh from defaults using provenance. Top 25, five mini-specs, kill list, jury answers, three wildcards, 200 raw ideas and 435 pair comparisons: `research/creative/blindspots.md`.

**A:** 1,985,451 household-use rooftop PV units; 860,408 conservative storage co-locations. 2024 median PV 9.84 kWp, p5–p95=4.00–19.86. 57 calibrated WPuQ/OPSD profiles. Final `pnpm x:external`: 234/234 positive PV proposals within that historical range;6/240 propose no PV. Approximate ratio Wasserstein=0.218 under 92%-usable scenario. Zero network attempts; batch and 676 policy replays identical; complete stress dictionaries identical across two full scenario runs.

**Failures:** one negative-capacity case; 39/70 displayed module identities inconsistent; 8 required metrics missing; 120 review-warning misses, 58 blocked. 15 toy ledgers pass. Stress is failed/incomplete DEV, not release certification.

**C:** expanded exact-input empirical oracle 62.30%; no proven 25% ceiling. Strict one-module scoring reverses validation ranking. No 2026 tuning/rescoring.

**Unverified/blocked:** 2026 registry cohort, unbiased attach rate, electrical pairing, adopter joint distribution, source-clock alignment, some reuse licences, final hidden-seed/HTTP/BOM/compatibility coverage and other-team scores.

**Checks/requests:** 18 external tests and web lint/typecheck pass. `pnpm test`: 108 pass, 3 timing failures; targeted retry also fails. Engine: fix domain/precision/empty-candidate metric loss; Eval: preserve failures and allocate independent final seed, confirm signed-option semantics; Pitch: qualify claims and latency. Details: `research/external/data/benchmark.md` and `data/external/README.md`.
