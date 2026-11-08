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
