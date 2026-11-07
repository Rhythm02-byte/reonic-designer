# CONTEXT: Reonic challenge, thinc! München 2026

Shared brief for everyone on the team and for any coding agent in this repo. What's here is needed for every task.
- Plan, milestones and who does what: [PLAN.md](PLAN.md)
- Data work: skill `reonic-data` (`.claude/skills/reonic-data/`)
- Evaluation and reporting results: skill `reonic-evaluate` (`.claude/skills/reonic-evaluate/`)
- One feature at a time: specs in [docs/specs/](docs/specs/)

## 0. Start here

**Before touching any code, read `Reonic_Hackathon_Challenge_final.pdf` completely** (8 pages). This file summarises the PDF but does not replace it. The judges score us against the PDF.

You understand it when you can answer these without looking:
1. Who are the two personas, and which one does the **minimum result** serve? (p. 4)
2. What does "as appropriate" mean, and why is "no battery" or "no heat pump" a valid expert answer? (p. 4)
3. What are the three core building blocks, and the three parts of the minimum result? (pp. 6–7)
4. What are the four steps of the demo moment? (p. 7)
5. What are the four evaluation criteria? (p. 8)
6. What exactly must be submitted, and by when? (p. 8)
7. What counts as "AI being a real part of the solution", and what does not? (p. 6)
8. What are we not allowed to do with the data? (p. 8)

## 1. The challenge

Planners at solar installers spend hours designing each home's system before an offer can go out. We build a tool that takes a few facts about a home and proposes a complete design: **PV (kWp), battery (kWh), heat pump (kW) and wallbox (kW)**, each only where appropriate, with a short explanation. The design should match what experienced planners actually sold, and we measure how close we get on projects the model has not seen.

**Deadline:** submission Sunday 8 Nov, 15:00. Working demo (plus a recorded fallback), GitHub repo with README, short pitch deck.

**Rules:** AI must be a real part of the solution, and models trained on the data count. An LLM is optional and may only phrase text. A single ungrounded LLM prompt does not count. Reonic data never leaves the team and is never committed.

## 2. Principles

- **Build first, then report what the data gives.** Reonic's advice: do not make results look better than they are. Ship a working version, measure it on the real data, and compare it with a baseline. Open questions are answered in the data or in writing, never assumed silently.
- **The model decides, rules constrain, the LLM only phrases.** No LLM in the decision path.
- **A planner override always wins.** Rules flag a locked value, they never change it.
- **Unknown stays unknown.** Missing inputs stay NaN through the pipeline. Never impute silently in the UI.
- **The model must beat a naive baseline** (`baseline.py`). If it doesn't, say so.

## 3. Architecture

```
HomeInputs ─► features (raw + physics-informed: EV kWh, future demand, kWp for full demand)
           ─► learned chain, physical order:
                heat pump? & size ─► PV? & size ─► battery? & size      then wallbox = rule (has an EV)
                (each step sees the upstream decision, so overrides propagate)
           ─► deterministic rules R01–R04 + snapping to sizes installers actually use
           ─► explanation: model confidence + similar past projects + rough physics/economics
           ─► validation: is this design unusual for homes like this one?
```

## 4. Repo map

| Path | What |
|---|---|
| `src/reonic/schema.py` | Canonical field names, `HomeInputs`, `Design` |
| `src/reonic/data.py` | Raw export → one row per project; `OPTION_CHOICE`, `MODULE_WP`, features |
| `src/reonic/physics.py` | Yield, self-consumption, EV and heat pump demand, capex, savings (rough constants) |
| `src/reonic/model.py` | `DesignModel` (classifier + regressor chain), `Neighbours` |
| `src/reonic/rules.py` | Rules R01–R04 and catalog snapping |
| `src/reonic/engine.py` | `Designer`: train / design / design_batch / validate / explain |
| `src/reonic/evaluate.py` | Held-out metrics → `reports/eval.json`, `reports/test_predictions.csv` |
| `src/reonic/baseline.py` | Naive rule-of-thumb designer |
| `src/reonic/synth.py` | Fake data shaped like the export, for tests and teammates without the data |
| `app.py` | Streamlit planner UI |
| `tests/` | Loader, rules, physics, engine (19 tests) |

Rules: R01 home already has a heat pump → none new · R02 no new or existing PV → no battery · R03 PV ≤ 30 kWp · R04 battery ≤ 2 kWh per kWp (new + existing PV) · snapping of battery, heat pump, wallbox to common sizes in the data.

## 5. Metric definitions

Per component, on held-out projects:
- `include_accuracy`, `include_f1`: did we include the component when the expert did?
- `size_median_rel_error`: size error where both included it.
- `within_tolerance`: include/exclude agrees **and** size within ±20% (PV) or ±25% (battery, heat pump). Wallbox: include/exclude only. Where the expert PV size is unknown, only include/exclude is scored.
- `whole_design_within_tolerance`: all four at once. **The headline number.**
- `expert_include_rate`: how often experts included it. Always read accuracy against this.

Default split is random 80/20. `--group-col installer_id` holds out one installer, the honest "unseen installer" test.

## 6. Status and decisions

**Status**
- [x] Repo skeleton, end-to-end pipeline, planner UI
- [x] Real data loaded (`reonic-data` skill); first real eval recorded in `reonic-evaluate`
- [ ] Every teammate has read the challenge PDF (§0)
- [ ] Reonic answers to the open questions (`reonic-data` skill, "Open questions")
- [ ] Physics constants checked with Reonic experts
- [x] Wallbox decided: deterministic "has an EV → wallbox" rule (CV showed no gain from a model). Whole-design score is 13.5% with it. Precision, recall and F2 reported (see `reonic-evaluate`)
- [x] Unseen-installer evaluation run in both directions: 18.5% / 9.8% whole design vs baseline 4.2% / 5.6% (see `reonic-evaluate`)
- [x] Demo flow works on real data: example held-out homes in the sidebar, live design next to the expert's, refine (EV) and override steps, app trained on the training split only. Covered by `tests/test_app.py`
- [ ] Tune battery and heat pump include thresholds on a validation split
- [x] Deviation analysis done: three patterns with counts and rates, chart in `docs/figures/` (see `docs/specs/deviation-analysis.md`)
- [ ] Alternatives/confidence · homeowner view (specs in `docs/specs/`)
- [ ] Pitch deck · demo recording · final README

**Decisions**
- 2026-11-07: Python + scikit-learn gradient boosting + Streamlit, for speed. No infrastructure.
- 2026-11-07: Model order heat pump → PV → battery → wallbox, following the physics (load → generation → storage).
- 2026-11-07: Wallbox is a deterministic rule (has an EV → wallbox), not a model. CV showed no gain from learning it; the cost is a lower whole-design score (13.2% vs 15.7%).
- 2026-11-07: LLM optional and last-mile only. It must never change numbers.
- 2026-11-07: No ticket tool. Tasks live in PLAN.md. Everyone reads the PDF before starting.
- 2026-11-07: Build on the real data and report the honest result, rather than tuning on the test set or hiding weak areas (wallbox, heat pump).

## 7. Team workflow

- **First:** read the PDF (§0). Then pick a workstream from [PLAN.md](PLAN.md) and tell the team.
- **Branches:** `<your-name>/<short-topic>`, small PRs into `main`. `main` always runs.
- **Before pushing:** `pytest -q` and `python -m reonic eval`.
- **Commits:** one-line summary of what changed and why.
- Update **Status** when you finish something others rely on. Record choices in **Decisions**.
