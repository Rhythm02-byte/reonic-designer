# Spec: where and why our designs differ from the experts

**Status:** not started · **Workstream:** Model & eval · **Stretch goal** (Reonic PDF p. 7)

## Problem

A single accuracy score hides where the model fails. Judges want to see the pattern, and the team needs it to decide what to fix.

## Behaviour

From `reports/test_predictions.csv`, produce:
- Miss rates per component, broken down by home type: consumption band, heating type, EV yes/no, installer, and option count.
- The two or three largest patterns, each with a plausible reason. Examples: budget or preference we can't see, noisy line items, package-driven designs.
- One chart and one pitch slide: "Where we disagree with experts, and why".

## Data and code

- Input: `reports/test_predictions.csv` (already written by `python -m reonic eval`).
- A small analysis script or notebook under `reports/` or `scripts/`. Its output must be reproducible from one command.

## Done when

- The breakdown runs from one command on the real data.
- Each pattern is written up with its count and rate, not just a description.
- Patterns we can't explain are listed as open, not guessed at.
- The slide uses real-data numbers only.

## Out of scope

Retraining the model on the deviations. This feature explains results; it does not change them.
