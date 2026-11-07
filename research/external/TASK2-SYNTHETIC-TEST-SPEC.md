## Summary (≤150 words)

As of **2026-11-07**, this is an implementation specification, not a generated dataset or measured result. Build an offline, seeded **plausibility stress suite** with no synthetic expert-design labels. Separate source-backed anchors and optional empirical resampling from deliberately balanced coverage, contradictions and extreme inputs. The suite measures structural validity, physical accounting, conditional behavior, uncertainty handling and reproducibility; it cannot establish installer agreement, German population performance or optimal sizing.

Read-only basis: `AGENTS.md`, `docs/HANDOFF-CODEX.md`, `PLAN.md` §§6/10, R2/R3/R5, `services/engine/tests/policy_synth.py` and `packages/contracts/openapi.json`. No confidential dataset, private rows or environment files were inspected. Only this report is delivered; commands and schemas below are proposed interfaces.

## Findings

### 1. Evidence and distribution policy

Use these explicit evidence classes on **every generation parameter**:

| Class | Meaning | Allowed interpretation |
|---|---|---|
| `empirical` | Distribution calculated from a pinned, licensed public artifact with documented filters and units | Describes that source cohort only |
| `source_anchor` | Published reference value or model profile, without its joint household distribution | Plausibility anchor, not a fitted probability law |
| `analyst_coverage` | All quotas, ranges, probabilities and perturbations proposed below | Stress coverage only; no prevalence claim |
| `unverified` | Semantics, access or evidence not resolved | Disabled from empirical mode; retain as a labelled research gap |

Opened primary evidence supports the following limited uses:

- **Household demand:** Stromspiegel's SFH table gives annual electricity without electric DHW of **1,800 / 2,700 / 3,500 / 3,800 / 4,500 kWh** for 1–5 people, and **2,100 / 3,200 / 4,100 / 4,700 / 6,000 kWh** with electric DHW. These are table reference values, not a microdata distribution. The same page gives a contradictory 2-person SFH value of 3,500 in its introductory prose; preserve this discrepancy and do not blend the values. [S1](https://www.stromspiegel.de/stromverbrauch-verstehen/stromverbrauch-im-haushalt/)
- **Existing PV/storage sizes:** the opened MaStR snapshot is version `2025-02-09-unboxed`, processed with open-MaStR v0.14.5; it warns of duplicates and states DL-DE-BY-2.0 attribution. No residential distribution, capacity quantile or household linkage was calculated here. [S2](https://zenodo.org/records/14843222)
- **Seasonal heat/COP shapes:** When2Heat `2023-07-27` supplies simulated national hourly profiles and distinguishes space/water heat and floor/radiator COP. Its heat series use MW; normalized national shapes are scenario inputs, not household peak loads or measured household distributions. It is CC BY 4.0 and documents corrected floor/radiator labels. [S3](https://data.open-power-system-data.org/when2heat/2023-07-27/README.md)
- **PV scenario dimensions:** JRC PVGIS exposes location, tilt, azimuth, installed kWp, hourly data and TMY. Its off-grid interface uses Wp/Wh, so a common unit assumption across PVGIS interfaces is unsafe. No fixed German annual-yield constant is asserted. [S4](https://re.jrc.ec.europa.eu/pvg_tools/en/)
- **Sizing uncertainty:** DIN Media discusses determining heating load and planning requirements; annual energy alone is insufficient for this suite to certify final installation sizing. The suite deliberately avoids turning the R3 annual-energy shortcut into a target HP label. [S5](https://www.dinmedia.de/de/themenseiten/nachhaltiges-bauen/heizen/waermepumpen)

**Minimum viable version:** use the source anchors and analyst coverage below. Set `empirical_enabled=false`. Do not call a lognormal around an anchor an empirical distribution. Future empirical adapters must pin artifact hash, licence, denominator, filters, missing-value rules, capacity meaning, duplicate handling and extraction script hash before enabling. For MaStR, distinguish operating rooftop units from other PV; a size filter alone does not prove a single-family home. Sample existing PV and storage marginals separately unless a documented household linkage exists. A registry asset is an existing input here, never simultaneously a target output.

### 2. Cases, conditioning and units

Generate latent scenarios first, then observed intake. Preserve both in the harness, but send **only observed intake** to the engine. Latent values specify known omissions/contradictions, never a hidden correct proposed system.

All distributions in this table, except the explicitly attributed demand anchors, are **analyst-selected coverage**. `U[a,b]` is continuous uniform; discrete sets are balanced deterministically. Draw within bands using stratified ranks with a seeded shuffle; round energy to 1 kWh and capacity to 0.1 in its stated unit. Do not round whole-case variables to catalog steps.

| Dimension | Proposed draw / conditioning | Mapping and guard |
|---|---|---|
| Occupancy + appliance demand | Balance persons 1–5 and electric-DHW yes/no. Let `m` be S1's corresponding table anchor; draw multiplier `U[0.6,1.6]`, appliance demand `m × multiplier`. Separate tail pool: 500–1,000 and 10,000–30,000 kWh/year. | `persons`, `demandKwh`; electric-DHW is harness metadata because contract has no such field. Multiplier and tails are not measured variance. |
| Electricity boundary | Default scenarios use appliance/DHW electricity excluding EV and HP. Dedicated ambiguity cases mark bill as whole-home/import-only/unknown. | Store `demand_boundary`; API cannot express it. Require assumption disclosure or clarification for ambiguous bills; prevent unannounced double counting. |
| Heating | Balance `Gas`, `Oil`, `Heatpump`, `OtherRenewable`, `OtherNonRenewable`, `Unknown`; include fossil planned-switch true/false. | Exact `heating.type` spelling includes **`Heatpump`**. Unknown is not fossil. |
| Useful heat | Conditional on heating scenario: area `U[70,250]` m²; choose independent intensity band 30–70, 70–140, or 140–250 kWh/(m²·year), balanced; `Q=area×intensity`. Renovated old-home cases occur in every age band. | `building.sqm`, `heating.heatDemandKwh`; ranges are stress assumptions, not IWU classes or W/m² design loads. |
| Fuel and existing HP electricity | When useful heat and fuel are both observed, draw explicit seasonal efficiency `U[0.65,0.95]`, set fuel=`Q/efficiency`; existing HP scenario uses seasonal performance `U[2,5]`, electricity=`Q/performance`. | `heating.fuelKwh`, `hpElecKwh`; thermal vs electrical kWh retained. Efficiencies are scenarios. Do not infer a target `heatPump.kw` from either formula. |
| Fuel cost | Either omitted, or generate from separately retained synthetic fuel price and fixed charge: cost=`fuel×price+fixed`. Price `U[0.06,0.20]` €/kWh and fixed `U[0,300]` €/year. | `heating.costEurYear`; price/fixed charge absent from API, so euros alone cannot reveal unique fuel consumption. Include this as an abstention case. |
| EV | Balance absent/current/planned; current or planned draws km `U[0,30000]`, independent efficiency `U[0.12,0.30]` kWh/km and home share `U[0,1]`. Planned year fixed relative to `as_of`, not wall clock. | `ev.has`, `kmPerYear`, `plannedYear`, `smartCharging`. Efficiency/home share are simulation metadata, not supported API keys. EV energy=`km×efficiency×home_share`, added once. |
| Existing assets | Balance none/PV only/PV+storage/storage only. PV `U[2,25]` kWp; storage `U[2,25]` kWh; wallbox absent or 11/22 kW. Trusted true/false balanced. | Nested `existingPv`, `existingStorage`, `existingWallbox`; storage-only is a deliberate retrofit/unsupported-use probe, not automatically physically impossible. New output vs total-asset semantics must be declared. |
| Roof | Balance unconstrained (`roofMaxModules` omitted), zero, tight 4–12, medium 13–30, large 31–60 modules. Balance supported roof enums; south/east-west orientation scenarios. | `building.roofMaxModules`, `roofType`, `orientation`. Integer module cap is explicit and never inferred from desired output. Missing roof is not zero roof. |
| Building/location | Balance years 1930/1975/1995/2015/2025 independently of renovation metadata. Three synthetic German city-center coordinates, fixed in manifest; outside-Germany coordinates separate. | `builtYear`, `location`; no real address. Unsupported geography must disclose fallback. No geographic population weighting. |
| Tariff | Price bands `U[0.15,0.25]`, `U[0.25,0.40]`, `U[0.40,0.60]` €/kWh; escalation 0/0.03/0.08 as fractions/year; flex true/false balanced. | `priceEurKwh`, `priceEscalation`, `flexTariff`; negative/zero price handled separately. No 2026 market-price distribution is claimed. |
| Installer/profile | Run each base over two configured installer IDs and an unseen ID; balance `H0`, family, home-office, senior only if supported. | Do not assume `synthA/synthB` load real production catalogs. Record unsupported identifiers and explicit global fallback; freeze catalog identity. |

Do not independently draw all components and hope they are plausible. Order: occupancy/DHW → appliance load; building/renovation scenario → useful heat → optional fuel/HP electricity; EV state → driving/charging metadata; existing assets → trust/age metadata; roof/location → profile choice; then observation/missingness. Catalog, policy predictions and signed design labels never condition the generator. Break these dependencies only in the labelled contradiction pool.

For optional profile scenarios, pin an offline PV artifact and normalize a chosen heat-space shape to its supplied annual useful heat. Keep DHW separate and avoid adding it twice. Calculate electricity as `sum_t(Q_t/COP_t)` with matching thermal/electrical boundaries, not annual heat divided by arithmetic mean COP. Validate time index, leap-year length, energy integration and timezone explicitly. Use distinct held-out public profile IDs/years for development and final synthetic suites. No online fallback is allowed during a scored run.

### 3. Deterministic pools and observation corruption

Proposed per-suite budget: **240 ordinary coverage bases + 120 missing/default bases + 120 boundary/contradiction bases + 120 metamorphic pairs = 720 requests** before simulator probes. Both members of a pair count as requests, but one pair is one metamorphic denominator. Allocate exact counts before sampling; report the resulting realized counts.

Minimum overlapping segment quotas across the 240 ordinary bases: ≥30 each heating type; ≥60 each EV absent/current/planned; ≥40 each existing-asset category; ≥30 each roof-cap band; ≥30 trusted and ≥30 untrusted asset cases. A deterministic covering-array assignment should satisfy these quotas and pairwise combinations where feasible. Quotas overlap and are not prevalence estimates. Fail generation if quotas cannot be met; do not quietly shrink coverage.

The 120 observation cases comprise 30 independently masked, 30 conditionally masked (EV km only among EV cases; fuel only among fossil cases; asset detail among asset-present cases), 30 placeholder cases, 30 all-default/minimal cases. These mechanisms are experiments, not estimates of real missingness. For placeholders use 4,500 kWh plus separately identical genuinely entered 4,500 values with provenance `entered`; compare with omitted demand and provenance `installer_default` / `national_default`. Frequency or value equality alone cannot determine a placeholder.

Respect the observed schema: `installerId` is required; demand defaults to 4,500, price to 0.32, escalation to 0.03; `demandKwh` is not nullable. Nullable nested fields permit explicit null; omitted nonnullable fields exercise defaults, explicit null there is a negative validation case. `ev.has` is boolean, so unknown EV is represented by omission plus external missingness metadata, not `has:null`. Test that default false is not presented as confirmed absence. Provenance confidence lies in [0,1]. Do not add synthetic metadata as unknown intake fields.

Allocate the 120 boundary cases as 40 malformed/type/domain probes, 40 finite extremes and 40 cross-field conflicts. Required probes include:

- Each numeric field at zero, a small positive value, negative, and applicable upper stress boundary; demand 0/200,000/4,500,000 kWh, negative km, 100,000 km, roof cap −1/0/1, future build year, latitude 100, and negative asset capacity.
- Unit corruption ×1,000 and ÷1,000 on demand/PV/storage/HP; W vs kW and cents vs euros. Preserve intended units in harness only; require rejection or explicit out-of-scope warning, without silent normalization based solely on size.
- `ev.has=false` with positive km; HP heating with fossil fuel and contradictory HP electricity; heat demand exceeding positive fuel input under a declared boiler-efficiency scenario; untrusted PV with implausible capacity; storage-only; unknown installer; unknown roof/heating enum; omission of required installer; invalid lock name.
- Missing/null/empty object distinctions, unknown extra key, string instead of numeric, invalid JSON `NaN`/`Infinity` tokens (raw transport tests, never JSONL numbers), valid JSON very large finite values. Extreme finite numbers still require controlled handling.

Current OpenAPI lacks many physical minimum/maximum constraints; successful schema parsing is not proof of domain validity. Freeze expected behavior per case **before** running models: `accept`, `reject`, or `review`. For invalid transport/schema require a controlled 4xx; for finite extreme/contradictory but schema-valid intake require 4xx or an explicit relevant warning with a bounded draft. Never accept a 5xx as abstention.

Expected abstention means a declared `review` state in the harness, backed by engine flags/provenance and a concrete missing input or conflict. Current API has flags but no dedicated abstention field. Report this limitation and define a versioned semantic mapping of existing codes; don't invent codes or map arbitrary prose after observing results. All-default heating/roof/fuel, incompatible locks, unknown asset boundary and cost-only heat evidence must not produce an unqualified install-ready claim. Abstention does not excuse malformed, physically invalid or lock-breaking output.

### 4. Independent checks, scores and hard gates

The existing `policy_synth.py` explicitly generates fake training-shaped data and warns never to report numbers from it. It creates HP labels from heat/2,000 and catalog snapping, PV from total demand, and battery from PV. **Do not use those generated labels, equations or scoring helpers as the expected design for this suite.** Generate intake only. A separate checker may use public catalog metadata and physical identities; it must not call the optimizer, reuse its chosen candidate or ask the same simulator to certify itself.

| Check family | Independent assertion / precondition | Severity and denominator |
|---|---|---|
| Response/units | Contract-valid JSON; finite numeric outputs, nonnegative physical capacities; positive integer module count for present PV; `kwp=modules×moduleWp/1000` within `max(1e-6,1e-6×kwp)` kWp. Null metrics stay null, not fabricated zero. | Hard gate; all accepted response designs, including alternatives; report cases affected and designs checked. |
| Feasibility | New PV respects explicit roof cap. Battery/HP/product IDs match frozen catalog definitions at stated units; no inferred manufacturer compatibility from matching capacities. Lock values/presence equal supplied valid current design; invalid lock/current combinations reject or flag conflict instead of silently changing. | Hard gate for documented constraints; denominator eligible designs / locked components respectively. Missing catalog makes check blocked, not passed. |
| Structural gates | New HP only for Gas/Oil/OtherNonRenewable, never an additional HP for `Heatpump`; existing-wallbox duplication and new-vs-total asset accounting checked against declared semantics. Conflicting locked requests must surface conflict. | Hard gate for unambiguous cases; denominator eligible designs per gate. Report semantic ambiguity separately. |
| BOM | Per-module quantities equal proposed module count, component lines agree with proposal, totals recomputed independently with declared VAT/rounding convention. | Hard gate where BOM exists and semantics specified; missing required BOM is its own failure. |
| Energy bounds | Self-consumption/autarky in [0,1]; nonnegative import/export/yield; zero-PV/no-storage/no-other-source toy yields zero PV energy and no solar savings. Undefined zero-denominator ratios may be null or explicitly documented zero. | Hard gate for defined metrics; count each metric and cases affected. |
| Conservation | Independently sum hourly balance and storage ledger: `PV+import+discharge=load+export+charge+curtailment+other_losses`; `ΔSoC=η_charge×charge−discharge/η_discharge−standby`. Define AC/DC boundary so losses appear once. Check SoC bounds and start/end inventory; residual ≤`1e-6×max(1,total_energy)` kWh. | Hard gate for instrumented trajectories only. Typical-day means cannot certify annual conservation; unavailable hourly trace is blocked coverage. |
| Exact toy physics | No-battery fixture: import=`sum(max(load−PV,0))`, export=`sum(max(PV−load,0))`; zero load/PV, constant load, isolated impulse and day/night shifted PV. Use hand-computable 2–24-step traces, zero losses then explicit known losses. | Hard gate; denominator supported toy scenarios. A test seam may be needed; no arbitrary profile injection API is claimed. |
| Offline/replay | Same seed/config/artifact hashes generate identical ordered JSONL. Repeated engine calls match canonical content excluding declared volatile latency/request IDs; network disabled and no LLM credentials. | Hard gate; all replayed requests. Any attempted network dependency is a failure, even if cached success masks it. |

**Conditional metamorphic pairs:** freeze all unmodified intake, locks, catalog, profile, weather, tariff and simulation parameters; record each change and its preconditions.

- Increasing fixed-design PV generation with no battery/curtailment cannot increase import under pointwise energy balance; increasing fixed load cannot decrease import. These test `/simulate` or the simulation seam, not the selected design.
- Increasing usable battery capacity cannot worsen the **best feasible** import objective when previous dispatch stays feasible, terminal SoC constraints match and grid arbitrage/standby changes are absent. Do not impose that theorem on a different greedy dispatch or on economic NPV; use diagnostics there.
- Demand↑ → PV proposal nondecrease is a declared PLAN product expectation, not a physical law for a coupled economic optimizer. Run unlocked pairs inside one supported installer/roof/profile regime with fixed candidate catalog, no budget/constraint changes, no existing-asset ambiguity. Report failures separately as product-policy diagnostics until the owner freezes this expectation as a gate. Do not require battery monotonicity as EV or HP is added.
- EV absent→present with feasible nonexisting wallbox should not lower wallbox propensity under the declared PLAN policy. If probability is not exposed, test observable wallbox behavior and report probability check unavailable; existing wallbox and future-EV cases form separate segments.
- All valid locks remain identical across demand/EV/heat edits. Shrinking roof cap cannot produce modules above the new cap; it need not preserve all other proposed sizes. Key-order changes preserve outputs; deleting genuinely unknown extra fields preserves outputs only when the agreed contract ignores them.
- Restoring a withheld fact measures sensitivity and correct provenance, not accuracy gain without real labels. Confidence need not narrow in every single case; missingness-vs-complete comparisons are diagnostics, not proof of calibration.

For each rule publish `{eligible, pass, fail, blocked, not_applicable, case_ids}` and eligibility reasons. Eligibility is assigned from input/preconditions, not whether output looks favorable. Expected accepted cases that crash, reject unexpectedly or omit a required metric count as failures, not exclusions. `reject` cases score controlled rejection, with invalid physical drafts a failure. For `review`, report **review sensitivity = correctly flagged / predeclared review cases** and **false-review rate = flagged / predeclared ordinary cases**; do not maximize abstention alone.

Publish per-pool and per-segment counts and rates with denominators: heating, EV state/km missing, demand band, roof cap/missing, existing assets/trust, installer known/unseen, provenance/default, input validity and profile family. Pairwise coverage matrix reports present/required combinations. No population-weighted overall accuracy or synthetic Expert Match Score. An optional descriptive `plausibility_pass_rate` is cases satisfying every applicable structural/physics check divided by all expected accepted cases, separately by pool; blocked required checks make the result **incomplete**. Report soft policy diagnostics separately.

**Release decision:** zero critical failures in structural/units/locks/physical identities/offline determinism; 100% required strata generated; zero blocked critical checks for a claimed scope. These are proposed engineering thresholds, not empirically calibrated safety guarantees. An attractive mean score cannot override one hard-gate failure. Catalog ratios such as battery≤1.5 kWh/kWp, inverter sizing bands, cycles/year targets and heat-load heuristics are policy flags/diagnostics unless separately justified for the exact product and operating condition; they are not universal physics gates.

### 5. Reproducible artifact and run contract

Proposed implementation interfaces (not existing commands):

```text
generate_cases --spec spec-v1 --split dev --seed 110701 --offline --out cases.jsonl
check_cases --cases cases.jsonl --manifest evidence.json --engine localhost --out report.json
```

Use an explicitly pinned PRNG algorithm/library version, deterministic sorting and per-family sub-seeds from SHA-256(`spec_version|suite_seed|family|base_id`) interpreted as an unsigned integer. Do not use Python's process-randomized `hash()`. Persist generated cases, interpreter/package versions and hashes; fixed seed alone is insufficient across dependency changes. Set `OFFLINE=1`, block outbound networking and fix `as_of=2026-11-07` for planned-year logic. Missing public artifacts fail setup; never fetch live during generation/checking.

One valid case record, using the **current nested contract**:

```json
{"case_id":"dev-ordinary-0001","base_id":"dev-b0001","split":"dev","pool":"ordinary","tags":["gas","no_ev","roof_tight"],"request":{"inputs":{"installerId":"CONFIGURED_INSTALLER_ID","demandKwh":3800,"persons":4,"priceEurKwh":0.32,"ev":{"has":false},"heating":{"type":"Gas","heatDemandKwh":18000},"building":{"roofMaxModules":12},"provenance":{"demandKwh":{"source":"entered","confidence":1}}},"locks":[]},"latent":{"demand_boundary":"appliance_excluding_ev_hp","electric_dhw":false},"expectation":{"action":"accept","checks":["schema","units","roof","hp_gate"]},"pair":null,"evidence_ids":["S1","A-demand-multiplier","A-roof-quota"]}
```

Replace configured installer ID before freezing; it is a placeholder in this example. Additional harness fields: `spec_version`, `request_sha256`, `observed_mask`, `corruption` (field, original synthetic value, transformation), `pair={id,role,changed_paths,preconditions}`, and expected semantic reason IDs. `expected_design` / synthetic output labels are forbidden. `latent` is never included in engine requests, examples to the model, model fitting or scoring features.

Manifest `evidence.json` must include:

```text
suite: spec_version, split, seed, as_of, generator_commit/hash, config_sha256,
       prng, runtime_versions, contract_sha256, catalog_sha256, model_sha256,
       offline, requested/realized quotas, case_file_sha256
evidence[]: id, kind, title, publisher, url, release, accessed_at,
            license, artifact_sha256, local_artifact_id, units, population_scope,
            filters, retained_n, missing_rules, transformations, verified_status
parameters[]: name, value/range, evidence_class, evidence_ids, rationale
```

For anchors without downloaded artifacts, set artifact hash/local ID/retained count to null and explicitly say `landing_or_table_verified`; never fabricate hashes, sample counts or extraction results. Include every analyst parameter as an `A-*` entry with rationale and no empirical publisher. Report JSON includes engine/config versions, input counts, rule/segment tables, failures, abstention table, missing instrumentation, wall-time p50/p95 with hardware and each status. Performance latency is descriptive unless a separately frozen service target exists.

### 6. Holdout and anti-overfit protocol

1. Freeze spec, checker, parameter evidence, catalog and model before final runs. Keep all corruption siblings and metamorphic descendants with their `base_id`; no base/profile year crosses dev/final splits. Use disjoint synthetic seeds and disjoint public profile IDs where available.
2. Developers may iterate on a disclosed dev suite (`seed=110701`). Final synthetic seed and outputs stay with evaluator until model freeze; record the seed hash beforehand, reveal seed with final report. No policy fitting, threshold choice, catalog edits, default detection or generator-range selection using final failures or real test labels.
3. Fit any learned preprocessing/OOD thresholds on training only and choose settings on validation. This follows the primary scikit-learn guidance that test data must not drive model choices. [S6](https://scikit-learn.org/stable/common_pitfalls.html)
4. Keep real temporal expert-match evaluation entirely separate. Do not import raw labels into the generator or use a held-out expert's module count as a synthetic roof cap. PLAN's real-data oracle experiment must remain explicitly labelled upper-bound research, outside this suite.
5. Run real final test once after selection. If final synthetic failures prompt fixes, disclose that final suite as used for development; retain original failure report and evaluate the repaired version on a newly frozen, evaluator-controlled suite. Do not silently reroll a difficult seed or remove bad cases.
6. Sharing generator/checker code does not itself create independent evidence of model quality. Report specification coverage and known untested behaviors; no synthetic pass rate becomes a claim of expert accuracy, conformity coverage, actual savings or German market representativeness.

## Implications for our product

- Implement intake-only generation separately from the existing fake-labelled policy test helper.
- Ship balanced stress coverage first; enable empirical resampling only with verified artifacts and semantics.
- Make omission/default/provenance handling observable; 4,500 can be a genuine value.
- Freeze accepted/rejected/review expectations and semantic flag mappings before evaluation.
- Add a simulator test seam for hand-computable traces; mark annual conservation blocked until available.
- Preserve structural/physics hard gates independently of any aggregate score.
- Treat monotonic design preferences as conditional product checks, and assess fixed-design physics separately.
- Keep final synthetic robustness and real held-out expert agreement as separate evidence.

## Open questions / uncertainty

**UNVERIFIED:** empirical parameter distributions, final public-profile adapters, and the proposed checker's runtime behavior have not been established by this specification. Analyst coverage quotas are not measured German population frequencies.

- This report does not implement or run a generator, engine suite or statistical extraction. Every quota/range/threshold is a proposal; no new performance result is claimed.
- Current asset semantics, catalog availability, BOM quantity conventions, simulator instrumentation and existing warning codes require owner confirmation in implementation. The proposed report can expose a gap without modifying the shared API.
- Stromspiegel's table/prose discrepancy remains unresolved. The table anchors do not establish distributions for EV/HP-inclusive total bills.
- MaStR residential classification, PV/storage linkage and precise usable/rated semantics remain adapter gates. No public installation-size histogram has been fitted.
- WPuQ paper and Zenodo record could not be opened successfully in this pass. R2 remains a useful lead, but no WPuQ empirical parameter is marked newly verified here. No public source has established a full German joint distribution over all intake fields and expert bundles in this report.
- Synthetic conditional checks cannot certify optimal economic choices, manufacturer compatibility, installation compliance or actual seasonal performance. Independent technical review remains outside this suite's evidence.

## Sources (numbered list: title — publisher — date — URL)

All following URLs were opened **2026-11-07**; undated pages may change. No quotation exceeds 15 words.

1. **S1 — Stromverbrauch im Haushalt**, including SFH annual-consumption table — Stromspiegel / co2online — undated, page includes 2024 context — [URL](https://www.stromspiegel.de/stromverbrauch-verstehen/stromverbrauch-im-haushalt/).
2. **S2 — open-MaStR [unboxed], version 2025-02-09** — Open Energy Family / Zenodo — published 2025-02-10 — [URL](https://zenodo.org/records/14843222).
3. **S3 — When2Heat Heating Profiles README** — Open Power System Data / Ruhnau and Muessel — 2023-07-27 — [URL](https://data.open-power-system-data.org/when2heat/2023-07-27/README.md).
4. **S4 — Photovoltaic Geographical Information System** — European Commission Joint Research Centre — interface last-update label 2025-10-10 — [URL](https://re.jrc.ec.europa.eu/pvg_tools/en/).
5. **S5 — Wärmepumpenanlagen: Planung, Installation und Betrieb** — DIN Media — undated — [URL](https://www.dinmedia.de/de/themenseiten/nachhaltiges-bauen/heizen/waermepumpen).
6. **S6 — Common pitfalls and recommended practices: data leakage** — scikit-learn documentation — current, undated — [URL](https://scikit-learn.org/stable/common_pitfalls.html).
