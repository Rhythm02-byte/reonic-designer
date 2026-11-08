# Measured profile sensitivity

Computed 2026-11-08. [WPuQ 2019 hourly data](https://zenodo.org/records/5642902) and [OPSD 2020-04-15](https://data.open-power-system-data.org/household_data/2020-04-15/), both CC-BY-4.0; source hashes/field meanings in `data/external/README.md` and `sources.json`.

Retained 27 complete WPuQ NO_PV household shapes and 27 separately metered HP electric shapes, plus OPSD 2016 residential2 grid household, residential4 EV and residential4 HP. 57 normalized 8760-hour shapes total; no new imputation. WPuQ excludes six incomplete profiles per feed; OPSD retains documented upstream interpolation and drops Feb 29 from leap 2016 before normalization. Residential4 gross-minus-HP/EV reconstruction has 29 negative hours and is excluded, not clipped. OPSD is **cumulative kWh**: upstream hourly `.last()` readings require backward differencing. HP electric energy is not heat output, and charger kWh is not vehicle kilometres. See [OPSD processing notebook](https://github.com/isc-konstanz/household_data/blob/2020-04-15/processing.ipynb), accessed 2026-11-08.

Same fixed engine dispatch/Kassel PV weather and equal annual load in both alternatives. Household 4500 kWh; HP 5000 electric kWh from 17000 useful kWh at modeled SCOP 3.4; EV 1512 kWh from the existing 12000-km model. These are scenario choices, not measured household demands. Comparing timing with equal annual energy avoids confusing weather-volume and demand-volume effects. WPuQ's source clock conversion is not fully established, so 0/+1 h shifts are included; source-year weekday calendar differs from H0's 2023. This is a sensitivity study, **not observed autarky error, independent simulator validation, or population confidence interval**.

## Coupled home systems: measured shape minus engine shape

For household+HP, preserve the paired household and HP shapes from each retained WPuQ home, scaling separately to 4500+5000 kWh. For household+EV, hold H0 fixed and replace only the EV shape with the single OPSD residential EV shape scaled to 1512 kWh.

| Fixed PV kWp / nominal battery kWh | Scenario | Profile/clock scenarios | Autarky delta pp p5 | p50 | p95 | Self-consumption delta pp p50 |
|---|---|---:|---:|---:|---:|---:|
| 5/0 | household_plus_hp | 54 | -4.20 | -0.64 | 1.98 | -1.29 |
| 5/0 | household_plus_ev | 2 | 7.29 | 7.57 | 7.85 | 9.63 |
| 9/5 | household_plus_hp | 54 | -5.75 | -0.07 | 3.14 | -0.06 |
| 9/5 | household_plus_ev | 2 | 7.66 | 8.17 | 8.69 | 5.68 |
| 12/10 | household_plus_hp | 54 | -7.80 | -1.55 | 6.11 | -1.37 |
| 12/10 | household_plus_ev | 2 | 2.07 | 2.21 | 2.36 | 0.79 |

The full isolated-component tables remain in `data/external/profile_calibration.json`. Quantiles summarize this selected cohort and two clock conventions, not uncertainty over German homes. Hourly measured data still smooth intrahour fluctuations. The same dispatch is used on both sides, so this cannot certify its correctness; independent toy balance checks live in stress.py.

## Temperature and recommendations

WPuQ weather HDF5 uses datetime64 **nanoseconds**, unlike electrical seconds. Its temperature group unit attribute is °C. Provisional binned relative HP electricity is in `profiles/metadata.json`; weather/feed clock ambiguity means these bins are disabled as fitted model calibration. They measure electric timing, not COP or design heat load. The downloaded weather is retained as a research diagnostic, not secretly injected into engine outputs.

Engine owner: (1) add an optional **local calibrated profile** seam/family without changing the default before validation; test fixed systems on held-out public homes and source years, (2) keep household, EV and HP demand boundaries explicit to avoid adding electric heating/charging twice, (3) use the observed sensitivity to qualify savings claims rather than translate this small cohort into a universal correction factor. Model selection and real expert agreement remain separate.

Rebuild: `node scripts/py.mjs eval/external/pack/build_profiles.py`; load compact arrays with `eval/external/profiles.py`. The existing engine was not edited.
