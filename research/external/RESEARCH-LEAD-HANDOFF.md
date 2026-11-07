# Research lead handoff · 7 November 2026

## Deliverables

Read these current supplements before using the original reports:

1. [TASK1-RESEARCH-COMPLETION.md](TASK1-RESEARCH-COMPLETION.md): decision-relevant R1–R6 gaps, five Kaggle candidates, licences and field mappings. **None of the reviewed datasets supplies verified installer-selected design labels.** This is a bounded finding about the reviewed datasets, not every dataset online.
2. [TASK2-SYNTHETIC-TEST-SPEC.md](TASK2-SYNTHETIC-TEST-SPEC.md): implementation-ready intake-only generator/checker specification, proposed 720-request coverage suite, source anchors, analyst-selected stress distributions, independent hard gates, denominators and anti-overfit protocol. **Specification only; not an implemented or executed test framework.**
3. [TASK3-COMPATIBILITY-VERIFIED.md](TASK3-COMPATIBILITY-VERIFIED.md): reopened manufacturer evidence and source-inspected current engine paths. Manufacturer support is conditional on models/counts/firmware. The engine currently snaps numeric sizes; it does not enforce the pairing matrix.
4. [Pitch script and claim ledger](pitch-codex/PITCH.md), [offline HTML deck](pitch-codex/index.html), [pinned aggregate evidence](pitch-codex/evidence-pinned.json), [presentation QA](pitch-codex/qa-report.json). Eight main slides, three appendices; five-minute script including a 75-second demo. Arrow keys navigate, N shows notes, O opens overview, F requests fullscreen. Open the HTML in a browser. External links are optional; no remote scripts/fonts/telemetry load.

## Important corrections and claim boundaries

- **OPSD residential EV:** the earlier R2 report incorrectly said its EV channel was industrial-only. The upstream schema includes `DE_KN_residential4_ev`. It supports measured charging-profile evidence, not driving distance, wallbox rating or installer-selected output. The correction and exact schema link are in Task 1.
- **Zolar:** distinguish the ceased original installation business from the software/website subsequently acquired by Sollit. The old configurator remains historical inspiration; current exact flow availability is not established.
- **Selected-model results:** pitch evidence is pinned from `eval/results/latest.json` **selection.test**, not the legacy top-level H1 headline. Selected M1 PV match is 56.3% vs B0 42.5%, but EMS is 58.8 vs 61.1 and whole-design match 16.9% vs 20.6%. Test n=325; validation n=232. Source snapshot generated 2026-11-07T18:59:49+00:00, SHA256 stored in JSON. Codex did not rerun evaluation or select a model.
- **Existing docs/PITCH.md:** its statement “we beat it overall” is not supported by the currently pinned selected-model results. Its unseen-installer, time-saving, trust/conversion and Ask-next claims also need precise local evidence or hypothesis labels. This work supplies a separate revised script rather than editing Claude's document.
- **Simulation versus field evidence:** simulation-backed trade-offs are not measured savings. Source-inspected code is not an end-to-end runtime test. Public/synthetic profiles cannot be scored as expert designs without real design labels.
- **Compatibility example:** BYD's cited BCU2.0 matrix permits three HVM modules with PLENTICORE G3; listed Fronius/SMA/GoodWe families begin at four. This is researched support, not current engine enforcement or installation approval.

## Scope of changes

All changes are under `research/external/`. Application, contracts, model configuration, PLAN.md, docs/PITCH.md and eval implementation were left untouched. The three task reports are separate Markdown deliverables. Original research is retained with update pointers. No private dataset/raw rows, credentials or private test predictions were accessed for this work; pitch data is aggregate-only. No public hosting or messages to another agent/board were performed.

The HTML presentation was checked in headless Chromium: all 11 slides, layout overflow, numerical strings against the pinned evidence, five-minute timing, navigation, notes, overview, print visibility, mobile controls, zero page errors and zero unexpected network requests. Screenshots were visually inspected. This verifies the presentation, not the product. Geist is not bundled, so the deck uses an offline system-font fallback.

## Remaining work, in priority order

1. Rehearse the actual planner → edit → diff → homeowner curve path; verify lock/share before adding them to the timed demo. A fallback video is not recorded here.
2. Reconcile final official evaluation results with the separate pitch script. Do not choose whichever test row looks best. If results/config change, deliberately repin evidence and update the deck; the verification script reports whether the current source still matches the pinned hash.
3. Implement only the narrow dev stress suite first, using Task 2's spec. Keep synthetic development/final pools separate and do not use synthetic pass rates as expert accuracy. No extra real-test tuning.
4. If demo-critical, implement a small allowlist for the exact intended battery/inverter family; otherwise keep the current compatibility statement at research status. Exact full-system electrical/hydraulic design, accessory BOM, licences and region/firmware checks remain open.
5. R7–R9 remain deferred pending explicit review materials and the intended review scope. Ask-next/oracle uplift, calibrated intervals, complete BOM export, deployment and a third-installer pilot are not marked completed by this research.

## Short prompt to give Claude

> Read research/external/RESEARCH-LEAD-HANDOFF.md and its linked Task 1–3 reports. Use pitch-codex/PITCH.md and index.html as a separate evidence-grounded pitch draft. Correct the unsupported overall-win claim, preserve UNVERIFIED labels, and reconcile only demo-critical findings. Manufacturer pairings are researched; current engine behavior is catalogue snapping, not pairing enforcement. Keep synthetic plausibility tests separate from expert-match evaluation and do not tune on the final test.
