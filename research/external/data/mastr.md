# MaStR market context, not expert accuracy

Extracted 2026-11-08 from [Open Energy Family/open-MaStR 2025-02-09-unboxed](https://zenodo.org/records/14843222), published 2025-02-10. **© Bundesnetzagentur / Marktstammdatenregister 2025, DL-DE-BY-2.0**; derived filters/aggregates by Codex. All source URLs, downloaded SHA-256 and field meanings are in [`data/external/README.md`](../../../data/external/README.md) and `sources.json`.

The retained PV cohort is activated/in-operation Germany units, household-use, building/roof/facade, gross module 1–30 kWp, commissioning 2018–2026. This is a household-use rooftop **proxy**, not verified single-family systems or household totals. Gross module power is distinct from inverter/net kW; official registration guidance defines module peak power. [BNetzA registration guide, 2024-04-01](https://www.marktstammdatenregister.de/MaStRHilfe/files/regHilfen/Registrierungshilfe_Solar.pdf), accessed 2026-11-08.

## Actual extraction

| PV commissioning year | Retained units | p5 kWp | p25 | p50 | p75 | p95 | Registered one-to-one co-locations | Observed link share | Usable battery/PV ratio p50 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2018 | 53,978 | 3.12 | 5.30 | 7.25 | 9.72 | 13.28 | 9,287 | 17.2% | 1.000 |
| 2019 | 80,801 | 3.51 | 5.76 | 8.19 | 9.86 | 15.93 | 17,219 | 21.3% | 0.969 |
| 2020 | 145,336 | 3.78 | 6.20 | 8.78 | 9.86 | 16.07 | 41,154 | 28.3% | 0.980 |
| 2021 | 185,821 | 4.07 | 6.66 | 9.24 | 10.39 | 18.57 | 70,014 | 37.7% | 0.911 |
| 2022 | 271,464 | 4.18 | 6.84 | 9.31 | 10.40 | 17.60 | 109,856 | 40.5% | 0.914 |
| 2023 | 686,330 | 4.26 | 7.14 | 9.60 | 11.62 | 18.04 | 273,583 | 39.9% | 0.902 |
| 2024 | 535,307 | 4.00 | 7.04 | 9.84 | 12.40 | 19.86 | 323,272 | 60.4% | 0.904 |
| 2025 partial | 26,414 | 4.20 | 7.65 | 10.32 | 13.76 | 22.95 | 16,023 | 60.7% | 0.889 |

Totals: scanned 4,953,448 PV rows, retained 1,985,451; scanned 1,755,316 storage rows, retained 1,641,534 positive-capacity lithium units whose single linked storage-installation capacity is verified in both reference directions. No selected conflicting or identical duplicate unit rows were found. Federal-state splits and p5/p25/p50/p75/p95 for every storage year are in `mastr_summary.json`.

**2026 is unavailable**, not zero: the snapshot predates it. 2025 is partial through the snapshot date and registration lag affects late 2024 too. The benchmark's 2024 comparison is explicitly historical; it does not establish 2026 German population plausibility.

## Link semantics

Capacity in this snapshot is populated on `StromSpeicher` installation, while `EinheitenStromSpeicher.NutzbareSpeicherkapazitaet` is empty. The adapter joins legacy `SpeMastrNummer` to storage installation (SSE) `MastrNummer` only when its single `VerknuepfteEinheit` matches that SEE unit, avoiding copying one installation capacity across several units. The official model separates storage installation capacity in **usable kWh** from unit power. [BNetzA data structure, 2018](https://www.marktstammdatenregister.de/MaStRHilfe/files/regHilfen/MaStR-Datenstruktur_%28Marktakteure_Einheiten_und_Gruppierungsobjekte%29_final.pdf), [export specification rev 26.2, 2026-10-01](https://www.marktstammdatenregister.de/MaStRHilfe/files/gesamtdatenexport/Dokumentation%20MaStR%20Gesamtdatenexport/Dokumentation%20MaStR%20Gesamtdatenexport.pdf), accessed 2026-11-08. Column spelling is verified in the pinned snapshot dictionary; current spec is a cross-check, not a claim of identical schema.

Solar `SpeMastrNummer` is empty in every retained solar row. We therefore require a shared **nonempty technical location ID and operator ID**, exactly one selected PV and one selected storage unit. 860,408 pairs satisfy this conservative registry-reference rule. Multiple units within either retained cohort or absent links are excluded. This is registered co-location under one operator, **not proof of electrical coupling** or a single dwelling. Postcode/address proximity is never used. The observed link share is **not a national battery attach-rate estimate**; 1,125,043 retained PV units are ambiguous or unlinked. Storage may be retrofitted later than PV: ratios are grouped by PV commissioning year and observed at snapshot, not battery attachment at original commissioning.

For 2024 PV, the linked subset has 323,272 co-locations; median usable kWh/kWp=0.9035, p5–p95=0.4830–1.6667. The standalone 2024 lithium storage marginal has 531,059 units, median 9.5 usable kWh; it is not household-only.

## A defensible planner sentence

> In the 2024 household-use rooftop registry cohort with a unique co-located lithium storage unit, 9 kWp is at the 38.5th empirical percentile (323,272 co-locations; snapshot 2025-02-09).

Percentile here is 100×share(PV≤9), including ties. It describes observed register units. It does not say that 9 kWp is correct for this customer, nor that the registry pair is a certified matched system. Do not shorten it to “62nd percentile of 2025 German homes with batteries.” Actual values, cohort and date must be shown.

## Testable owner requests

1. Eval/Engine: treat the register ratio as external context first. If trying a prior, freeze candidate strength on pre-2026 folds and keep expert imitation/physics objectives separate; do not tune to make registry histograms match.
2. Engine: expose product-specific **usable** capacity if a direct ratio comparison is wanted. The present0.92 dispatch fraction is only a scenario; nominal and usable batteries cannot be silently mixed.
3. Eval: refresh to a documented newer snapshot for a real 2026 comparison, and validate direct PV/storage references if the newer schema provides them. Never backfill absent-year data or infer household links from postcode.

### Refresh lead verified in current official schema

The official rev26.2 export specification (2026-10-01), section5.5.8/page100, documents `GemeinsamRegistrierteSolareinheitMastrNummer` as the solar unit registered with a storage unit. That field is absent from the pinned2025 storage CSV header, so it was not used or guessed. A newer snapshot containing it may support direct register-reference pairing instead of conservative co-location. Its actual completeness/cardinality and any electrical-coupling interpretation still need measurement. [Official specification](https://www.marktstammdatenregister.de/MaStRHilfe/files/gesamtdatenexport/Dokumentation%20MaStR%20Gesamtdatenexport/Dokumentation%20MaStR%20Gesamtdatenexport.pdf), accessed2026-11-08. The2018 object model usesSSE for the storage grouping object; the snapshot reference column remains spelled `SpeMastrNummer`. Match exact reference values rather than assuming a prefix from a current documentation example.
