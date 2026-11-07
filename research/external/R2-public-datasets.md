**Correction (2026-11-07):** OPSD also has a residential EV channel, `DE_KN_residential4_ev`; the industrial-only statement below is superseded. See [TASK1-RESEARCH-COMPLETION.md](TASK1-RESEARCH-COMPLETION.md) for the authoritative schema, Kaggle additions, licences and mappings. No reviewed public source establishes installer-selected bundle labels.

## Summary (≤150 words)

As of **2026-11-07**, prioritize **MaStR** for German installation-size distributions and **WPuQ** for German household/heat-pump electricity profiles. LBNL’s 2026 public dataset explicitly includes PV DC capacity and battery kWh, making it useful for external bundle plausibility checks. [MaStR snapshot](https://zenodo.org/records/14843222), [WPuQ](https://www.nature.com/articles/s41597-022-01156-1), [LBNL guide](https://eta-publications.lbl.gov/sites/default/files/2026-08/lbnl_publicdatafile_userguide_8.07.26.pdf)

No checked source was verified to provide unrestricted German household records pairing all our intake fields with complete expert-designed outputs. Registry comparisons assess market realism, not household-specific sizing accuracy.

Important restrictions include HTW’s noncommercial licence, restricted MCS/Pecan Street access and Irish CER research-use conditions. [HTW](https://solar.htw-berlin.de/elektrische-lastprofile-fuer-wohngebaeude/), [MCS](https://certificate.microgenerationcertification.org/Home/Terms/), [Pecan Street](https://www.pecanstreet.org/dataport/licenses/), [Irish CER](https://doi.org/10.7929/ISSDA/BX59EU)

## Findings

**Mapping convention:** every requested field not explicitly mapped below remains `null`/unknown:

`demandKwh`, `hasEv`, `evKm`, `heatingType`, `heatDemandKwh`, `existingPvKwp`, `existingStorageKwh`, `pvKwp`, `batteryKwh`, `heatPumpKw`, `hasWallbox`.

An installed capacity may represent an existing-system input **or** an observed historical output. Never place the same observed asset on both sides of a prediction benchmark.

### Installation and market datasets

| Dataset | Licence, access, size, format, time | Relevant fields and explicit mapping | Caveats |
|---|---|---|---|
| **MaStR / open-mastr** | DL-DE-BY-2.0; free XML, processed database/CSV. Official bulk updates daily. Verified 2025-02-09 snapshot: 1.6 GB. [Landing](https://www.marktstammdatenregister.de/MaStR/Datendownload), [snapshot](https://zenodo.org/records/14843222) | `Bruttoleistung` → `pvKwp` or `existingPvKwp`, after verifying PV rating semantics. `NutzbareSpeicherkapazitaet` → `batteryKwh` or `existingStorageKwh`, after unit verification. Commissioning/status/postcode support filtering. [Dictionary](https://zenodo.org/records/14843222/files/bnetza_open_mastr_datapackage.json?download=1) | No household demand/tariff verified. Handle expansions/status/duplicates. Postcode matching does not establish PV–battery household linkage. |
| **LBNL Tracking the Sun / 2026 distributed solar-storage data** | Free public CSV; explicit reuse licence U. Underlying collection about 5.3 million systems; public file about 4.0 million PV systems, 81 fields, through 2025. [Landing](https://emp.lbl.gov/publications/us-distributed-solar-and-storage-0) | `PV_system_size_DC` → `pvKwp`; `battery_rated_capacity_kWh` → `batteryKwh`. Also battery kW, installed/battery prices, date, ZIP/city/state and equipment. [Guide](https://eta-publications.lbl.gov/sites/default/files/2026-08/lbnl_publicdatafile_userguide_8.07.26.pdf) | **Battery kWh exists.** Missing values use −1; many fields incomplete. Rated is not necessarily usable capacity. Prices nominal USD. Filter residential SFH and expansion records. |
| **UK MCS MID** | Registry since 2010; raw access restricted/proprietary. Public aggregates separate. Battery statistics cover April 2024–March 2026, XLSX/ODS. [MID](https://mcsfoundation.org.uk/projects/mcs-installations-database-mid/), [terms](https://certificate.microgenerationcertification.org/Home/Terms/), [statistics](https://www.gov.uk/government/statistics/mcs-certified-domestic-battery-installation-statistics) | With permission: useful heat demand → `heatDemandKwh`; previous heating → `heatingType`; thermal capacity → `heatPumpKw`; PV/battery capacity → outputs after dictionary verification. [Restricted schema](https://github.com/nestauk/asf_core_data) | Public aggregates cannot become household rows. Capacity rating conditions and household pairing need verification. Registration does not grant unrestricted reuse. |
| **Australia CER** | Generally CC BY 4.0, exceptions apply. Free monthly CSV/XLSX; series from 2001. Battery scheme data from July 2025. September 2026 snapshot: 4.56 million PV and 546,789 battery installations. [Data](https://cer.gov.au/markets/reports-and-data/small-scale-installation-postcode-data), [terms](https://cer.gov.au/about-us/our-policies/copyright) | Postcode/year counts and capacity totals. PV kW/count and battery usable kWh/count support **aggregate** `pvKwp`/`batteryKwh` checks. No household-row mapping. | Certification lag, upgrades and off-grid systems affect interpretation. Heat-pump category concerns **water heaters**, not space-heating HP output. |
| **Netherlands CBS / CERES-derived** | Public CBS statistics generally CC BY 4.0; downloads/API. Table updated June 2026; recent years provisional. Installation microdata is restricted separately. [Table](https://www.cbs.nl/nl-nl/cijfers/detail/85005NED?dl=B0C79), [microdata](https://www.cbs.nl/nl-nl/onze-diensten/maatwerk-en-microdata/microdata-zelf-onderzoek-doen/microdatabestanden/zonnestroominstallaties-kenmerken-en-elektriciteitsproductie-van-zonnestroominstallaties) | Panel kWp, inverter kW, production, size/sector/region. Aggregate residential panel kWp/count → `pvKwp` plausibility only. | No open household bundle mapping verified. Inverter kW is not panel kWp. Registration errors/incompleteness are acknowledged by Stedin. [Stedin](https://www.stedin.net/zakelijk/open-data/opgesteld-vermogen) |
| **Belgium / Fluvius** | Free API/export; custom Fluvius licence, full terms require review. Storage API: 197,124 records, modified 2026-11-07; monthly metadata. [Schema](https://opendata.fluvius.be/api/explore/v2.1/catalog/datasets/1_22-energieopslagsystemen-gekoppeld-op-distributienet), [licence](https://opendata.fluvius.be/p/licentieopendatafluvius/) | `capaciteit_kwh` → `batteryKwh` or `existingStorageKwh`; usable/nominal definition U. Also technology, inverter kVA, postcode and commissioning month. | No verified demand/price/PV linkage. Separate production/charger datasets exist, but their schemas were not established here. Do not infer `evKm` or household wallbox ownership. [Inventory](https://www.vlaamsenutsregulator.be/sites/default/files/uploads/lijst_open_data_fluvius.pdf) |
| **Switzerland SFOE production plants** | Free CSV ZIP/GPKG/Interlis/API; attribution terms `terms_by`. Monthly; modified September 2026. CSV ZIP fetched: 19.7 MB; row count/start U. [Landing](https://opendata.swiss/en/dataset/elektrizitatsproduktionsanlagen) | `TotalPower`, `InitialPower`, category, commissioning, address/postcode/coordinates. PV `TotalPower` → candidate PV mapping only after confirming DC/peak convention. [Model](https://pubdb.bfe.admin.ch/de/publication/download/10449) | Small unsubsidized voluntary registrations incomplete. No verified load, battery, HP or price fields. Account for expansions. |
| **EnergySage** | Public PDF marketplace reports; raw data packages marketed separately. Latest report September 2026/H1 2026. No open microdata licence verified. [Reports](https://www.energysage.com/data/) | Published size, equipment and price distributions → aggregate plausibility only. | Shopping/quote transactions are not necessarily signed installations. No supported household-row mapping. |

### Household and simulation datasets

| Dataset | Licence/access, size, format, period | Explicit mapping and limits |
|---|---|---|
| **HTW 74 household profiles** | CC BY-NC 4.0; free share/password `profile`. 74 one-year, one-second profiles; CSV roughly 5 GB compressed/45 GB unpacked. Published 2015. [Landing](https://solar.htw-berlin.de/elektrische-lastprofile-fuer-wohngebaeude/) | Integrate documented active power → `demandKwh`. Other fields unknown. Synthesized from measured material; not 74 independent complete raw field years. No detailed household/equipment metadata. Commercial reuse unresolved. [Documentation](https://solar.htw-berlin.de/wp-content/uploads/HTW-Repraesentative-elektrische-Lastprofile-fuer-Wohngebaeude.pdf) |
| **WPuQ / Schlemminger 2022** | CC BY 4.0; 38 German SFHs, May 2018–2020; HDF5, 10-second through hourly, weather/metadata. Verified 2019 hourly file: 110.6 MB. [Paper](https://www.nature.com/articles/s41597-022-01156-1), [record](https://zenodo.org/api/records/5642902) | Gross household electricity → `demandKwh`; known HP homes → `heatingType=HeatPump`; separate HP electricity → simulation channel. **Not** useful `heatDemandKwh` or thermal `heatPumpKw`. Check PV/net-load boundaries, gaps, solar-thermal DHW and resistance-heater-heavy cases. |
| **When2Heat / OPSD** | CC BY 4.0; free CSV/XLSX/SQLite; 28 countries, hourly 2008–2022; July 2023 release; CSV about 313 MB. [README](https://data.open-power-system-data.org/when2heat/2023-07-27/README.md) | Normalize German SFH space/water heat profiles and scale to separately supplied `heatDemandKwh`; use ASHP radiator/floor COP scenarios. National MW values are not household demand or peak capacity. |
| **IDEAL, UK** | CC BY 4.0; 255 homes, 2016–2018; richer measurements in 39. Household sensor ZIP 14.77 GB; documentation 4.39 MB. [Repository](https://datashare.ed.ac.uk/items/15e82917-56ed-4282-99ef-7f211bf87f9d/full) | Documented whole-home electricity → `demandKwh`; survey heating → `heatingType` after dictionary checks. Gas is fuel input, not useful heat. Exact raw columns/units and equipment capacity mappings U; unequal observation periods. |
| **Pecan Street** | Registration/approval; free university tier covers 75 homes under academic restrictions; commercial access paid. Broader offerings 2012–present; package size varies. [Access](https://www.pecanstreet.org/access/), [licences](https://www.pecanstreet.org/dataport/licenses/) | Authenticated whole-home load → `demandKwh`; documented `car1` charger channel supports EV-charging scenarios/observed presence, not `evKm`. `gen` is PV generation, not nameplate size. [Dictionary](https://www.pecanstreet.org/wp-content/uploads/2019/04/Dataport-metadata-dictionary.pdf) |
| **NREL ResStock / EULP** | EULP entry links CC BY 4.0; software terms separate. Free S3 CSV/Parquet; original EULP about 550,000 residential models at 15-minute resolution. Pin release/weather year. [OEDI](https://data.openei.org/submissions/4520), [registry](https://registry.opendata.aws/nrel-pds-building-stock/) | Annual electricity → `demandKwh`; fuel/equipment metadata → `heatingType`; explicitly thermal load → `heatDemandKwh`. Release-specific names/capacities U. Synthetic US stock is not German expert-design truth; EV modelling varies by release. |
| **OPSD Household / CoSSMic** | Attribution licence; retain exact version terms. Free CSV/XLSX/SQLite, April 2020 release. Catalogue describes 11 sites, including six residential IDs. Hourly CSV 15 MB; minute file 851 MB. [README](https://data.open-power-system-data.org/household_data/2020-04-15/README.md) | Residential import/export/PV channels support gross-load reconstruction where complete → `demandKwh`. HP electricity supports heating-type/profile evidence, not thermal capacity. Documented EV channel belongs to an industrial site. Check cumulative processing and interpolation flags. |
| **BDEW SLP 2025** | **2025 update confirmed:** H25/G25/L25/P25/S25. Free XLSX/guide; redistribution licence U. Profiles normalized to one million kWh/year. [Downloads](https://www.bdew.de/energie/standardlastprofile-strom/) | H25 → fallback shape scaled to supplied `demandKwh`, following dynamisation. P25/S25 reflect PV/storage-influenced grid withdrawals; do not apply PV/storage again as though they were appliance demand. No household sizing labels. [Guide](https://www.bdew.de/media/documents/2025-03-17_AWH_Aktualisierte_SLP_Strom_2025_Ver%C3%B6ffentlichung.pdf) |
| **Ireland CER trial** | Approved noncommercial research/teaching request; geographical/access conditions. 2009–2010; over 5,000 residential participants plus businesses; meter TXT ZIPs and XLS survey/allocation files. [Landing](https://doi.org/10.7929/ISSDA/BX59EU), [manifest](https://www.ucd.ie/issda/t4media/cer-manifest.pdf) | Meter ID + half-hour kWh → `demandKwh` after residential/complete-year filtering. Heating survey mapping needs dictionary verification. Capacities, EV km and wallbox outputs unknown. Separate tariff-treatment/control profiles. |

### Top-five rankings

Researcher judgments, not measured performance rankings.

| Rank | Installation-size plausibility | Simulation profiles |
|---|---|---|
| 1 | MaStR: German PV/storage distributions | WPuQ: German household/HP electricity |
| 2 | LBNL: explicit PV and battery sizes | OPSD Household: accessible German energy balances |
| 3 | Fluvius: installation-level storage kWh | IDEAL: larger measured household/context sample |
| 4 | SFOE: individual PV capacities | ResStock: diverse synthetic heat/end-use scenarios |
| 5 | MCS public aggregates; raw access conditional | HTW: useful load diversity if licence fits |

The ranking follows the fields, access restrictions and transfer limitations documented above.

### Verified download snippet

URLs were returned by the WPuQ Zenodo record API. This downloads public data; the hourly file was not downloaded during research.

```python
from pathlib import Path
import requests

out = Path("public-wpuq")
out.mkdir(exist_ok=True)

files = {
    "datapackage.json":
        "https://zenodo.org/api/records/5642902/files/datapackage.json/content",
    "2019_data_60min.hdf5":
        "https://zenodo.org/api/records/5642902/files/2019_data_60min.hdf5/content",
}
for name, url in files.items():
    with requests.get(url, stream=True, timeout=(20, 120)) as response:
        response.raise_for_status()
        with (out / name).open("wb") as target:
            for chunk in response.iter_content(1024 * 1024):
                target.write(chunk)
```

## Implications for our product

- Separate installation-distribution checks from simulation validation.
- Start with a pinned MaStR subset and one WPuQ hourly year.
- Preserve absent fields as unknown.
- Record DC/AC, rated/usable and electrical/thermal semantics explicitly.
- Keep observed output capacity out of corresponding prediction inputs.
- Label resistance-heater-heavy WPuQ cases as stress scenarios.
- Resolve HTW commercial-use rights before embedding profiles.
- Treat BDEW/When2Heat as declared fallback models.
- Defer restricted sources until access and permitted use are clear.
- Attach source, release, licence, units and transformations to fixtures.

## Open questions / uncertainty

- LBNL reuse licence, BDEW redistribution rights and full Fluvius terms remain U.
- MaStR storage units, Swiss peak/DC convention, IDEAL channel units and release-specific ResStock names need adapter verification.
- No verified source provides `evKm` paired with the complete installation bundle.
- Public download availability and record counts can change.
- LBNL’s linked Google Drive file could not be fetched by the browser; no replacement URL is invented.

## Sources (numbered list: title — publisher — date — URL)

All accessed **2026-11-07**.

1. Bulk export / snapshot / dictionary — MaStR, Open Energy Family — snapshot 2025-02-09 — [Export](https://www.marktstammdatenregister.de/MaStR/Datendownload), [snapshot](https://zenodo.org/records/14843222), [dictionary](https://zenodo.org/records/14843222/files/bnetza_open_mastr_datapackage.json?download=1).
2. Distributed Solar and Storage / public guide — Berkeley Lab — August 2026 — [Landing](https://emp.lbl.gov/publications/us-distributed-solar-and-storage-0), [guide](https://eta-publications.lbl.gov/sites/default/files/2026-08/lbnl_publicdatafile_userguide_8.07.26.pdf).
3. MID and access terms — MCS — undated — [MID](https://mcsfoundation.org.uk/projects/mcs-installations-database-mid/), [terms](https://certificate.microgenerationcertification.org/Home/Terms/).
4. MCS data descriptions — Nesta — undated — [Repository](https://github.com/nestauk/asf_core_data).
5. Domestic battery statistics — DESNZ — 2026-05-28 — [URL](https://www.gov.uk/government/statistics/mcs-certified-domestic-battery-installation-statistics).
6. Postcode data / copyright — CER Australia — September 2026 snapshot — [Data](https://cer.gov.au/markets/reports-and-data/small-scale-installation-postcode-data), [terms](https://cer.gov.au/about-us/our-policies/copyright).
7. PV statistics / microdata / copyright — CBS — June 2026 update — [Statistics](https://www.cbs.nl/nl-nl/cijfers/detail/85005NED?dl=B0C79), [microdata](https://www.cbs.nl/nl-nl/onze-diensten/maatwerk-en-microdata/microdata-zelf-onderzoek-doen/microdatabestanden/zonnestroominstallaties-kenmerken-en-elektriciteitsproductie-van-zonnestroominstallaties), [terms](https://www.cbs.nl/en-gb/about-us/website/copyright).
8. Installed capacity — Stedin — December 2025 snapshot — [URL](https://www.stedin.net/zakelijk/open-data/opgesteld-vermogen).
9. Storage schema / licence — Fluvius — November 2026 — [Schema](https://opendata.fluvius.be/api/explore/v2.1/catalog/datasets/1_22-energieopslagsystemen-gekoppeld-op-distributienet), [terms](https://opendata.fluvius.be/p/licentieopendatafluvius/).
10. Open-data inventory — Vlaamse Nutsregulator — undated — [URL](https://www.vlaamsenutsregulator.be/sites/default/files/uploads/lijst_open_data_fluvius.pdf).
11. Production plants / model — SFOE — September 2026 metadata — [Landing](https://opendata.swiss/en/dataset/elektrizitatsproduktionsanlagen), [model](https://pubdb.bfe.admin.ch/de/publication/download/10449).
12. Marketplace reports — EnergySage — September 2026 edition — [URL](https://www.energysage.com/data/).
13. Residential profiles — HTW Berlin — 2015 — [Landing](https://solar.htw-berlin.de/elektrische-lastprofile-fuer-wohngebaeude/), [documentation](https://solar.htw-berlin.de/wp-content/uploads/HTW-Repraesentative-elektrische-Lastprofile-fuer-Wohngebaeude.pdf).
14. WPuQ paper / data — Schlemminger et al., Scientific Data / Zenodo — 2022 / 2021 — [Paper](https://www.nature.com/articles/s41597-022-01156-1), [data](https://zenodo.org/api/records/5642902).
15. When2Heat — OPSD — 2023-07-27 — [README](https://data.open-power-system-data.org/when2heat/2023-07-27/README.md).
16. IDEAL — University of Edinburgh — 2021 — [URL](https://datashare.ed.ac.uk/items/15e82917-56ed-4282-99ef-7f211bf87f9d/full).
17. Dataport access, licence, dictionary — Pecan Street — undated / 2019 dictionary — [Access](https://www.pecanstreet.org/access/), [terms](https://www.pecanstreet.org/dataport/licenses/), [dictionary](https://www.pecanstreet.org/wp-content/uploads/2019/04/Dataport-metadata-dictionary.pdf).
18. EULP / ResStock — NREL/OEDI/AWS — 2021 onward — [OEDI](https://data.openei.org/submissions/4520), [registry](https://registry.opendata.aws/nrel-pds-building-stock/).
19. Household Data — OPSD — 2020-04-15 — [README](https://data.open-power-system-data.org/household_data/2020-04-15/README.md).
20. Standardlastprofile Strom — BDEW — 2025-03-17 — [Downloads](https://www.bdew.de/energie/standardlastprofile-strom/), [guide](https://www.bdew.de/media/documents/2025-03-17_AWH_Aktualisierte_SLP_Strom_2025_Ver%C3%B6ffentlichung.pdf).
21. Customer Behaviour Trial — CER/ISSDA — 2009–2010; manifest 2012 — [Landing](https://doi.org/10.7929/ISSDA/BX59EU), [manifest](https://www.ucd.ie/issda/t4media/cer-manifest.pdf).
