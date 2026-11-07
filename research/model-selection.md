# Model selection (validation only, test scored once)

Protocol: train offers <= 2025-09-30, validate 2025-10-01..2025-12-31 (n=232 projects, two installers; one has only 21 train rows), refit on train+validation (<= 2025-12-31), score 2026 once (n=325). Nothing below was chosen by looking at 2026. Code: `eval/select_model.py` (run with `python eval/run.py --data dataset --offline --select`). Aggregates only.

Caveat: n=232 gives roughly +-3 EMS points of noise, so small validation differences are not evidence. The 2026 baseline numbers for B0/B0c/B1/M1 had been seen in an earlier run, but no decision used them.

## Validation: M1 upgrades (greedy, kept only if EMS improves; best PV gate per row)

| Candidate | EMS | Whole design | PV +-20% | Battery +-25% | Kept |
|---|---|---|---|---|---|
| base M1 (installer one-hot) | 56.80 | 16.4% | 47.0% | 50.9% | |
| + physics features (simulator NPV-optimal kWp, economic battery) | 57.37 | 18.5% | 48.3% | 53.0% | yes |
| + installer PV prior (median kWp by demand bucket, out-of-fold) | 58.04 | 19.8% | 51.7% | 54.3% | yes |
| + depth 3, min leaf 20 | 58.45 | 22.8% | 50.4% | 56.9% | |
| **+ depth 3, min leaf 40 (gate 0.5)** | **58.55** | 23.7% | 52.2% | 55.6% | yes |
| + depth 2, min leaf 40 | 57.73 | 24.6% | 52.2% | 56.0% | |
| + depth 4, min leaf 30, l2 1 | 57.95 | 23.3% | 52.2% | 53.9% | |

## Validation: per-component source (within-tolerance, tie-break EMS)

| Component | B0 | B0c | H1 | M1+ | SIM | Chosen |
|---|---|---|---|---|---|---|
| Heat pump | 96.6 | 95.7 | 95.7 | 96.6 | | M1 (tie with B0) |
| PV (gate 0.5) | 44.8 | 44.4 | | 52.2 | | M1, gate 0.5 (0.3/0.4: 48.3, 0.6: 52.2) |
| Battery | 39.2 | 46.6 | 39.2 | 55.6 | 23.3 | M1 |
| Wallbox | 75.0 | 76.7 | 76.7 | 76.7 | | B0c (EV rule; tie, first listed) |

The simulator's economic battery (SIM) matches installers least: they size batteries by habit and package, not by NPV. It stays as the explanation/validation signal, not the sizing source.

Chosen config (`services/engine/config/policy.json`): mode composite, sources {pv M1, battery M1, heatPump M1, wallbox B0c}, pvGate 0.5, features {physics, installerPrior}, trees {maxDepth 3, minLeaf 40}, conformal {pv 0.636 kWp, battery 0}.

## Test 2026 (scored once, n=325): EMS / whole design / PV / battery

| Model | EMS | Whole design | PV +-20% | Battery +-25% |
|---|---|---|---|---|
| B0 installer median | 61.1 | 20.6% | 42.5% | 47.4% |
| B0c conditioned median | 59.0 | 19.1% | 43.1% | 39.4% |
| B1 rule of thumb | 55.0 | 14.8% | 32.9% | 40.0% |
| M1 (previous selected) | 58.8 | 16.9% | 56.3% | 48.6% |
| M1+ (validated upgrades) | 60.4 | 20.9% | 59.7% | 49.2% |
| Composite (served) | 60.4 | 20.9% | 59.7% | 49.2% |

Composite equals M1+ on the test split (the only different component, the wallbox EV rule, scores the same as the learned EV rule).

## p10-p90 interval coverage of the expert size (target 80%)

| | PV | Battery |
|---|---|---|
| Validation, before conformal | 74.9% | 85.8% |
| Validation, after (calibration set, in-sample) | 80.9% | 85.8% |
| Test, M1 original | 75.4% | 57.2% |
| Test, M1+ before conformal | 80.1% | 83.6% |
| Test, composite after conformal | 85.5% | 83.6% |

Split-conformal (CQR) widening was calibrated on the train-only model; the model refit on more data is already better calibrated, so test PV coverage overshoots to 85.5%. Safe side, slightly wider than needed.

## Reading for the pitch

On installer-style matching the learned policy now beats the installers' own median on PV size (59.7% vs 42.5% within +-20%) and ties it on the whole-design metric (20.9% vs 20.6%), but it does not beat it on the composite Expert Match Score (60.4 vs 61.1), because B0 gets the battery/wallbox habits right by construction. The gains came from regularisation and an installer-specific size prior, not from the simulator. Differences of one or two points are inside the noise of 325 test projects.

## Oracle: what is one answered question worth? ("Ask next", PLAN 6.9)

Same selected composite, refit on train <= 2025-12-31, test 2026 (n=325), scored once, nothing tuned (`python eval/run.py --oracle`, code `eval/oracle.py`, block `oracle` in `eval/results/latest.json`). Each row designs the same test homes with the field unknown, then answered (unknown / answered).

| Field | Unknown state | EMS | Whole design | PV +-20% | Battery +-25% | Wallbox |
|---|---|---|---|---|---|---|
| Demand | every demand replaced by the 4,500 kWh default | 56.0 / 60.4 | 12.3% / 20.9% | 46.5% / 59.7% | 43.1% / 49.2% | 78.2% / 78.2% |
| EV | flag and km blanked (flag "no" gives the same numbers) | 59.9 / 60.4 | 20.3% / 20.9% | 60.6% / 59.7% | 49.2% / 49.2% | 76.0% / 78.2% |
| Roof (UPPER BOUND) | no cap vs cap = the expert's own module count | 60.4 / 67.8 | 20.9% / 32.9% | 59.7% / 82.5% | 49.2% / 52.0% | 78.2% / 78.2% |
| Heat demand | blanked for Gas/Oil homes | n=3 only: no reading | | | | |

Reading: knowing the real demand is worth +4.4 EMS and +8.6 points of whole-design matches (PV +13 points): it is the one input whose absence the model cannot hide. The EV flag mostly moves the wallbox (+2.2 points) and little else. The roof row is an upper bound, not a forecast: the cap equals the expert's kWp, so PV can only match or undershoot; a measured roof is a looser cap and is worth less, but the direction (PV within tolerance 59.7% to 82.5%) shows why installers' unrecorded roof size is the data's ceiling. Heat demand has only 3 Gas/Oil homes in the test split, so it is reported but not interpretable. Existing PV / storage are not in the experiment (about 1% of homes).
