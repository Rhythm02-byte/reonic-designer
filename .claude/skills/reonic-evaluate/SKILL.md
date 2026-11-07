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

Headline: `whole_design_within_tolerance`. Always read component accuracy against `expert_include_rate`. Heat pump accuracy of 99% is trivial because experts include one in 0.3% of designs.

## Recorded results

| Date | Data | Split | Model whole-design | Baseline | Notes |
|---|---|---|---|---|---|
| 2026-11-07 | real export, `OPTION_CHOICE=first`, untuned | random | 15.7% | 3.8% | PV 45% vs 16%; battery 39% vs 24%; wallbox 61% vs 74% (model worse) |

Add a row every time the model, thresholds, option choice or data changes. Never overwrite an old row.

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
