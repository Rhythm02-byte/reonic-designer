# Metric research: protocol and candidates (written BEFORE running anything)

## Protocol (fixed)
- **Data for decisions:** offers ≤ 2025-12-31 only. Four expanding time folds: train < quarter q, validate on q (q = 2025 Q1..Q4), plus 20 random 80/20 splits (seeds 0..19). The 2026 test is the final exam: scored by `npm run eval`, never used to choose.
- **Primary metric:** whole design within tolerance (PV ±20%, battery/heat pump ±25%, wallbox include). Secondary: closeness (EMS), PV, battery.
- **Adopt a candidate only if:** paired gain in whole design vs the current default is > 0 on the mean of the 4 folds AND > 1 sd of the 20-split paired gap, AND EMS does not drop more than 1 point. Otherwise it's reported as "no effect", not tuned further.
- **One shot per candidate:** at most 3 settings per idea, all listed here before running. Every run is recorded (`kind: "research"`).
- **Leakage guard:** a feature may only use what a planner knows before the offer; the shuffled-label check must still collapse to baseline.

## Candidates (ranked by expected effect)
| # | Idea | Why it might work | Settings to try |
|---|---|---|---|
| 1 | Bundle classification | Installers sell packages; battery ≈ 0.93 kWh/kWp follows PV. Predicting the (PV, battery, wallbox) bundle jointly targets whole design directly | top-K bundles per installer K ∈ {10, 20}; GBM vs kNN vote |
| 2 | Catalogue sizing as classification | Choose the catalogue size with the highest P(within tolerance) instead of regress + round | ordinal GBM over catalogue steps |
| 3 | TabPFN (Nature 2025) | Foundation model for small tables (≤10k rows); we have ~1.6k | default; ensemble of 4; check latency < 400 ms and licence |
| 4 | Recency weighting | Habits drift; 2026 resembles late 2025 more than 2024 | half-life {6, 12} months |
| 5 | Wallbox threshold for whole design | Current threshold optimises accuracy, not the joint hit | threshold chosen on folds |
| 6 | Placeholder-demand handling | 29% rows carry 4,500 kWh; their demand carries no information | flag feature; separate prior |
| 7 | kNN + GBM stacking | Small noisy data favours blends | weights {0.3, 0.5} |
| 8 | MaStR kWh/kWp prior by year (after Codex delivers) | Independent market evidence for the battery step | prior strength {low, high} |
| 9 | Haiku with tools picks among the top-3 bundles | Test, not expected to win (LLMs lead only at ≤8 labels, arXiv 2411.04324) | validation only; temperature 0; strict JSON |

## Results
(filled in per candidate: fold gains, 20-split gap, decision)
