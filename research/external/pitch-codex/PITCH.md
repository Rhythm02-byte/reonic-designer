# Home Energy Designer: five-minute pitch

**Draft for rehearsal, 7 November 2026.** Eight slides; target 5:00 including a 75-second demonstration. The presentation works offline. Its product diagram is an explanatory schematic, **not a live application screenshot**. Current capabilities described here are supported by source/document inspection, **not runtime verification by this pitch work**. A live application demonstration is conditional on the local engine and web app passing rehearsal. No completed pilot, measured business impact or optimal-design guarantee is claimed.

Evidence is pinned to `evidence-pinned.json`, generated **2026-11-07T18:59:49+00:00**, copied from `eval/results/latest.json`. Use its `test` block, representing the original **`selection.test`**, and its validation-selected **M1, PV gate 0.6**. The original top-level headline describes H1 and must not replace the selected result.

## Spoken script and slide direction

### 1. A first draft your planner can defend

**0:00–0:30 · 30 seconds**

**On screen:** Home Energy Designer. “Installer habits + energy trade-offs + visible assumptions.” A simple home-to-draft diagram; no invented performance metric.

“A homeowner asks for solar, storage, perhaps a heat pump and an EV charger. The planner has to turn incomplete information into a proposal they can explain.

“Our idea is a first draft your planner can defend: learn from the installer's previous choices, check energy trade-offs with a deterministic simulator, and make the assumptions visible. The planner keeps responsibility for the final design.”

### 2. Missing inputs matter more than another decimal

**0:30–1:00 · 30 seconds**

**On screen:** “Known / Assumed / Still needed.” Illustrative fields: annual electricity, future EV, roof capacity. Label them as examples, not extracted household records.

“The challenge is more than predicting a number. A roof limit, a future EV or an assumed annual consumption can change the proposal. A precise-looking answer can hide those gaps.

“We therefore separate a proposed size from the evidence behind it. Our evaluation asks whether the draft resembles recorded expert choices. That is useful evidence, but it does not prove that a design is optimal or installation-ready.”

### 3. Learn installer habits. Check energy trade-offs.

**1:00–1:35 · 35 seconds**

**On screen:** Inputs → learned installer policy → hourly simulation → general rules/catalogue steps → reviewable draft. Caption: “Explanatory architecture diagram.”

“The learned policy proposes component sizes. Hourly simulation estimates energy and economic outcomes under stated assumptions. General rules and catalogue snapping keep proposed sizes on supported numerical steps.

“These are distinct jobs: imitate choices, explore trade-offs, and support review. Language models may phrase explanations or parse an input change. They do not size the system. The deterministic path works without an LLM API key.

“The current battery curve is a physics-based comparison, not a guarantee of future savings.”

### 4. PV improves. Whole-design accuracy still needs work.

**1:35–2:15 · 40 seconds**

**On screen:** Three paired comparisons. Prominent PV result, equally readable EMS and whole-design results. Footer: “2026 test n=325; validation n=232; M1 selected on validation.”

“Here is the result we can defend. We selected M1 on 232 validation projects, then scored the selected configuration on 325 projects from 2026.

“PV agreement within the stated twenty-percent tolerance rose from 42.5 to 56.3 percent against the installer-median baseline: 13.8 percentage points.

“The broader result is mixed. EMS fell from 61.1 to 58.8, and whole-design agreement fell from 20.6 to 16.9 percent. We are not claiming an overall accuracy win. We have a useful PV improvement and clear work remaining on the complete bundle.”

### 5. One change. A visible consequence.

**2:15–3:30 · 75 seconds**

**On screen:** Live local app after rehearsal, otherwise the clearly labelled offline walkthrough. Follow the sequence below.

“Let me show the workflow using an illustrative household, not a private customer record.

“Here are the inputs and the proposed system. I change annual electricity from 4,500 to 6,500 kilowatt-hours. The diff shows the actual consequence for the proposal and calculated outcomes. A result that stays the same is also informative; a bigger input does not force every component to grow.

“Now look at the battery comparison. The question is what the next size adds under these assumptions, and what it costs. The planner can discuss that trade-off instead of presenting the recommendation as inevitable.

“This is the starting point for a qualification conversation. The installer still checks the roof, equipment and site.”

### 6. When we don't know, the planner should see it

**3:30–4:00 · 30 seconds**

**On screen:** Two columns: “Current: stated inputs and scenario assumptions” / “Next: rank the questions that could change the design.” Mark Ask-next **planned; implementation not verified**.

“The next step is Ask-next: rank missing or placeholder inputs by how much an answer could change the design or price, then show at most three questions.

“We are not presenting that ranking as completed. It needs implementation and evaluation. The principle is simple: ask about a meaningful uncertainty before adding another decimal to the answer.”

### 7. Compatibility has a concrete rule

**4:00–4:25 · 25 seconds**

**On screen:** Small manufacturer-evidence example, not a product approval badge. “Current: catalogue snapping. Next: pairing validation.”

“Compatibility is also specific. In BYD's reviewed matrix, three HVM modules are listed with KOSTAL PLENTICORE G3; Fronius Symo GEN24 Plus starts at four. Firmware and exact revisions matter too.

“We researched those conditions. The current engine snaps sizes to catalogue steps; it does not enforce manufacturer pairing rules. That is the next validation layer.”

### 8. Give the planner a better starting point

**4:25–5:00 · 35 seconds**

**On screen:** “Next: supervised planner pilot.” Three outcomes: correction time, design changes, homeowner comprehension. “Compare with today's workflow.”

“Our proposition is a better starting point for the planner: a useful PV draft, an inspectable energy comparison, and a clear boundary between calculation and final approval.

“Next, we would run a supervised pilot against the existing workflow. We would measure time to a reviewed proposal, corrections, and whether homeowners understand the trade-offs. We have not measured those business outcomes yet.

“The goal is practical: help the planner reach a proposal they can explain, correct and stand behind.”

## Demonstration runbook and fallback

Use a synthetic, manually entered household. Annual electricity **4,500 → 6,500 kWh** is the fixed illustrative edit for both deck and app, not an expected output or private observation. Keep other settings fixed. Rehearse the exact browser state, diff and homeowner battery-curve route before presenting. The main flow has no EV edit.

| Time within slide 5 | Action | Narration purpose |
|---|---|---|
| 0–15 s | Show initial inputs and draft | Establish which assumptions are supplied. |
| 15–35 s | Change annual electricity 4,500 → 6,500 kWh; wait for recalculation and show the diff | Connect an input to actual observed outputs; invent no delta. |
| 35–60 s | Open the existing homeowner battery comparison in the offer view | Explain selected versus alternative size, annual savings and self-sufficiency, only where actually shown. |
| 60–75 s | Point to assumptions and return to deck | State what still needs installer review. |

**Optional, only after successful rehearsal:** within the same 75 seconds, replace up to ten seconds of the explanation with a battery pin and repeated demand edit to show whether the pin is preserved. Say “This battery is pinned; now I repeat the demand edit” only when the observed state supports it. Sharing may be used solely as the rehearsed route to the homeowner curve; otherwise open the offer view directly. Neither optional flow adds time or becomes a promised capability.

**Fallback trigger:** switch immediately if the app errors, uses unexplained demo data, or stalls for more than five seconds. Do not debug on stage. Say: “I am switching to the offline walkthrough. This is a schematic of the interaction, not a live calculation.” Use the deck's demand 4,500 → 6,500 → proposal diff → battery-trade-off diagram. Explain the same sequence without invented numeric results. If a recording exists and has been checked, it may replace the schematic; no recording is promised here.

Do not demo unverified Ask-next, complete BOM/CSV export or manufacturer pairing rejection. Do not promise public QR access without rehearsal. The offline deck has no dependency on those features. Capture no private project rows in screenshots, recordings or shared links.

## Jury Q&A

- **“Does this beat the installer median?”** On selected-model PV agreement, yes: 56.3% versus 42.5%. On EMS and whole-design agreement, no. We report both and keep that baseline in the next evaluation.
- **“Why not present H1's better EMS?”** H1 was not the validation-selected configuration in this pinned run. Choosing the best test result afterward would change the selection protocol. Future selection belongs on validation, followed by a clearly versioned evaluation.
- **“Are expert choices ground truth?”** They are observed reference choices for imitation, not proof of technical or economic optimality. Missing constraints and multiple acceptable systems limit that interpretation.
- **“Why not use an LLM to design everything?”** Sizing comes from the learned policy, deterministic calculations and rules. Language assistance is optional and cannot certify engineering suitability.
- **“Is the battery optimum reliable?”** It is a scenario comparison under the simulator's load, weather, tariff, loss and price assumptions. It is not a guaranteed return or a site-specific engineering approval.
- **“Does it handle every installer or heat pump?”** Broad transfer is not established by this evidence. Two-installer history is a narrow base; rare component cases need separate assessment. Do not turn high absence-dominated component agreement into a sizing claim.
- **“Is compatibility solved?”** Selected manufacturer conditions are researched. Pairing enforcement, full accessories and site checks are not implemented as a complete validation layer.
- **“What business impact have you measured?”** None in a completed pilot. Time savings, fewer corrections and better comprehension are pilot hypotheses, with the existing workflow as comparator.

## Claim ledger and source paths

| Claim | Evidence / status | Allowed wording |
|---|---|---|
| M1 selected; PV gate 0.6 | Pinned `chosen`; criterion validation EMS, tie-break whole design | “Validation-selected M1.” |
| Validation 232; 2026 test 325 | Pinned windows/counts; refit train+validation through 2025-12-31 | “Pinned evaluation,” not a new Codex rerun. |
| PV 56.3% vs B0 42.5% | Pinned `test.M1.pv` / `test.B0.pv`, rounded | “+13.8 percentage points,” not “13.8% relative.” |
| EMS 58.8 vs 61.1 | Same selected test block | Explicitly acknowledge lower aggregate score. |
| Whole design 16.9% vs 20.6% | Same selected test block | Explicitly acknowledge lower agreement. |
| Hourly simulator, physics curve, numeric catalogue snapping | Handoff and compatibility code audit; live interaction still needs rehearsal | “Current mechanism,” not guaranteed economics. |
| Ask-next ranking | Handoff next-work item | “Planned; implementation not verified.” |
| BYD HVM module-count example | Task 3's manufacturer matrix V2.22, 2026-10-10 | “Researched conditional pairing,” not enforced or certified. |
| Full BOM export / pilot / business uplift | Not established | Omit completion and causal-impact claims. |

**Primary numeric source:** [evidence-pinned.json](evidence-pinned.json), source SHA-256 `41a377ed18480e1ac1ec20592bafaf2c370eb04b145f64641f331ae4e6db6821`. Do not substitute a changing `latest.json` without refreshing the entire evidence presentation.

**Repository sources:** [pitch notes](../../../docs/PITCH.md), [handoff](../../../docs/HANDOFF-CODEX.md), [design system](../../../docs/DESIGN.md), [Task 3 compatibility audit](../TASK3-COMPATIBILITY-VERIFIED.md), [R5 evaluation boundaries](../R5-learning-configurations.md), [R6 trust evidence](../R6-homeowner-trust.md). These links are relative for portable artifact review.

**Manufacturer source:** [BYD HVS/HVM BCU2.0 compatible inverter list V2.22](https://site.bydbatterybox.com/uploads/downloads/BCU2.0_261010_BYD_Battery_Box_Premium_HVS%26HVM_Compatible_Inverter_List_V2.22-6ac9cfeb73807.pdf), previously opened and documented in Task 3. Counts alone omit firmware, region, accessories and site conditions.

**Reconciliation rule:** `docs/PITCH.md` contains aspirational Ask-next/business wording and a Q&A overall-win statement that conflict with the pinned selected result. This script deliberately uses the narrower supported claims. No shared pitch notes, application files or evaluation artifacts were edited.
