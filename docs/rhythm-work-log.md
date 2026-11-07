# Rhythm's work log and ideas

A running record so teammates can see what was done, what was tried, what worked, and what is left. Numbers come from
the saved reports (`reports/*.json`, git-ignored: re-run the scripts to regenerate) and use the real export, which is
confidential and not in git. Last updated Sat 7 Nov 2026, evening.

How to read a result: every comparison is 5-fold out-of-fold on all 1,593 projects with a bootstrap 95% interval on the
gain. **Believe a gain only if the whole interval is above zero.** "Whole design" = PV, battery, heat pump and wallbox all
within tolerance (PV ±20%, battery and heat pump ±25%).

## 0. What improved (summary)

| Area | Before | After | Evidence | Status |
|---|---|---|---|---|
| Whole design, fresh folds (seeds 1-3) | 14.7% | **18.7%** (+4.0, interval +2.8 to +5.1) | `scripts/remaining_tests.py confirm` | Opt-in, not the default |
| Battery within tolerance, fresh folds | 40.8% | **46.0%** (+5.2, +3.7 to +6.7) | same | Opt-in |
| PV within tolerance, fresh folds | 49.4% | 51.4% (+1.9, +0.6 to +3.4) | same | Opt-in |
| Gain over the typical design | – | +2.3 (+0.5 to +4.1) | same | Opt-in |
| Battery on time-ordered splits | 40.6 / 41.0 / 49.2 / 47.9% | 45.7 / 49.8 / 52.1 / 52.4% | `scripts/time_split_best.py` | Gain in 4 of 4 windows |
| Whole design on time-ordered splits | 13.7 / 12.7 / 19.7 / 19.0% | 18.4 / 16.2 / 19.0 / 22.9% | same | Gain in 3 of 4; noisy |
| Rule bugs (battery over its cap, negative battery, a crash) | 19 broken in 600 fuzzed homes | 0 in 600, and 0 in a fresh 2,000 | `scripts/fuzz_engine.py` | **Fixed on main** |
| Crash on a small training subset with no heat pump | Crashed | Trains | `tests/test_coverage_sizing.py` | **Fixed on main** |
| Unit tests | 57 | 78 | `pytest` | On main |
| Stale numbers in README, deck, demo script | Found by eye | Caught by `scripts/preflight.py` | 17 + 20 + 11 numbers | On main |

What did **not** improve, and is not worth more time: placeholder-row handling, installer as a feature, neighbour blend,
hand-tuned or nested-CV boosting settings, one model per installer, and more training data (the learning curve is flat).
The shipped default is unchanged, so the app, README and deck still show whole design 15.3% out-of-fold.
Safe claim for the pitch: battery sizing improves by roughly 3 to 9 points, PV is unchanged, and the whole-design gain is
real but smaller and noisier than the random-fold headline.

## 1. What I built (on `main`)

| Area | What | Where |
|---|---|---|
| Loader | Rebuilds one row per project from the raw export, with the known quirks handled | `src/reonic/data.py` |
| Model | Chained gradient boosting: heat pump → PV → battery; wallbox is a fixed rule (EV → wallbox) | `src/reonic/model.py` |
| Rules | R01–R04 plus catalogue snapping; planner overrides always win | `src/reonic/rules.py` |
| Evaluation | Precision/recall/F1/F2, tolerance scoring, unseen-installer, rule-of-thumb and typical-design baselines | `src/reonic/evaluate.py`, `baseline.py` |
| Honesty checks | Leakage (customer-grouped, shuffled labels, time split), 30 random splits, bootstrap | `scripts/leakage_checks.py`, `repeated_splits.py` |
| Robustness | Fuzzing of 2,000 odd homes: 0 broken rules; preflight that checks README, deck and demo script against the reports | `scripts/fuzz_engine.py`, `preflight.py` |
| Deviation analysis | Where and why we differ from the experts | `scripts/deviation_analysis.py`, `docs/specs/deviation-analysis.md` |
| Business case, deck, demo script | Transparent assumptions; 7-slide deck; scripted demo | `docs/` |

## 2. Where the model stands (current defaults)

- Out-of-fold whole design **15.3%**; typical design (same median size for everyone) 16.1%; rule of thumb 5.3%.
- Real edge: **PV size**, +8.2 points over the typical design (95% interval +5.0 to +11.4).
- No clear edge on the whole design, and a new installer is not beaten by a typical design (train 2a8ba8e2 → test
  23c108b7: 18.5% vs 31.5%).
- Wallbox: a learned model did no better than the rule "has an EV → wallbox", so it is a rule.

## 3. Improvement ideas tested

Harness: `PYTHONPATH=src .venv/bin/python scripts/improvement_ideas.py <idea>[+<idea>...]`. 21 variants run.
Gain is on whole design over the current model (15.3%).

| Idea | Result | Verdict |
|---|---|---|
| Coverage sizing: pick the size that fits the most plausible expert sizes | +2.0 (+0.3 to +3.6); battery +3.4, PV +0.2 | Helps, about 3× slower to train |
| Placeholder rows (4,500 kWh demand): down-weight / drop / flag | −0.7 / −1.3 / +0.5, all intervals include 0 | No help |
| Installer as a feature | −0.6 (−1.7 to +0.4) | No help; cannot help a new installer |
| Neighbour blend with the 25 most similar homes | +2.6 after the rules, but +1.2 (−0.3 to +2.6) done properly in the engine | Mostly an artefact: the first version skipped catalogue snapping |
| Tuning boosting settings (2 hand-picked) | +0.6 and +1.3, intervals include 0 | Unproven; the shorter setting trains ~6× faster |
| **Battery catalogue: snap to all 40 sizes instead of the top 15** | +1.3 (+0.8 to +1.9); battery +3.3 | Helps, free. Top 15 sizes cover 96% of installed batteries but the coarse grid misses the ±25% band |
| **Coverage sizing + 40-size battery catalogue** | **19.0%, +3.6 (+2.0 to +5.3); battery +7.0** | Best so far |

Unseen installer for the best setting (whole design): 9.8% → 11.1% and 18.5% → 18.8%. PV is worse in one direction
(−3.9). The typical design still wins when training on the smaller installer.

### Remaining checks (`scripts/remaining_tests.py confirm | curve | nested | installer`)

| Check | Result | Verdict |
|---|---|---|
| **Confirm the best setting on fresh folds** (fold seeds 1-3; the search used seed 0) | Whole design 14.7% → 18.7%, **+4.0 (+2.8 to +5.1)**; PV +1.9 (+0.6 to +3.4); battery +5.2 (+3.7 to +6.7). Gain over the typical design: +2.3 (+0.5 to +4.1) | **Holds.** Not a selection artefact. |
| Learning curve (20% to 100% of training data) | Current model 15.9 / 14.7 / 15.4 / 15.2 / 14.6%; best setting 17.1 / 16.9 / 18.5 / 17.3 / 17.8% | **Flat.** More data of this kind will not help; the limit is what the inputs tell us. |
| Nested tuning (6 settings, picked by inner CV) | Whole +1.4 (-0.1 to +3.0); PV +1.1; battery +0.9 | Not proven. Small and the interval includes 0. |
| One model per installer | Whole +0.2 (-1.3 to +1.7); battery -1.5 | **No help.** |

The best setting beats both the current model and the typical design on folds it was not chosen on.

### Cross-check by a teammate's port (reported 7 Nov, evening)

A teammate ported these ideas into their own pipeline (time-ordered validation window, `policy.json`). Their report says
coverage sizing + the 40-size catalogue did **not** reproduce there (scored worse on their validation window; only a
battery-only coverage variant passed, +0.4 points, which they call noise), their 2026 test showed no real gain, and
their 2,000-home fuzz found 194 rule-breaking designs. I cannot see their code, so I checked what I can here.

- **Time-ordered splits here** (`scripts/time_split_best.py`, n=315 each, so about ±2.5 points of noise per row):

  | Split | Whole design: current / best / typical | Battery: current / best |
  |---|---|---|
  | Last 20% per installer | 13.7 / 18.4 / 18.7 | 40.6 / 45.7 |
  | Train first 60%, test next 20% | 12.7 / 16.2 / 11.4 | 41.0 / 49.8 |
  | Train first 70%, test next 20% | 19.7 / 19.0 / 13.0 | 49.2 / 52.1 |
  | Train first 80%, test next 20% | 19.0 / 22.9 / 24.1 | 47.9 / 52.4 |

  Battery gains in all four windows (+2.9 to +8.8). Whole design gains in three of four. PV is flat. Against the typical
  design it is mixed (wins two windows, ties one, loses one). So the battery gain reproduces on time splits here, and
  the whole-design gain is smaller and noisier than the random-fold number. Their pipeline differs, so the two results
  are not in conflict, but **do not claim more than "battery sizing improves, PV is unchanged".**
- **Their fuzz found real bugs; ours had a blind spot.** My fuzzer never combined tiny PV with a battery and never fed
  negative existing PV. With those added it found 19 problems in 600 homes: battery above the 2 kWh/kWp cap when the
  smallest catalogue size exceeded the cap (snapping fell back to the whole catalogue), negative battery sizes from a
  negative existing-PV entry, and one crash. Fixed in `rules.py` (negative PV counts as none; stay under the cap), with
  regression tests. Earlier "0 of 2,000" referred to the narrower fuzzer.
- What they flagged that we do not have: PV rounding past the roof cap (ours caps before rounding, checked).

## 4. Code that exists but is opt-in

`Designer.train(df, sizing="coverage", battery_catalog_top=40, blend=0.5, sample_weight=..., params=...)`. The defaults
are unchanged, so the app, README, deck and demo script still show the old numbers. Switching the default means
regenerating the reports, README, deck and demo script, then running `scripts/preflight.py` (~40 min; training gets
~2.5× slower, so also save the trained model to disk).

## 5. How to check or add an idea

1. Pull `main`, set up the venv, and put your own copy of the export in `data/raw`.
2. Run an existing idea: `PYTHONPATH=src .venv/bin/python scripts/improvement_ideas.py coverage+snap40`.
3. Add yours: one `elif part == "my_idea":` branch in `run_variant` in `scripts/improvement_ideas.py`. Combine with `+`.
4. Read the row: gain, interval, PV and battery columns, placeholder vs other rows, seconds.
5. Before claiming a win, confirm on `scripts/repeated_splits.py` and `scripts/unseen_installer.py`, then
   `scripts/preflight.py`.

Each run overwrites `reports/improvement_ideas.json`; copy the printed table if you want to keep it.

## 6. Left to do

- [x] Confirm the best setting on fresh folds: holds (+4.0, interval +2.8 to +5.1).
- [ ] Decide whether to make coverage + 40-size catalogue the default, then regenerate numbers, README, deck, demo script.
- [ ] Save the trained model to disk so the app starts fast.
- [ ] PVGIS yield (phase 1: cached lookup with fallback to 950 kWh/kWp). Cannot change the evaluated score: the export has no location.
- [x] Nested-CV tuning, learning curve, per-installer models: done, none needed (see section 3).
- [ ] Ask Reonic: which option was signed, module wattage at 2a8ba8e2, is 4,500 kWh a default; time per design, offers per week.
- [ ] Record the fallback demo video; rehearse twice; team review of the deck.
- [ ] Faris's PRs #2 and #4 conflict with `main` in `CONTEXT.md` and `README.md`; keep both sides when resolving. His Evaluation tab should show the new `typical` key in `eval.json`.
- [ ] Final submission Sun 8 Nov 2026, 15:00.

## 7. Decisions and dead ends (so nobody repeats them)

- Wallbox is a rule, not a model (5-fold CV: model 73.2%, EV rule 76.5%, never-include 75.7%, AUC 0.52).
- Battery and heat pump include cut-offs stay at 0.5 (flat from 0.30 to 0.75).
- The original headline "beats the baseline" was misleading: the rule of thumb is weak. The fair reference is the typical design.
- Placeholder rows are noisy but dropping them hurts PV by 9 points; keep them.
- A model fit used to crash on a small training subset with no heat pump at all (a column with one value); fixed in `model.py` and covered by a test.
- Overconfident probabilities and "placeholder rows are no worse" were hypotheses I tested and dropped.
