# CONTEXT: Reonic challenge, thinc! München 2026

Shared brief for everyone on the team and for any coding agent working in this repo.
Keep the **Status** and **Decisions** sections current; they are the source of truth.

## 0. Start here: read the challenge PDF first

**Before touching any code, every teammate reads `Reonic_Hackathon_Challenge_final.pdf` completely** (8 pages, about 15 minutes).
This file summarises the PDF but does not replace it. The PDF is how the judges will score us.

You understand it when you can answer these without looking:
1. Who are the two personas, and which one does the **minimum result** serve? (p. 4)
2. What does "as appropriate" mean, and why is "no battery" or "no heat pump" a valid expert answer? (p. 4)
3. What are the three core building blocks, and what are the three parts of the minimum result? (pp. 6–7)
4. What are the four steps of the demo moment? (p. 7)
5. What are the four evaluation criteria? (p. 8)
6. What exactly must be submitted, and by when? (p. 8)
7. What counts as "AI being a real part of the solution", and what does not? (p. 6)
8. What are we not allowed to do with the data? (p. 8)

Then read this file, then the README.

## 1. The challenge in one paragraph

Planners at solar installers spend hours designing each home's system before an offer can go out.
Build an AI system that turns a few facts about a home into a complete design: **PV (kWp), battery (kWh)
and heat pump (kW), each only if appropriate** (we also predict the wallbox, which the data shows is common), with a short explanation. The design must decide the way an
experienced planner would, measured against the designs installers actually delivered (Reonic's dataset).
Source: `Reonic_Hackathon_Challenge_final.pdf` (see §0).

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
HomeInputs ─► features (raw + physics-informed: EV kWh, future demand, kWp needed for full demand)
           ─► learned chain, in physical order:
                heat pump? & size ─► PV? & size ─► battery? & size ─► wallbox? & size
                (each step sees the upstream decision, so the design is coherent and overrides propagate)
           ─► deterministic rules (IDs R01–R04): hard constraints + snap to sizes installers actually use
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
| `src/reonic/data.py` | Raw Reonic export → one canonical row per project (inputs + rebuilt expert design), `OPTION_CHOICE`, `MODULE_WP`, feature building |
| `src/reonic/physics.py` | Yield, self-consumption, EV and heat pump demand, capex, savings. Rough constants, all marked TODO-calibrate |
| `src/reonic/model.py` | `DesignModel` (classifier + regressor chain), `Neighbours` (similar projects) |
| `src/reonic/rules.py` | Rules R01–R06 and catalog snapping |
| `src/reonic/engine.py` | `Designer`: train / design / design_batch / validate / explain. The one engine behind every view |
| `src/reonic/evaluate.py` | Held-out metrics + `reports/eval.json` + per-project `reports/test_predictions.csv` |
| `src/reonic/baseline.py` | Naive rule-of-thumb designer |
| `src/reonic/synth.py` | **Fake** data shaped like the real export, for tests and teammates without the data |
| `app.py` | Streamlit planner UI (Design / Validate & compare / Evaluation) |
| `tests/` | Loader (on a hand-made mini export), rules, physics, engine (19 tests) |

Rules: R01 existing heat pump → no new one · R02 no new or existing PV → no battery · R03 PV ≤ 30 kWp · R04 battery ≤ 2 kWh per kWp (new + existing PV) · snapping of battery, heat pump and wallbox to the most common sizes in the data. (Roof and budget rules were dropped: the export has no roof area or budget.)

## 6. Metrics (definitions)

Per component, on held-out projects:
- `include_accuracy` / `include_f1`: did we include the component when the expert did?
- `size_median_rel_error`: size error where both included it.
- `within_tolerance`: agrees on include/exclude **and** size within ±20% (PV) or ±25% (battery, heat pump). Wallbox: include/exclude only. Where the expert PV size is unknown (NaN), only include/exclude is scored.
- `whole_design_within_tolerance`: all four at once. **This is the headline number for the pitch.**
- `expert_include_rate`: how often experts included it. Read accuracy against this, because heat pump accuracy of 99% is trivial when experts include one in 0.3% of designs.

Split: random 80/20 by default. `--group-col installer_id` trains on one installer and tests on the other, the honest "unseen installer" number. The report also breaks the score down per installer.

## 7. Data: status and open questions

**Status (2026-11-07):** real export received and loaded. It lives in `data/raw/<installer_id>/` (gitignored; copy it there from the shared download). `python -m reonic build` writes the flattened table to `data/projects.csv` for inspection. Synthetic numbers must never go in the pitch.

**What the export contains:** two folders, which we assume are two installers.

| | `23c108b7` | `2a8ba8e2` |
|---|---|---|
| Projects | 336 usable (342 in status quo) | 1,257 usable (1,277) |
| Projects with >1 option | 6% | 22% |
| PV size recoverable | 99% | 93% |
| Period | 2025 | mid-2024 → 2025 |

- `projects_status_quo.csv` holds the home before the offer, which gives us the **inputs**.
- `project_options_parts.csv` holds every line item of every offered option. The **expert design is rebuilt from these** in `data.option_designs`.

**Quirks handled in `data.py`:**
- **Units:** `_kw`/`_kwh`/`_wh` columns hold W/Wh, so values are divided by 1000. `energy_price_per_wh` × 1000 gives €/kWh.
- **Swapped columns:** battery capacity is in `inverter_power_kw` on `BatteryStorage` rows, and inverter power is in `battery_capacity_kwh` on `Inverter` rows.
- **PV kWp is rebuilt** in this order of priority:
  1. `Module` rows (W × qty)
  2. "Complete Package … 10.8kWp + 9kWh" names
  3. module count from per-module lines (`DC Install…`, `Substructure…`, `Roof Mounting…`) × `MODULE_WP` = 450 W (**assumed**)
  4. otherwise NaN (offered but size unknown, 90 projects)
- **Battery** = itemised `BatteryStorage` rows. A package's kWh only counts when the battery isn't itemised, to avoid double counting.
- **Several options per project, signed one not marked.** `OPTION_CHOICE = "first"` (lowest option_number) **until Reonic answers**.

**What the data says about the problem:**
- **Heat pumps are almost never offered:** 0.3% of chosen designs (31 rows in the whole export). The heat pump decision is effectively "no", so we can't learn sizing from this data. In the pitch, say so honestly. Note that many heat pump offers are separate options, which `OPTION_CHOICE="first"` may drop.
- **The real components are PV, battery and wallbox.**
  - Batteries appear in about 89% of designs (median 9–10 kWh).
  - PV in about 86% (median about 8 kWp).
  - A wallbox in 26%, and an EV makes one much more likely.
- **Storage-only retrofits exist** for homes that already have PV (R02 allows them).
- **Inputs are thin:**
  - Reliable: demand, price, price increase, EV, load profile, existing PV/battery/wallbox, flexible tariff.
  - Sparse: heating type and heating demand, about 12%.
  - Essentially empty: house size and inhabitants, under 1%.
  - Absent: roof area and budget.
- **The installers behave differently.** At `2a8ba8e2`, PV tracks demand and battery tracks PV. At `23c108b7`, designs look package-driven.
- **Outliers to look at (data & EDA workstream):** consumption 0 or 50,000 kWh, PV up to 99.9 kWp, battery up to 108 kWh. These may be commercial projects or data errors.

**First real evaluation** (random split, `OPTION_CHOICE=first`, untuned):

| Metric | Model | Baseline |
|---|---|---|
| Whole design within tolerance | **15.7%** | 3.8% |
| PV within ±20% | 45% | 16% |
| Battery within ±25% | 39% | 24% |
| Wallbox include accuracy | 61% | 74% |

The model **loses on wallbox**, so threshold tuning is needed. The numbers will move once the signed-option and module-wattage answers arrive.

**Open questions for Reonic** (to ask the experts on site):
1. **Which option was signed?** Lowest or highest option_number, or can't it be told from the data?
2. **What module wattage does installer `2a8ba8e2` use?** And is the quantity on DC Install / Substructure lines always the module count?
3. Are `inverter_power_kw` and `battery_capacity_kwh` really swapped in the export?
4. Do package lines include the battery, or can a separate battery come on top?
5. Does `energy_demand_wh` include an existing EV or heat pump?
6. What do the folder IDs represent: installers?
7. Realistic time per design today, and offer → signed rate, for the business case.

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

- **First:** read the challenge PDF (§0). Then pick a workstream from §8 and tell the team which one you've taken.
- **Tasks** are tracked in this file: the §11 Status checklist plus the workstreams in §8. We don't use a ticket tool.
- **Branches:** one per task, named `<your-name>/<short-topic>` (e.g. `nikita/eda-outliers`). Small PRs into `main`, and `main` always runs.
- **Before pushing:** `pytest -q` and `python -m reonic eval`.
- **Commits:** one-line summary of what changed and why.
- Update **Status** (§11) when you finish something that changes what others can rely on. Record choices in **Decisions** (§10).

## 10. Decisions log

- 2026-11-07: Python + scikit-learn gradient boosting + Streamlit, chosen for speed. No infrastructure.
- 2026-11-07: Model order heat pump → PV → battery, following the physics (load → generation → storage).
- 2026-11-07: LLM is optional and last-mile only (plain-language explanation for homeowners). It must never change numbers.
- 2026-11-07: No ticket tool. Tasks live in this file (§8 workstreams, §11 Status). Everyone reads the challenge PDF before starting.

## 11. Status

- [x] Repo skeleton, end-to-end pipeline on synthetic data, UI
- [x] Real data loaded: loader rebuilt around the Reonic export, 19 tests passing, first real eval beats baseline 15.7% vs 3.8%
- [ ] Every teammate has read the challenge PDF (§0)
- [ ] Answers from the Reonic experts to the signed-option and module-wattage questions (§7)
- [ ] Physics constants calibrated with Reonic experts
- [ ] Include-probability thresholds tuned; wallbox is currently worse than the baseline
- [ ] Deviation analysis · alternatives/confidence · homeowner view
- [ ] Pitch deck · demo recording · final README
