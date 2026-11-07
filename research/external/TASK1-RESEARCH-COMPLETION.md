## Summary

Research date: **2026-11-07**. This supplements R1–R6; it does not replace them or claim their open questions are all solved. Public metadata only was inspected. No dataset files, private rows, credentials, application code or existing reports were changed.

The most useful addition is a correction: OPSD's published schema includes **residential EV charging**, alongside residential heat-pump electricity and PV generation. It is a better immediate profile candidate than an unrelated synthetic district-heating fault dataset. [OPSD schema](https://data.open-power-system-data.org/household_data/2020-04-15/datapackage.json)

Five Kaggle candidates are assessed below. Prefer upstream releases; a Kaggle licence card does not override upstream rights. None of the newly reviewed datasets contains verified **installer design labels**: household intake paired with an installer-selected target system. Operational fault labels and measured installed-system channels are different evidence. This conclusion is limited to these reviewed sources, not all datasets on the internet.

R1's Zolar availability question is partly resolved: the original installation company ceased business; software/website continue under a different owner. [Zolar notice](https://zolar.de/fuerkunden)

## Findings

**Evidence method.** Kaggle landing pages were opened but often returned no readable body. Public Kaggle `datasets/view/<owner>/<slug>` and `datasets/list/<owner>/<slug>` metadata endpoints were successfully read over HTTPS, without downloading data files. Links below identify both landing and metadata evidence. `totalBytes` is reported as an API inventory value, not an independently measured archive size. Search-list sizes sometimes differ; do not mix those with expanded inventories. No account or Kaggle credentials were used.

**1. Household electricity: UCI mirror — usable secondary choice.** Exact landing: [uciml/electric-power-consumption-data-set](https://www.kaggle.com/datasets/uciml/electric-power-consumption-data-set). Kaggle's card reports “Database: Open Database, Contents: Database Contents”, version 1, updated 2016-08-23, and 132,960,755 bytes. This is the card's wording, not a blanket public-domain permission. [Kaggle metadata](https://www.kaggle.com/api/v1/datasets/view/uciml/electric-power-consumption-data-set)

The authoritative UCI release explicitly grants **CC BY 4.0**. It contains 2,075,259 minute observations from one Sceaux, France household, December 2006–November 2010; semicolon-delimited TXT, 126.8 MB listed uncompressed, 19.7 MB download. Fields: date/time, global active/reactive power, voltage, intensity and three submeter energies. Active power is kW; submeter energy is Wh per minute. About 1.25% of observations are missing. [UCI original](https://archive.ics.uci.edu/dataset/235/individual+household+electric+power+consumption)

**Mapping:** complete-year integration `sum(Global_active_power / 60)` gives candidate `demandKwh`, subject to missingness treatment and project demand boundaries. The water-heater/air-conditioning submeter cannot establish a space-heating heat pump. `hasEv`, `evKm`, `heatingType`, `heatDemandKwh`, existing capacities and all design outputs remain unknown. Use for timing/aggregation tests, not German household diversity. Prefer UCI directly and retain its attribution and licence.

**2. Combined load, heat-pump electricity and PV: OPSD mirror — highest practical priority.** Exact landing: [mexwell/household-load-and-solar-generation](https://www.kaggle.com/datasets/mexwell/household-load-and-solar-generation). Card: **CC BY 4.0**, updated 2024-03-04; API inventory 968,209,546 bytes. It describes CSV at 1/15/60-minute resolution and reproduces OPSD channel documentation. Mirror equivalence/checksums are **UNVERIFIED**. [Kaggle metadata](https://www.kaggle.com/api/v1/datasets/view/mexwell/household-load-and-solar-generation)

Prefer [OPSD's pinned 2020-04-15 release](https://data.open-power-system-data.org/household_data/): published formats include CSV, XLSX and SQLite; listed minute/hour CSV sizes are 851/15 MB, ZIP 149 MB. Observation coverage varies by site; exact usable household-year counts remain **UNVERIFIED**. Documentation warns of minute-to-day gaps and interpolation. [Release documentation](https://data.open-power-system-data.org/household_data/2020-04-15/README.md)

**Correction to R2:** upstream metadata explicitly identifies `DE_KN_residential4_ev` in kWh, not only an industrial EV channel. The same schema includes `DE_KN_residential4_heat_pump`, residential PV/import/export and interpolation flags; the data licence identifier is **CC-BY-4.0**. [Authoritative schema](https://data.open-power-system-data.org/household_data/2020-04-15/datapackage.json)

**Mapping:** residential import + PV − export can support gross electricity reconstruction when all channels and boundaries are complete. Separate HP/EV electricity before scaling household-only `demandKwh`, if that is the contract's definition. The HP channel supports observed `heatingType=HeatPump`; the EV channel supports observed charging presence, potentially `hasEv=true` with provenance. Neither yields `evKm` or charger ownership/rating. PV kWh is generation, not `existingPvKwp`/`pvKwp`; HP electrical kWh is neither useful `heatDemandKwh` nor thermal `heatPumpKw`. Battery capacities and recommended outputs remain unknown. These are proposed adapter rules, not executed transformations.

**3. Heat-pump faults: AI DHC — reject for household sizing.** Exact landing: [mathieuvallee/ai-dhc-heatpump-cop](https://www.kaggle.com/datasets/mathieuvallee/ai-dhc-heatpump-cop). Card: **CC BY-SA 4.0**, updated 2023-02-28; inventory 235,551,125 bytes. File-list metadata confirms CSV scenarios such as `csv/HeatPump-bc00-s0-000.csv`. The description explicitly calls the data **synthetic COP-decrease faults**. Granularity, simulated calendar span, field names/units and complete file count remain **UNVERIFIED**; metadata did not expose columns. [Card metadata](https://www.kaggle.com/api/v1/datasets/view/mathieuvallee/ai-dhc-heatpump-cop), [file inventory](https://www.kaggle.com/api/v1/datasets/list/mathieuvallee/ai-dhc-heatpump-cop)

The description also includes IEA DHC copyright/republication restrictions concerning the publication/report; whether these restrict the dataset beyond its CC card is **UNVERIFIED**. Obtain clarification before redistribution. The upstream project concerns district-heating forecasting/failure detection, and its portal requests registration for additional material. [IEA project](https://www.iea-dhc.org/the-research/annexes/annex-xiii/annex-xiii-project-03)

**Mapping:** none of the project intake/output fields is verified. A synthetic fault scenario is not an expert household installation recommendation. Do not treat its COP fault label as `heatPumpKw` or use it to calibrate household heat demand. Possible future fault robustness work is outside the demo's sizing objective.

**4. Heat/COP scenarios: When2Heat mirror — useful fallback, upstream preferred.** Exact landing: [matthewjansen/when2heat-european-heating-demand-dataset](https://www.kaggle.com/datasets/matthewjansen/when2heat-european-heating-demand-dataset). Card: **CC BY 4.0**, updated 2025-01-30; inventory 2,662,887,552 bytes including supplementary material. It identifies the 2023-07-27 OPSD source. Exact mirror file inventory and equality to upstream remain **UNVERIFIED**. [Kaggle metadata](https://www.kaggle.com/api/v1/datasets/view/matthewjansen/when2heat-european-heating-demand-dataset)

The original is simulated country-level hourly demand/COP for 28 European countries, 2008–2022, with space/water heat and source/sink-specific COP. Its licence is **CC BY 4.0**, with separate MIT script terms and specified attribution. [Upstream README](https://data.open-power-system-data.org/when2heat/2023-07-27/README.md)

**Mapping:** use a normalized German space/water shape scaled to a separately supplied `heatDemandKwh`; use an explicitly chosen COP scenario to derive electrical consumption. The source provides scenario shapes, not measured household `heatDemandKwh`, `heatingType` or selected `heatPumpKw`. All other intake fields and recommended equipment outputs remain unknown. Do not use country MW totals as a home's design heat load.

**5. PV generation: two Indian plants — useful metadata example, rights unresolved.** Exact landing: [anikannal/solar-power-generation-data](https://www.kaggle.com/datasets/anikannal/solar-power-generation-data). Version 1, updated 2020-08-18; 11,233,523 bytes across four CSVs: generation and weather files for each plant. Two plants, 34 days; generation is inverter-level, weather plant-level. Licence wording is **“Data files © Original Authors”**; no affirmative commercial reuse licence was verified. [Card metadata](https://www.kaggle.com/api/v1/datasets/view/anikannal/solar-power-generation-data), [file inventory](https://www.kaggle.com/api/v1/datasets/list/anikannal/solar-power-generation-data)

The public explorer documents 15-minute observations and generation columns `DATE_TIME`, `PLANT_ID`, `SOURCE_KEY`, `DC_POWER`, `AC_POWER`, `DAILY_YIELD`, `TOTAL_YIELD`; AC/DC power are described as kW. Exact start/end dates, weather-field units and independently checked scale consistency remain **UNVERIFIED**. [Indexed Kaggle explorer](https://www.kaggle.com/anikannal/solar-power-generation-data)

**Mapping:** generation channels could test PV time-series handling after rights/unit checks. They do not establish panel nameplate `pvKwp`/`existingPvKwp`; 34 days do not validate German annual yield. Household demand, EV, heating, battery and installer-selected outputs remain unknown. No upstream original plant release with clearer rights was established. Defer embedding this data.

**Additional upstream lead: HEAPO.** ETH's March 2025 release describes 1,408 Zurich households with heat pumps, 15-minute/daily electricity, November 2018–March 2024, eight weather stations and 410 consultant visit protocols. Zenodo lists a 458,317,017-byte ZIP and API licence `cc-by-4.0`. [Landing](https://zenodo.org/records/15056919), [metadata](https://zenodo.org/api/records/15056919)

It could expand HP operational diversity beyond WPuQ; these consultant protocol labels concern operation/optimization, not our supervised bundle targets. Exact electrical metering boundaries, useful-heat channels, nested formats and field-to-contract mapping remain **UNVERIFIED**. Do not prioritize its adapter before the simpler OPSD/WPuQ path.

**R1 availability resolved in part.** Zolar's own notice states that ZOLAR GmbH's insolvency proceedings opened 2025-08-01 and its business ceased; Sollit acquired software/website, while the separate Zolar Wow company continues. Keep the old configurator as historical design inspiration; current access to that exact flow remains **UNVERIFIED**. [Company notice](https://zolar.de/fuerkunden)

## Implications for our product

Recommended decisions, not implemented changes:

- Use upstream OPSD/WPuQ for public profile realism and When2Heat for declared thermal scenarios. Kaggle adds discoverability; it supplies no reason to replace a pinned authoritative source.
- Add a source manifest before fixtures: release, licence, source URL, checksum, electrical/thermal and power/energy units, timestamp convention, missingness/interpolation and household demand boundary. Exclude windows whose missingness would make an annual total misleading.
- Keep profile realism evaluation separate from expert imitation. Public traces can challenge timing, energy conservation and sensitivity; they cannot establish correct installer design accuracy.
- Keep unknown inputs unknown. Generation does not identify nameplate capacity; charging energy does not identify kilometres; electricity consumed by a heat pump does not identify thermal output. Presence evidence needs provenance and its own uncertainty.
- For the demo, retain the R1/R6 design direction: comparable variants, annual economics, editable assumptions, battery incremental value and a visible human review status. These remain product hypotheses, not measured trust improvements. See [R1](R1-competitor-ux.md) and [R6](R6-homeowner-trust.md).
- Retain R3's preliminary sizing boundary and R4's draft-record exclusions. Do not activate unresolved usable-capacity, phase, firmware, accessory or installed-price entries merely because a related dataset exists. See [R3](R3-heat-pump-sizing.md), [R4](R4-product-catalog-prices.md) and [compatibility note](COMPATIBILITY.md).

## Open questions / uncertainty

The following is the remaining work, not an assertion that all R1–R6 research has been completed:

| Area | Resolved here | Still incomplete / next decision |
|---|---|---|
| R1 competitor UX | Zolar company/software distinction | Authenticated controls/screen counts, mobile/accessibility and exact current configurator. Enerflow identity still UNVERIFIED; do not silently substitute Enerflo. |
| R2 public data | Five exact Kaggle references; upstream licence preference; residential OPSD EV correction | No adapters, downloads, row quality checks or empirical validation. AI DHC columns/time and rights ambiguity; Indian PV permission; mirror equivalence unresolved. |
| R2 earlier licensing | OPSD licence explicitly identified | LBNL reuse grant still UNVERIFIED; BDEW redistribution rights still UNVERIFIED; full Fluvius terms still UNVERIFIED. Reopened landing pages did not supply a clear grant. [LBNL](https://emp.lbl.gov/publications/us-distributed-solar-and-storage-0), [BDEW](https://www.bdew.de/energie/standardlastprofile-strom/), [Fluvius](https://opendata.fluvius.be/p/licentieopendatafluvius/) |
| R3 heat-pump selection | No new universal coefficients claimed | Seasonal boiler efficiencies, age-only load-hours, exact German SKU/phase maps and full capacity curves remain unresolved. Existing subsidy claims are not newly validated by this supplement; check the applicable official programme version before product use. |
| R4 catalogue/pricing | No invented missing prices | Installer net prices, revision/availability, SAJ usable energy, full stack/firmware/accessory constraints and turnkey inclusions remain unresolved. Resolve only exact demo components first. |
| R5 learning | Public profile data classified correctly | Alternative-label semantics, defaults, split integrity, model gain and interval coverage require local evaluation; literature cannot settle them. No private records inspected here. |
| R6 trust | No causal uplift invented | Comprehension, chart preference, appropriate skepticism and incorrect-explanation detection need product testing. |

R7–R9, research integration into PLAN/pitch, application fixes, contract work and full compatibility remain outside this deliverable. No board message was sent.

## Sources

All links were opened or returned by search on **2026-11-07**; Kaggle API URLs were successfully read as public metadata using HTTPS requests when browser extraction failed. Dataset payloads were not fetched. Source publication/release dates are stated above; otherwise date is unknown.

1. UCI — [original household data and CC BY 4.0 terms](https://archive.ics.uci.edu/dataset/235/individual+household+electric+power+consumption).
2. Kaggle contributors — exact landing, view-metadata and file-inventory URLs accompany each candidate above; these are contributor claims, not independent validation.
3. Open Power System Data — [Household release](https://data.open-power-system-data.org/household_data/), [README](https://data.open-power-system-data.org/household_data/2020-04-15/README.md), [machine-readable licence/schema](https://data.open-power-system-data.org/household_data/2020-04-15/datapackage.json) — 2020-04-15.
4. Ruhnau et al./OPSD — [When2Heat documentation](https://data.open-power-system-data.org/when2heat/2023-07-27/README.md) — 2023-07-27.
5. IEA DHC — [Annex XIII Project 03](https://www.iea-dhc.org/the-research/annexes/annex-xiii/annex-xiii-project-03) — project period 2020–2023.
6. Brudermüller et al./ETH Zurich — [HEAPO record](https://zenodo.org/records/15056919), [record metadata/licence](https://zenodo.org/api/records/15056919) — 2025-03-24.
7. Zolar — [customer/company status notice](https://zolar.de/fuerkunden) — undated, proceedings date 2025-08-01.
8. Kaggle staff — [licences are self-reported and require verification](https://www.kaggle.com/general/157880) — discussion date approximate, not used as legal clearance.
