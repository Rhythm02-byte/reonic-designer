# Critic, debate and tournament report

As of **2026-11-08**. These are research priorities and requests for the owners, not shipped product changes. Hours and risk are reviewer estimates. No expected numerical model gain has been invented. The imminent freeze favors evidence, replay and the existing demo over a new modeling branch.

## Auditable process

The generator produced 200 raw ideas across 20 separately retained lenses, consolidated to 30 stable IDs. Its typical-team probabilities are subjective and uncalibrated. The critic sent a specific objection for every ID. The generator replied, accepting or amending all objections; the explicit post-debate disposition for each is retained in `tournament.json`. The critic then acted as the provisional judge; a distinct parent/Claude review remains required. No fictitious human expert or independent third judge is implied.

`python research/creative/critic/rank.py` runs 435 head-to-head comparisons (every pair among 30). Each decision applies exposed weights: jury impact 35%, evidence available before freeze 30%, estimated build time 20%, demo safety 15%. Axes run from 0 to 5, higher better. Time is `max(0, 5*(1-hours/8))`; safety is five minus risk. A weighted difference smaller than 0.075 is a tie. Elo starts at 1500, K=24, logistic scale 400; twenty seeded match orders are replayed and averaged. This is **rubric-derived judgment**, not a learned quality estimator or independent proof. Match rationales and each idea's order range are retained. Identical or near-identical evidence/time estimates should not be interpreted as a meaningful rank difference.

The method is inspired by [AI co-scientist](https://arxiv.org/abs/2502.18864) and its [explicit auto-evaluation limitation](https://research.google/blog/accelerating-scientific-breakthroughs-with-an-ai-co-scientist/) (2025; accessed 2026-11-08). Our protocol does not reproduce its scientific experiments.

## Top 25 after the debate

`source-audit.md` supplies actual CodeGraph seams and primary URLs with access dates. A repo reference below is internal evidence, not an external fact. A conditional idea stays conditional even if it ranks above a ready-to-demo item. Category `UX` means a workflow/pitch proposal; **no new UI is authorized or implemented**.

| Rank / ID / Elo | Idea / category | Why the jury cares | Evidence or source | Hours / risk | Owner / first concrete step |
|---|---|---|---|---|---|
| 1 · I23 · 1733 | Claim hygiene · pitch | A false overall-win or labor-saving claim can defeat the honest PV result. | `docs/PITCH.md` table vs Q&A; `docs/BACKLOG.md` current latency note. | 0.5 / low | Pitch: replace superiority with clear PV gain/whole-design tie; qualify oracle and elapsed-time figures; remeasure latency. |
| 2 · I02 · 1718 | One-question rescue · pitch | Demonstrates a useful action despite imperfect prediction. | `ask_next.py:203`, existing `AskNext.tsx`; oracle qualification in PITCH. | 0.5 / low | Pitch: rehearse frozen synthetic missing-demand→entered-demand interaction and separately cite the measured masking result. |
| 3 · I17 · 1684 | Offline replay receipt · risk | Makes the proof rerunnable and protects the demo from artifact drift. | Store/model load and external runner seams; future report until implemented. | 1 / low | Engine/Eval: capture config/model/code hashes, package versions, offline mode and repeated-output comparison. |
| 4 · I03 · 1661 | Genuine 4,500 vs default · data | Exposes a realistic data defect without pretending every 4,500 bill is fake. | `_entered` respects provenance; `design_policy:448` warning ignores it. | 1.5 / low | Eval: run identical synthetic values with entered/default/omitted provenance; send engine owner the warning discrepancy. |
| 5 · I20 · 1660 | HP evidence scope · pitch | Prevents sparse-label physics heuristics being sold as expert learning. | PITCH says HP ~2%; schema/site-input limitations; no new estimate. | 0.5 / low | Pitch: describe physics-led draft and site inputs still needed; make no standards-compliance claim. |
| 6 · I24 · 1653 | Frozen scoring sensitivity · risk | Shows metric choice is not selected to manufacture a win. | `eval/metrics.py:98`; ceiling workstream. | 1 / low | Eval: freeze any-option and ±1-module definitions, report all versus baseline, keep primary score. |
| 7 · I09 · 1652 | Paired win/loss audit · model | Explains where assistance helps and where habit wins. | Existing validation split and `policy_metrics`; no 2026 tuning. | 1 / low | Eval: aggregate model-only/baseline-only/both/neither hits with paired uncertainty on validation. |
| 8 · I13 · 1652 | Independent stress ledger · risk | A lock or asset-accounting bug can invalidate a correct average. | Synthetic test spec; `rules.audit` is an engine check, not an independent oracle. | 2 / low | Eval: predeclare accept/reject/review, independently check units/locks/roof, publish eligible/pass/fail/blocked. |
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

The ranking is not a recommendation to build all 25. I23/I02/I17/I03/I20 total an estimated **4 hours of owner work/review**, with no new UI. I05/I06/I13 are high-value evaluation follow-ups, partly delivered by the parallel workstreams. Availability of an owner, real extracted artifacts, and the final demo remain stronger constraints than tiny Elo differences.

## Top five mini-specs

### I23 — Claim hygiene

**What/how:** Prepare precise replacement language for the Pitch owner: clear PV gain, whole-design tie; elapsed request-to-offer time is not labor effort; oracle roof cap is not a measured roof-survey result; final-artifact latency needs a fresh receipt. **Measure without overfitting:** an evidence checklist linking every displayed figure to population, split, run/config and qualifier; this changes claims, not model selection. **Demo moment:** answer the median-baseline question before the jury asks it. **Cut line:** if the owner cannot update before freeze, retain the written request and say the qualifier aloud; never claim edits landed when they did not.

### I02 — One-question rescue

**What/how:** Use the existing Ask-next interaction on a frozen synthetic home with unknown demand, then enter a documented synthetic demand and show the resulting draft. Keep the separate published masking result labelled oracle and its denominator visible. **Measure:** interaction completes, entered provenance is respected, draft and locks remain coherent; no prospective accuracy gain is inferred. **Demo moment:** the tool asks for the missing bill fact instead of producing more confident prose. **Cut line:** if live engine latency/fallback is unreliable, use a rehearsed screen recording clearly labelled; do not present fixture output as live learned prediction.

### I17 — Offline replay receipt

**What/how:** Add a report beside the evaluation artifacts containing model/config/code hashes, runtime versions, offline flag and a canonicalized repeated-output check. This is an owner request/research artifact, not new product UI. **Measure:** identical artifact/config inputs reproduce aggregate outputs and no undeclared external dependency is needed; report attempted-network coverage separately. **Demo moment:** show Claude's rerun command and the receipt instead of asking the jury to trust a screenshot. **Cut line:** missing artifact or incomplete network instrumentation is reported blocked; a hash alone does not prove freshness or privacy.

### I03 — Provenance audit

**What/how:** Predeclare identical synthetic 4,500-kWh requests with entered, extracted, installer-default, national-default and omitted provenance. Inspect Ask next and the numeric-default warning. CodeGraph already shows different provenance treatment between these paths. **Measure:** a frozen behavior matrix, no fitting and no private test rows; don't automatically require identical model sizes where policy intentionally uses provenance. **Demo moment:** a genuine 4,500-kWh bill should not be called a confirmed fake default. **Cut line:** Codex reports the discrepancy and owner request; no unauthorized engine rewrite or untested new missingness model.

### I20 — Heat-pump evidence scope

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
