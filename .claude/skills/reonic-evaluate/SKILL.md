---
name: reonic-evaluate
description: Use when running the model evaluation, comparing the model with the baseline, changing thresholds or metrics, or writing up results for the pitch or README. Covers how to report results honestly.
---

# Evaluating the Reonic designer

## Run

```bash
python -m reonic eval                          # random 80/20 split
python -m reonic eval --group-col installer_id # unseen-installer split (the honest number)
```

Outputs: `reports/eval.json` (all metrics, per installer) and `reports/test_predictions.csv` (one row per held-out project, expert vs ours vs baseline). The Streamlit Evaluation tab reads `eval.json`.

## Metrics (definitions in CONTEXT.md §5)

Headline: `whole_design_within_tolerance`. Always read component accuracy against `expert_include_rate`. Heat pump accuracy of 99% is trivial because experts include one in 0.8% of chosen designs (13 of 1,593).

## Unseen-installer evaluation (`scripts/unseen_installer.py`)

Trains on one installer and tests on the other, then swaps. Wallbox is the deterministic EV rule. Output: `reports/unseen_installer.json`.

| Split | Train | Test | Whole design | Baseline | PV ±20% | Baseline PV | Battery ±25% | Baseline battery | Wallbox P / R / F2 |
|---|---|---|---|---|---|---|---|---|---|
| Random 80/20 | 1,274 | 319 | 13.5% | 3.8% | 45.8% | 16.0% | 38.9% | 23.8% | 0.50 / 0.07 / 0.09 |
| Train `2a8ba8e2`, test `23c108b7` | 1,257 | 336 | **18.5%** | 4.2% | 39.9% | 13.1% | 47.3% | 18.2% | 0.67 / 0.19 / 0.22 |
| Train `23c108b7`, test `2a8ba8e2` | 336 | 1,257 | **9.8%** | 5.6% | 33.8% | 19.6% | 32.0% | 30.4% | 0.54 / 0.07 / 0.08 |

Reading:
- The model beats the baseline on the whole design in both directions, so it carries over to an installer it has not seen.
- Transfer is uneven. Training on the large installer and testing on the small one gives 18.5%. The reverse gives 9.8%, and the battery result there (32.0% vs 30.4%) is no better than the baseline. A model trained on 336 projects does not learn enough.
- The PV score for `2a8ba8e2` as the test installer depends on the assumed 450 W module wattage (see the sensitivity table), because that installer's PV sizes are rebuilt from module counts.
- Each direction is one run with no repeats, and the test sets are 336 and 1,257 projects, so treat differences of a few points as noise. Report both directions, not just the better one.

## Effect of treating 0 kWh consumption as unknown

13 projects (0.8%, all at `2a8ba8e2`) carry an annual consumption of exactly 0 kWh, which is impossible. `data.py` now loads these as unknown. Random-split whole-design score moved from 13.2% to 13.5%; the other numbers in this file were re-run after the change.
Demo finding: one of these homes (0 kWh, 24 kWp expert PV) had been picked by accident as an "easy" demo example, and made the model look wrong when the input was bad.

## Wallbox decision: deterministic rule

**Decision (2026-11-07): the wallbox follows the rule "home has an EV → wallbox, else none"** (`src/reonic/model.py`, `RULE_BASED`). Size is the most common installed size (11 kW). An unknown EV flag counts as no EV. Reason: 5-fold CV showed the learned model did no better than this rule (see below).

Wallbox include decision on the test split (precision, recall, F1, F2 with beta=2), model = baseline because both are the same rule:

| Metric | Value |
|---|---|
| Precision | 0.500 |
| Recall | 0.072 |
| F1 | 0.126 |
| F2 (beta = 2) | 0.087 |

Trade-off to state in the pitch: switching from the learned wallbox (cut-off 0.78) to the rule raises wallbox accuracy from 67% to 74%, but **lowers the whole-design score from 15.7% to 13.2%**, because the rule finds only 7% of the homes that get a wallbox. Accuracy rewards saying "no" (only 24% of homes have one), so read the wallbox on recall and F2, not accuracy. Only about 6% of homes have an EV, so most wallbox homes cannot be identified from the inputs we have.

## Wallbox threshold study (`scripts/wallbox_threshold.py`)

Cut-off chosen on out-of-fold training predictions only: 0.78. Out-of-fold accuracy: model 76.2%, EV rule 76.5%. The EV rule is as good as the model, so the wallbox model adds no information beyond the EV flag.

Test split, scored once: isolated model 74.9% vs EV baseline 74.0%. The 0.9-point gain is 3 homes out of 319, which is noise. The full pipeline gets 67%, not 75%, because the wallbox step is trained with true PV and battery sizes as inputs but predicts with its own predicted sizes. That train/predict mismatch is the likely cause, and it is not fixed by threshold tuning.

## Recorded results

| Date | Data | Split | Model whole-design | Baseline | Notes |
|---|---|---|---|---|---|
| 2026-11-07 | real export, `OPTION_CHOICE=first`, untuned | random | 15.7% | 3.8% | PV 45% vs 16%; battery 39% vs 24%; wallbox 61% vs 74% (model worse) |
| 2026-11-07 | real export, wallbox cut-off 0.78 (chosen by 5-fold CV on train) | random | 15.7% | 3.8% | wallbox 67% vs 74% (still worse). Isolated wallbox classifier: 74.9% vs 74.0% on test, within noise |
| 2026-11-07 | real export, wallbox = deterministic EV rule | random | 13.2% | 3.8% | wallbox 74% = baseline; precision 0.50, recall 0.07, F2 0.09. PV and battery unchanged |
| 2026-11-07 | real export, wallbox = EV rule | unseen installer | 18.5% (train 2a8ba8e2) / 9.8% (train 23c108b7) | 4.2% / 5.6% | see the unseen-installer table. Battery gain vanishes when training on the small installer |

Add a row every time the model, thresholds, option choice or data changes. Never overwrite an old row.

## Sensitivity to unanswered questions (`scripts/sensitivity.py`)

Same random split and seed for every run. Output: `reports/sensitivity.json`.

| Signed option | Module wattage | Whole design | PV within ±20% | Battery within ±25% | Baseline whole design |
|---|---|---|---|---|---|
| first | 400 W | 14.4% | 46.1% | 39.8% | 3.8% |
| first | 450 W (default) | 15.7% | 45.1% | 39.2% | 3.8% |
| first | 500 W | 14.7% | 46.7% | 39.5% | 3.4% |
| last | 400 W | 13.5% | 46.7% | 37.0% | 3.1% |
| last | 450 W | 12.5% | 45.8% | 34.8% | 3.4% |
| last | 500 W | 13.8% | 46.7% | 36.4% | 3.4% |

Reading: the model stays ahead of the baseline in all six runs. The range is 12.5–15.7%. The conclusion does not depend on either open assumption. Report the range, not the best run.

## Default demand check (`scripts/default_demand_check.py`)

Question: are the 457 projects with exactly 4,500 kWh (29%) distorting the result?

| Comparison | Whole design | PV | Battery | Test rows | Baseline |
|---|---|---|---|---|---|
| A. all rows | 15.7% | 45.1% | 39.2% | 319 | 3.8% |
| B. without the 4,500 kWh rows | 14.9% | 46.1% | 43.9% | 228 | 5.3% |
| C. default rows only, same model | 18.3% | 56.1% | 34.1% | 82 | — |
| C. other rows only, same model | 14.8% | 41.4% | 40.9% | 237 | — |

Reading: removing the default rows does not change the overall conclusion. **Correction:** the "no worse than other homes" reading came from only 82 test rows. On all 1,593 projects (out-of-fold, `scripts/deviation_analysis.py`), placeholder homes at `2a8ba8e2` get the battery right 26% of the time (n=391) against 41% for other homes (n=866), with no such gap at `23c108b7`. See `docs/specs/deviation-analysis.md`. Test sets are small (82 and 228 rows), so differences of a few points are within noise. The check does not prove the 4,500 kWh values are wrong, only that they don't break the result.

## Simulation study (`scripts/simulation_study.py`)

Writes `reports/simulation_study.json`. These numbers are **not** comparable with the real table above: the simulated designs follow a policy we wrote (`src/reonic/simulate.py`), not installer behaviour.

| Experiment | Result | What it tells us |
|---|---|---|
| A. Recovery of our own policy (30% heat pump homes) | whole design 34.7%; PV 65%, battery 47%, heat pump 81%, wallbox 98% | Even a known rule is only partly recovered. Part of that is the noise we added on purpose, so it is not a ceiling. |
| B. Inputs blanked at 0 / 25 / 50 / 75% | 34.7 → 29.5 → 24.8 → 18.7% | Accuracy falls about 5 points per 25% of missing inputs. Gaps hurt, but gradually. |
| C. Heat pump sizing, trained with 0% vs 30% heat pump homes | 77.4% → 81.0% | Small gain over "never a heat pump" (77%). Sizing is barely learned even with examples. |
| D. Train on simulation, test on real export | whole design 4.2% | The policy does not resemble installers. Simulation cannot replace expert labels. |

Use these to say: the pipeline works, missing inputs cost accuracy, and simulation cannot stand in for Reonic's data. Do not use them as evidence of expert accuracy.

## Rules for reporting

1. **Test set is for reporting only.** Tune thresholds on a validation split carved from the training data, never on the test set.
2. **Report against the baseline every time.** If the model loses on a component, say so in the same table.
3. **Use the unseen-installer split** for anything shown to judges, and report both.
4. **Show sensitivity** to the open questions: rerun with `OPTION_CHOICE=last` and with another module wattage, and report the range, not one lucky number.
5. **Synthetic numbers never go in the pitch.** They are for tests only.
6. **Heat pump and wallbox results** must be stated with their limitation (few heat pump examples; wallbox is include/exclude only).

## Threshold tuning (when asked)

- The include cut-off (currently 0.5 in `DesignModel.predict`) becomes a per-component value chosen on validation data.
- Choose it by the cost of each error: a missed battery loses a sale, an unneeded one makes the offer look oversold. Write the chosen value and the reason in CONTEXT.md §6.
- Re-run the full evaluation afterwards and add a row to the table above.
