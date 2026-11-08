# Critic source and feasibility audit

Accessed: **2026-11-08, Europe/Berlin**. Repository inspected on branch `next`; no product code changed. External product descriptions below are vendor claims, not independently benchmarked capabilities. Competitor availability and other teams' intentions are separate questions: **other teams' methods and scores remain UNVERIFIED**.

## Why generic feature parity is weak differentiation

| Verified primary source | Narrow fact supported | Implication (our judgment) |
|---|---|---|
| [Reonic quick planning](https://docs.reonic.com/docs/en/offers-plan-pv-quick-planning), updated 2026-09-09 | Reonic already documents component/package-based indicative offers without roof placement or yield simulation; it distinguishes this from AI planning. | A fast quote or package selector alone is insufficient novelty. Focus on learned installer behavior, independent checks, and which fact to ask next. |
| [Reonic energy flows](https://docs.reonic.com/docs/en/offers-simulation-cat-energy-flows), updated 2026-09-30 | Existing PV/storage can be entered separately from additions, and multiple battery variants can be compared. | Existing-vs-new semantics are core workflow correctness; a battery comparison is useful but not itself a new category. |
| [Aurora AI Roof documentation](https://docs.aurorasolar.com/reference/ai-roof), undated | Aurora exposes automatic roof modeling, an asynchronous process requiring imagery/LIDAR, with fallback when unavailable. | Do not enter an overnight roof reconstruction race; establish which existing upstream geometry Rhythm could consume later. |
| [OpenSolar Auto Design](https://www.opensolar.com/auto-design/), undated | OpenSolar markets automated 3D design, shading, BOM and proposal integration, with auto-design described as beta. | A 3D house, BOM and share link are table stakes in an established workflow. Do not imply that these capabilities prove our sizing accuracy. |
| [1KOMMA5 official overview](https://1komma5.com/en/), undated | The vendor describes Heartbeat AI as controlling connected home energy systems and connecting them to electricity markets. | Runtime dispatch is a different problem from a pre-installation signed-offer recommendation. Say which problem Rhythm solves. |
| [Enpal.One+](https://www.enpal.de/enpal-one), undated | Enpal describes coordinating household devices and buying/selling electricity. | Do not casually claim our fixed-tariff simulation beats dynamic control products. We have not run that comparison. |

No source above establishes a public score on this challenge's signed bundles, a reproducible competitor training recipe, or any score of another hackathon team.

## Methods: what the cited work does and does not warrant

| Source | Verified scope | Application here |
|---|---|---|
| [Zhang et al., Verbalized Sampling](https://arxiv.org/abs/2510.01171), submitted 2025-10-01, revised 2026-07-15 | Prompts for a distribution of responses rather than one response; reports increased diversity across several tasks. | Ask for many ideas with subjective typicality estimates. Our probabilities are elicitation devices, not measured team frequencies or calibrated likelihoods. |
| [Liang et al., EMNLP 2024](https://arxiv.org/abs/2305.19118), revised 2024-10-09 | Evaluates multi-agent debate and degeneration of thought in translation and arithmetic reasoning. It also warns that LLM judging can be unfair across different models. | Generator and critic actually exchange arguments; a named judge must expose decisions. This is a process aid, not evidence that our proposed product ideas work. |
| [Gottweis et al., AI co-scientist](https://arxiv.org/abs/2502.18864), submitted 2025-02-26; [Google explanation](https://research.google/blog/accelerating-scientific-breakthroughs-with-an-ai-co-scientist/), 2025-02-19 | Uses generation, debate and tournament evolution. Google's account explicitly calls Elo an auto-evaluation, not independent ground truth. | Our deterministic tournament ranks reviewer judgments only. Preserve all matches, scores, weights, objections, and sensitivity to order. |
| [Si, Yang and Hashimoto](https://arxiv.org/abs/2409.04109), 2024-09-06 | In a study with over 100 NLP researchers, LLM ideas were judged more novel and slightly weaker on feasibility. | Every surviving idea needs an actual repo seam, a first action, and a cut line. This result does not generalize automatically to installer planning. |
| [Doshi and Hauser](https://pmc.ncbi.nlm.nih.gov/articles/PMC11244532/), Science Advances, 2024-07-12 | In an experiment about short-story writing, AI assistance improved individual ratings but made outputs more similar. | Preserve three low-typicality wildcards despite the deadline-focused tournament. This is a motivation for diversity protection, not proof of hackathon outcomes. |

## Feasibility checked with CodeGraph

Queries executed before code inspection: `AskNext ask_next designer validate battery coverage conformal simulation`; `design _bat_variant simulate baseline audit rules uncertainty yearly economic_battery`; `input_provenance _entered fit_calibration apply_calibration metrics score aggregate`; `eval/metrics.py services/engine/engine/policy/conformal.py services/engine/engine/design.py attach_metrics`.

| Seam | Current behavior observed | Consequence for ideas |
|---|---|---|
| `services/engine/engine/ask_next.py:74`, `_entered` | Entered/extracted provenance skips the corresponding candidate. | A provenance demo has a real seam. Test genuine 4,500 separately from omission/default. |
| `services/engine/engine/design.py:448` | `DEMAND_DEFAULT_LIKE` is appended for every demand equal to 4,500, independent of entered provenance. | Ask the engine owner to refine warning semantics; do not equate value equality with a confirmed placeholder. No edit made here. |
| `services/engine/engine/ask_next.py:203` | Candidate answers re-run the policy; score is estimated probability of a design change times a price swing. | It is sensitivity/value-of-information ranking under assumed answer weights, not an estimated accuracy improvement or minutes saved. |
| `services/engine/engine/design.py:274`, `attach_metrics` | A battery sweep supplies without-battery/economic/max-independence variants; metrics failures fall back without breaking the draft. | Reuse existing second-opinion outputs. Label assumption-driven simulation and missing metrics explicitly; no universal optimality claim. |
| `services/engine/engine/policy/physics.py:66` | Economic battery is the best candidate among supplied sizes under the simulator, with a zero fallback on exception. | A zero economic battery can mean a failure path unless separately observed. A demo receipt should include successful metrics, not just the chosen number. |
| `services/engine/engine/policy/designer.py:457` | Similar-home percentile flags use a local neighbor subset, with at least five positive sizes. | This is an installer-neighbor comparison, different from a MaStR population cohort percentile. Never silently substitute one for the other. |
| `services/engine/engine/design.py:450` | Unknown installer produces `INSTALLER_UNKNOWN` and pooled behavior. | Existing support for an unseen installer is not demonstrated calibration for new installers; two training installers limit transfer evidence. |
| `eval/metrics.py:98` | Primary whole-design metric ANDs all four tolerance matches; unknown offered size scores inclusion only. Interval coverage is per component among known positive expert sizes. | Whole-design agreement is not average component accuracy. Report missing size denominators; marginal interval coverage is not joint bundle confidence. |
| `services/engine/engine/models/schemas.py:21` | Provenance confidence is a declared field with bounds [0,1]. | These values are not empirically calibrated probabilities of correctness. Avoid converting them to an automatic install-ready threshold. |

## Claim hygiene requests for the owners

1. `docs/PITCH.md` says in likely Q&A that we "beat it overall"; the same document reports 20.9% vs 20.6% whole design and 61.0 vs 61.1 EMS. Use "clear PV gain, whole-design tie" consistently. Owner: Pitch.
2. `docs/PITCH.md` reports 92 ms p50; `docs/BACKLOG.md` records current 0.35–0.5 s under load after physics features. Remeasure the actual final artifact/cold and warm state; neither unqualified number is safe. Owner: Engine/Pitch.
3. The roof +12 points uses a cap derived from the target expert module count. It is an oracle upper bound, not an experiment measuring the value of a roof survey. Real demand recovery is a masking/oracle experiment, not a prospective customer trial. Owner: Pitch.
4. A broad near-neighbor label spread does not prove that no better function exists. Exact-input collision bounds constrain a finite sample under declared inputs; singletons make the empirical bound weak. Owner: Eval/Pitch.
5. Signed projects show what was sold among observed offers, not what every homeowner needed, wanted, could afford, or would have bought under another design. Avoid causal sales/physical-need claims. Owner: Pitch/Engine.
6. `research/experiments.md` includes a candidate asking Haiku to pick among top-three bundles. This conflicts with AGENTS.md's LLM-never-sizes rule and must not run on private project rows or become the sizing source. Request removal/reframing by the document owner; do not treat it as authorization. Owner: Engine/Pitch.

All requests are read-only findings. No edits to another owner's folders, no private rows, and no commits.
