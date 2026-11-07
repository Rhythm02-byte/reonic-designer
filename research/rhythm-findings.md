# Teammate prototype (`reonic-designer`): recorded findings

Digest of what the prototype in `_incoming/reonic-designer` learned, so nothing is lost when `_incoming/` is deleted.
Aggregates only, no raw rows. The prototype used its own loader (first option = expert design, 450 W assumed where only a module count exists) on the same 1,593 projects. Its numbers are **not** directly comparable with `eval/results/latest.json` (different ETL, PV target and metric definitions); see "How our port compares" at the end.

## Design of the prototype (ported to `services/engine/engine/policy/`)

- Chain heat pump -> PV -> battery -> wallbox; per component an include classifier + size regressor (sklearn HistGradientBoosting), teacher forcing at training time, planner locks flow downstream. Include cut-off 0.5.
- Wallbox is a rule: EV in the home -> wallbox (most common installed size, 11 kW); unknown EV flag -> no wallbox.
- Rules R01 existing HP -> no new HP; R02 no new/existing PV -> no battery; R03 PV <= 30 kWp; R04 battery <= 2 kWh/kWp; sizes snapped to the 15 most frequent installed sizes. Locked values are flagged, never changed.
- Unknown stays NaN (HGB handles it). PV target NaN = "offered, size not recoverable": only include/exclude is scored.
- Case base: k=25 nearest past projects drive explanations and "unusual for similar homes" flags (share that got the component, size percentile).

## Metric definitions

Per held-out project, a size matches within PV +-20%, battery +-25%, heat pump +-25%, wallbox include/exclude only. `whole_design_within_tolerance` = all four at once (headline). Always read include accuracy against `expert_include_rate` (heat pump accuracy 99% is trivial: experts include one in 0.8% of designs).

## Data evidence (1,593 projects with parts, two installers)

| | `23c108b7` | `2a8ba8e2` |
|---|---|---|
| Projects | 336 | 1,257 |
| With >1 option | 6% | 22% |
| PV size recoverable | 99% | 93% |
| Period | 2025 | mid-2024 to 2025 |

- Chosen designs (lowest option number): battery in ~89%, PV ~86%, wallbox 26% (much likelier with an EV), heat pumps 13 of 1,593 (0.8%; 31 heat pump line items across all options). Too few to learn HP sizing.
- Storage-only retrofits exist for homes that already have PV.
- Inputs reliable: demand, price, price increase, EV yes/no, load profile, existing PV/battery/wallbox, flexible tariff. Heating type and heating demand ~12% filled; house size and inhabitants < 1%; roof area and budget absent. Blank shares: heating type 88%, EV km 96%, household size 100%, PV size 6%.
- Installers behave differently: PV tracks demand at `2a8ba8e2`; designs look package-driven at `23c108b7`. Battery brands Sigenergy 89% vs Huawei 49% / EcoFlow 40%; modules Sunpro 94% vs AIKO 75%; existing PV 0% vs 1.4%.
- 13 projects (0.8%, all `2a8ba8e2`) carry demand 0 kWh: impossible, treat as unknown.
- Outliers to decide on, not silently drop: demand 0 or 50,000 kWh, PV up to 99.9 kWp, battery up to 108 kWh (commercial or errors).
- Named modules at `2a8ba8e2` are 475 W (AIKO) and 455 W (Trina): the assumed 450 W is probably low.
- Swapped columns: inverter rows' `battery_capacity_kwh`/1000 matches the kW in the inverter name for 98% of 52 rows. Battery rows match a "+ N kWh" package name for 71% of 77 options (all `23c108b7`); the 29% mismatch is unexplained.
- Packages: 77 of 149 options with a package kWh also have a separate battery row (possible double count in those 77).
- Demand does not seem to include an existing EV/HP: homes with an EV have median demand 4,000 vs 4,500 kWh without; HP homes 4,000 vs 4,500 (weak, unadjusted).

## Default-demand check (exactly 4,500 kWh)

457 of 1,593 projects (29%) show exactly 4,500 kWh (round 4,000 kWh only 5-7%): very likely a tool default.

| Comparison (random split) | Whole design | PV | Battery | Test rows | Baseline |
|---|---|---|---|---|---|
| all rows | 15.7% | 45.1% | 39.2% | 319 | 3.8% |
| without the 4,500 rows | 14.9% | 46.1% | 43.9% | 228 | 5.3% |
| default rows only (same model) | 18.3% | 56.1% | 34.1% | 82 | |
| other rows only (same model) | 14.8% | 41.4% | 40.9% | 237 | |

Removing them does not change the conclusion; differences of a few points are noise at these test sizes. It does not prove the values are wrong. (We keep `demand_is_default` and `demand_round500` as model features.)

## Sensitivity to unanswered Reonic questions (random 80/20, seed 0)

| Signed option | Module Wp | Whole design | PV +-20% | Battery +-25% | Baseline whole design |
|---|---|---|---|---|---|
| first | 400 | 14.4% | 46.1% | 39.8% | 3.8% |
| first | 450 | 15.7% | 45.1% | 39.2% | 3.8% |
| first | 500 | 14.7% | 46.7% | 39.5% | 3.4% |
| last | 400 | 13.5% | 46.7% | 37.0% | 3.1% |
| last | 450 | 12.5% | 45.8% | 34.8% | 3.4% |
| last | 500 | 13.8% | 46.7% | 36.4% | 3.4% |

Range 12.5-15.7%; the model stays ahead of their (weak) rule-of-thumb baseline in all six. Report the range, not the best run. Our own grid is `python eval/run.py --sensitivity`.

## Wallbox study

- Learned wallbox model vs EV rule, 5-fold CV on train only (cut-off 0.78 chosen out-of-fold): accuracy 76.2% vs 76.5%, so the model adds no information beyond the EV flag.
- Test split, scored once: isolated model 74.9% vs EV rule 74.0% (3 homes out of 319 = noise). In the full pipeline the learned wallbox got 67% because the step is trained with true PV/battery sizes but predicts with its own (train/predict mismatch).
- Decision: deterministic EV rule. Trade-off: wallbox accuracy 67% -> 74% but whole-design 15.7% -> 13.2%, because the rule finds only 7% of the homes that get a wallbox (precision 0.50, recall 0.07, F1 0.13, F2 0.09). Only ~6% of homes have an EV, so most wallbox homes cannot be identified from the inputs. Accuracy rewards saying "no" (24% of homes have one): read wallbox on recall/F2.

## Other recorded results (their pipeline)

| Split | Train / test | Whole design | Baseline | PV +-20% | Battery +-25% |
|---|---|---|---|---|---|
| Random 80/20 | 1,274 / 319 | 13.5% | 3.8% | 45.8% | 38.9% |
| Train `2a8ba8e2`, test `23c108b7` | 1,257 / 336 | 18.5% | 4.2% | 39.9% | 47.3% |
| Train `23c108b7`, test `2a8ba8e2` | 336 / 1,257 | 9.8% | 5.6% | 33.8% | 32.0% (baseline 30.4%) |

Transfer is uneven: a model trained on 336 projects does not learn enough for the big installer. Treating demand 0 as unknown moved random whole-design 13.2% -> 13.5%.

Simulation study (policy we wrote, not installer behaviour; never an accuracy claim): recovery of a known rule 34.7% whole-design; accuracy falls ~5 points per 25% of inputs blanked (34.7 / 29.5 / 24.8 / 18.7% at 0/25/50/75%); HP sizing barely learned even with 30% HP homes (77.4 -> 81.0%); a model trained on simulation scores 4.2% on the real export.

## Open questions for Reonic (still unanswered)

1. Which option was signed (lowest/highest/unrecoverable)? 2. Module wattage at `2a8ba8e2`, and is the DC Install/Substructure quantity always the module count? 3. Are inverter/battery columns swapped (data says yes) and why do 29% of battery rows disagree with package names? 4. Do package lines include the battery? 5. Does `energy_demand_wh` include an existing EV/HP (data says no)? 6. Are the folder IDs installers? 7. Time per design today and offer-to-signed rate (business case). 8. Is 4,500 kWh a default?

## Prototype's future work (specs)

Confidence + one alternative per component (re-run the engine with a lock); deviation analysis (miss rates by consumption band / heating / EV / installer / option count, from per-project predictions); homeowner variant view on the same engine within installer-offered limits. Per-component include thresholds still to be tuned on a validation split (a missed battery loses a sale; an unneeded one oversells).

## How our port compares

`python eval/run.py` reports M1 (the ported chain, with installer one-hot, quantile intervals, our ETL) next to our baselines on temporal, random 80/20 seed 0 and both leave-one-installer-out directions, with both Expert Match Score and the metrics above. See `eval/results/latest.json` and the final section of the engine hand-off for the numbers.
