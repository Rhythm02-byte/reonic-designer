# Rhythm blind spots and opportunities

Final research synthesis, **2026-11-08**, branch `next`. No product change or commit is implied. Every implementation outside the Codex allowlist is an owner request.

## Final judge decision

The parent agent reviewed the generator pool, all canonical objections/dispositions, rubric/matches, source audit, CodeGraph feasibility notes and ceiling results. **Accept the original rubric as a deadline-priority list, then promote I13 to first after measured stress failures**, preserving every original Elo/match and all three wildcards. Final top five: I13, I23, I02, I17, I03; HP evidence scope is sixth. Small Elo gaps are not meaningful. Do not sum every idea into an implementation commitment. Observed bounded-output and metric-availability defects, then claims/replay/provenance, outrank new learners before freeze because they are reviewable and reduce demo risk. Model expected gains remain UNKNOWN pending registered experiments.

Amend I23: also remove the unqualified **test scored once** statement. The parallel read-only jury review (`research/jury/review.md`) found at least three recorded test-scored runs; repeated access does not prove test-driven tuning, but is inconsistent with once-only wording. Ordinary planner artifact training may include all years; label synthetic workflow examples as workflow, and use a verifiably cutoff-trained artifact for an unseen comparison. These are requests to Engine/Eval/Pitch, not edits performed by this task.

The generator and critic were separate agents and exchanged arguments. The parent is the final synthesis judge, not an independent domain expert. The 435 pair decisions remain rubric-derived by the critic; the parent accepts their prioritization, not their numerical objectivity. Claude reviews both evidence and implementation.

## Post-tournament measured evidence and final priority

The parent proposed and the independent critic accepted promoting **I13 from original rank 8/Elo1652.2 to final rank1**. This is a declared evidence-based override, not a rewritten tournament result. [Critic follow-up](critic/post-evidence.md) records the argument, uncertainty and acceptance conditions. All original 435 match records and scores remain intact.

The DEV suite found one negative PV-capacity output, 39/70 strict displayed-module arithmetic failures, and 8/347 missing required metric fields in the full-response follow-up. These counts describe distinct checks: 39 precision inconsistencies are not 39 impossible installations; 120 missing relevant review warnings are not 120 physical violations, and 58 review cases are adapter-blocked. See [stress handoff](ceiling/STRESS.md) and `eval/external/results.json` for final run provenance and scoped denominators. No model was changed or tuned to these failures. Parent final judge: prioritize a narrow owner repair/validation before adding claims or a learner.

The additional-input audit found current model omissions but little available data: occupancy/area/build-year each occur in 6/1268 development rows. Expanding the grouping adds only one empirical oracle match (62.22%→62.30%). This does not establish a universal accuracy ceiling or a hidden feature win. Field capture timing remains a leakage gate.

## Auditable process

The generator produced 200 raw ideas across 20 separately retained lenses, consolidated to 30 stable IDs. Its typical-team probabilities are subjective and uncalibrated. The critic sent a specific objection for every ID. The generator replied, accepting or amending all objections; the explicit post-debate disposition for each is retained in `tournament.json`. The critic acted as provisional pairwise judge; the distinct parent reviewed and accepted the prioritization above. Claude review remains pending. No fictitious human expert or independent third judge is implied.

`python research/creative/critic/rank.py` runs 435 head-to-head comparisons (every pair among 30). Each decision applies exposed weights: jury impact 35%, evidence available before freeze 30%, estimated build time 20%, demo safety 15%. Axes run from 0 to 5, higher better. Time is `max(0, 5*(1-hours/8))`; safety is five minus risk. A weighted difference smaller than 0.075 is a tie. Elo starts at 1500, K=24, logistic scale 400; twenty seeded match orders are replayed and averaged. This is **rubric-derived judgment**, not a learned quality estimator or independent proof. Match rationales and each idea's order range are retained. Identical or near-identical evidence/time estimates should not be interpreted as a meaningful rank difference.

The method is inspired by [AI co-scientist](https://arxiv.org/abs/2502.18864) and its [explicit auto-evaluation limitation](https://research.google/blog/accelerating-scientific-breakthroughs-with-an-ai-co-scientist/) (2025; accessed 2026-11-08). Our protocol does not reproduce its scientific experiments.

## Top 25 after the debate

`source-audit.md` supplies actual CodeGraph seams and primary URLs with access dates. A repo reference below is internal evidence, not an external fact. A conditional idea stays conditional even if it ranks above a ready-to-demo item. Category `UX` means a workflow/pitch proposal; **no new UI is authorized or implemented**.

| Rank / ID / Elo | Idea / category | Why the jury cares | Evidence or source | Hours / risk | Owner / first concrete step |
|---|---|---|---|---|---|
| 1 · I13 · 1652* | Observed structural/metric failures · risk | A negative draft or silent simulation loss undermines the demo before any accuracy claim. | `ceiling/STRESS.md`, final720-case DEV receipt and 24-response subset; original Elo preserved. | Engine 2–4 + Eval 1–2 / medium, uncertain | Engine/Eval: reject negative domain inputs, preserve module arithmetic, handle empty simulation candidates and assert required metric availability; rerun frozen failures. |
| 2 · I23 · 1733 | Claim hygiene · pitch | A false overall-win or labor-saving claim can defeat the honest PV result. | `docs/PITCH.md` table vs Q&A; `docs/BACKLOG.md` current latency note. | 0.5 / low | Pitch: replace superiority with clear PV gain/whole-design tie; qualify oracle and elapsed-time figures; remeasure latency. |
| 3 · I02 · 1718 | One-question rescue · pitch | Demonstrates a useful action despite imperfect prediction. | `ask_next.py:203`, existing `AskNext.tsx`; oracle qualification in PITCH. | 0.5 / low | Pitch: rehearse frozen synthetic missing-demand→entered-demand interaction and separately cite the measured masking result. |
| 4 · I17 · 1684 | Offline replay receipt · risk | Makes the proof rerunnable and protects the demo from artifact drift. | Store/model load and external runner seams; future report until implemented. | 1 / low | Engine/Eval: capture config/model/code hashes, package versions, offline mode and repeated-output comparison. |
| 5 · I03 · 1661 | Genuine 4,500 vs default · data | Exposes a realistic data defect without pretending every 4,500 bill is fake. | `_entered` respects provenance; `design_policy:448` warning ignores it. | 1.5 / low | Eval: run identical synthetic values with entered/default/omitted provenance; send engine owner the warning discrepancy. |
| 6 · I20 · 1660 | HP evidence scope · pitch | Prevents sparse-label physics heuristics being sold as expert learning. | PITCH says HP ~2%; schema/site-input limitations; no new estimate. | 0.5 / low | Pitch: describe physics-led draft and site inputs still needed; make no standards-compliance claim. |
| 7 · I24 · 1653 | Frozen scoring sensitivity · risk | Shows metric choice is not selected to manufacture a win. | `eval/metrics.py:98`; ceiling workstream. | 1 / low | Eval: freeze any-option and ±1-module definitions, report all versus baseline, keep primary score. |
| 8 · I09 · 1652 | Paired win/loss audit · model | Explains where assistance helps and where habit wins. | Existing validation split and `policy_metrics`; no 2026 tuning. | 1 / low | Eval: aggregate model-only/baseline-only/both/neither hits with paired uncertainty on validation. |
| 9 · I05 · 1587 | Signed-option ambiguity · data | Label interpretation may matter more than a larger learner. | ETL reconstruction plus mentor confirmation still required. | 2 / low | Eval: audit aggregate option ambiguity, request signed-option semantics, never replace primary with easiest option. |
| 10 · I04 · 1573 | Expert vs simulator ledger · feature | Shows an installer habit and a separate assumption-driven opinion. | `attach_metrics`, `economic_battery`, frozen successful scenario receipt. | 1.5 / medium | Engine: capture candidate sizes, tariff/profile assumptions and disagreement; do not label a real-world optimum. |
| 11 · I19 · 1562 | New vs total retrofit audit · risk | Prevents double-counted existing PV/storage and misleading incremental economics. | Engine conversion seams; [Reonic existing-system documentation](https://docs.reonic.com/docs/en/offers-simulation-cat-energy-flows), updated 2026-09-30, accessed 2026-11-08. | 2 / low | Eval: agree synthetic existing/new fixtures with owner before any behavior change. |
| 12 · I25 · 1556 | Avoid the auto-layout race · pitch | Positions the learned decision aid in a mature workflow. | [Aurora roof API](https://docs.aurorasolar.com/reference/ai-roof), [OpenSolar Auto Design](https://www.opensolar.com/auto-design/), accessed 2026-11-08. Vendor claims only. | 1 / low | Pitch: say learned installer choices + asking + auditable proof; other-team scores/methods remain UNVERIFIED. |
| 13 · I16 · 1555 | Buying vs physical need · risk | Separates what was sold from a causal or engineering optimum. | Signed-project sampling; PITCH wallbox/EV mismatch. | 1 / low | Pitch: label imitation target and missingness; do not infer no EV from absent flag. |
| 14 · I06 · 1547 | Tolerance collision bound · model | Tests the ceiling story without declaring a universal 25% cap. | Exact-input collision analysis from workstream C. | 2 / low | Eval: publish feature grouping, tolerance intersections, singleton denominator and empirical-bound limits. |
| 15 · I01 · 1496 | Survey-needed checklist · UX | Turns unknown roof/budget into an honest handoff. | Existing provenance/flags; [Reonic quick indicative planning](https://docs.reonic.com/docs/en/offers-plan-pv-quick-planning), updated 2026-09-09, accessed 2026-11-08. | 0.5 / low | Pitch: draft a text checklist of missing evidence; no invented readiness threshold or new UI. |
| 16 · I18 · 1492 | Installer transfer audit · model | Makes transfer evidence assessable rather than overstated. | Two-installer scope; `INSTALLER_UNKNOWN` pooled fallback. | 2 / low | Eval: report each leave-one-installer direction and counts; avoid universal unseen-installer calibration. |
| 17 · I28 · 1484 | WILDCARD: show median winning · pitch | Demonstrates intellectual honesty while explaining workflow value. | Fixed synthetic/validation counterexample, not cherry-picked test superiority. | 0.75 / medium | Pitch: keep as rehearsed Q&A fallback; show the next useful question or constraint. |
| 18 · I11 · 1444 | Qualified MaStR percentile · data | Adds independent practice context with a declared cohort. | Workstream A only if actual extraction succeeds; official register IDs for linkage. | 1.5 / medium | Eval: print sample year/filter/count and rooftop proxy; never call size popularity correctness. |
| 19 · I12 · 1437 | Measured-profile gap · data | Makes optimistic self-consumption assumptions visible. | Workstream A measured artifacts only; fixed-design comparison. | 2 / medium | Eval: compare named household-year profiles, report gap and coverage, no population confidence interval. |
| 20 · I27 · 1437 | Collect roof and budget · data | Proposes a testable path beyond the current missing inputs. | PITCH oracle motivates collection but does not measure its prospective gain. | 2 / low | Eval: freeze a future prospective collection protocol; no gain claim before data. |
| 21 · I14 · 1430 | Selective risk/coverage · model | Shows which drafts can be supported by observed validation evidence. | Validation-only calibration; no transfer guarantee. | 3 / medium | Eval: freeze threshold on pre-2026 folds and show coverage/error tradeoff; defer deployed threshold. |
| 22 · I21 · 1402 | One-more-module scenario · feature | Gives a concrete constraint sensitivity rather than fake precision. | Existing PV sweep/roof cap; coupled outputs may be nonmonotone. | 2 / medium | Engine: compare one frozen home under adjacent module caps; no shadow-price theorem. |
| 23 · I10 · 1380 | Sourced savings scenarios · feature | Shows dependence on tariff/profile choices. | Only cited, frozen bounds are acceptable; no new measured evidence yet. | 3 / medium | Engine: deterministic scenario envelope; defer if source bounds unavailable, never call a confidence interval. |
| 24 · I15 · 1349 | Question value per minute · model | Could prioritize a real qualification call rather than a large price swing alone. | Current score is sensitivity × price swing; user-time costs unmeasured. | 4 / medium | Eval: propose timed planner study; no accuracy/minutes-saved claim from hypothetical weights. |
| 25 · I08 · 1348 | Tolerance-mass classes · model | Optimizes hit probability at supported sizes rather than squared error. | Already registered in `research/experiments.md`; expected gain UNKNOWN. | 5 / medium | Engine: after freeze, evaluate registered classifier on fixed pre-2026 folds and adoption gate. |
The ranking is not a recommendation to build all 25. Final I13/I23/I02/I17/I03 total an estimated **6.5–9.5 combined owner hours**, with uncertainty and no new UI. I13 repair scope is 3–6 hours across Engine/Eval; the original 2-hour estimate covered the harness, not repairing subsequently observed defects. Start with the smallest bounded-output and missing-metrics repairs. This is not a commitment that every change fits before freeze. I05/I06/I13 are high-value evaluation follow-ups, partly delivered by the parallel workstreams. Availability of an owner, real extracted artifacts, and the final demo remain stronger constraints than tiny Elo differences.

## Top five mini-specs

### I13 — Bounded drafts and visible simulation availability

**What/how:** Ask Engine to reject or explicitly bound negative/contradictory physical inputs; preserve PV modules×moduleWp arithmetic at serialization; handle empty/nonfinite simulation candidate sets without silently losing required metrics. Keep review-code mapping work separate from physical defects. These are owner requests; Codex does not edit engine/web. **Measure without overfitting:** retain the original failed DEV receipt, add targeted independent fixtures, freeze artifact/config/source hashes, rerun unchanged DEV checks, then ask Eval to run a newly held independent seed/profile allocation. No model/metric/2026 tuning. **Demo moment:** the same invalid roof input is controlled, and every shown savings metric has successful simulation provenance. **Cut line:** no broad optimizer rewrite, UI, universal warning or relaxed identity check chosen after failures. If a narrow repair cannot be validated, explicitly limit the demo claim/path; do not declare stress passed. Estimated 2–4 Engine plus 1–2 Eval hours, uncertain.

### I23 — Claim hygiene

**What/how:** Prepare precise replacement language for the Pitch owner: clear PV gain, whole-design tie; elapsed request-to-offer time is not labor effort; oracle roof cap is not a measured roof-survey result; final-artifact latency needs a fresh receipt. **Measure without overfitting:** an evidence checklist linking every displayed figure to population, split, run/config and qualifier; this changes claims, not model selection. **Demo moment:** answer the median-baseline question before the jury asks it. **Cut line:** if the owner cannot update before freeze, retain the written request and say the qualifier aloud; never claim edits landed when they did not.

### I02 — One-question rescue

**What/how:** Use the existing Ask-next interaction on a frozen synthetic home with unknown demand, then enter a documented synthetic demand and show the resulting draft. Keep the separate published masking result labelled oracle and its denominator visible. **Measure:** interaction completes, entered provenance is respected, draft and locks remain coherent; no prospective accuracy gain is inferred. **Demo moment:** the tool asks for the missing bill fact instead of producing more confident prose. **Cut line:** if live engine latency/fallback is unreliable, use a rehearsed screen recording clearly labelled; do not present fixture output as live learned prediction.

### I17 — Offline replay receipt

**What/how:** Add a report beside the evaluation artifacts containing model/config/code hashes, runtime versions, offline flag and a canonicalized repeated-output check. This is an owner request/research artifact, not new product UI. **Measure:** identical artifact/config inputs reproduce aggregate outputs and no undeclared external dependency is needed; report attempted-network coverage separately. **Demo moment:** show Claude's rerun command and the receipt instead of asking the jury to trust a screenshot. **Cut line:** missing artifact or incomplete network instrumentation is reported blocked; a hash alone does not prove freshness or privacy.

### I03 — Provenance audit

**What/how:** Predeclare identical synthetic 4,500-kWh requests with entered, extracted, installer-default, national-default and omitted provenance. Inspect Ask next and the numeric-default warning. CodeGraph already shows different provenance treatment between these paths. **Measure:** a frozen behavior matrix, no fitting and no private test rows; don't automatically require identical model sizes where policy intentionally uses provenance. **Demo moment:** a genuine 4,500-kWh bill should not be called a confirmed fake default. **Cut line:** Codex reports the discrepancy and owner request; no unauthorized engine rewrite or untested new missingness model.

## Additional retained mini-spec: I20 — Heat-pump evidence scope

**What/how:** Write a short pitch/Q&A evidence statement that HP examples are sparse and the draft is physics-led, with site evidence still required. No new card/UI. **Measure:** every HP claim accurately distinguishes observed labels, engineering assumptions and unavailable evidence; no held-out threshold tuning. **Demo moment:** explain why the system asks about heat demand rather than claiming confidence from a tiny minority class. **Cut line:** if required site inputs are absent, do not imply an installation-ready or standards-compliant heat-pump design.

## Protected wildcards

These survive independently of Elo, preserving diversity rather than letting deadline feasibility erase it. [Doshi & Hauser](https://pmc.ncbi.nlm.nih.gov/articles/PMC11244532/), 2024-07-12, accessed 2026-11-08, motivates this precaution through a short-story experiment; it is not evidence about hackathon teams.

1. **I28 — Show the median winning** (rank 17): Q&A-only honest counterexample with a useful next action. Keep the opening focused; avoid cherry-picked held-out stories.
2. **I29 — Sell the information first** (rank 27, Elo 1308): future pitch-only survey qualification before an equipment quote. Information pricing and sales effect are untested hypotheses. Cut all prefreeze workflow changes.
3. **I30 — Uncertainty-expiry energy passport** (rank 29, Elo 1273): future versioned facts/assumptions receipt that expires when roof, tariff or household facts change. No deployment/export lifecycle work before freeze; privacy and maintenance requirements need separate design.

## Kill list

- New roof reconstruction or panel-placement UI: exceeds the authorized scope and competes with established vendor capabilities; no time to validate geometry or shading.
- LLM sizing or public APIs over project rows: violates the task's privacy and deterministic-sizing rules, regardless of creativity.
- Picking an easier metric or any offered option only when it makes us win: metric overfitting; report fixed sensitivities alongside the unchanged primary metric.
- Calling neighbor spread a proven 25% ceiling: omitted features and finite samples do not establish that bound.
- A new TabPFN/bundle/classifier default before the registered fold protocol: attractive but unmeasured; no numeric expected gain or rushed 2026 tuning.
- A general Pareto frontier from today's battery sweeps: no proof that all system candidates/objectives were searched, and no new UI allowed.
- Real-world economic optimum or guaranteed savings from a single simulator scenario: current assumptions and fallback paths cannot support that claim.
- MaStR attach rates from postcode matching, roof systems labelled verified residential, or market quantiles labelled expert accuracy: semantic shortcuts invalidate the outside check.
- Treating a good synthetic pass rate as expert agreement, economic value, legal compliance or population safety: report coverage and blocked instrumentation instead.
- Sales ROI from elapsed CRM days: elapsed waiting time does not measure planner labor, conversion uplift or realized financial value.

## Jury questions and honest answers

| Likely question | Answer we can defend |
|---|---|
| Why do you tie the installer's usual design? | Whole-design is an AND of four matches, and observed package habits dominate several components. We show a clear PV gain and a whole-design tie; missing roof/budget are plausible constraints, not a proven 25% universal ceiling. |
| Another team says it scores 25%. Are you worse? | Their score is UNVERIFIED until the same target reconstruction, temporal split, tolerance, option selection and test access rules are compared. We will compare on a shared frozen protocol. |
| Why not just use the median? | It is a strong baseline and sometimes the right answer. It does not itself ask which missing fact changes the draft, preserve planner locks, show local ranges, or distinguish installer practice from a simulation opinion. Those workflow benefits still need user validation. |
| Is asking the roof proven to add 12 points? | No. That experiment caps PV at the expert's own module count, so it is an oracle upper bound. A prospective survey trial is the next experiment. |
| Does the bill question double accuracy? | The published masking/oracle comparison shows sensitivity to restoring known annual demand under that evaluation. It is not a prospective randomized customer-question trial. Use the current run's exact numbers and denominator. |
| Are the confidence ranges a guarantee for this customer? | They are component-level calibration results on a stated sample. They are not joint bundle probabilities or a guarantee for a new installer or shifted population. |
| Does the economic battery prove experts oversell? | No. It is the best tested candidate under stated simulation assumptions, not observed customer utility or causal evidence. We expose the disagreement for the planner to discuss. |
| Are you building something Reonic does already? | Reonic already documents planning, packages, variants and energy flows. Our proposed contribution is learning its installers' observed choices, exposing limits and prioritizing missing information with a reproducible comparison. Product integration and value still require validation. |
| How do you know the labels are correct? | They are reconstructed from parts and inferred option selection; we document unit fixes and ambiguity. Mentor-confirmed signed-option semantics and sensitivity reporting are more credible than hiding uncertainty. |
| Does public data validate your model? | It validates a stated plausibility/profile comparison, not installer-bundle accuracy. Public measured profiles and register sizes answer different questions from signed-offer labels. |
| Does it generalize to every installer? | We have two installers and a pooled fallback. Two leave-one-installer directions are limited transfer evidence, not broad market calibration. |
| What is still unverified? | Other-team scores; a population performance ceiling; prospective time/conversion gains; economically optimal real-world sizes; unmatched register battery/PV links; any measured-profile/source coverage that A could not obtain. |

## Files and checks

- `source-audit.md`: opened primary sources, dates, method boundaries, repo seams and owner requests.
- `rank.py`: stdlib-only deterministic tournament replay; accesses no private data or engine.
- `tournament.json`: all 30 assessments, generator reply summary, judge decisions, rubric, 435 pair rationales, Elo/order ranges.
- `raw-pool-with-elo.json`: all 200 raw lens/probability records, mapped to canonical Elo. The generator's original pool is preserved unchanged.

Checked by running the replay and validating 30 unique candidates, exactly 435 distinct unordered pairs, zero-sum Elo around 1500, finite scores, 200 mapped raw records, and all three protected wildcards. This is research-process validation, not a product test. No private rows, product edits or commits.

## Method and morphological box

Distribution-first prompting is motivated by Zhang et al.'s Verbalized Sampling [S1]. The present probabilities answer the user's **typical-team likelihood** instruction, a pragmatic adaptation; they are not the model probability distribution in the paper and do not reproduce its experiment. The lens pools were kept separate until consolidation. Liang et al. motivate an adversarial critique rather than repeated self-reflection [S2]. The separate critic challenged every shortlisted candidate; the generator accepted the restrictions and sent explicit amendments. Elo-style tournament ranking is inspired by co-scientist, not an empirical estimate of business value [S3].

Si et al. found novelty and feasibility can diverge in an NLP research-idea study, which motivates our repository feasibility pass; their result does not establish energy-domain productivity [S4]. Doshi and Hauser studied short-story outputs and observed greater similarity with AI assistance; this is a diversity warning, not a universal theorem about teamwork [S5]. We retain wildcards even if they rank poorly.

| Axis | Options used to create combinations |
|---|---|
| Inputs | current facts; provenance; roof/budget; measured load; existing assets; artifact state |
| Learner | existing chain; bundle ranker; catalogue classifier; empirical CDF; fixed simulator; no new model |
| Objective | whole-design hit; selective risk; scenario economics; plausibility; invariant preservation; information value |
| UX (proposal only) | current Ask next; current approved alternatives; spoken survey checklist; replay report; future passport |
| Proof | fixed validation folds; exact collisions; aggregate paired discordance; public measured profiles; offline stress; prospective opt-in cases |

The ten explicit combinations are in the morphological-box lens in `ideas.json`; no claim is made that all Cartesian combinations are feasible.


## What other teams might do

Competitor products already advertise automated roof/layout/design workflows: Aurora's official AI page [S6], OpenSolar Ada [S7], and Reonic's planning platform [S8]. Enpal and 1KOMMA5 advertise connected household energy management [S9,S10]. These are vendor descriptions, not independent performance validations. We verified **no public comparison of their expert-bundle prediction accuracy** and cannot infer their training data or methods.

Our subjective scenarios for hackathon teams are tabular model + median baseline, an LLM wrapper, roof geometry, an energy optimizer, a polished proposal flow, or a “highest accuracy” slide. Their actual work and scores are **UNKNOWN / UNVERIFIED**. Differentiate through observable proof: tell the jury exactly where the model wins, show input evidence changes the workflow, and show a second-reader disagreement with assumptions. Do not claim competitors lack uncertainty, ask-next, or simulation.


# Ceiling and literature

Prepared 2026-11-08, Europe/Berlin. Workstream C. **No verified paper or competitor result establishes a better whole-design score on this challenge's data and metric. The rumoured other-team scores remain UNVERIFIED. Neither ~21% nor ~25% is a demonstrated information-theoretic ceiling.**

## What the existing claim does and does not establish

`docs/PITCH.md` reports 20.9% vs 20.6% on 325 held-out 2026 projects and a wide PV range within a broad consumption/no-EV segment. Those are repository results, not external benchmarks. Wide outcomes within a coarse segment are consistent with missing roof/budget, different product packages, target reconstruction errors, or remaining measured features. They do not isolate those causes and cannot upper-bound every function of the full inputs.

The new aggregate-only audit (`eval/external/ceiling/audit.py`) excludes 2026 from every analysis. It loads canonical parquet using the existing evaluation loader, freezes the current policy configuration, and makes no model-selection changes. Its empirical oracle permits a separate prediction for every **exact input-equivalence group**, and counts the greatest possible overlap of the four target tolerance regions. It permits arbitrary sizes and ignores catalogue/rule constraints, so it is optimistic. Unlike counting the most common exact output tuple, it permits an intermediate size to match multiple different labels.

**Interpretation:** an exact collision bound applies to this finite set and the named representation. Singletons can be memorized. It is not a held-out accuracy prediction or a population Bayes bound. A coarse bin summary applies only to functions restricted to those bins. No 2026 labels were used for the diagnostic or for choosing tolerances.

### Measured results (2026-11-08)

Run: `node scripts/py.mjs eval/external/ceiling/audit.py`. Tests: `node scripts/py.mjs -m pytest -q eval/external/ceiling` → **4 passed**. Full aggregate results and script/config SHA-256 are in `eval/external/ceiling/results.json`. The first attempt detected a floating-boundary mismatch between a permissive checker epsilon and the production metric; the checker was corrected to use the production comparison exactly, then the complete frozen analysis reran. No policy/model/config changes were made.

| Representation, offers through 2025 | n | Exact groups | Singleton rows | Rows in duplicate groups | Maximum empirical matches | Optimistic empirical bound |
|---|---:|---:|---:|---:|---:|---:|
| Canonical input columns | 1,268 | 547 | 450 | 818 | 789 | 62.22% |
| Expanded potentially pre-offer ETL fields (availability/provenance not certified) | 1,268 | 548 | 451 | 817 | 790 | 62.30% |
| Model base features | 1,268 | 546 | 448 | 820 | 788 | 62.15% |
| Served features including configured physics (installer prior redundant within exact groups) | 1,268 | 546 | 448 | 820 | 788 | 62.15% |
| Coarse installer/demand-500-bin/EV/heating (**diagnostic only**) | 1,268 | 120 | 49 | 1,219 | 490 | 38.64% |

Largest exact group: 220 projects. At least 479 empirical errors are unavoidable for any deterministic function of these canonical input columns on this particular finite set, even with arbitrary output capacities. Duplicate-only canonical bound: 41.44%. This supports ambiguity but **does not establish a ~25% ceiling**. The 450 singleton rows alone contribute 35.49 percentage points of the optimistic canonical bound through memorization. More useful deployment limits require held-out estimation and/or controlled annotation of missing inputs.

**Additional-input audit:** `build_projects` retains fields that `INPUT_COLS` omits. Adding the 12 potentially pre-offer fields below changes the finite-sample upper bound only to **790/1,268 = 62.30%** (548 groups, 451 singleton rows, 817 duplicate rows, largest group 219; duplicate-only bound 41.49%; at least 478 incompatible empirical labels). It adds just one oracle match. Most apparently useful building/occupancy fields are almost entirely missing, so “the model ignored roof-like features” is not a supported high-gain claim.

| Additional ETL field | Nonmissing / 1,268 development projects |
|---|---:|
| `load_profile` (raw profile label, already represented coarsely as `load_family`) | 1,268 |
| `base_price_month` | 0 |
| Existing PV build year / tilt / orientation | 17 / 17 / 17 |
| Existing storage build year | 8 |
| Existing wallbox charge kW | 4 |
| Heating annual cost / cost escalation | 25 / 0 |
| House area / build year / inhabitants | 6 / 6 / 6 |

These are aggregate non-null counts, not verified measurement quality. The export does not establish when a field was entered relative to the offer. Existing assets are particularly vulnerable to planned-system contamination, as the ETL's trust flags recognize; cost units also require the existing ETL safeguards. A future candidate must audit capture timing and legitimate planner availability before training. IDs, customer keys, offer/signature timestamps and output-derived flags are excluded from this expanded representation. The bound is still representation-specific; additional unrecorded roof/budget/site observations can change it. No predictive gain was tested from the extra fields.

Scoring sensitivity, same fixed served configuration/predictions, validation Q4 2025 (n=232; train n=1,036):

| Whole-design definition | Ours | Installer median B0 | Ours minus B0 |
|---|---:|---:|---:|
| Frozen primary relative tolerance | 24.14% | 17.67% | +6.47 pp |
| Relative PV tolerance OR one assumed 450 W module | 24.14% | 17.67% | +6.47 pp |
| Absolute ±450 W PV only, other targets unchanged | 7.33% | 13.36% | **−6.03 pp** |
| Any complete offered option, relative tolerances | 24.57% | 17.67% | +6.90 pp |

Across 20 random 80/20 splits of the 1,268 development projects, mean paired whole-design gap ± sample SD: primary **+1.02 ±1.68 pp**; absolute one-module **−0.49 ±1.70 pp**; any-option **+0.91 ±1.86 pp**. Thus a much stricter module metric can reverse the Q4 ranking; any-option makes little difference here. Neither alternative demonstrates an unambiguous overall winner. The relative-or-one-module definition adds no whole-design hits for these fixed predictions.

The four expanding-quarter primary paired gaps are +2.49 / +6.67 / +6.44 / +6.47 pp (Q1–Q4; n=241/225/202/232). **These are retrospective scoring diagnostics with the current configuration, which itself was chosen on Q4; they are not newly unbiased validation/model-selection evidence.** No alternative candidate was trained or selected by this audit. The protocol remains mandatory for future proposals.

Denominator audit, development cohort: 246/1,268 projects have multiple options; 87 primary PV sizes are “offered, unknown capacity”; no unknown primary battery/HP/wallbox capacities. These 87 score PV presence only, weakening the interpretation of “all sizes right.” Option-count histogram (count: projects): 1:1022, 2:196, 3:26, 4:19, 5:1, 6:2, 7:1, 10:1. Row identifiers and values were neither saved nor printed.

## Three methods worth testing

All expected gains below are **UNKNOWN on Reonic**. None is a promise of extra percentage points. Owner: Engine, evaluated by Eval. The existing `research/experiments.md` controls adoption: four expanding 2025 quarter folds; 20 fixed random 80/20 splits over offers through 2025; positive mean temporal whole-design gain exceeding one SD of the paired random gap; EMS loss at most one point; at most three preregistered settings; 2026 is the final exam. Settings proposed here must be copied into that owner's protocol **before** any candidate run; this audit does not authorize changing it.

| Priority | Method and concrete adaptation | Why it fits this repo | Frozen candidate settings to request | Measurement and cut line |
|---|---|---|---|---|
| 1 | Joint package retrieval with tolerance-aware decision: retrieve training homes, enumerate their complete PV/battery/HP/wallbox packages, choose the feasible package with maximum neighbour-weighted probability of the **whole** tolerance hit. Include a per-installer package-frequency fallback. | `Designer.design_batch_full` already chains targets; `Neighbours` already supplies nearby labels. The gap may be the joint decision objective rather than representation power. Independent component maxima need not maximize their conjunction. | k=25, top 10 packages; k=25, top 20; k=50, top 20. No fourth variant. Candidate sizes and package vocabulary come from training only; all rules remain active. | Use the fixed primary metric and paired protocol, and separately top-3 package coverage as a workflow diagnostic. Cut if gain fails adoption or added inference cost breaks the owner's service target. Expected gain UNKNOWN. |
| 2 | **Explicitly pinned local TabPFN v2** as a small-table challenger, with the same inclusion/size targets, folds, catalogue and rules. Evaluate an offline batch harness first. | Around 1,600 projects makes a small-table challenger reasonable. The Nature paper concerns general tabular prediction, not this energy task. | Default v2; four-estimator v2 ensemble; no further tuning. Owner must pin code/checkpoint versions and verify those exact version APIs first. | Same paired protocol; measure warm/cold inference, RAM and GPU requirements. Cut before freeze if weights are unavailable locally or projected UI latency is unacceptable. No cloud client: data must stay on this machine. Expected gain UNKNOWN. |
| 3 | Label reconstruction/ambiguity audit **before** robust training: training-only out-of-fold disagreement ranking, stratified by installer, recoverable/unknown sizes and option count, followed by human/ETL review. Keep genuine alternate designs distinct from corrupt targets. | `training_frame` reconstructs targets from one primary option; `policy_metrics` treats offered unknown size as inclusion-only. This is a concrete mechanism that might affect every candidate. | Audit-only; verified-error exclusion; verified-error weight 0.5. Human verification must precede exclusions, using training records only. | Report audited error yield and reviewer agreement, then paired protocol for any training change. Cut robust-loss experiments if no verified errors or annotation capacity. Expected gain UNKNOWN; missing roof/budget is not automatically a mislabeled design. |

The package proposal is an adaptation of bundle recommendation [C2] and frequency-aware neighbour methods [C3], not a claim that a grocery sequence model transfers unchanged. Each home has one design event; the installer's previous projects can supply chronological frequency, but there is no rich repeated purchase history for the homeowner. More elaborate graph recommendation can be cold-start dominated with only two installers.

TabPFN warning: the **current** official repository no longer defaults to v2; it describes v3.5 as default and gives different licences for code and weight families. A bare install/default constructor would not reproduce the requested v2 experiment. The official repository distinguishes local inference from a hosted client. The v2 weight licence includes an attribution requirement [C7]. This is a feasibility/licence gate, not evidence of a Reonic gain.

Confident Learning assumes a class-conditional corruption model [C4]. Our continuous sizes and omitted roof/budget do not establish that assumption. Automatically pruning unusual homes as noisy would erase valid choices and could inflate apparent agreement. Learning Using Privileged Information requires extra information available during training [C5]; it does not magically recover roof measurements absent from the export. Gather or verify such information first.

## Literature and competitor evidence

| Source | Verified scope | What it does **not** establish |
|---|---|---|
| Jbene et al., 2023, personalized PV configuration recommendation [C1] | Uses meteorological forecasting and collaborative filtering for residential PV configuration; abstract says trained on simulated data and evaluated on simulated holdout plus real data. | No verified PV+battery+HP+wallbox expert-bundle benchmark, identical CRM fields, or score comparable with our 20.9%. Full-text implementation/details unavailable here. |
| Bundle-recommendation survey [C2] | Distinguishes selecting existing bundles from generating new ones; reviews tasks and evaluation. | No guaranteed gain for sparse one-off installer projects. |
| TIFU-kNN [C3] | Demonstrates the value of personalized frequency and neighbours in next-basket recommendation. | Grocery users' repeated purchases are not installer designs for new households. |
| TabPFN v2 Nature paper [C6] | A tabular foundation model evaluated on small/medium tables. | No experiment on this challenge, no proof of overcoming missing information. |
| Reonic official offer documentation [C8] | Describes battery suggestions based on consumption and planned PV; quick-planning docs distinguish manual packages from AI-assisted flows. | No public held-out CRM imitation accuracy, algorithm specification or fair comparison with our baseline. |
| Aurora official AI Roof documentation [C9] | Documents roof generation from imagery/LIDAR, followed by AutoDesigner, with coverage/failure prerequisites. | No comparable whole-bundle imitation metric. Roof-aware production engineering is a different input regime. |

Search coverage: queried PV/battery/heat-pump sizing from CRM/installer history, PV collaborative filtering, bundle/next-basket methods, tabular foundation models, ambiguous/noisy labels, and Reonic/Aurora official documentation on 2026-11-08. A Polish PV-installer paper lead concerns monthly installation counts/average capacity; its publisher fetch returned HTTP 429, so it is not used as validated evidence. Absence of a found paper is not proof none exists.

**Differentiation implication (inference):** “AI solar design,” batteries based on consumption, and offers in one workspace are already advertised capabilities. The defensible hackathon distinction is independently measured installer-policy imitation, honest failure analysis and a concrete missing-information workflow, rather than claiming unprecedented automatic sizing.

## Scoring sanity, fairness and requests

The primary production metric requires PV within ±20%, battery and HP within ±25%, and wallbox presence agreement. Offered-but-unrecoverable sizes are NaN and score presence only. Missing output sizes are not awarded correct capacity. The legacy EMS is a different weighted closeness score; its `bundle_match` omits PV inclusion, and HP inclusion is inferred from positive recovered kW. Do not call EMS “whole-design accuracy.” All these details are verified from `eval/metrics.py` and `training_frame` via CodeGraph on 2026-11-08.

The preregistered sensitivity comparison uses **unchanged predictions** under four definitions: current relative primary-option metric; current relative or at least one assumed 450 W module PV tolerance; stricter absolute ±450 W PV tolerance; and current relative metric matching **any one complete offered option**. It never mixes components across different options. Presence gates stay enforced. A 450 W module is an explicit sensitivity assumption, not a verified per-project module rating. Any-option match rewards projects with more options and does not prove matching the signed choice. It should be secondary until primary/signed-option semantics are confirmed.

Fairest to report now: keep the frozen primary metric next to per-component scores and baseline with the same denominator; publish the full sensitivity table without selecting whichever definition flatters us. Add option-count and unknown-size denominators. Ask Reonic whether “primary” identifies the accepted offer, and whether roof/budget/site-visit fields can be joined using valid project IDs. Never tune the metric on 2026.

Requests for owners: (Engine/Eval) preregister package/TabPFN/audit candidates in `research/experiments.md`; (Pitch) replace a hard “~25% ceiling” assertion with “missing inputs limit us; the exact ceiling is unproven”; (Engine) confirm full served feature semantics for untrusted existing assets before treating the base-feature collision bound as full-input evidence; (Reonic/Pitch) verify signed-option mapping and obtain a small authorized roof/budget annotation sample.

## Sources

All accessed **2026-11-08**. Research summaries above are paraphrases. URLs link primary papers, publishers or vendor documentation. Live documentation is a dated observation, not a frozen release.

- **C1:** Jbene, Saadane, Tigani & Chehri. *Personalized PV system recommendation for enhanced solar energy harvesting using deep learning and collaborative filtering*. Sustainable Energy Technologies and Assessments 60, 103563 (December 2023). Publisher abstract verified; full text not inspected. https://www.sciencedirect.com/science/article/abs/pii/S2213138823005568 ; DOI https://doi.org/10.1016/j.seta.2023.103563
- **C2:** Sun et al. *A Survey on Bundle Recommendation: Methods, Applications, and Challenges*. arXiv v1 2024-11-01, current v2 2026-02-26. https://arxiv.org/abs/2411.00341
- **C3:** Hu et al. *Modeling Personalized Item Frequency Information for Next-basket Recommendation*. arXiv 2020-05-31. https://arxiv.org/abs/2006.00556
- **C4:** Northcutt, Jiang & Chuang. *Confident Learning: Estimating Uncertainty in Dataset Labels*. JAIR 2021; arXiv current v6 2022-08-22. https://arxiv.org/abs/1911.00068
- **C5:** Vapnik & Izmailov. *Learning Using Privileged Information: Similarity Control and Knowledge Transfer*. JMLR 16 (2015). https://www.jmlr.org/beta/papers/v16/vapnik15b.html
- **C6:** Hollmann et al. *Accurate predictions on small data with a tabular foundation model*. Nature 637, 319–326; published 2025-01-08. Article available through search result and PDF; direct article re-open hit the publisher authentication redirect. https://www.nature.com/articles/s41586-024-08328-6 ; https://www.nature.com/articles/s41586-024-08328-6.pdf
- **C7:** PriorLabs official TabPFN repository README, current main observed 2026-11-08; version-specific local inference and licensing. https://github.com/PriorLabs/TabPFN
- **C8:** Reonic official documentation, undated current pages observed 2026-11-08. https://docs.reonic.com/docs/en/offers-overview-create-an-offer ; https://docs.reonic.com/docs/en/offers-plan-pv-quick-planning
- **C9:** Aurora official AI Roof API documentation, undated current page observed 2026-11-08. https://docs.aurorasolar.com/reference/ai-roof
- **C10:** Wu & Zhu. *Multi-label classification: do Hamming loss and subset accuracy really conflict with each other?* NeurIPS 2020. This supports treating component and joint objectives as distinct; it is not an energy-domain gain claim. https://proceedings.neurips.cc/paper_files/paper/2020/hash/20479c788fb27378c2c99eadcf207e7f-Abstract.html

## Source register

All accessed **2026-11-08**; dates below are publication/version dates as shown in primary pages. No external number is used to estimate a Rhythm gain.

- **S1:** Zhang et al., *Verbalized Sampling: How to Mitigate Mode Collapse and Unlock LLM Diversity*, submitted 2025-10-01, current arXiv revision shown 2026-07-15. [Primary abstract](https://arxiv.org/abs/2510.01171). Distribution prompting and typicality-bias motivation only.
- **S2:** Liang et al., *Encouraging Divergent Thinking in Large Language Models through Multi-Agent Debate*, EMNLP 2024, arXiv revision 2024-10-09. [Primary abstract](https://arxiv.org/abs/2305.19118). Reports degeneration-of-thought and proposes debate; also cautions judges may be biased.
- **S3:** Gottweis et al., *Accelerating scientific discovery with Co-Scientist*, submitted 2025-02-26; current revision shown 2026-06-29. [Primary abstract](https://arxiv.org/abs/2502.18864). Structured generation/critique and tournament evolution; biomedical validation does not validate this hackathon ranking.
- **S4:** Si, Yang, Hashimoto, *Can LLMs Generate Novel Research Ideas?*, 2024-09-06. [Primary abstract](https://arxiv.org/abs/2409.04109). Human-rated NLP idea novelty/feasibility study.
- **S5:** Doshi and Hauser, *Generative artificial intelligence enhances creativity but reduces the diversity of novel content*, arXiv revision 2024-03-14; Science Advances 2024 DOI linked by the primary record. [Author preprint](https://arxiv.org/abs/2312.00506), [journal DOI](https://doi.org/10.1126/sciadv.adn5290). Journal direct fetch returned 403; primary preprint opened successfully.
- **S6:** Aurora Solar, *Aurora AI*, undated current marketing page. [Official page](https://aurorasolar.com/aurora-ai/). Advertises AI-assisted site design; no independent accuracy comparison assumed.
- **S7:** OpenSolar, *Auto Design*, undated current product page. [Official page](https://www.opensolar.com/auto-design/), [official support: Ada Auto Design](https://support.opensolar.com/hc/en-us/articles/13780099656719-Designing-using-Ada-Auto-Design). Advertises standardized automatic designs with component/control/pricing settings.
- **S8:** Reonic, German homepage, undated current. [Official page](https://reonic.com/de-de/). Advertises CRM, planning, simulation, offers, 3D roof module layout and installer AI tools; no published expert-bundle benchmark found here.
- **S9:** Enpal, *Stromtarif*, undated current. [Official page](https://www.enpal.de/stromtarif). Describes Enpal.One household integration; no tariff savings number repeated.
- **S10:** 1KOMMA5, *Heartbeat AI*, undated current. [Official page](https://1komma5.com/de/heartbeat/). Describes household energy management; no vendor savings figure repeated.


## Appendix: raw idea pool and all pairwise decisions

The complete lens/probability/canonical-ID/Elo pool is [critic/raw-pool-with-elo.json](critic/raw-pool-with-elo.json). The original separate lens responses are [generator/ideas.json](generator/ideas.json); 200 candidates, 20 lenses, 59 below the subjective 10% typicality threshold. All probabilities are subjective prompts for diversity, not measured frequencies of other teams.

All 30 canonical generator arguments, critic objections, amended dispositions, axis scores, 435 unique comparisons and twenty Elo order replays are retained in [critic/tournament.json](critic/tournament.json), regenerated with `python research/creative/critic/rank.py`. The source and CodeGraph audit is [critic/source-audit.md](critic/source-audit.md). Original generator mini-specs and morphology are [generator/REPORT.md](generator/REPORT.md).

The final parent judge accepts KEEP/DEFER/CONDITIONAL dispositions as scoped in the tournament; explicitly prohibited ideas remain prohibited even if ranked. Three wildcards survive outside the top-25 cutoff: I28, I29, I30. No new UI, LLM sizing, private data upload, 2026 selection or unreviewed product change is authorized by this research.

### Raw lens candidates

Elo is inherited from the canonical idea; these are not 200 independently evaluated implementations.

| ID | Lens | Candidate | Subjective typical-team probability | Canonical | Elo |
|---|---|---|---:|---|---:|
| 01-01 | Reonic CTO | Replay receipt | 18% | I17 | 1683.9 |
| 01-02 | Reonic CTO | Existing/new boundary | 8% | I19 | 1562.5 |
| 01-03 | Reonic CTO | Joint package learner | 55% | I07 | 1306.4 |
| 01-04 | Reonic CTO | No silent lock violation | 35% | I13 | 1652.2 |
| 01-05 | Reonic CTO | Input provenance is part of the model | 18% | I03 | 1660.6 |
| 01-06 | Reonic CTO | Typed survey-needed handoff | 7% | I01 | 1495.9 |
| 01-07 | Reonic CTO | Installer transfer failure table | 25% | I18 | 1492.2 |
| 01-08 | Reonic CTO | Metric contract before optimization | 18% | I24 | 1652.7 |
| 01-09 | Reonic CTO | Regret not resemblance | 8% | I26 | 1271.2 |
| 01-10 | Reonic CTO | Expiry on assumption changes | 3% | I30 | 1273.2 |
| 02-01 | Reonic customer-success lead | Ask one useful question on a call | 45% | I02 | 1718.1 |
| 02-02 | Reonic customer-success lead | Effort-weighted qualification | 7% | I15 | 1349.3 |
| 02-03 | Reonic customer-success lead | Separate elapsed and working time | 12% | I23 | 1733.1 |
| 02-04 | Reonic customer-success lead | Prevent replacement-as-addition confusion | 8% | I19 | 1562.5 |
| 02-05 | Reonic customer-success lead | Explain battery oversell concern | 40% | I04 | 1572.7 |
| 02-06 | Reonic customer-success lead | Collect missing roof/budget | 35% | I27 | 1437.0 |
| 02-07 | Reonic customer-success lead | Future EV intent is not current EV | 28% | I16 | 1555.4 |
| 02-08 | Reonic customer-success lead | Confirm-before-send checklist | 35% | I01 | 1495.9 |
| 02-09 | Reonic customer-success lead | Own a baseline loss | 4% | I28 | 1484.3 |
| 02-10 | Reonic customer-success lead | Facts passport across handoffs | 6% | I30 | 1273.2 |
| 03-01 | 15-year installer planner | Existing-system accounting first | 40% | I19 | 1562.5 |
| 03-02 | 15-year installer planner | Preserve the part I locked | 45% | I13 | 1652.2 |
| 03-03 | 15-year installer planner | Compare to my actual cohort | 15% | I11 | 1444.3 |
| 03-04 | 15-year installer planner | Do not replace heat-loss calculation | 40% | I20 | 1660.1 |
| 03-05 | 15-year installer planner | Which option was really signed? | 15% | I05 | 1587.5 |
| 03-06 | 15-year installer planner | Reuse my successful packages | 60% | I07 | 1306.4 |
| 03-07 | 15-year installer planner | One more roof module tradeoff | 9% | I21 | 1401.9 |
| 03-08 | 15-year installer planner | Two approved offers not twenty | 35% | I22 | 1347.1 |
| 03-09 | 15-year installer planner | 4500 could be real | 8% | I03 | 1660.6 |
| 03-10 | 15-year installer planner | Survey before quote | 7% | I29 | 1308.4 |
| 04-01 | Sceptical homeowner | Why the larger battery? | 60% | I04 | 1572.7 |
| 04-02 | Sceptical homeowner | Savings when tariff assumptions fail | 35% | I10 | 1379.9 |
| 04-03 | Sceptical homeowner | What still needs a site visit? | 40% | I01 | 1495.9 |
| 04-04 | Sceptical homeowner | A simpler approved alternative | 45% | I22 | 1347.1 |
| 04-05 | Sceptical homeowner | Do not infer EV from a charger sale | 7% | I16 | 1555.4 |
| 04-06 | Sceptical homeowner | Is HP really sized for cold days? | 22% | I20 | 1660.1 |
| 04-07 | Sceptical homeowner | Show assumptions that can expire | 4% | I30 | 1273.2 |
| 04-08 | Sceptical homeowner | No labor-savings marketing claim | 15% | I23 | 1733.1 |
| 04-09 | Sceptical homeowner | Show a case AI loses | 3% | I28 | 1484.3 |
| 04-10 | Sceptical homeowner | Pay for certainty first | 4% | I29 | 1308.4 |
| 05-01 | ML researcher jury | Tolerance collision ceiling | 18% | I06 | 1547.1 |
| 05-02 | ML researcher jury | Freeze score definitions | 40% | I24 | 1652.7 |
| 05-03 | ML researcher jury | Paired discordance not two percentages | 22% | I09 | 1652.5 |
| 05-04 | ML researcher jury | Transfer calibration | 40% | I18 | 1492.2 |
| 05-05 | ML researcher jury | Coverage-risk curve | 25% | I14 | 1429.8 |
| 05-06 | ML researcher jury | Default-value provenance negative control | 7% | I03 | 1660.6 |
| 05-07 | ML researcher jury | Ambiguous signed-option labels | 18% | I05 | 1587.5 |
| 05-08 | ML researcher jury | Joint bundle probability | 65% | I07 | 1306.4 |
| 05-09 | ML researcher jury | Optimize tolerance coverage | 28% | I08 | 1347.5 |
| 05-10 | ML researcher jury | Decision regret without label worship | 9% | I26 | 1271.2 |
| 06-01 | VC | Measure actual planner effort later | 40% | I23 | 1733.1 |
| 06-02 | VC | Workflow wedge rather than roof arms race | 20% | I25 | 1555.9 |
| 06-03 | VC | Unique missing-data collection loop | 40% | I27 | 1437.0 |
| 06-04 | VC | Auditable infrastructure trust | 15% | I17 | 1683.9 |
| 06-05 | VC | Qualification cost not inference cost | 7% | I15 | 1349.3 |
| 06-06 | VC | Draft-to-survey handoff | 15% | I01 | 1495.9 |
| 06-07 | VC | Longitudinal energy passport | 8% | I30 | 1273.2 |
| 06-08 | VC | Trust by admitting median wins | 3% | I28 | 1484.3 |
| 06-09 | VC | Avoid overselling to reduce objections | 40% | I04 | 1572.7 |
| 06-10 | VC | Information product before hardware | 5% | I29 | 1308.4 |
| 07-01 | Competitor PM - Enpal | Do not copy integrated tariff promises | 30% | I25 | 1555.9 |
| 07-02 | Competitor PM - Enpal | Test tariff dependence | 30% | I10 | 1379.9 |
| 07-03 | Competitor PM - Enpal | Retrofit existing hardware boundary | 9% | I19 | 1562.5 |
| 07-04 | Competitor PM - Enpal | Show energy economics versus sales habit | 45% | I04 | 1572.7 |
| 07-05 | Competitor PM - Enpal | Compare planner-approved packages | 55% | I22 | 1347.1 |
| 07-06 | Competitor PM - Enpal | Proof tied to system versions | 8% | I17 | 1683.9 |
| 07-07 | Competitor PM - Enpal | Local roof/budget evidence advantage | 30% | I27 | 1437.0 |
| 07-08 | Competitor PM - Enpal | Qualification friction measure | 15% | I15 | 1349.3 |
| 07-09 | Competitor PM - Enpal | Cost of regret | 8% | I26 | 1271.2 |
| 07-10 | Competitor PM - Enpal | Public loss as trust move | 2% | I28 | 1484.3 |
| 08-01 | Competitor PM - 1KOMMA5 | No unsupported tariff optimization | 45% | I10 | 1379.9 |
| 08-02 | Competitor PM - 1KOMMA5 | Compatibility and installed assets boundary | 30% | I19 | 1562.5 |
| 08-03 | Competitor PM - 1KOMMA5 | Installer assistance not EMS control | 40% | I25 | 1555.9 |
| 08-04 | Competitor PM - 1KOMMA5 | Assumption changes trigger review | 5% | I30 | 1273.2 |
| 08-05 | Competitor PM - 1KOMMA5 | Independent cohort evidence | 18% | I11 | 1444.3 |
| 08-06 | Competitor PM - 1KOMMA5 | Actual profile shape sensitivity | 20% | I12 | 1437.3 |
| 08-07 | Competitor PM - 1KOMMA5 | Fixed-design second opinion | 30% | I04 | 1572.7 |
| 08-08 | Competitor PM - 1KOMMA5 | Buying versus usage distinction | 8% | I16 | 1555.4 |
| 08-09 | Competitor PM - 1KOMMA5 | Prospective field evidence | 22% | I27 | 1437.0 |
| 08-10 | Competitor PM - 1KOMMA5 | Information-only first offer | 3% | I29 | 1308.4 |
| 09-01 | Competitor PM - Aurora Solar | Avoid roof automation feature race | 60% | I25 | 1555.9 |
| 09-02 | Competitor PM - Aurora Solar | Roof cap value rather than fake geometry | 8% | I21 | 1401.9 |
| 09-03 | Competitor PM - Aurora Solar | Versioned design evidence | 10% | I17 | 1683.9 |
| 09-04 | Competitor PM - Aurora Solar | Declare missing survey facts | 30% | I01 | 1495.9 |
| 09-05 | Competitor PM - Aurora Solar | Useful question before roof model | 20% | I02 | 1718.1 |
| 09-06 | Competitor PM - Aurora Solar | Learn installer package style | 35% | I07 | 1306.4 |
| 09-07 | Competitor PM - Aurora Solar | Ground truth target ambiguity | 9% | I05 | 1587.5 |
| 09-08 | Competitor PM - Aurora Solar | National register reference population | 20% | I11 | 1444.3 |
| 09-09 | Competitor PM - Aurora Solar | Installer transfer evidence | 15% | I18 | 1492.2 |
| 09-10 | Competitor PM - Aurora Solar | Honest baseline failure reveal | 3% | I28 | 1484.3 |
| 10-01 | Competitor PM - OpenSolar | Do not claim auto-design novelty | 55% | I25 | 1555.9 |
| 10-02 | Competitor PM - OpenSolar | Narrow approved option set | 50% | I22 | 1347.1 |
| 10-03 | Competitor PM - OpenSolar | Empirical package policy | 40% | I07 | 1306.4 |
| 10-04 | Competitor PM - OpenSolar | Independent expert-match audit | 18% | I24 | 1652.7 |
| 10-05 | Competitor PM - OpenSolar | Economics disagreement as second reader | 30% | I04 | 1572.7 |
| 10-06 | Competitor PM - OpenSolar | Rules remain true after locks | 25% | I13 | 1652.2 |
| 10-07 | Competitor PM - OpenSolar | Provenance-sensitive qualification | 9% | I03 | 1660.6 |
| 10-08 | Competitor PM - OpenSolar | Reduce information burden | 10% | I15 | 1349.3 |
| 10-09 | Competitor PM - OpenSolar | Capture budget constraints | 25% | I27 | 1437.0 |
| 10-10 | Competitor PM - OpenSolar | Survey as an initial product | 4% | I29 | 1308.4 |
| 11-01 | Radiology second-reader analogy | Independent physics second reader | 55% | I04 | 1572.7 |
| 11-02 | Radiology second-reader analogy | Escalate ambiguous home | 40% | I01 | 1495.9 |
| 11-03 | Radiology second-reader analogy | Sensitivity against deferral rate | 15% | I14 | 1429.8 |
| 11-04 | Radiology second-reader analogy | Reader disagreement ledger | 10% | I09 | 1652.5 |
| 11-05 | Radiology second-reader analogy | Hospital/domain shift analogy | 20% | I18 | 1492.2 |
| 11-06 | Radiology second-reader analogy | Trace the model version | 30% | I17 | 1683.9 |
| 11-07 | Radiology second-reader analogy | Sparse-subtype evidence warning | 22% | I20 | 1660.1 |
| 11-08 | Radiology second-reader analogy | Critical invariant not mean accuracy | 30% | I13 | 1652.2 |
| 11-09 | Radiology second-reader analogy | Show a second-reader disagreement openly | 5% | I28 | 1484.3 |
| 11-10 | Radiology second-reader analogy | Stale study requires new facts | 4% | I30 | 1273.2 |
| 12-01 | Credit adverse-action analogy | Specific missing-fact reason | 35% | I01 | 1495.9 |
| 12-02 | Credit adverse-action analogy | Challenge incorrect input provenance | 15% | I03 | 1660.6 |
| 12-03 | Credit adverse-action analogy | Actionable smallest information request | 10% | I15 | 1349.3 |
| 12-04 | Credit adverse-action analogy | Metric consequences transparent | 25% | I24 | 1652.7 |
| 12-05 | Credit adverse-action analogy | Groupwise uncertainty audit | 25% | I18 | 1492.2 |
| 12-06 | Credit adverse-action analogy | Who benefits and who loses | 20% | I09 | 1652.5 |
| 12-07 | Credit adverse-action analogy | Behavior score is not physical need | 6% | I16 | 1555.4 |
| 12-08 | Credit adverse-action analogy | Reproducible decision receipt | 30% | I17 | 1683.9 |
| 12-09 | Credit adverse-action analogy | Prospective missing-data collection | 15% | I27 | 1437.0 |
| 12-10 | Credit adverse-action analogy | Defer equipment decision for evidence | 5% | I29 | 1308.4 |
| 13-01 | Car-configurator analogy | Choose coherent packages | 65% | I07 | 1306.4 |
| 13-02 | Car-configurator analogy | Only compatible approved choices | 60% | I22 | 1347.1 |
| 13-03 | Car-configurator analogy | Replacement versus added equipment | 25% | I19 | 1562.5 |
| 13-04 | Car-configurator analogy | Locked option invariant | 40% | I13 | 1652.2 |
| 13-05 | Car-configurator analogy | Discrete catalogue target | 50% | I08 | 1347.5 |
| 13-06 | Car-configurator analogy | Next roof module price step | 9% | I21 | 1401.9 |
| 13-07 | Car-configurator analogy | Nearest suitable package regret | 18% | I26 | 1271.2 |
| 13-08 | Car-configurator analogy | Which configuration was purchased? | 10% | I05 | 1587.5 |
| 13-09 | Car-configurator analogy | Ask budget before expensive choice | 35% | I15 | 1349.3 |
| 13-10 | Car-configurator analogy | Versioned household configuration | 4% | I30 | 1273.2 |
| 14-01 | Chess best-move/eval-bar analogy | Best candidate plus alternatives | 60% | I22 | 1347.1 |
| 14-02 | Chess best-move/eval-bar analogy | Regret of second choice | 22% | I26 | 1271.2 |
| 14-03 | Chess best-move/eval-bar analogy | Flat evaluation means defer | 9% | I14 | 1429.8 |
| 14-04 | Chess best-move/eval-bar analogy | Roof-cap principal variation | 4% | I21 | 1401.9 |
| 14-05 | Chess best-move/eval-bar analogy | One answer changes the move | 25% | I02 | 1718.1 |
| 14-06 | Chess best-move/eval-bar analogy | Different objectives yield different moves | 18% | I04 | 1572.7 |
| 14-07 | Chess best-move/eval-bar analogy | Paired blunders not aggregate score | 8% | I09 | 1652.5 |
| 14-08 | Chess best-move/eval-bar analogy | Same engine and position replay | 25% | I17 | 1683.9 |
| 14-09 | Chess best-move/eval-bar analogy | Show the baseline winning line | 4% | I28 | 1484.3 |
| 14-10 | Chess best-move/eval-bar analogy | Incomplete board means no final move | 6% | I01 | 1495.9 |
| 15-01 | Insurance underwriting analogy | Refer unknown roof/budget | 45% | I01 | 1495.9 |
| 15-02 | Insurance underwriting analogy | Coverage-risk tradeoff | 40% | I14 | 1429.8 |
| 15-03 | Insurance underwriting analogy | Missingness mechanism | 20% | I03 | 1660.6 |
| 15-04 | Insurance underwriting analogy | Reference cohort selection | 25% | I11 | 1444.3 |
| 15-05 | Insurance underwriting analogy | New installer population shift | 20% | I18 | 1492.2 |
| 15-06 | Insurance underwriting analogy | Scenario stress envelope | 35% | I10 | 1379.9 |
| 15-07 | Insurance underwriting analogy | Loss function before approval | 15% | I24 | 1652.7 |
| 15-08 | Insurance underwriting analogy | Collect high-value facts | 25% | I27 | 1437.0 |
| 15-09 | Insurance underwriting analogy | Existing assets declared explicitly | 25% | I19 | 1562.5 |
| 15-10 | Insurance underwriting analogy | Assumptions expire after household change | 6% | I30 | 1273.2 |
| 16-01 | Assumption reversal | Rank packages instead of predict sizes | 55% | I07 | 1306.4 |
| 16-02 | Assumption reversal | Ask before predicting | 35% | I02 | 1718.1 |
| 16-03 | Assumption reversal | Use simulator to disagree rather than size | 25% | I04 | 1572.7 |
| 16-04 | Assumption reversal | Measure observability rather than accuracy | 8% | I06 | 1547.1 |
| 16-05 | Assumption reversal | Minimize regret rather than imitate | 12% | I26 | 1271.2 |
| 16-06 | Assumption reversal | Lead with a loss rather than a win | 3% | I28 | 1484.3 |
| 16-07 | Assumption reversal | Offer information rather than equipment | 2% | I29 | 1308.4 |
| 16-08 | Assumption reversal | Collect labels for questions not systems | 7% | I27 | 1437.0 |
| 16-09 | Assumption reversal | Sell readiness not precision | 8% | I01 | 1495.9 |
| 16-10 | Assumption reversal | Maintain facts not a one-time quote | 5% | I30 | 1273.2 |
| 17-01 | SCAMPER | Substitute bundle ranking for chain | 50% | I07 | 1306.4 |
| 17-02 | SCAMPER | Combine habit and physics as disagreement | 30% | I04 | 1572.7 |
| 17-03 | SCAMPER | Adapt underwriting referral | 12% | I14 | 1429.8 |
| 17-04 | SCAMPER | Magnify one useful question | 35% | I02 | 1718.1 |
| 17-05 | SCAMPER | Put replay evidence to another use | 8% | I17 | 1683.9 |
| 17-06 | SCAMPER | Eliminate unsupported business claim | 18% | I23 | 1733.1 |
| 17-07 | SCAMPER | Reverse offer then survey order | 3% | I29 | 1308.4 |
| 17-08 | SCAMPER | Substitute measured profile for smooth H0 | 45% | I12 | 1437.3 |
| 17-09 | SCAMPER | Combine retrofit boundaries consistently | 12% | I19 | 1562.5 |
| 17-10 | SCAMPER | Reduce choice overload | 50% | I22 | 1347.1 |
| 18-01 | Morphological box | Installer ID x bundle classifier x joint hit x approved menu x temporal folds | 30% | I07 | 1306.4 |
| 18-02 | Morphological box | Provenance x boosted chain x calibrated missingness x ask-next x paired test | 8% | I03 | 1660.6 |
| 18-03 | Morphological box | Measured load x simulator x import gap x second-opinion x public replay | 25% | I12 | 1437.3 |
| 18-04 | Morphological box | Missing mask x calibrated model x risk-coverage x refer x heldout calibration | 12% | I14 | 1429.8 |
| 18-05 | Morphological box | Budget x ranked catalogue x regret x Pareto choice x prospective cases | 8% | I26 | 1271.2 |
| 18-06 | Morphological box | Cohort year x empirical CDF x plausibility x percentile x register metadata | 18% | I11 | 1444.3 |
| 18-07 | Morphological box | Existing assets x accounting x invariants x locked draft x stress cases | 20% | I19 | 1562.5 |
| 18-08 | Morphological box | Roof unknown x fixed policy x readiness x site survey x critical checks | 12% | I01 | 1495.9 |
| 18-09 | Morphological box | Artifact hash x same engine x reproducibility x receipt x deterministic replay | 10% | I17 | 1683.9 |
| 18-10 | Morphological box | Changing household x versioned facts x validity x passport x follow-up | 3% | I30 | 1273.2 |
| 19-01 | Premortem 15:30 lost | Jury says we overstated the tie | 35% | I23 | 1733.1 |
| 19-02 | Premortem 15:30 lost | Jury questions selected signed option | 12% | I05 | 1587.5 |
| 19-03 | Premortem 15:30 lost | Jury has seen solar auto-design already | 45% | I25 | 1555.9 |
| 19-04 | Premortem 15:30 lost | Retrofit double-counts installed equipment | 15% | I19 | 1562.5 |
| 19-05 | Premortem 15:30 lost | Jury asks for HP sizing evidence | 35% | I20 | 1660.1 |
| 19-06 | Premortem 15:30 lost | Demo cannot run offline | 50% | I17 | 1683.9 |
| 19-07 | Premortem 15:30 lost | Manual override breaks a rule silently | 15% | I13 | 1652.2 |
| 19-08 | Premortem 15:30 lost | Metric appears chosen after results | 20% | I24 | 1652.7 |
| 19-09 | Premortem 15:30 lost | Savings collapse under plausible prices | 35% | I10 | 1379.9 |
| 19-10 | Premortem 15:30 lost | We hid the baseline and lost trust | 6% | I28 | 1484.3 |
| 20-01 | Accuracy capped at 25 percent thought experiment | Win on information acquisition | 45% | I02 | 1718.1 |
| 20-02 | Accuracy capped at 25 percent thought experiment | Win on independent second opinion | 40% | I04 | 1572.7 |
| 20-03 | Accuracy capped at 25 percent thought experiment | Win on bounded handoff | 25% | I01 | 1495.9 |
| 20-04 | Accuracy capped at 25 percent thought experiment | Win on critical error prevention | 40% | I13 | 1652.2 |
| 20-05 | Accuracy capped at 25 percent thought experiment | Win on reproducibility | 30% | I17 | 1683.9 |
| 20-06 | Accuracy capped at 25 percent thought experiment | Win on prospective data collection | 20% | I27 | 1437.0 |
| 20-07 | Accuracy capped at 25 percent thought experiment | Win on honesty of claims | 30% | I23 | 1733.1 |
| 20-08 | Accuracy capped at 25 percent thought experiment | Win on transparent population limits | 20% | I18 | 1492.2 |
| 20-09 | Accuracy capped at 25 percent thought experiment | Win on selling certainty before hardware | 3% | I29 | 1308.4 |
| 20-10 | Accuracy capped at 25 percent thought experiment | Win on continuity after quote | 5% | I30 | 1273.2 |
