# PLAN: Reonic home energy designer

Deadline: **Sunday 8 Nov, 15:00.** Read [CONTEXT.md](CONTEXT.md) and the challenge PDF first.

## Approach

Build, measure, report. We don't tune until the numbers look good. Each step produces a result we can compare against the baseline on the real data. Where Reonic's answers are missing we use a stated default and show the sensitivity.

1. Get a working designer on the real data (done: 15.7% whole-design vs 3.8% baseline).
2. Improve only where the evaluation shows a clear gap, and record each change in CONTEXT.md §6.
3. Report what works and what doesn't, with the numbers, in the pitch.

## Milestones

| Milestone | When | Done when |
|---|---|---|
| M0 · Data in | Done | Real export loads; first eval recorded |
| M1 · Minimum result | Sat 22:00 | Planner sees a complete design with reasons, changes an input and gets an updated design, and the eval against held-out real projects is recorded |
| M2 · Stretch | Sun 09:00 | At least two of: deviation analysis, confidence/alternatives, homeowner view |
| M3 · Freeze | Sun 13:00 | Code frozen. Deck, recording and README final. Demo rehearsed twice |
| Submit | **Sun 15:00** | Repo link, deck, recording |

## Workstreams

Each workstream has one owner. Claim one by writing your name here.

| Workstream | Owner | Output |
|---|---|---|
| 1. Data & EDA | _open_ | Findings on outliers, bundles and thresholds; fill the open questions; feed back into features and rules |
| 2. Model & eval | _open_ | Per-component thresholds tuned on validation data; group split result; deviation analysis |
| 3. Product & UI | _open_ | Demo flow on real data; validation view; homeowner view (spec) |
| 4. Pitch & business case | _open_ | Deck; time-per-offer model with labelled assumptions; demo script; recording |

## Other approaches we could take

These are alternatives to the current design. We pick the one that scores best on the data, and say in the pitch why.

1. **Rank the offered options instead of predicting one design.** Each project has several options, so we can learn which option installers prefer. This avoids guessing the signed option and suits the planner's "give me a few, let me choose".
2. **Readable rules learned from the data.** Fit a shallow decision tree and turn its splits into rules, such as "battery when demand > X and PV > Y". Easy to explain to a planner, and a clean way to compare with the gradient-boosting model.
3. **Simulation plus optimisation.** For each candidate design, estimate yearly savings minus cost with the physics module, and pick the best. Physically plausible by construction, but depends on calibrated constants.
4. **Case retrieval (analogue method).** Show the most similar real projects and their designs, then adjust the closest one. Very transparent, fits the "validate against similar homes" view.
5. **Narrow the scope to validation.** Instead of generating designs, flag offers that are unusual against installer history. We can measure it honestly and it fits the planner use case.
6. **LLM for language only.** Plain-language explanations for the homeowner view, constrained so that every number comes from our evidence lines. This is where the $200 of Claude credits fit best. It does not touch the decision.

**Our recommendation:** combine 1, 2 and 4. Rank options per project, explain with the rules and similar cases, and keep 3 as a stretch. Use 5 as the fallback if the design quality stays low. Use 6 for the homeowner text only.

## Budget

- Claude credits: $200 (about €200). Planned use: Claude Code work, and the optional LLM explanation in approach 6. Log spend here as it happens.

## Data sources (research, 2026-11-07)

**Simulation (approach 1):** built in `src/reonic/simulate.py`, study in `scripts/simulation_study.py`. Results and limits are in the `reonic-evaluate` skill. Summary: the pipeline works, missing inputs cost accuracy, and a simulated policy cannot stand in for installer labels.

**Public datasets (approach 2):** Kaggle has no public set of installer designs. Candidates, not yet downloaded:

| Source | Useful for | Not useful for |
|---|---|---|
| ~~`mexwell/household-load-and-solar-generation` (Kaggle)~~ | Removed: only 6 homes, too small to use | — |
| Pecan Street free sample, 10 homes, 1-minute (Kaggle, needs free registration) | Real load with solar, HVAC and EV circuits | Design decisions; only 10 homes |
| Open heat pump datasets, about 400 homes, 2-minute (openmod forum) | Heat pump operation | Sizing decisions; licence and source to check |
| When2Heat (Kaggle) | Simulated country-level heat demand | Per-home data |
| Connecticut incentive enrolments for solar and batteries (data.ct.gov, via the search tools) | Possibly real installed sizes by installer | Heat pumps; US market; fields not yet inspected |

Our conclusion: Kaggle can make the load profiles and physics more realistic. It cannot supply the label we need, which is what installers sold. Check the licence on every download before use. Put downloads in `data/external/` (gitignored). Never upload Reonic data to Kaggle or any other service.

## Open risks

- The heat pump can't be learned from this data (13 of 1,593 chosen designs, 0.8%). Say so in the pitch.
- Wallbox is worse than the baseline. Thresholds need tuning on validation data, not the test set.
- Signed option and module wattage are unknown until Reonic answers. Show sensitivity to both.
