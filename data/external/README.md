# Public external evidence pack

Prepared **2026-11-08**. Raw public downloads stay in `raw/`, ignored by this directory's `.gitignore`. No confidential Reonic rows are copied here. This pack supplies **plausibility and profile sensitivity**, never expert-match accuracy.

## Run offline

```powershell
pnpm x:external
node scripts/py.mjs -m pytest -q eval/external
```

The default sampler is `public-marginals`; `--sampler balanced-coverage` reproduces the separate coverage scenario. The full 720-request stress plus replay can take several minutes on a busy laptop. Successful process completion means the benchmark ran; its printed `FAIL_WITH_BLOCKED_COVERAGE` is an engine finding, not a stress pass.

The runner requires the existing local `services/engine/models/designer.joblib`, the policy config and these cached aggregates/profiles. It does not fit a model or fetch data. `OFFLINE=1` is set and Python outbound socket calls are rejected while scoring. That guard is an in-process check, not a system firewall. Model/config/source/cache hashes and canonical batch replay are recorded in `eval/external/results.json`. Do not treat the artifact's training set as a new held-out evaluation: the public synthetic inputs have no expert labels.

Rebuild from public sources (online acquisition is explicit):

```powershell
node scripts/py.mjs eval/external/pack/download.py
services/engine/.venv/Scripts/python.exe -m pip install -r eval/external/requirements-acquisition.txt
node scripts/py.mjs eval/external/pack/mastr.py
node scripts/py.mjs eval/external/pack/build_profiles.py
```

On POSIX use the venv's `bin/python` for the optional install. The German reference facts in `german_priors.json` are explicit verified transcriptions of pinned HTML with source hashes; they are not a newly fitted joint distribution.

The scripts use stdlib HTTP/ZIP, existing pandas/numpy and optional h5py; **open-mastr is not required** for the pinned Zenodo snapshot. Acquisition verifies Zenodo size and MD5; locally computed SHA-256 values are below and in `sources.json`. Parser tests use synthetic fixtures. All scored public caches are smaller than 5 MB. `raw/mastr_filtered_v3.pkl` is a local public-row cache; delete this exact cache file if deliberately changing extraction filters, then rebuild. It is never a committed artifact.

## Sources, verified fields and limits

**MaStR**: Bundesnetzagentur, processed by Open Energy Family/open-MaStR v0.14.5, Zenodo `2025-02-09-unboxed`, published 2025-02-10. **DL-DE-BY-2.0**, attribution: © Marktstammdatenregister 2025 / Bundesnetzagentur; derived summaries and filters by Codex, 2026-11-08. [Snapshot](https://zenodo.org/records/14843222), [licence](https://www.govdata.de/dl-de/by-2-0). The snapshot warns about duplicates; exact selected duplicates and conflicting unit IDs are checked explicitly.

Used meanings verified against the snapshot's dictionary and cross-checked with the [official export specification, rev 26.2, 2026-10-01](https://www.marktstammdatenregister.de/MaStRHilfe/files/gesamtdatenexport/Dokumentation%20MaStR%20Gesamtdatenexport/Dokumentation%20MaStR%20Gesamtdatenexport.pdf). Current specification is newer than the snapshot: column names come from the pinned snapshot, never invented from the current model.

| Field(s) | Verified meaning and adapter use |
|---|---|
| `EinheitMastrNummer` | Generating/storage **unit** identity (SEE); distinct from storage installation (SSE) and EEG installation identifiers. Deduplicate at unit identity. |
| `Bruttoleistung` | PV module gross/nameplate kW, treated as kWp. [Official solar registration guide, 2024-04-01](https://www.marktstammdatenregister.de/MaStRHilfe/files/regHilfen/Registrierungshilfe_Solar.pdf) explicitly defines summing module peak powers. This is not `Nettonennleistung` or inverter active power. |
| `Inbetriebnahmedatum` | Unit commissioning date; use calendar year, not registration/update/EEG commissioning date. |
| `EinheitBetriebsstatus`, `EinheitSystemstatus` | Retain `In Betrieb`, `Aktiviert`, with `Land=Deutschland`. |
| `Lage`, `Nutzungsbereich` | Retain building/roof/facade location and `Haushalt` use, gross 1–30 kWp, years 2018–2026 requested. Household-use rooftop proxy; no proof of single-family dwelling or total household system size. |
| `Bundesland` | Unit federal state, aggregate region split. Postcode/coordinates/address are never linkage keys. |
| `SpeMastrNummer` | Reference from unit to storage installation. Solar values are absent in this snapshot; do not invent direct links. |
| storage installation `MastrNummer`, `VerknuepfteEinheit`, `NutzbareSpeicherkapazitaet`, `AnlageBetriebsstatus` | Usable capacity is on **StromSpeicher installation** in this snapshot, not populated on the unit table. Join legacy `SpeMastrNummer` reference to storage installation ID (SSE) and require its single explicit linked SEE to equal the storage unit ID; installation in operation. Exclude duplicated/ambiguous mappings. Usable capacity is **kWh**, not power or nominal capacity. [Official data structure, 2018](https://www.marktstammdatenregister.de/MaStRHilfe/files/regHilfen/MaStR-Datenstruktur_%28Marktakteure_Einheiten_und_Gruppierungsobjekte%29_final.pdf) and export specification distinguish the objects. |
| `Batterietechnologie` | Retain lithium batteries with positive finite usable kWh. The standalone storage marginal has no residential size cap and is not presented as household-only. |
| `LokationMastrNummer`, `AnlagenbetreiberMastrNummer` | Technical registry location and operator references. Require both nonempty and exactly one selected PV plus one selected storage unit for a conservative **registered co-location**. This is one-to-one within retained cohorts, not guaranteed electrical pairing or all equipment at the site. |

The ratio report uses registered co-locations. The fraction with an observed link is **not** an unbiased German battery attach rate. The 2025 cohort is partial, the 2026 cohort unavailable; the benchmark compares a separately labelled 2024 historical reference. Ratios are usable battery kWh / gross PV kWp. The engine's nominal battery capacities are converted only in a labelled 92% usable dispatch **scenario**, not a verified product-specific conversion. Wasserstein compares the generated ratios to an equally weighted 1001-point empirical quantile sketch (midpoints q=(i+0.5)/1001): approximate descriptive distance, not a goodness-of-fit test.

**WPuQ**: Schlemminger et al./ISFH, [Zenodo 5642902](https://zenodo.org/records/5642902), metadata version 2.0; **CC BY 4.0**. Sources: [datapackage](https://zenodo.org/records/5642902/files/datapackage.json?download=1), [paper](https://www.nature.com/articles/s41597-022-01156-1), [upstream processor](https://github.com/ISFH/WPuQ/blob/master/WPuQ/dataprocessor.py). Use 2019 hourly `NO_PV/SFH*/HOUSEHOLD` and `/HEATPUMP` only. Schema `P` is **W active power**; `P_TOT` is total active power. Hourly mean W /1000 gives kWh for each one-hour interval. The upstream code resamples by mean. Do not sum three phases again when using `P_TOT`. The electrical index is encoded Unix-like seconds by upstream naive-date subtraction; source local/UTC interpretation is not fully resolved. We retain date-order8760 hours and bracket 0/+1 h shifts rather than claim exact civil-clock alignment. No leap day in 2019. Strict finite nonnegative complete years only, no new gap imputation.27 complete household and 27 HP profiles retained,6 per feed excluded. NO_PV avoids uncertain reconstructed behind-meter PV. HP electric energy never becomes thermal capacity or useful heat.

Weather HDF5 uses a **different index encoding** (`index_kind=datetime64`, nanoseconds), not the electrical seconds. `WEATHER_SERVICE/IN/WEATHER_TEMPERATURE_TOTAL` unit attribute states°C. Hourly means of weather are used for provisional HP-versus-temperature summaries; unresolved source-clock alignment prevents using the bins as a calibrated model or COP curve. Normalized profiles sum to 1 and carry public source IDs; absolute meter traces are not shipped.

**OPSD / CoSSMic**, [release 2020-04-15](https://data.open-power-system-data.org/household_data/2020-04-15/), **CC BY 4.0**, scripts MIT. Attribution: Open Power System Data. 2020. Data Package Household Data. Version2020-04-15 (primary measurements CoSSMic). [Schema](https://data.open-power-system-data.org/household_data/2020-04-15/datapackage.json), [README](https://data.open-power-system-data.org/household_data/2020-04-15/README.md), [processing notebook](https://github.com/isc-konstanz/household_data/blob/2020-04-15/processing.ipynb).

`utc_timestamp` labels UTC periods; `interpolated` marks upstream filled channels. All used `DE_KN_*` columns are **cumulative kWh readings**, not interval kWh or instantaneous kW. Processing notebook resamples using hourly `.last()`: backward difference gives energy for the currently labelled hour, with minute-boundary approximation. Require both finite counter boundaries. Keep 2016 then remove only Feb 29 and renormalize. Residential2 grid import is the grid-only household proxy; residential4 EV and HP channels provide separate electric end-use shapes. Gross residual import+PV-export-EV-HP produces 29 negative hours for residential4, so that household reconstruction is excluded rather than clipped. Residential4 charging establishes neither charger power nor kilometres. Upstream interpolation is retained and flagged; broader source-household flag counts are in metadata. Three OPSD profiles retained. Scenarios use equal annual energies and do not validate population representativeness or actual realized savings.

**Stromspiegel/co2online** demand anchor, current page observed 2026-11-08: [household table](https://www.stromspiegel.de/stromverbrauch-verstehen/stromverbrauch-im-haushalt/). Without-electric-DHW SFH values for 1–5 people are 1800/2700/3500/3800/4500 kWh/year. These are reference facts, **not** an empirical joint sampling distribution. Introductory 2-person prose conflicts with the table; the adapter explicitly uses the table. Demand multipliers, EV km, useful-heat volumes and price scenarios are analyst assumptions. The default runner now uses the additional verified national household/heating/plug-in marginals below, while the stress suite and optional `--sampler balanced-coverage` remain balanced. A population-weighted German adopter score is blocked until a suitable joint distribution is established. No copyright licence for republishing the page is asserted; page bytes are ignored and only cited numeric facts are used.

## Artifacts and requests

- `mastr_summary.json`: year/state quantiles, linked co-location ratios and coverage diagnostics.
- `profiles/measured.npz` + `profiles/metadata.json`:57 calibrated normalized shapes; loader `eval/external/profiles.py`.
- `profile_calibration.json`: fixed 5/9/12-kWp and 0/5/10-kWh systems, isolated and combined loads, same dispatch/weather; sensitivity rather than independent physics validation.
- `eval/external/stress.py`: dev intake-only stress suite; supported checks and blocked transport/BOM/compatibility/final-evaluator scope reported separately.
- `research/external/data/triage.md`: all other public/Kaggle sets, licence gates and next contribution.

Engine requests: evaluate measured shape families on fixed systems without adding HP/EV twice; review actual bill demand boundary; investigate default provenance and unbounded/conflicting inputs from stress report. Any MaStR prior must be tested on pre-2026 folds, with registry cohort/capacity mismatch explicit. Do not fit to public typicality or synthetic cases as if they were expert designs. Pitch requests: contextual percentile wording must carry year/filter/count; no 2026 German claim from this snapshot.

## Downloaded artifact hashes

Full records are machine-readable in `sources.json`. MD5 match means equality with the publisher's listed checksum, not validation of source correctness. All accessed 2026-11-08. Documentation bytes are used locally for citation/verification and not redistributed.

| Local raw artifact | Version | Licence | SHA-256 | Source URL |
|---|---|---|---|---|
| raw/mastr_bnetza_open_mastr_datapackage.json | 2025-02-09-unboxed | dl-de/by-2-0 | 6d254c8cb1929a8e379bd01c946fa6b2184d7caff1f818ffa4c518fe83d95062 | [source](https://zenodo.org/api/records/14843222/files/bnetza_open_mastr_datapackage.json/content) |
| raw/mastr_LICENSE | 2025-02-09-unboxed | dl-de/by-2-0 | ea501a9831827961060e6e1c28f1ea668dbe5fe6abd3b166dba65801f47c7195 | [source](https://zenodo.org/api/records/14843222/files/LICENSE/content) |
| raw/mastr_bnetza_mastr_solar_raw.csv.zip | 2025-02-09-unboxed | dl-de/by-2-0 | f4a4840dc9b63f2c321d2f13dfdbb960682eefa63d89fd11ab9478441e410c08 | [source](https://zenodo.org/api/records/14843222/files/bnetza_mastr_solar_raw.csv.zip/content) |
| raw/mastr_bnetza_mastr_storage_raw.csv.zip | 2025-02-09-unboxed | dl-de/by-2-0 | 526b80bfa26d336d6445a3d9bdaf4ad60bd6fbf35a914e5b9d8c13b0dec9cdd4 | [source](https://zenodo.org/api/records/14843222/files/bnetza_mastr_storage_raw.csv.zip/content) |
| raw/mastr_bnetza_mastr_storage_units_raw.csv.zip | 2025-02-09-unboxed | dl-de/by-2-0 | 601d22d9f38b0aa3819d29ade3b96d5f64613d4dcea66f24f58761e5f78bff77 | [source](https://zenodo.org/api/records/14843222/files/bnetza_mastr_storage_units_raw.csv.zip/content) |
| raw/wpuq_2019_weather.hdf5 | 2.0 | CC-BY-4.0 | 580bfa3824b6647a83ab4ab972ec6a429cddde721bec07da2962a52ec00068c5 | [source](https://zenodo.org/api/records/5642902/files/2019_weather.hdf5/content) |
| raw/wpuq_2019_data_60min.hdf5 | 2.0 | CC-BY-4.0 | 9b105849231109fb84d60bce005a3a5f5440e30ef3be10571036fa6359619d42 | [source](https://zenodo.org/api/records/5642902/files/2019_data_60min.hdf5/content) |
| raw/wpuq_datapackage.json | 2.0 | CC-BY-4.0 | ac57d7c9780b292c1298d9b42db7657a6bdd3aced698038045496c2fcfc02655 | [source](https://zenodo.org/api/records/5642902/files/datapackage.json/content) |
| raw/opsd_datapackage.json | 2020-04-15 | CC-BY-4.0 | 93500241f4bb19f84f2668b100f53ec531e0c7dcbfa5d8759425c1375d588670 | [source](https://data.open-power-system-data.org/household_data/2020-04-15/datapackage.json) |
| raw/opsd_README.md | 2020-04-15 | CC-BY-4.0 | b3c7b45c40f5e0a3e9a6505b61a40132a0b5b6dc63fd45432f0cd1fa8ec7a01f | [source](https://data.open-power-system-data.org/household_data/2020-04-15/README.md) |
| raw/opsd_household_data_60min_singleindex.csv | 2020-04-15 | CC-BY-4.0 | 15956440b27465686eae2abf5895cbc3dab80f934a891bcb2f4f944428e97d60 | [source](https://data.open-power-system-data.org/household_data/2020-04-15/household_data_60min_singleindex.csv) |
| raw/opsd_main.ipynb | 2020-04-15 | MIT | 5620dd0ac50d8bcc143894dd6b6fc27f44e859f4d4f98649944ea53333b577a0 | [source](https://raw.githubusercontent.com/isc-konstanz/household_data/2020-04-15/main.ipynb) |
| raw/opsd_processing.ipynb | 2020-04-15 | MIT | 355932c852148b845dca679acdf855d3f2d01128dc5a38e1df794163d63a3116 | [source](https://raw.githubusercontent.com/isc-konstanz/household_data/2020-04-15/processing.ipynb) |
| raw/wpuq_dataprocessor.py | current observed 2026-11-08 | UNVERIFIED documentation; citation only, not redistributed | c2ed8a2f38db507e618011d5dd8ecc1e25def85054ca5d30ca7f25392365f2eb | [source](https://raw.githubusercontent.com/ISFH/WPuQ/master/WPuQ/dataprocessor.py) |
| raw/mastr_export.pdf | current observed 2026-11-08 | UNVERIFIED documentation; citation only, not redistributed | 9eae230cb879f4a0bb07c1fcf4b28831473bb898c962b81a1f1443b725cc1181 | [source](https://www.marktstammdatenregister.de/MaStRHilfe/files/gesamtdatenexport/Dokumentation%20MaStR%20Gesamtdatenexport/Dokumentation%20MaStR%20Gesamtdatenexport.pdf) |
| raw/mastr_filtering.pdf | current observed 2026-11-08 | UNVERIFIED documentation; citation only, not redistributed | ffca5b297038e682a3ffc338e978e38c442979e527040fbf74a3c63a789a932b | [source](https://www.marktstammdatenregister.de/MaStRHilfe/files/regHilfen/Anleitung_zur_Datenfilterung.pdf) |
| raw/mastr_solar_registration.pdf | current observed 2026-11-08 | UNVERIFIED documentation; citation only, not redistributed | 53e32cfb84f95531a6ba8b0d7f2d400a72be6bd30b5a9431c1094b9a08d8f3d8 | [source](https://www.marktstammdatenregister.de/MaStRHilfe/files/regHilfen/Registrierungshilfe_Solar.pdf) |
| raw/mastr_structure.pdf | current observed 2026-11-08 | UNVERIFIED documentation; citation only, not redistributed | 9f487a2a776c8dc5dcafa4c3f71e0896a816b4aa4de8c2f2cdc879fa8234a33c | [source](https://www.marktstammdatenregister.de/MaStRHilfe/files/regHilfen/MaStR-Datenstruktur_%28Marktakteure_Einheiten_und_Gruppierungsobjekte%29_final.pdf) |
| raw/mastr_AnlageStromSpeicher.html | current observed 2026-11-08 | UNVERIFIED documentation; citation only, not redistributed | d63a5474747e6f633e734cbd0e0d1a8956414015d99d3f189d0f1afe63966b68 | [source](https://openenergyplatform.github.io/mastr-docs/schema/classes/AnlageStromSpeicher/) |
| raw/mastr_EinheitSolar.html | current observed 2026-11-08 | UNVERIFIED documentation; citation only, not redistributed | 9f6e7afa436a93fce090d0b0a4691e962a0f4ec90d02d8500b286546081fe9f7 | [source](https://openenergyplatform.github.io/mastr-docs/schema/classes/EinheitSolar/) |
| raw/stromspiegel.html | current observed 2026-11-08 | UNVERIFIED documentation; citation only, not redistributed | af40682f49c16d01d6b27c97a00d22727923b93d81e2720d34590746f371a058 | [source](https://www.stromspiegel.de/stromverbrauch-verstehen/stromverbrauch-im-haushalt/) |

## Additional German marginal anchors

`german_priors.json` records successful official HTML extraction, three source hashes and every mapping/assumption. Destatis 2024 household-size shares are 42.3/32.8/11.7/9.4/3.8% for 1/2/3/4/5+ people. EVS 2023 reports 6.0% of households with an electric car **or plug-in hybrid**, not pure BEVs or vehicle share. Census 2022 dwelling heat shares are 56% gas, 19% oil, 4% wood/pellets, 3% solar/geothermal/ambient group and 18% remaining (including 15% district heat). The group-to-Heatpump mapping is an analyst proxy; remaining heat maps Unknown. Independent mixing of different-year marginals is a labelled scenario, never an adopter joint distribution.

- [Official source](https://www.destatis.de/DE/Themen/Gesellschaft-Umwelt/Bevoelkerung/Haushalte-Familien/Tabellen/1-3-privathaushalte-neuer-zeitvergleich.html), 2024 final results, page stand2026-04-13, accessed 2026-11-08; SHA-256 `db6d17784f0e6cec310858b543d0f4f006c7ab5a09bc37ddee3dc436099d59ac`. Page redistribution licence UNVERIFIED; ignored HTML is not shipped.
- [Official source](https://www.destatis.de/DE/Themen/Gesellschaft-Umwelt/Einkommen-Konsum-Lebensbedingungen/Ausstattung-Gebrauchsgueter/Tabellen/liste-fahrzeuge-d.html), EVS 2023 at Jan1, page stand2026-08-17; do not use distinct LWR2024 table, accessed 2026-11-08; SHA-256 `0bece31f8e6e28d8ae1c206604511fa3a0ec0028a46927dc98d9076da815ab0e`. Page redistribution licence UNVERIFIED; ignored HTML is not shipped.
- [Official source](https://www.destatis.de/DE/Presse/Pressemitteilungen/Zensus2022-Pressemitteilungen/PM_zenus2022_45.html), Zensus2022, press release2024-06-25 corrected rental figures, accessed 2026-11-08; SHA-256 `0aa61a88379aa6bb78465dc805306031b434ad5ff9a06f0eae4ce9f876b1cde2`. Page redistribution licence UNVERIFIED; ignored HTML is not shipped.
