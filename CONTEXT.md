# CONTEXT: Reonic challenge, thinc! München 2026

Read this first. It is the shared brief for everyone on the team and for any coding agent working in this repo.
Keep the **Status** and **Decisions** sections current; they are the source of truth.

## 1. The challenge in one paragraph

Planners at solar installers spend hours designing each home's system before an offer can go out.
Build an AI system that turns a few facts about a home into a complete design: **PV (kWp), battery (kWh)
and heat pump (kW), each only if appropriate**, with a short explanation. The design must decide the way an
experienced planner would, measured against the designs installers actually delivered (Reonic's dataset).
Source: `../Reonic_Hackathon_Challenge_final.pdf`.

## 2. Deadlines and deliverables

| When | What |
|---|---|
| Sat 7 Nov, 14:00 | Build starts |
| **Sun 8 Nov, 15:00** | **Submission:** working end-to-end demo (plus a recorded fallback), GitHub repo with README (setup, approach, known limitations), short pitch deck (problem, solution, evaluation, value for installers and homeowners) |

**Minimum result (do this first):**
1. For a project, propose a complete design (PV, battery, heat pump as appropriate) plus a short explanation.
2. Measure closeness to expert designs on **projects the system has not seen**.
3. The planner changes an input or component and gets an updated design.

**Stretch goals:** analyse where and why we deviate from the experts · alternatives and confidence per recommendation · a planner validation view ("this battery is unusually large") or a homeowner view on the same engine.

**Judging (equal weight, no percentages given):** technical depth (reproduce expert decisions and measure it convincingly) · user fit (planner and/or homeowner, refine and understand) · business impact (time per offer, quality, win rate) · execution and demo.

**Rules:** AI must be a real part of the solution; models trained on the data count, an LLM is optional. A single ungrounded LLM prompt does not count. **Reonic data must never leave the team: never commit it** (`data/` is gitignored).

## 3. The 5-minute demo story (what judges want to see)

1. A planner enters a few facts about a home (sidebar).
2. A complete system appears with a short "why" (Design tab).
3. Refine: "the family is buying an EV next year". Tick *Electric car* and PV/battery adapt. Or override a component and watch everything downstream re-plan.
4. Check against reality: the same project next to the expert design (Validate & compare tab), then accuracy across many projects versus a naive baseline (Evaluation tab).

## 4. Architecture

```
HomeInputs ─► features (raw + physics-informed: EV kWh, heat demand, kWp needed, roof limit)
           ─► learned chain, in physical order:
                heat pump? & size ─► PV? & size ─► battery? & size
                (each step sees the upstream decision, so the design is coherent and overrides propagate)
           ─► deterministic rules (IDs R01–R06): hard constraints + snap to sizes installers actually use
           ─► explanation: model confidence + what the k most similar past projects got + physics/economics
           ─► validation: is this design unusual for homes like this one?
```

Principles:
- **The model decides, rules constrain, the LLM (optional) only phrases.** No LLM in the decision path.
- **A planner override always wins.** Rules flag a locked value; they never change it.
- **Unknown stays unknown.** A missing input is NaN all the way through; the gradient-boosting models handle it natively. Never impute silently in the UI.
- **Report against a baseline.** `baseline.py` is a naive rule of thumb, and the model has to beat it.

## 5. Repo map

| Path | What |
|---|---|
| `src/reonic/schema.py` | Canonical field names, `HomeInputs`, `Design` |
| `src/reonic/data.py` | Load the dataset, **`COLUMN_MAP` / `HEATING_MAP` (fill these when the real data arrives)**, feature building |
| `src/reonic/physics.py` | Yield, self-consumption, EV and heat pump demand, capex, savings. Rough constants, all marked TODO-calibrate |
| `src/reonic/model.py` | `DesignModel` (classifier + regressor chain), `Neighbours` (similar projects) |
| `src/reonic/rules.py` | Rules R01–R06 and catalog snapping |
| `src/reonic/engine.py` | `Designer`: train / design / design_batch / validate / explain. The one engine behind every view |
| `src/reonic/evaluate.py` | Held-out metrics + `reports/eval.json` + per-project `reports/test_predictions.csv` |
| `src/reonic/baseline.py` | Naive rule-of-thumb designer |
| `src/reonic/synth.py` | **Fake** data in the canonical schema so everything runs before the real data arrives |
| `app.py` | Streamlit planner UI (Design / Validate & compare / Evaluation) |
| `tests/` | Rules, physics and engine behaviour (13 tests) |

Rules: R01 existing heat pump → no new one · R02 no PV → no battery · R03 PV ≤ roof area / 5.5 m² and ≤ 30 kWp · R04 battery ≤ 2 kWh per kWp · R05 (implicit) snap battery and heat pump to the most common installed sizes · R06 flag if cost > budget +10%.

## 6. Metrics (definitions)

Per component, on held-out projects:
- `include_accuracy` / `include_f1`: did we include the component when the expert did?
- `size_median_rel_error`: size error where both included it.
- `within_tolerance`: agrees on include/exclude **and** size within ±20% (PV) or ±25% (battery, heat pump).
- `whole_design_within_tolerance`: all three at once. **This is the headline number for the pitch.**

Split: random 80/20 by default. If the data has an installer or company ID, run `--group-col <col>` so we test on unseen installers. That is the more honest number.

## 7. Data: status and open questions

**Status:** not received yet. Everything currently runs on `synth.py` fake data. **Never quote synthetic numbers in the pitch.**

When it arrives:
1. Put the file in `data/` (gitignored).
2. Fill `COLUMN_MAP` and `HEATING_MAP` in `data.py`.
3. Run `python -m reonic eval --data data/<file>`.

Questions for the Reonic experts on site:
- Does annual consumption already include an existing EV or heat pump? This changes the demand features.
- Does a blank component size mean "not installed"? (Currently assumed yes.)
- Is there an installer ID? (Needed for the group split.) A date? (Needed for a time split.)
- Which inputs does a planner really have at first contact? That is our minimum input set.
- Typical module power and battery product sizes; heat pump sizing rule of thumb (W/m² or heat load).
- Realistic time per design today (hours) and offer → signed conversion rate, for the business case.

## 8. Plan and milestones

| Milestone | Target | Done when |
|---|---|---|
| M0: real data in | Sat 16:00 | Real data loads, column maps filled, first `eval` run on real data |
| M1: minimum result | Sat 22:00 | Beats the baseline on held-out data; explanation and refine work on real data |
| M2: stretch | Sun 09:00 | Deviation analysis, alternatives/confidence, validation or homeowner view |
| M3: freeze | Sun 13:00 | Code freeze. Deck, demo recording and README final. Rehearse the demo twice |
| Submit | **Sun 15:00** | |

Workstreams (one owner each):
1. **Data & EDA:** load real data; find expert thresholds and typical bundles (battery-to-PV ratio, heat pump by heating type, sizes by consumption) → feed into features and rules.
2. **Model & eval:** include thresholds (tune by cost of error, not 0.5 by default), hyperparameters, group split, deviation analysis.
3. **Product/UI:** demo flow, validation view, homeowner "try variants" view.
4. **Pitch & business case:** deck, time-per-offer model, demo script, recording.

## 9. Team workflow

- **Tickets:** Linear project "Reonic · Home Energy Designer (thinc! 2026)", team MAR, tickets MAR-54 to MAR-69:
  https://linear.app/marketing-vibe-coding/project/reonic-home-energy-designer-thinc-2026-0e10cbdb4a2d
  - Milestones M0–M3 match §8.
  - Labels: Phase (MVP / Stretch / Wrap-up) and Workstream (Data & EDA / Model & Eval / Product & UI / Pitch & Business).
- **Claiming a ticket:** assign yourself and move it to In Progress.
- **Branches:** one per ticket, using Linear's "Copy git branch name" (e.g. `rhythmkashik02/mar-54-...`) so the PR links to the ticket automatically. Small PRs into `main`, and `main` always runs.
- **Before pushing:** `pytest -q` and `python -m reonic eval`.
- **Commits:** put the ticket ID in the message (e.g. `MAR-54: map Reonic columns`).
- Update **Status** below when you finish something that changes what others can rely on.

## 10. Decisions log

- 2026-11-07: Python + scikit-learn gradient boosting + Streamlit, chosen for speed. No infrastructure.
- 2026-11-07: Model order heat pump → PV → battery, following the physics (load → generation → storage).
- 2026-11-07: LLM is optional and last-mile only (plain-language explanation for homeowners). It must never change numbers.

## 11. Status

- [x] Repo skeleton, end-to-end pipeline on synthetic data, UI, 13 tests passing
- [ ] Real data loaded (M0)
- [ ] Physics constants calibrated with Reonic experts
- [ ] Include-probability thresholds tuned (on synthetic data the heat pump is under-predicted at 0.5)
- [ ] Deviation analysis · alternatives/confidence · homeowner view
- [ ] Pitch deck · demo recording · final README
