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


## Tournament, night of 7-8 Nov 2026 (pre-registered 04:15 WEST, before any run)
Harness: `pnpm x:research -- <id>|all` (`eval/research.py`, plug-ins in `eval/research/candidates/`). Candidates are wrappers only
(feature transform / `Designer` config override / prediction post-processor); no engine file is edited.

**Protocol as run (fixed now):**
- Rows: offers ≤ 2025-12-31 (asserted). Folds: train `when` < quarter start, validate on the quarter, q = 2025 Q1..Q4 (expanding).
  Random: 20 × 80/20 splits, seeds 0..19 (`honesty.SPLIT_SEEDS`).
- Reference = the current default (`config/policy.json` as of 04:00: composite M1/M1/M1/B0c, physics + installer prior,
  battery coverage), trained on the same rows. All gains are **paired** (same validation rows).
- **Adopt** a setting only if (a) mean whole-design gain over the 4 folds > 0, (b) mean 20-split paired gain > 1 sd of the
  20 paired gains, (c) mean EMS (closeness, primary option) over the 4 folds drops ≤ 1 point. Best setting per idea only if it passes.
- **Combined winner:** the passing settings stacked into one config, re-run once, and it must ALSO pass (a)–(c) with fresh
  split seeds 20..39 (never used for selection). Shuffled-label control on the Q4 fold for the adopted config.
- Leakage: habit / repeat-customer features of a row only use training rows with `when` strictly before that row (unit-tested).
- Reported, never adopted on: any-option whole design (#42), selective prediction (#41).

| id | Idea (# in the 50) | Kind | Settings (max 3, fixed) |
|---|---|---|---|
| pkg | Joint package retrieval, Codex #1 (1) | post-processor | `k25_top10`, `k25_top20`, `k50_top20`: candidates = the installer's top-N training packages (PV, battery, HP, wallbox); score = share of the k nearest training homes whose design the package hits within tolerance; tie/zero → installer's most frequent package; rules R01–R05 still applied |
| joint | Joint PV+battery decision (2) | post-processor | `samples`: PV candidate from the PV quantiles, battery from quantiles conditioned on that PV, maximise P(PV hit)·P(battery hit); `samples_gate`: same, battery include decided jointly (p·hit vs 1−p) |
| tolpv | Tolerance-mode PV (3) | config | `cov_samples`: sizing.coverage = [pv, battery]; `cov_catalog`: same + coverageCandidates = catalog |
| wbx | Wallbox threshold for whole design (4) | post-processor | learned P(wallbox) (HGB on base features), include if ≥ τ, τ ∈ {0.3, 0.5, 0.7} |
| habit | Installer rolling package habit (9) | feature | windows `30d`, `90d`, `all` (expanding): installer's earlier offers → median kWp, battery share, median kWh, wallbox share, modal PV bucket, n |
| repeat | Repeat customer via `customer_id` (10) | feature / override | `feature`: flag + earlier offer's 4 sizes; `copy`: when an earlier offer exists, serve its design |
| placeholder | Placeholder demand (11) | feature | `nan`: demand 4,500 or 0 kWh → unknown; `interact`: placeholder flag × installer columns |
| lag | Request→offer lag (12) | feature | `days`: lag in days (NaN unknown). Caveat: unknown at request time in the product |
| recency | Recency weighting (20) | model | half-life `6m`, `12m` (sample weights on every boosted tree) |
| blend | kNN + GBM blend (21) | config | sizing.blend ∈ {0.3, 0.5} |
| select | Selective prediction (41) | metric | whole design on the 30% / 50% most confident homes (confidence = include certainty × PV interval tightness) |
| anyopt | Any-option match (42) | metric | whole design vs any of the expert's options |
| haiku | Haiku picker over top-5 packages (36, step 5) | post-processor | `claude-haiku-5-5`, temperature 0, answer = enum of candidate ids, cached by input hash; 4 validation folds only |

**Deviation noted before the Haiku run (04:50):** Claude Haiku 5.5 rejects any non-default sampling parameter (`temperature: 0` returns a 400), so the picker runs with thinking disabled, effort `low`, and every answer cached by sha256(prompt version + model + home + candidates + tool outputs): reruns are bit-identical from the cache. No API key on the machine yet → the picker serves candidate c1 (the retrieval's top package) until one is added; then only `haiku` is re-run.

**Combined winner, pre-registered 05:15 after the single-idea runs and BEFORE running it** (`combo`, 3 settings):
`A_tolpv_catalog` = tolpv:cov_catalog + repeat:copy · `B_joint` = joint:samples + repeat:copy ·
`C_bat_catalog` = battery coverage with catalog candidates only (PV unchanged) + repeat:copy. C is a *declared post-hoc
ablation*: the component breakdown showed the A/B gains come from the battery (+8 pts within tolerance), while PV got
slightly worse. Each is run on the 4 folds + fresh seeds 20..39 (never used for selection) and must pass (a)–(c) there.
If several pass, the simplest one is recommended (C, then A, then B), not the highest-scoring one. Shuffled-label
control on Q4 for the recommended one.

## Results (run 04:20–05:20 WEST, 8 Nov; reference = default config/policy.json trained on the same rows)
Whole design within tolerance, percentage points, paired. Folds = 2025 Q1 / Q2 / Q3 / Q4. EMS Δ = fold-mean closeness change.
Raw per-unit aggregates: `eval/research/results/*.json`; every row is a `kind: "research"` line in `eval/history/runs.jsonl`.

| setting | fold gains | mean fold gain | 20-split gain (mean ± sd) | EMS Δ | decision |
|---|---|---|---|---|---|
| pkg:k25_top10 | -3.3 / -4.4 / -3.6 / -2.2 | -3.37 | +0.61 ± 2.45 | -1.43 | no effect |
| pkg:k25_top20 | +0.4 / -3.5 / -4.5 / -2.6 | -2.56 | +0.81 ± 2.56 | -0.38 | no effect |
| pkg:k50_top20 | +0.4 / -5.3 / -1.8 / -0.9 | -1.88 | +1.44 ± 2.49 | -0.40 | no effect |
| habit:30d | +0.8 / +2.6 / -5.0 / -3.4 | -1.25 | +0.33 ± 2.43 | -2.03 | no effect |
| habit:90d | -0.8 / +2.6 / -5.5 / +1.3 | -0.59 | +0.22 ± 2.28 | -2.55 | no effect |
| habit:all | -4.1 / +4.4 / -1.4 / +1.3 | +0.04 | +0.41 ± 2.14 | -1.68 | no effect |
| repeat:feature | +0.0 / +0.0 / +0.0 / +0.0 | +0.00 | +0.00 ± 0.00 | -0.00 | no effect |
| repeat:copy | +0.0 / +0.4 / +0.0 / +0.0 | +0.11 | +0.30 ± 0.25 | -0.14 | ADOPT |
| placeholder:nan | +2.5 / +3.1 / -3.6 / +0.0 | +0.48 | -0.16 ± 1.73 | -0.20 | no effect |
| placeholder:interact | -0.4 / -0.4 / -2.7 / +0.9 | -0.68 | +0.04 ± 0.66 | -0.07 | no effect |
| lag:days | +0.0 / +0.0 / +0.0 / +0.0 | +0.00 | +0.02 ± 1.48 | -0.00 | no effect |
| joint:samples | +5.0 / +6.1 / -5.5 / -4.3 | +0.34 | +4.11 ± 2.26 | -0.25 | ADOPT |
| joint:samples_gate | +5.0 / +6.1 / -5.5 / -4.3 | +0.34 | +4.11 ± 2.26 | -0.25 | ADOPT |
| tolpv:cov_samples | +1.2 / -1.8 / -2.3 / -3.9 | -1.67 | +1.61 ± 2.39 | -0.26 | no effect |
| tolpv:cov_catalog | +5.0 / +2.6 / -3.2 / -2.6 | +0.46 | +3.23 ± 2.64 | -0.43 | ADOPT |
| wbx:t0.3 | -2.1 / -3.5 / -2.3 / -0.4 | -2.07 | -1.89 ± 1.13 | -2.24 | no effect |
| wbx:t0.5 | -0.4 / +0.4 / +0.0 / -0.4 | -0.10 | -0.20 ± 0.35 | -0.21 | no effect |
| wbx:t0.7 | -0.4 / +0.9 / -0.5 / -0.4 | -0.11 | -0.30 ± 0.46 | -0.19 | no effect |
| recency:6m | -1.2 / +3.9 / +0.0 / -1.7 | +0.24 | -0.57 ± 1.79 | -0.05 | no effect |
| recency:12m | -0.4 / +2.6 / -2.3 / -2.2 | -0.55 | +0.02 ± 1.50 | -0.76 | no effect |
| blend:w0.3 | +2.5 / -0.9 / -2.7 / -0.4 | -0.39 | +1.12 ± 1.56 | -0.01 | no effect |
| blend:w0.5 | +4.1 / -0.4 / -4.1 / -0.4 | -0.20 | +1.16 ± 1.87 | -0.11 | no effect |
| haiku:top5 | not run: no ANTHROPIC_API_KEY on the machine (fallback c1 = pkg:k25_top20, already "no effect") | | | | pending |

**Combined winner (fresh split seeds 20..39, never used for selection):**

| setting | fold gains | mean fold gain | fresh 20-split gain | EMS Δ | decision |
|---|---|---|---|---|---|
| combo:C_bat_catalog | +3.7 / +3.9 / +0.5 / +0.0 | +2.03 | +1.59 ± 1.36 | +0.36 | **passes — recommended** |
| combo:A_tolpv_catalog | +5.0 / +3.1 / −3.2 / −2.6 | +0.57 | +3.72 ± 1.63 | −0.61 | passes (loses on Q3/Q4) |
| combo:B_joint | +5.0 / +6.6 / −5.5 / −4.3 | +0.45 | +3.52 ± 2.09 | −0.44 | passes (loses on Q3/Q4) |

Shuffled-label control, C on 2025 Q4: 19.4% vs 24.1% real default (collapses below the real model, as it must).

**Reading:**
- Only one mechanism carries a gain: size the battery by coverage over the **catalogue sizes** instead of the predicted
  quantile samples (`sizing.coverageCandidates: "catalog"`, battery within tolerance ≈ +8 pts). joint/tolpv's PV changes
  hurt PV and lose on the two most recent quarters; C keeps PV as is and has no losing fold.
- repeat:copy (serve the customer's earlier design) passes alone but is tiny (+0.1 fold / +0.3 split); it needs code
  (customer lookup), C's sizing part is a pure `config/policy.json` change.
- Package retrieval (Codex #1), habit features, placeholder demand, lag, wallbox threshold, recency, blend: no effect.
- Selective prediction (#41, default, fold mean): 23.6% whole design on the 30% most confident homes, 19.6% on the top
  50%, 16.0% on all. Any-option match (#42): 16.0% → 16.9% (C: 17.9%).
- Q1/Q2 folds train on only 347/588 rows; the 20-split gains are the larger-sample evidence.
