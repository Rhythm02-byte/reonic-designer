# Jury verdict: next

**Verdict: credible working slice, not yet a convincing finalist story.** The reconciled scores are technical depth **6/10**, user fit **6/10**, business impact **4/10**, and execution/demo **5/10**. These are jury judgments using the requested anchors, not competition predictions.

The AI is real and the planner workflow is the best differentiator: ask a consequential question, update the draft, inspect a warning, keep planner control, and share approved options. Accuracy alone will not distinguish this submission. The served policy matches the whole design on **68/325** later projects versus **67/325** for the historical median bundle; its observed PV advantage is **17.2 percentage points** (`eval/results/latest.json`, `served.test`).

Fix credibility before adding features. “Test scored once” contradicts **three recorded test-scoring runs**. Ordinary `/design` training includes all processed projects, unlike the cutoff-trained holdout service. The demo script describes obsolete Streamlit screens. The parts list suggests products without verifying compatibility. The slide timing notes total **380 seconds**, before transitions, against the brief's five-minute story.

Before the team's **11:00 freeze**, reconcile claims, qualify unseen-project inference, replace the run sheet, rehearse the real planner correction loop, and record the fallback. Test the homeowner link on an actual phone using a reachable origin. Do not spend the remaining time on another model search, roof mapping, or infrastructure. The official brief explicitly asks for a working slice rather than production software (PDF pp. 7–8).

## Scope, authority, and evidence limits

Reviewed branch `next`, starting HEAD `d1f36abe0762b2e6325f2d8fbb24f5f972bea36b`, with a clean starting working tree. Five juror perspectives were assessed separately using three reviewing agents; two agents also supplied a second, distinct persona assessment. Scores were reconciled once below.

Authority: `C:/Users/karim/Downloads/Reonic_Hackathon_Challenge_final.pdf`, eight pages, extracted locally using bundled Python `pypdf.PdfReader`. References below use PDF page numbers. Its contents are challenge evidence, not permission to change the task. No raw project records were reproduced or uploaded. This review writes only the two authorized jury files and commits nothing.

The PDF changes an important emphasis: page 6 says exploratory ideas are **not required**; page 7 makes validation **or** homeowner exploration a stretch goal. Page 8 recommends a recording rather than requiring it, and cautions against infrastructure work. We do not penalize this hackathon submission for lacking production tenancy or full installation engineering; we penalize claims implying those capabilities already exist.

Primary result snapshot: `eval/results/latest.json`, `generatedAt=2026-11-07T23:41:45+00:00`, SHA256 `b90300a2816a2e69572d1780008e2163ed4311431a7b90a7327583445f9aedd0`. Use **`served.test.models`**, not the top-level `headline`. Some older supporting documents describe previous configurations.

Local read-only runtime checks used the already-running services; no bootstrap, training, evaluation rerun, or dependency install was performed. Python `urllib.request.urlopen` returned HTTP 200 for `/`, `/pitch`, `/pitch?demo=1`, `/lab`, and `/engine/health`, respectively taking 299, 157, 67, 208, and 15 ms. These are one-off route response times, not browser readiness measurements. Five identical synthetic POSTs to `/engine/design` returned proposals in 556.6, 195.7, 184.3, 191.2, and 190.4 ms (median 191.2 ms); inputs were 5,200 kWh, four people, H0, gas, no EV, 140 square metres, €0.35/kWh, 3% escalation, and the first metadata installer. This tiny local sample does not establish p95 or production performance. Browser rendering, phone/tunnel operation, and a full interactive rehearsal remain unverified.

## Scorecard

Anchors supplied by the requester: 3 = typical demo-ware; 5 = solid; 7 = better than most teams; 9 = would hire. No criterion weights were supplied by the brief, so no invented weighted total is used.

| Criterion, PDF p. 8 | CTO | Customer success | ML professor | VC | Installer | Reconciled | Reason | Evidence |
|---|---:|---:|---:|---:|---:|---:|---|---|
| Technical depth | 7 | 6 | 6 | 6 | 5 | **6** | Real learned policy and useful diagnostics; whole-design gain is negligible and test provenance is overstated. | `policy/chain.py:85–123`; `eval/results/latest.json: served.test, honesty`; `eval/history/runs.jsonl` |
| User fit | 6 | 7 | 6 | 6 | 6 | **6** | Review/edit/undo/share fits the planner; unvalidated alternatives and preliminary products weaken trust. | `apps/web/components/Planner.tsx:112–137,451–560`; `AskNext.tsx:13–41`; `Offer.tsx:66–189`; `apps/web/lib/api.ts:202–223` |
| Business impact | 4 | 4 | 4 | 3 | 4 | **4** | Plausible qualification and offer workflow; no measured labor saving, conversion improvement, or commercial validation. | `docs/business-case.md`; `docs/PITCH.md §7`; PDF p. 5 |
| Execution and demo | 5 | 5 | 6 | 5 | 5 | **5** | Running endpoints and a deck exist; stale script, unsupported claims, excess timing, and no verified fallback hurt the story. | `docs/demo-script.md`; `slides.tsx`; `docs/BACKLOG.md A`; local HTTP checks above |

Code paths abbreviated as `policy/...` in this report mean `services/engine/engine/policy/...`.

CTO: the boosted presence/size/quantile chain qualifies as AI under PDF p. 6; OpenAPI contracts provide an integration boundary, not proof of an installed Reonic integration. Customer success: the ask-next/correction loop is useful tomorrow as an assisted draft, provided uncertainty remains visible. ML professor: retain the PV result and explicitly report the whole-design tie. VC: the workflow is a credible wedge; standard models and two installers do not demonstrate a moat. Installer: candidate equipment and a schematic house help qualification, but do not certify roof layout, electrical design, heat loss, or component compatibility.

## Minimum, stretch, and submission checklist

“Present” means supported by source or the stated runtime check; it does not mean a complete browser rehearsal passed.

| Brief requirement | Status | Proof and qualification |
|---|---|---|
| Complete proposal with short explanation, PV/battery/HP as appropriate (pp. 2, 7) | **Present** | `engine/design.py`, `policy/designer.py`; `Planner.tsx` system cards/reasons. Learned component inclusion and rules allow omission. PDF p. 4 explicitly says every home need not receive every component. |
| Measurement against experts on unseen projects (pp. 6–7) | **Present, qualified** | `eval/results/latest.json → served.test`, temporal cutoff and aggregate results. Repeated test access means this is a later temporal holdout, not an untouched once-only final exam. |
| Planner changes an input/component and gets updated design (p. 7) | **Present** | `Planner.tsx:112–137`; design effect and editable system cards; `AskNext.tsx`. Actual browser interaction still needs rehearsal. |
| Analysis of where/why designs deviate (p. 7) | **Partial** | `research/data-correlations.md`, `research/model-selection.md`, `docs/figures/deviation_chart.png`, per-installer metrics. Missing roof/budget is a plausible explanation, not a causal identification of every miss. No clear live segmented error diagnosis. |
| Alternatives and confidence for every recommendation (p. 7) | **Partial** | Quantile ranges, `PartRange.tsx`, `api.ts:202–223` variants. Coverage is aggregate size coverage, not correctness probability; current adapter substitutes component toggles for richer engine alternatives and catches validation failure as empty warnings. |
| Planner validation view (p. 7) | **Present, qualified** | `Evidence.tsx:85–173`, planner flags, `/lab`, `policy/rules.py`. Rule/historical checks are not installation certification. |
| Homeowner exploration on the same engine (pp. 4, 7) | **Present, qualified** | `Offer.tsx`, encoded whole options in `lib/copy.ts`, pinned inference in `PartsList.tsx`. Fixed household inputs/approved whole alternatives fit the brief. Economic curve described in PITCH is absent. |
| Working end-to-end demo (p. 8) | **Partial verification** | Routes and synthetic design requests work; source shows workflow. No reviewed recording or verified phone/tunnel run. |
| Code plus short setup/approach/limitations README (p. 8) | **Present** | `README.md`, root `package.json`; claims corrections needed. |
| Short pitch covering problem, solution, evaluation, value (p. 8) | **Present, needs shortening** | `apps/web/components/pitch/slides.tsx` contains all topics; `docs/pitch/home-energy-designer.pptx` exists but was not visually audited here. Do not alternate between competing decks. |
| Short fallback recording, recommended (p. 8) | **Missing from reviewed docs tree** | `docs/BACKLOG.md A` still open; no `.mp4/.webm/.mov` found under `docs/`. A recording elsewhere may exist; none was supplied. |

## Evaluation cross-examination

**Is 2026 untouched? No, in the once-only sense.** Parsing `eval/history/runs.jsonl` yielded seven records, three with `testScored=true` (lines 5–7: one quick, two all). This is a lower bound: `eval/run.py` permits unrecorded runs, and `research/model-selection.md` admits earlier baseline scores were seen. All seven history records cite `a8cc4c2` with `dirty:true`, so a commit ID alone cannot reproduce the evaluated tree. Repeated evaluation does not prove test-driven tuning; it does disprove “scored once.” State both facts without accusing the team of demonstrated leakage.

**Is the live unseen example honest? Only with the inference route identified.** `policy/train.py:23–26` trains the saved ordinary `/design` model on all processed projects; `scripts/bootstrap.mjs:27–29` invokes that training. `engine/demo.py:181–184` fits the separate holdout designer through the cutoff. Loading the holdout home's inputs into the planner invokes ordinary `/design` (`Planner.tsx:160–163`, `api.ts:278–281`). Do not describe the revised planner prediction as unseen unless its actual artifact is pinned to the cutoff. The existence of a saved artifact trained by a different manual procedure cannot be established from this source alone.

**Is “installer's usual design” fair? Useful, but name it precisely.** B0 is an installer-specific historical median bundle (`engine/baseline.py:100–102`), with inclusion habits and no heat pump. It is a strong low-information benchmark, not an expert doing a new planning task. Include B0c and B1 in supporting evidence; do not use the weaker rule of thumb alone or turn a B0 comparison into a labor-saving claim. The current served composite's leave-one-installer-out performance is not established by older M1/H1 LOIO results.

**Are tolerances defensible? As declared scoring choices, not accepted engineering limits.** `eval/metrics.py:85–109` uses PV ±20%, battery/HP ±25%, and wallbox presence only. Unknown offered sizes receive inclusion-only treatment. A 10 kWp target permits a ±2 kWp PV deviation by arithmetic; that can be consequential on a roof. No recorded expert acceptance study validates these thresholds. Keep size MAE, inclusion precision/recall, and denominators alongside whole-design scoring. A near-perfect HP absence accuracy is weak evidence when positives are rare.

**What does the evidence actually say?**

| Question | Supported answer | Source |
|---|---|---|
| Whole-design advantage? | 68 vs 67 matched projects out of 325; +0.3077 percentage points. Treat as a tie. | `latest.json → served.test.models.{ours,B0}.wholeDesign` |
| EMS advantage? | Ours 61.0373 vs B0 61.1355; no observed advantage. | Same block, `ems` |
| PV advantage? | 59.6923% vs 42.4615%, +17.2308 points on this temporal sample. This is the strongest accuracy claim. | Same block, `pv` |
| Stable whole-design improvement? | Pre-2026 repeated splits give +0.6299 ± 1.9681 points SD, ahead in 11/20. Overlapping splits are not independent replications, and SD is not a confidence interval. | `honesty.repeatedSplits` |
| What survives shuffling? | Validation whole design: real 24.1379%, shuffled 21.7241% (SD 1.8936), B0 17.6724%. Whole design does not collapse to B0. PV drops to 40.2586% vs real 52.1552% and B0 44.8276%. | `honesty.shuffledLabels` |
| Does shuffling prove no leakage? | No. It supports an input-dependent PV contribution; retained rules, catalogue structure, and label marginals support much of the remaining score. Five permutations do not exhaust possible leakage. | `eval/honesty.py:74–89`; same aggregate block |
| Is the roof experiment a measured customer benefit? | No. Cap = expert module count injects target information. 20.9% → 32.9% is an oracle upper bound, not an expected gain from asking a homeowner. | `oracle.fields.roof` |
| Does real consumption help? | Under an artificial intervention replacing every demand with 4,500 kWh, whole design is 11.1%; restoring recorded demand gives 20.9%, +9.8 points. It is not a prospective call experiment or proof all 4,500 values are wrong. | `oracle.fields.demand` |
| Are 2,000 fuzz cases proof of physical validity? | No: zero recorded failures of the implemented checks on that seeded sample. It does not test every real roof or equipment pairing. | `honesty.fuzz`; `policy/rules.py` |

`latest.headline` chooses the best temporal-test EMS among candidate models (`eval/run.py:324–333`), currently H1 at 63.2644. That is an exploratory best-of-test result, not the shipped composite. Do not present it as shipped performance. Blocks may be carried between runs; pin config/artifact/result provenance together. `research/experiments.md` describes stricter adoption criteria but has an empty Results section: it is a proposed protocol, not evidence that the current model passed four folds and the repeated-split threshold.

Recommended wording: **“On 325 later projects from the supplied installers, our policy matches the whole design about as often as an installer-specific median bundle. It improves PV matching under our stated tolerance; the product helps planners expose assumptions, change the proposal, and explain their choices.”**

Stop saying: “scored once,” “beats experts,” “better overall,” “63.3% accuracy for our shipped model,” “shuffle proves no leakage,” guaranteed confidence in a correct design, proven unseen-installer fit, measured hours saved, or measured win-rate uplift.

## Top ten fixes, ordered by expected jury value per hour

Hours and value bands below are **reviewer planning estimates**, not measurements or promised score increases. Ordering favors credibility and reliable demonstration over speculative new accuracy. Each owner must implement in their own folders; this review implements none.

| Rank | What and acceptance condition | Owner | Estimated hours | Jury value/hour | Demo risk | Exact target |
|---:|---|---|---:|---|---|---|
| 1 | Replace every “scored once”; remove “beat overall”; pin the table to `served.test` and explain 68 vs 67. Presenter and README must tell the same story. | Pitch / Kian / Eval | 0.5 | Very high | Low | `README.md Results`; `docs/PITCH.md §§5,10`; slides `proof` text + notes; `research/model-selection.md` supporting story |
| 2 | Replace obsolete run sheet with the actual `/pitch` route and current screens; rehearse to the brief's five minutes. Remove duplicate accuracy narration. | Pitch / Kian | 0.5–0.75 | Very high | Low | `docs/demo-script.md`; slides `how`, `reading`, `proof`, `planner` |
| 3 | Resolve the unseen-demo boundary: use a demonstrably cutoff-trained artifact for live comparison or label ordinary planner edits as workflow only. Preserve artifact/config/hash and the aggregate result; avoid more tuning. | Engine / Eval | 0.5–1 | Very high | Medium if retraining | `policy/train.py:23–26`; `engine/demo.py:181–184`; `Planner.tsx:160–163`; presentation notes |
| 4 | Record the current full workflow and establish one fallback action; verify it plays locally before submission. | Pitch / Kian | 0.5–0.75 | High | Low | `docs/BACKLOG.md A` recording; `/pitch?demo=1` is labelled synthetic fallback, not unseen evidence |
| 5 | Give pending engine requests a bounded timeout and visible fallback/error; verify first load, engine refused, hung response, and return to live mode. | Web | 0.5–1 | High | Medium | `apps/web/lib/engine.ts:126–155`; `Pitch.tsx:143–181`; planner design effect |
| 6 | Validation failure must say “not validated,” not empty warnings; do not approve an unvalidated alternative by default. | Web | 0.25–0.5 | High | Low–medium | `apps/web/lib/api.ts:202–223`; planner offer options |
| 7 | Label BOM as suggested products pending site/compatibility confirmation; distinguish missing catalogue from no equipment and flag capacity mismatch on pinned sizes. | Web / Engine | 0.5–0.75 | High | Low | `engine/design.py:124–154`; `PartsList.tsx:26–27,57–76` |
| 8 | Test one synthetic homeowner offer on the actual phone and reachable origin; retain a local offer view if tunnel fails. Do not expose real holdout inputs through the share link. | Kian / Web | 0.5 | High | Low unless deployment expands | `OfferQr.tsx:13`; `proxy.ts`; `/offer`; `docs/BACKLOG.md A` tunnel decision |
| 9 | Time one complete synthetic planning task, including review/correction/share, and label it an internal task timing with no measured manual comparator. Otherwise use a clearly hypothetical value statement and a pilot plan. | Kian / Pitch | 0.5 | Medium–high | Low | `docs/PITCH.md §7`; slide `impact`; `docs/business-case.md` |
| 10 | Remove old latency/conflicting HP/coverage/example claims, replace `[Team names]` and `[ask Reonic]`, and make “Next: parts list” consistent with the draft BOM already shown. | Pitch / Kian | 0.25–0.5 | Medium–high | Low | slides `cover`, `impact`, `limits`; `docs/PITCH.md §§5,6,9`; audit below |

## Five-minute demo stress test

The existing `docs/demo-script.md` nominally allocates five minutes, but cannot be executed as written against `next`.

| Existing slot | What the script asks for | Jury friction / break point |
|---|---|---|
| Before 0:00 | `streamlit run app.py`, old data path, old Evaluation tab | Wrong application/commands. Reset to root `pnpm dev`, current `/pitch`, and verified artifacts. Do not bootstrap/train during presentation. |
| 0:00–0:30 | “Hours” problem | Brief p. 3 supports the qualitative problem; 8.2 elapsed days is not effort. State the distinction once. |
| 0:30–1:30 | Named typical home and exact old sizes | Current deck starts with missing consumption, then answers 5,200 kWh. Old named screens/sizes are unverified. Waiting for first inference or reading multiple reasons spends the minute. |
| 1:30–2:30 | EV edit, zero-PV override, restore | Good refinement idea, but current pitch uses EV and a 20 kWh battery lock. Pick one constraint demonstration; do not show both scripts' branches. |
| 2:30–3:30 | Two project comparisons and old metrics | Too much switching; obsolete PV/battery/whole-design scores conflict with the proof slide. Ordinary planner edits also need the unseen-artifact caveat. |
| 3:30–4:30 | Retrofit miss, HP miss, deviation image | Too many new homes to understand; old “never propose HP” conflicts with current source selection. Show one known limitation tied to the question the planner asks next. |
| 4:30–5:00 | Scenario euro benefit | Assumptions are allowed if explicit, but do not imply measured savings. End with the useful workflow and next pilot measurement. |

The **current** `slides.tsx` notes separately allocate 15 + 25 + 30 + 30 + 120 + 30 + 30 + 25 + 30 + 25 + 20 = **380 seconds (6:20)**. This excludes transition and failure recovery time. The first live planner appears only after the first 100 seconds under these notes. Cut time before the live moment.

Suggested **proposed** run sheet (time budgets, not measured rehearsal results): 0:00–0:15 problem; 0:15–0:35 home + proposal + one reason; 0:35–1:10 answer consumption; 1:10–1:35 add EV; 1:35–2:00 battery override, warning, correction/Undo; 2:00–2:40 one honest expert comparison plus aggregate tie/PV result; 2:40–3:10 homeowner option; 3:10–3:40 explain uncertainty and the roof upper bound; 3:40–4:10 compact architecture; 4:10–4:40 value hypothesis and limitations; 4:40–5:00 close/recovery reserve. Do not make a phone scan a required live step.

Failure cases: a refused engine connection can enter labelled fixtures, but a fetch with no timeout can wait indefinitely (`engine.ts:126`). Pitch readiness awaits design work, and its 900 ms scroll delay is not a completion signal (`Pitch.tsx:180–208`). Warm the planner and offer deliberately; do not call the result a cold-start benchmark. A localhost QR points the phone at itself; a tunnel needs a reachable origin and phone test. Holdout/project-loading features are intentionally refused on a nonlocal origin (`proxy.ts:1–16`), so keep the real-project evidence local. Since offer URLs encode household inputs (`lib/copy.ts:101–114`), use synthetic data for anything shared outside the team.

### Words on each slide

Measured locally by transpiling `slides.tsx` with TypeScript, calling each content slide's `body()`, rendering with `react-dom/server.renderToStaticMarkup`, stripping tags, and counting Unicode letter/number tokens (internal decimal/range/hyphen joins retained). Counts include sources and page numbers, exclude presenter notes/CSS/attributes. Live slides contain arbitrary embedded app content, so their full word count is state-dependent; the measured script chrome is reported separately.

| Slide | Words | Assessment |
|---|---:|---|
| 1 `cover` | 40 | Replace team placeholder; say the line, do not read the paragraph. |
| 2 `problem` | 74 | Keep elapsed/effort caveat; compress supporting text. |
| 3 `data` | 79 | Use one finding; “0.93 in every segment” is overstated. |
| 4 `how` | 103 | Densest slide; move after live demo or greatly compress. |
| 5 `planner` | Title 3; step label+hint counts 15 / 16 / 13 / 17 / 15 | Embedded UI varies. Show outputs; avoid reading presenter chrome. |
| 6 `offer` | Title 4; step label+hint 17 | Embedded offer varies. One option switch is enough. |
| 7 `proof` | 69 | Keep one table and one sentence; correct scored-once footnote. |
| 8 `reading` | 78 | Repeats proof; cut from main route. |
| 9 `asknext` | 93 | Excellent workflow idea; oracle disclaimer must be spoken, not buried. |
| 10 `impact` | 77 | Remove stale p95 and placeholder; separate benefit hypothesis from evidence. |
| 11 `limits` | 86 | Read one limitation; fix HP and BOM inconsistencies. |

## Claims audit

Statuses: **OK** = supported at the stated scope; **overstated** = source supports a narrower statement; **wrong** = contradicted by current evidence; **unverifiable** = no adequate reproducible evidence identified. Repeated instances across the three requested files are grouped; source locations identify where to correct them. Dates, versions, routes, and numeric identifiers are accounted for separately at the end. No public-source claim was independently revalidated online: this is a local evidence audit, and unverifiable items should be sourced or cut.

### Shared performance tables and quantitative claims

| Claim / occurrences | Status | Source and exact reading |
|---|---|---|
| Train through September 2025, choose Q4 2025, refit through December 2025; validation n=232, temporal test 2026 n=325 (`README Evaluation`, `PITCH §5`, slide `proof` notes) | **OK**, for evaluation | `latest.served`, `honesty.shuffledLabels`, `policy.json selectedOn`; separate ordinary all-data artifact caveat above. |
| Test “once” (`README Results`, `PITCH §§5,10`, slide `proof` body/notes) | **Wrong** | Three `testScored=true` history records, plus admitted earlier baseline access. |
| B1: 55.0 EMS / 14.8% whole / 32.9% PV / 40.0% battery | **OK** | `latest.served.test.models.B1`; same values in README/PITCH/proof slide. |
| B0: 61.1 / 20.6% / 42.5% / 47.4% | **OK** | `latest.served.test.models.B0`; describe historical median bundle, not a working planner. |
| Ours: 61.0 / 20.9% / 59.7% / 47.4% | **OK** | `latest.served.test.models.ours`; “whole design right” means within declared tolerances, not correctness/safety. |
| Closeness 0–100; PV ±20%, battery ±25%; all four components (`README` footnotes; PITCH/proof headings) | **OK**, metric definition | `eval/metrics.py`; HP ±25%, wallbox presence only, unknown-size treatment must also be disclosed. |
| +17 points PV, whole/battery tie (`README`, `PITCH §5`, slides `proof`, `reading`) | **OK** | Observed PV difference 17.2308 points; whole difference 0.3077 points. This is sample evidence, not universal superiority. |
| “We beat it overall” (`PITCH §10`) | **Wrong** as substantive performance claim | Whole differs by one project; EMS is lower. Contradicts PITCH's own tie statement. |
| Previous config 60.4 / 20.9% / 59.7% / 49.2%; battery swap +0.4 validation point (`PITCH §5`) | **OK**, historical | `research/model-selection.md` previous/coverage tables. Keep current and historical configs clearly separated; +0.4 is one validation project, not robust improvement. |
| Shuffled 21.7% vs real 24.1%; 20 random splits +0.6 ±2.0 points; 2,000 fuzz cases, zero failures/crashes (`README`, `PITCH §5`) | **OK** numbers | `latest.honesty`. ± is split SD, not CI. README “with every evaluation” is overstated because quick/partial modes exist. |
| “With shuffled answers the model loses its edge, so it learns real signal” (`README`) | **Overstated** | PV signal declines; shuffled whole design remains above B0. Does not certify lack of leakage. |
| Depth 3, minimum leaf 40 (`PITCH §5`) | **OK** | `services/engine/config/policy.json → model`. Selection is validation evidence, not proof it is universally best. |
| Economic battery matches experts 23% on validation n=232 (`PITCH §5`, slide `reading`) | **OK**, historical experiment | `research/model-selection.md → per-component source`, SIM 23.3%. “Experts size by habit, not economics” is an interpretation; no objective optimum was observed. |
| PV p10–p90 size range covers 85.5%, battery 83.6%, target 80% (`PITCH §5`, slide `proof` notes) | **Overstated** as current calibrated guarantee | Recorded in `research/model-selection.md` calibration table for the earlier composite; not a current served-coverage block in latest. Refitting after calibration and temporal shift weaken formal guarantees. Say empirical historical size coverage, not probability the design is right. |
| `/design` p50 92 ms / p95 133 ms cached, p95 345 ms uncached (`PITCH §5`, slide `impact`) | **Wrong** as current benchmark | `docs/BACKLOG.md C` explicitly says older before coverage sizing. Our five-request synthetic sample is reported above and cannot replace a p95 benchmark. `served.*.latencyP50ms` measures policy inference, not this API/UI path. |
| Signed-option guess × module wattage changes ~1.5 points; 60% masking costs ~2 EMS (`PITCH §5`) | **OK**, scoped legacy M1 experiment | `latest.sensitivity` M1 whole ranges about 11.3–12.9%; `robustness.blankRate` M1 EMS 55.235 →52.940. Do not silently attribute to current served composite. |
| Real kWh vs 4,500 gives +9.8 whole points (`README`, `PITCH §6`) | **OK**, intervention only | `oracle.fields.demand`: 11.0769 →20.9231%. Recorded values restored, not measured prospective question benefit. |
| Previous demand 12.3% →20.9%; PV 46.5% →59.7% (`PITCH §6`) | **OK**, historical label supplied | `research/model-selection.md`; current PV happens to be the same in `oracle.fields.demand`. Prefer one current table. |
| Roof 20.9% →32.9%, PV 59.7% →82.5%, +12 points (`README`, `PITCH §6`, slide `asknext`) | **OK only as oracle upper bound** | `oracle.fields.roof`, cap = expert module count. “Worth more than any model we could train” is **overstated**: no such comparison was established. |
| EV 20.3% →20.9% (`PITCH §6`) | **Wrong** for current table | Current `oracle.fields.ev` and `evAssumedNo`: 20.0% →20.9%, matching slide `asknext`. |
| EV PV ~equal (`PITCH §6`); 60.6% →59.7% (slide `asknext`) | **OK** with precision | `oracle.fields.ev`: recorded PV matching slightly falls; do not imply every answer improves every target. |
| Consumption 11.1% →20.9%, PV 46.5% →59.7%, n=325 (slide `asknext` notes/body) | **OK**, intervention | `oracle.fields.demand`; “roughly doubles” is approximate, not an exact doubling or real-world uplift. |
| Example battery 9–10 vs 5 kWh; extra 5 kWh, ~10 autarky points, payback 2.4 years later (`PITCH §6`) | **Unverifiable** as measured example | No input/config-linked reproducible result supplied. Label illustrative or replace with output from one pinned synthetic case. Current homeowner page has no promised curve. |
| <1 second complete draft (`PITCH §7`, slides `cover`, `impact`) | **Overstated** as general guarantee | Local five-request engine sample is consistent with subsecond API responses, but no UI/cold-start/tail benchmark. It is not time to reviewed offer. |

### Dataset, operations, and context numbers

| Claim / occurrences | Status | Source and exact reading |
|---|---|---|
| Built in 30 hours (`README` opening) | **Unverifiable** | No work-duration measurement identified. Brief pp. 2,8 supplies event dates/times, not this team's elapsed build time. |
| ~1,600 signed projects (`README`); 1,619 signed projects (`PITCH §3`, slide `data`) | **Overstated** | Latest evaluable count is 1,593 projects with parts. 1,619 may describe a broader export population; selected signed option remains an open question (`PLAN §17`). State population/filters and avoid verified “signed” labels without confirmation. |
| Two installers (`README`, PITCH, slides `data`,`limits`) | **OK** | `latest.installers`; `research/data-correlations.md`. This does not demonstrate generalization at scale. |
| Installer 1 request→offer 8.2 days n=257; installer 2 16h n=18; signature 29/20 days (`PITCH §2`; slide `problem` repeats first) | **Unverifiable** in reviewed reproducible aggregates | These appear in pitch text without a pinned extraction/result. Keep only with a reproducible aggregate query and population; retain elapsed-not-effort label. |
| ~355k installs 2025 vs ~395k 2024, ZVEH (`PITCH §2`) | **Unverifiable** | No primary result linked in this claim. Remove from main pitch unless sourced; unnecessary to demonstrate the challenge. |
| Installer 2 ~25% offers lack PV (`PITCH §3`, slide `data`) | **Unverifiable** as stated population | Related project/option aggregates vary in `research/data-correlations.md` and `rhythm-findings.md`. Supply denominator and distinguish offers/projects/options before quoting. |
| Exactly 4,500 kWh as placeholder, correlation −0.53 (`README`, `PITCH §3`, slides `data`,`planner`) | **Overstated** as confirmed default | `research/data-correlations.md §1` supports pooled Spearman −0.53 between default flag and PV inclusion. `PLAN §17` still asks whether value is a tool default. Say suspected default; it is not proof every such home has unknown consumption. |
| Battery ≈0.93 kWh/kWp “in every segment” (`README`, `PITCH §3`, slides `data` and `reading` notes) | **Overstated** | `research/data-correlations.md §2`: segment medians vary, e.g. 0.84 to 1.01 in listed groups. Say roughly one kWh per kWp in these data; correlation is not causal proof of a habit. |
| Similar homes 5.4–12.6 kWp, p10–p90, n=216, 4–5 MWh/no EV (`README`, `PITCH §3`, slide `data`) | **Unverifiable** as exact cohort statistic | Repeated in old demo/pitch and deviation narrative, but no pinned numeric cohort artifact identified here. Image exists; do not infer causality or a hard ceiling for all future models from the stated range. |
| Wallboxes 24.6%, only 9% of those with EV flag (`PITCH §3`) | **Unverifiable** as exact full-export aggregate | Related figures in historical analyses use other populations; latest test has 24% wallbox positives. Need explicit cohort/filter query. Do not substitute test percentage. |
| 1–3 next questions (`README`, `PITCH §1`), one batched model call (`README How`) | **OK**, implementation description | `engine/ask_next.py → ask_next`; question ranking is counterfactual model sensitivity × price swing, not empirically calibrated probability of a customer's answer. |
| Hourly year and 20-year economics (`README`, `PITCH §4`, slide `how`) | **OK**, model horizon | `engine/sim/`; this is a modeled period, not 20 years of observed outcomes. |
| HP ~2% of designs, so physics-led/not learned (`README Limits`, `PITCH §9`, slide `limits`) | **Overstated / inconsistent** | `policy.json` selects M1 for HP. Historical `rhythm-findings.md` reports 13/1,593 (0.8%) primary designs and 31 line items across options. Specify population, separate include decision from sizing, and match the actual served code. |
| One reference weather site, Kassel (`README Limits`, `PITCH §9`, slide `limits`) | **OK**, stated model limitation | Simulator source/config and `research/battery-and-simulations.md`; no location-specific performance claim follows. |
| Prices are 2026 ranges (`README Limits`, `PITCH §9`, slide `limits`) | **OK only as dated assumptions** | `services/engine/config/market.json`, `research/source-check.md`, `research/external/R4-product-catalog-prices.md`; source research does not establish all corrections were integrated or a binding quote. |
| Evaluation ~13 min (`README Run`) | **Overstated** as expected runtime without machine/config | Latest `durationSec=645.4` is about 10.8 minutes; duration varies. Use “several minutes” or a dated measured range. |

All requested-file numeric examples are covered above, including presenter notes: the demo uses 4,500 unknown demand, 5,200 answered demand, 12,000 EV km/year, and a 20 kWh battery lock (`slides.tsx:20–23,211–223`). These are **OK as scripted synthetic inputs**, not observed performance or private project facts. Four components and the coupled ordering are **OK** implementation descriptions (`policy/chain.py`, `designer.py`), with the HP source caveat above.

Nonempirical numeric tokens: **OK as references/configuration**, not evidence of outcomes: section/list numbers; B0/B0c/B1/M1 identifiers; PDF pp. 5/7/8 references (verified against the attached PDF); 2025/2026 cutoffs and event labels; `/pitch?demo=1`; logo tapped three times; ports 3000/8000; Node 24+/pnpm 10+/Python 3.11+ prerequisite declarations; Next.js 16/React 19/Tailwind 4 repository-stack labels. Root `package.json` and frontend manifests are the authority for executable scripts/dependencies; environment-specific installation compatibility was not exhaustively tested. Slide numbers and CSS sizes are layout, not factual claims. Slide note timing is audited separately above. The five-minute story is official on PDF p. 7; 11:00 freeze is a team rule, while 15:00 submission is official on PDF pp. 2,8.

## What to cut

- New model searches and candidate integrations. The current evidence does not justify spending the freeze window chasing a tiny whole-design increment.
- Main-stage slide `reading`, repeated metric explanations, and most of `how`'s text. One architecture sentence plus one proof table is sufficient.
- New bill OCR, live LLM demos, real roof mapping, haptics, multi-user workspace, and production hosting work. They add failure paths without strengthening the required story.
- Unsupported market totals, exact cohort anecdotes without a source, p95 133 ms, and any “hours/days → subsecond” comparison that equates a draft with an approved offer.
- Claims of install-ready BOM, guaranteed confidence, or an economic homeowner curve that is not shown. Cut the claim rather than attempt full compatibility engineering before freeze.
- A required live phone QR scan and public real-project selection. Use synthetic sharing and keep local evidence local.

## Premortems

**It is 15:30 and we did not place. The jury's three reasons:**

1. “The measured full-system result was a tie, yet they told us the test was only scored once and implied broader superiority. The contradictions made the evidence harder to trust.”
2. “We watched data slides and screen changes instead of a planner confidently correcting one useful proposal. The demo ran long and the old script/fallback was not dependable.”
3. “We saw plausible components and hypothetical value, but no demonstrated reduction in the work to a reviewed offer, and no clear boundary between preliminary products and checked engineering.”

**It is 15:30 and we won. The jury's three reasons:**

1. “They made uncertainty actionable: one important question changed the proposal, and a planner could challenge, correct, and explain it.”
2. “They measured honestly against a strong baseline, showed where they tied, and limited the PV claim to what the data supports. Their reality check was credible.”
3. “The whole story worked within five minutes: home → proposal → refinement → expert evidence → understandable homeowner choice. The fallback worked, and the next business measurement was concrete.”

These are scenario judgments, not forecasts about other teams or the actual jury.
