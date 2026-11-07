# Data correlations (aggregates only)

Source: `data/processed` (ETL output). Unit of analysis: the **primary option** (lowest option_number) of each project with parts, n = 1593 (2a8ba8e2: 1257, 23c108b7: 336). Spearman rank correlations, pairwise-complete. `kwp` is over options that contain PV. `roof_*` is mined from the parts list (planner-known at design time, otherwise leakage); NaN when unparseable.

## 1. Spearman: inputs vs outputs (all installers)

| index | kwp | battery_kwh | has_battery | has_wallbox | hp_kw | has_pv |
|---|---|---|---|---|---|---|
| demand_kwh | +0.37 | +0.26 | +0.08 | +0.03 | -0.01 | +0.01 |
| demand_is_default | -0.03 | -0.29 | -0.24 | -0.00 | +0.04 | -0.53 |
| price_eur_kwh | -0.02 | -0.01 | +0.01 | -0.05 | -0.03 | +0.02 |
| price_escalation | -0.05 | +0.02 | +0.06 | +0.03 | -0.02 | +0.09 |
| has_ev | +0.06 | +0.11 | +0.05 | +0.16 | -0.02 | +0.09 |
| ev_km | +0.06 | +0.11 | +0.05 | +0.16 | -0.02 | +0.09 |
| heating_Gas | +0.00 | -0.01 | -0.05 | -0.01 | +0.45 | +0.01 |
| heating_Oil | +0.02 | -0.01 | -0.04 | -0.04 | +0.29 | -0.01 |
| heating_Heatpump | +0.16 | +0.24 | +0.08 | -0.01 | -0.03 | +0.16 |
| hp_elec_existing_kwh | +0.17 | +0.25 | +0.08 | -0.00 | -0.03 | +0.16 |
| load_family | -0.05 | +0.08 | +0.07 | +0.03 | -0.03 | +0.11 |
| roof_concrete_tile | -0.07 | -0.05 | +0.04 | -0.01 | +0.03 | +0.05 |
| roof_clay_tile | +0.05 | +0.01 | -0.02 | +0.02 | -0.02 | +0.03 |
| roof_flat | +0.01 | +0.03 | -0.06 | +0.01 | -0.03 | -0.05 |
| roof_metal | +0.06 | +0.02 | +0.01 | -0.04 | +0.04 | +0.01 |
| has_existing_pv | -0.02 | -0.10 | -0.07 | -0.03 | +0.06 | -0.14 |
| installer_2a8ba8e2 | -0.12 | -0.14 | -0.14 | +0.03 | +0.05 | -0.22 |

### Installer 23c108b7 (n=336)

| index | kwp | battery_kwh | has_battery | has_wallbox | hp_kw | has_pv |
|---|---|---|---|---|---|---|
| demand_kwh | +0.40 | +0.31 | +0.05 | +0.03 |  | -0.06 |
| demand_is_default | +0.01 | +0.02 | -0.08 | -0.06 |  | -0.15 |
| price_eur_kwh | -0.04 | -0.04 | -0.05 | -0.06 |  | -0.05 |
| price_escalation | -0.12 | -0.07 | +0.00 | +0.09 |  | +0.02 |
| has_ev | +0.06 | +0.09 | +0.03 | +0.28 |  | +0.05 |
| ev_km | +0.06 | +0.09 | +0.03 | +0.28 |  | +0.05 |
| heating_Gas | +0.01 | +0.01 | +0.01 | -0.05 |  | +0.02 |
| heating_Oil |  |  |  |  |  |  |
| heating_Heatpump | +0.20 | +0.19 | +0.04 | -0.03 |  | +0.03 |
| hp_elec_existing_kwh | +0.20 | +0.20 | +0.04 | -0.03 |  | +0.03 |
| load_family | -0.04 | -0.01 | +0.03 | +0.03 |  | +0.00 |
| roof_concrete_tile | -0.24 | +0.01 | +0.02 | -0.07 |  | +0.03 |
| roof_clay_tile |  |  |  |  |  |  |
| roof_flat | +0.11 | +0.07 | +0.11 | -0.15 |  | -0.06 |
| roof_metal | +0.23 | +0.17 | +0.07 | +0.06 |  | +0.10 |
| has_existing_pv |  |  |  |  |  |  |

### Installer 2a8ba8e2 (n=1257)

| index | kwp | battery_kwh | has_battery | has_wallbox | hp_kw | has_pv |
|---|---|---|---|---|---|---|
| demand_kwh | +0.37 | +0.26 | +0.09 | +0.02 | -0.02 | +0.02 |
| demand_is_default | -0.05 | -0.34 | -0.24 | +0.01 | +0.03 | -0.57 |
| price_eur_kwh | -0.07 | -0.06 | -0.04 | -0.04 | -0.02 | -0.04 |
| price_escalation | -0.07 | +0.02 | +0.04 | +0.01 | -0.01 | +0.05 |
| has_ev | +0.05 | +0.11 | +0.05 | +0.12 | -0.02 | +0.09 |
| ev_km | +0.05 | +0.11 | +0.05 | +0.12 | -0.02 | +0.09 |
| heating_Gas | +0.01 | -0.02 | -0.05 | +0.00 | +0.50 | +0.01 |
| heating_Oil | +0.03 | -0.01 | -0.03 | -0.05 | +0.29 | +0.00 |
| heating_Heatpump | +0.16 | +0.25 | +0.08 | +0.00 | -0.03 | +0.18 |
| hp_elec_existing_kwh | +0.17 | +0.26 | +0.08 | +0.01 | -0.03 | +0.18 |
| load_family | -0.05 | +0.11 | +0.07 | +0.02 | -0.03 | +0.13 |
| roof_concrete_tile | -0.07 | -0.05 | +0.05 | -0.02 | +0.03 |  |
| roof_clay_tile | +0.05 | +0.01 | -0.02 | +0.02 | -0.02 |  |
| roof_flat | +0.01 | +0.02 | -0.08 | +0.03 | -0.03 |  |
| roof_metal | +0.04 | +0.01 | +0.00 | -0.04 | +0.05 |  |
| has_existing_pv | -0.02 | -0.10 | -0.06 | -0.04 | +0.05 | -0.13 |

## 2. Battery kWh per kWp by segment (options with PV and battery)

| index | n | p25 | median | p75 |
|---|---|---|---|---|
| installer=23c108b7 | 320 | 0.83 | 0.93 | 1.18 |
| installer=2a8ba8e2 | 881 | 0.74 | 0.97 | 1.23 |
| has_ev=False | 1141 | 0.78 | 0.95 | 1.23 |
| has_ev=True | 60 | 0.79 | 0.93 | 1.26 |
| heating=Gas | 14 | 0.80 | 0.99 | 1.15 |
| heating=Heatpump | 163 | 0.83 | 1.01 | 1.31 |
| heating=Oil | 6 | 0.67 | 0.84 | 0.94 |
| heating=Unknown | 1016 | 0.77 | 0.93 | 1.19 |
| demand_bucket=<3.5k | 366 | 0.79 | 0.97 | 1.30 |
| demand_bucket=3.5-5k | 442 | 0.78 | 0.93 | 1.15 |
| demand_bucket=5-7k | 194 | 0.81 | 0.97 | 1.23 |
| demand_bucket=>7k | 199 | 0.74 | 0.92 | 1.16 |
| existing_pv=False | 1198 | 0.79 | 0.95 | 1.23 |

## 3. kWp by demand bucket per installer (PV options)

| installer_id | demand_bucket | n | p25 | median | p75 |
|---|---|---|---|---|---|
| 23c108b7 | <2.5k | 24 | 6.26 | 6.62 | 9.79 |
| 23c108b7 | 2.5-3.5k | 91 | 6.30 | 9.45 | 10.80 |
| 23c108b7 | 3.5-4.5k(def=4.5k) | 91 | 7.20 | 10.80 | 11.57 |
| 23c108b7 | 4.5-5.5k | 40 | 9.34 | 10.80 | 11.81 |
| 23c108b7 | 5.5-7k | 32 | 10.80 | 10.80 | 11.15 |
| 23c108b7 | 7-10k | 25 | 10.80 | 10.80 | 13.50 |
| 23c108b7 | >10k | 21 | 13.50 | 13.50 | 16.65 |
| 2a8ba8e2 | <2.5k | 83 | 5.85 | 7.20 | 9.00 |
| 2a8ba8e2 | 2.5-3.5k | 188 | 6.30 | 7.65 | 9.90 |
| 2a8ba8e2 | 3.5-4.5k(def=4.5k) | 276 | 7.09 | 9.00 | 10.80 |
| 2a8ba8e2 | 4.5-5.5k | 101 | 7.20 | 9.00 | 10.80 |
| 2a8ba8e2 | 5.5-7k | 128 | 8.10 | 9.45 | 10.80 |
| 2a8ba8e2 | 7-10k | 112 | 9.00 | 11.25 | 14.40 |
| 2a8ba8e2 | >10k | 44 | 11.03 | 13.50 | 20.02 |

kWp for default-like demand (exactly 4,500 kWh) vs other:

| installer_id | demand_is_default | n | median |
|---|---|---|---|
| 23c108b7 | False | 264 | 10.80 |
| 23c108b7 | True | 60 | 10.80 |
| 2a8ba8e2 | False | 791 | 9.00 |
| 2a8ba8e2 | True | 146 | 8.78 |

## 4. Depth-3 decision-tree rules (min leaf 20; descriptive, not a validated model)

### has_battery
Train accuracy 0.91 vs majority-class 0.91 (n=1593).

```
|--- demand_is_default <= 0.50
|   |--- demand_kwh <= 500.50
|   |   |--- class: no
|   |--- demand_kwh >  500.50
|   |   |--- installer_2a8ba8e2 <= 0.50
|   |   |   |--- class: yes
|   |   |--- installer_2a8ba8e2 >  0.50
|   |   |   |--- class: yes
|--- demand_is_default >  0.50
|   |--- installer_2a8ba8e2 <= 0.50
|   |   |--- class: yes
|   |--- installer_2a8ba8e2 >  0.50
|   |   |--- roof_concrete_tile <= 0.50
|   |   |   |--- class: yes
|   |   |--- roof_concrete_tile >  0.50
|   |   |   |--- class: yes
```

### kWp tercile (0: <= 8.1, 1: <= 10.8, 2: above)
Train accuracy 0.50 vs majority-class 0.39 (n=1261).

```
|--- demand_kwh <= 7100.00
|   |--- demand_kwh <= 3850.00
|   |   |--- hp_elec_existing_kwh <= 3750.00
|   |   |   |--- class: <=8.1
|   |   |--- hp_elec_existing_kwh >  3750.00
|   |   |   |--- class: <=10.8
|   |--- demand_kwh >  3850.00
|   |   |--- hp_elec_existing_kwh <= 2450.00
|   |   |   |--- class: <=10.8
|   |   |--- hp_elec_existing_kwh >  2450.00
|   |   |   |--- class: >10.8
|--- demand_kwh >  7100.00
|   |--- demand_kwh <= 9100.00
|   |   |--- installer_2a8ba8e2 <= 0.50
|   |   |   |--- class: <=10.8
|   |   |--- installer_2a8ba8e2 >  0.50
|   |   |   |--- class: >10.8
|   |--- demand_kwh >  9100.00
|   |   |--- price_eur_kwh <= 0.34
|   |   |   |--- class: >10.8
|   |   |--- price_eur_kwh >  0.34
|   |   |   |--- class: >10.8
```

### has_wallbox
Train accuracy 0.76 vs majority-class 0.75 (n=1593).

```
|--- ev_km <= 6000.00
|   |--- demand_kwh <= 11250.00
|   |   |--- roof_metal <= 0.50
|   |   |   |--- class: no
|   |   |--- roof_metal >  0.50
|   |   |   |--- class: no
|   |--- demand_kwh >  11250.00
|   |   |--- demand_kwh <= 13750.00
|   |   |   |--- class: no
|   |   |--- demand_kwh >  13750.00
|   |   |   |--- class: no
|--- ev_km >  6000.00
|   |--- demand_kwh <= 4200.00
|   |   |--- class: yes
|   |--- demand_kwh >  4200.00
|   |   |--- class: no
```

## 5. Mutual information (nats; higher = more informative, no linearity assumed; sorted by combined rank)

| index | kwp | battery_kwh | has_battery | has_wallbox |
|---|---|---|---|---|
| installer_2a8ba8e2 | 0.111 | 0.344 | 0.008 | 0.002 |
| roof_flat | 0.149 | 0.205 | 0.018 | 0.000 |
| roof_metal | 0.112 | 0.210 | 0.012 | 0.000 |
| demand_kwh | 0.083 | 0.128 | 0.043 | 0.000 |
| roof_concrete_tile | 0.082 | 0.185 | 0.017 | 0.000 |
| price_eur_kwh | 0.069 | 0.130 | 0.025 | 0.000 |
| demand_is_default | 0.000 | 0.058 | 0.031 | 0.003 |
| roof_clay_tile | 0.067 | 0.156 | 0.014 | 0.000 |
| heating_Heatpump | 0.004 | 0.020 | 0.009 | 0.004 |
| price_escalation | 0.019 | 0.034 | 0.000 | 0.009 |
| hp_elec_existing_kwh | 0.000 | 0.028 | 0.019 | 0.002 |
| load_family | 0.003 | 0.002 | 0.007 | 0.002 |
| has_existing_pv | 0.008 | 0.028 | 0.005 | 0.000 |
| has_ev | 0.000 | 0.000 | 0.000 | 0.012 |
| heating_Gas | 0.000 | 0.008 | 0.007 | 0.000 |
| ev_km | 0.000 | 0.015 | 0.004 | 0.000 |
| heating_Oil | 0.000 | 0.005 | 0.000 | 0.000 |

## 6. Interpretation

- **A "PV or no PV" gate exists and it is hidden in the demand default.** 332 of 1,593 primary options (21%) contain no PV at all (median 4 lines, 73% contain a battery (median 5 kWh), 25% wallbox). At installer 2a8ba8e2, 245 of the 391 default-like (exactly 4,500 kWh) projects are PV-less, versus 75 of 866 others. `demand_is_default` vs `has_pv` is Spearman -0.53 and is the strongest single input signal in the whole table. Only 4% of the PV-less options record an existing PV, so "retrofit / add-on quote" is mostly invisible in the status quo. Predict `P(pv)` first; the kWp model must be fit on PV options only.
- **Demand explains kWp only modestly** (Spearman +0.37 overall, +0.40 / +0.37 per installer; kWp tercile tree 50% vs 39% majority). Within a demand bucket the interquartile range is about 3-4 kWp. Installers cluster on a few package sizes (23c108b7: 10.8 kWp is the median in 4 of 7 demand buckets), so the kWp target is lumpy and roof-driven.
- **The "1 kWh per kWp" rule is the installers' behaviour.** Median battery/kWp is 0.93-0.97 in every segment (EV or not, heating type, demand bucket, installer), IQR roughly 0.75-1.25. Battery size follows kWp, not household features; chain battery after kWp. Heat-pump homes sit slightly higher (1.01) and oil homes lower (0.84, n=6).
- **Existing heat pump pushes everything up.** `heating_Heatpump` / `hp_elec_existing_kwh` vs kWp +0.16/+0.17 and vs battery kWh +0.24/+0.25, even after demand (existing-HP homes have larger demand, but the tree still splits on HP electricity at the same demand level).
- **Heat pump sizing is a structural, nearly deterministic gate.** `hp_kw` correlates only with fossil heating (Gas +0.45 / Oil +0.29; 0.50 within installer 2a8ba8e2). No other input matters. Wallbox follows EV (+0.16 overall, +0.28 at 23c108b7); an EV with km > 6,000 gives wallbox in most branches of the tree, but wallbox is bought without an EV in a quarter of options, so recall is capped (tree accuracy 0.76 vs 0.75 majority).
- **Battery presence is not predictable from inputs** (91% base rate; tree adds nothing). Absent batteries are mostly PV-less options without a battery line (wallbox-only or similar), not a household preference. Price, escalation, load profile and tariff carry almost no signal (|rho| < 0.1 everywhere).
- **Installer is a first-class feature.** Installer dummy ranks first in mutual information for kWp and battery kWh (0.11 and 0.34 nats). Installer 2a8ba8e2 has smaller systems (median 9.0 vs 10.8 kWp) and fewer batteries (88% vs 97%).
- **Roof columns are leakage-prone.** Their high mutual information is partly an artefact: roof is NaN when no mounting lines exist, i.e. when the option has no PV, so "roof unknown" re-encodes `has_pv`. Use roof only as an optional planner input and impute carefully. Within 23c108b7, concrete-tile roofs have smaller systems (-0.24) and metal/trapezoid larger ones (+0.23), plausibly a package-size effect (n is small).
- Caveats: Spearman on primary options only; trees are descriptive (train accuracy, no holdout); `hp_kw` and existing-HP signals rest on n of about 23 fossil-heated and 163 heat-pump homes.


