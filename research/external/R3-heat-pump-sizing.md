## Summary (≤150 words)

As of **2026-11-07**, minimal household data supports a **screening estimate**, followed by installer verification. Use fuel consumption, an explicit seasonal efficiency and consistent full-load hours. Select equipment using capacity at the required outdoor/flow temperatures, not its model number. [BWP guide](https://www.waermepumpe.de/fileadmin/user_upload/waermepumpe/07_Publikationen/BWP_LF_WPDimensionierung.pdf)

Fraunhofer observed substantial consumption-relative oversizing but did not isolate a universal causal efficiency penalty. KfW changed subsidy conditions on **2026-07-21**, so historical defaults are obsolete. [Fraunhofer](https://www.ise.fraunhofer.de/content/dam/ise/de/documents/projekte/WP-QS_Schlussbericht.pdf), [KfW](https://www.kfw.de/inlandsfoerderung/Bundesf%C3%B6rderung-f%C3%BCr-effiziente-Geb%C3%A4ude/Anpassungen-2026/)

The product ladders below distinguish commercial size classes from standardized output. Universal boiler-efficiency coefficients, an IWU W/m² table and a building-age-only full-load-hours table were not verified.

## Findings

### A reproducible screening method

1. **Normalize consumption.** Record billing period, DHW inclusion, other heating sources, renovations and unusual underheating. Oil deliveries require correction for tank-stock changes. These are proposed intake checks.

2. **Convert expenditure only with the actual tariff:**

   \[
   E_\mathrm{fuel}=(C_\mathrm{annual}-C_\mathrm{fixed})/p_\mathrm{fuel}
   \]

   Annual euros alone cannot establish consumption.

3. **Convert oil consistently.** BAFA lists **9.94 kWh/litre lower heating value** and **10.6 kWh/litre gross calorific value**. The efficiency denominator must match. Billed gas kWh must retain its billing basis. [BAFA](https://www.bafa.de/SharedDocs/Downloads/DE/Energie/ea_ermittlung_gesamtenergieverbrauch.pdf?__blob=publicationFile)

   \[
   Q_\mathrm{useful,total}=E_\mathrm{fuel}\eta_\mathrm{seasonal}
   \]

4. **Expose boiler efficiency.** BWP’s calculator accepts utilization directly or derives it from generator type/age; its internal coefficients were not established here. [BWP API](https://api.waermepumpe.de/documentation/heatingLoad)

   | Boiler | Prototype scenario only | Evidence status |
   |---|---:|---|
   | Old standard boiler | 0.75 | **UNVERIFIED population default** |
   | Low-temperature boiler | 0.85 | **UNVERIFIED population default** |
   | Condensing boiler | 0.90 | **UNVERIFIED population default** |
   | Unknown | Show scenarios | No silent point default |

   These are editable engineering assumptions, not DIN coefficients.

5. **Separate DHW accounting:**

   \[
   Q_\mathrm{space}=Q_\mathrm{useful,total}-Q_\mathrm{DHW}-Q_\mathrm{other}
   \]

   Prefer summer consumption or measured DHW. BWP documents separate methods, including a water-use default of **30 litres/person/day**; this does not justify a universal annual percentage. [BWP API](https://api.waermepumpe.de/documentation/heatingLoad)

6. **Compute a clearly labelled preliminary equivalent.** DIN Media gives **2,100 h/year** as a first approximation for SFH heat pumps supplying **heating and DHW**:

   \[
   P_\mathrm{screen,total}=Q_\mathrm{useful,total}/2100
   \]

   Do not first subtract DHW and then apply that combined-demand convention. Space-only methods need consistent hours, climate and heating-limit assumptions. [DIN Media](https://www.dinmedia.de/de/themenseiten/nachhaltiges-bauen/heizen/waermepumpen), [BWP API](https://api.waermepumpe.de/documentation/heatingLoad)

7. **Resolve climate and emitters.** Use postcode-specific design outdoor temperature and assess required flow temperature. DIN EN 12831/DIN TS 12831 calculations and room-level emitter checks remain separate from this shortcut. [BWP guide](https://www.waermepumpe.de/fileadmin/user_upload/waermepumpe/07_Publikationen/BWP_LF_WPDimensionierung.pdf), [climate map](https://www.waermepumpe.de/presse/news/details/bwp-klimakarte-nach-postleitzahlen-fuer-normaussen-und-jahresmitteltemperaturen-ab-sofort-online/)

8. **Select from capacity curves.** A proposed simplified load line is:

   \[
   P_\mathrm{load}(T)=P_\mathrm{design}
   (T_\mathrm{balance}-T)/(T_\mathrm{balance}-T_\mathrm{design})
   \]

   Clamp heating above the balance temperature. The bivalence point intersects this line with available HP output. BWP gives **−7 to −2°C** as contextual industry guidance, not a mandatory universal setting. Model resistance heating separately:

   \[
   P_\mathrm{rod}=\max(0,P_\mathrm{load}-P_\mathrm{HP,available})
   \]

   [BWP bivalence guidance](https://www.waermepumpe.de/verbraucher/darum-waermepumpe/fragen-sie-die-experten/antwort-der-experten/sollte-ich-besser-eine-waermepumpe-mit-groesserer-heizleistung-nehmen-um-reserven-bei-tiefen-aussentemperaturen-zu-haben/)

### Build-year fallback

IWU/TABULA provides archetypes and annual energy-balance methods. **Annual kWh/m² is not W/m² design load.** A universal IWU heat-load table was not verified. [IWU](https://energieprofil.iwu.de/)

The following is instead **Bosch’s approximate screening table**, unsuitable as a final purchase decision. [Bosch table](https://www.bosch-homecomfort.com/de/de/wohngebaeude/wissen/heizungsratgeber/heizleistung-berechnen//)

| Year | 100 m² | 150 m² | 200 m² |
|---|---:|---:|---:|
| Through 1977 | 163 W/m² | 161 | 160 |
| 1978–1983 | 115 | 114 | 113 |
| 1984–1994 | 99 | 98 | 97 |
| 1995–2001 | 67 | 66 | 65 |
| 2002–2008 | 45 | 44 | 44 |
| From 2009 | 38 | 37 | 37 |

Use \(P=Aq/1000\), retaining the age/condition assumption. Renovation can invalidate it. A numerical full-load-hours table by building standard alone remains **UNVERIFIED**.

### Oversizing, temperature and tanks

- Fraunhofer’s 2025 report found average evaluated air-source output at **A−7/W35 approximately 50% above** consumption-derived load. It did **not** establish a universal causal relationship between oversizing, cycling and efficiency. [Report](https://www.ise.fraunhofer.de/content/dam/ise/de/documents/projekte/WP-QS_Schlussbericht.pdf)
- Its project results report 49 air-source units with 2024 JAZ **2.6–4.9**, mean **3.4**. These are field observations, not promised performance. [Results](https://www.ise.fraunhofer.de/de/forschungsprojekte/wp-qs-im-bestand.html)
- Aira’s declared 8 kW model SCOP is **4.7 at W35 versus 3.5 at W55**. Holding heat demand constant implies approximately 34% more electricity at the latter rating. This is arithmetic from one vendor’s test figures, not a universal field penalty. [Specifications](https://www.airahome.com/de-de/waermepumpen/ausseneinheiten)
- Vaillant’s DHW orientation is **120–150 l for 1–2 people**, **170–200 l for 3–4**, **210–300 l for 5+**. Confirm recovery and draw-off requirements. [Guidance](https://www.vaillant.de/ratgeber/technologie-verstehen/waermepumpe/warmwasserspeicher-waermepumpe/)
- **200 l buffer + 300 l DHW is not a universal rule.** Bosch documents configuration-specific minimum system water volumes of 14 l for smaller Compress 5800i models and 35 l for larger models; system water volume is not separate buffer volume. [Brochure](https://www.bosch-homecomfort.com/fr/media/country_pool/residential/service/brochures/pac/032025-bosch_brochure-compress5800aws-210x297.pdf)

### Product ladders

These are documented families, **not a verified German market-share ranking**. Phase refers to the specified outdoor unit; indoor units and resistance heaters require separate fields.

| Brand/model | Documented size classes or outputs | Supply and limitations |
|---|---|---|
| **Vaillant aroTHERM plus /8.1** | Commercial classes 3/5/7/10/12 kW | 3/5/7: 230 V; 10/12: 400 V. [Manufacturer](https://www.vaillant.de/produkte/arothermplus/) |
| **Viessmann Vitocal 250-A** | Classes 04/06/08/10/13/16/19. Types 10/13/16/19 publish A7/W35 nominal 7.3/8.1/8.5/9.0 kW. | Type 10: 230/400 V alternatives; 13/16/19: 400 V. Smaller SKU mapping U. [Modernization](https://www.viessmann.de/de/produkte/waermepumpe/vitocal-250-a.html), [small models](https://www.viessmann.de/de/produkte/waermepumpe/vitocal-250-a-neubau.html) |
| **Daikin Altherma 3** | 3 R: 4/6/8; H MT: 8/10/12; H HT: 14/16/18 classes | Package/heater supply varies; complete German phase map U. [German catalogue](https://www.daikin.de/content/dam/Internet-DAG/Broschueren/2023/DAIKIN%20Altherma%20W%C3%A4rmepumpen%20Prospekt%2004_2023%20430007.pdf), [2026 catalogue](https://www.daikin.at/content/dam/DACE-AT/document-library/catalogues/heat/Daikin_Katalog_Waermepumpen_2026.pdf) |
| **Bosch Compress 5800i AW** | Classes 4/5/7/10/12; maximum A−7/W35: 3.92/5.42/6.71/9.57/11.56 kW | 4/5/7: 230 V; 10/12: 400 V, from Swedish technical table. Verify German SKU. [Technical table](https://www.bosch-homecomfort.se/produkter/luftvattenvarmepumpar/compress-5800i-aw/teknisk-fakta/) |
| **Stiebel WPL-A Plus** | Model classes 05.2/07.2/10.2/13.2; not exact nominal kW | 05.2/07.2: 230 V; 10.2: 230/400 V alternatives; 13.2: 400 V. [Manual](https://assets.stiebel-eltron.com/celum/Docs/originalFile/DOC-00126219.pdf) |
| **Panasonic Aquarea L** | 5/7/9 kW WH-WDG…LE5 | One-phase family; heater/package supply separate. [Manufacturer](https://www.aircon.panasonic.eu/DE_de/product/hydraulic-split-l-generation-1-phase-r290-1/) |
| **WOLF CHA** | CHA-07, CHA-10, CHA-16/20; last designation is one model family | Listed 400 V; numerals are not a common rating condition. [Electrical guide](https://static1.wolfeu.website.svc.wolf.eu/public/assets/editors/de-de/professionals/downloads/onepager-elektro-unterverteilung-02-23.pdf) |
| **Aira** | Maximum A−7/W35: 6/8/12 kW; maximum A7/W35: 9.5/12/16 kW | 6/8: 230 V; 12: 400 V. [Manufacturer](https://www.airahome.com/de-de/waermepumpen/ausseneinheiten) |
| **Samsung EHS Mono R290** | 5/8/12/16 commercial classes | UK page: 5 one-phase; 8/12 one-/three-phase options. Complete German map U. [Manufacturer](https://samsung-climatesolutions.com/gb/b2c/products/ehs/mono/r290.html) |
| **LG THERMA V R290** | Announced 7/9, supplementing 12/14/16 classes | European 2024 brochure lists 12/14/16 one-phase, 9/12/14/16 three-phase. Current German 7/9 mapping U. [Announcement](https://www.lgcorp.com/media/release/27980), [brochure](https://www.lg.com/content/dam/channel/wcms/pl/business/download/airsolution/LG_2024_Therma-V-R290-Monobloc_20240321_221354458_.pdf) |

### §14a EnWG and KfW 458

§14a concerns qualifying **electrical grid demand**, not thermal HP kW. Module 1 provides a local annual reduction; Module 2 reduces the network-charge work component by **60%**, with separate metering; Module 3 offers time-variable network charges combined with Module 1. These are not discounts on the entire electricity bill. [BNetzA](https://www.bundesnetzagentur.de/993240), [BWP 2026 guide](https://www.waermepumpe.de/fileadmin/user_upload/Praxisratgeber__14a_2026_WEB.pdf)

KfW’s current published conditions changed **21 July 2026**:

| Item | Published condition |
|---|---|
| Basic grant | 30% |
| First-dwelling eligible-cost cap | €28,000 |
| Climate-speed bonus | 16%, eligibility-dependent |
| Efficiency bonus | Removed |
| Income bonus | 40% up to €30k taxable income; 30% up to €40k; 10% up to €50k |
| Family adjustment | Thresholds increase once by €10k with an eligible minor child |
| Overall ceiling | Normally 70%; 80% for qualifying self-occupiers within the lowest adjusted income threshold |

The 80% threshold is normally €30k, or €40k with the applicable family adjustment. Do not infer eligibility from fuel type alone. [KfW changes](https://www.kfw.de/inlandsfoerderung/Bundesf%C3%B6rderung-f%C3%BCr-effiziente-Geb%C3%A4ude/Anpassungen-2026/), [programme 458](https://www.kfw.de/inlandsfoerderung/Privatpersonen/Bestehende-Immobilie/F%C3%B6rderprodukte/Heizungsf%C3%B6rderung-f%C3%BCr-Privatpersonen-Wohngeb%C3%A4ude-(458)/)

### Five synthetic worked examples

Examples 1–3 include heating and DHW and use the combined 2,100 h convention. Efficiencies/tariffs are **explicit example assumptions**. No result establishes final equipment size.

| Input | Assumptions and calculation | Screening result |
|---|---|---:|
| **18,000 kWh gas** | Assumed seasonal efficiency 0.90 on billed-energy basis: 18,000×0.90/2,100 | **7.71 kW** |
| **2,500 l oil** | Hi basis, assumed efficiency 0.85: 2,500×9.94×0.85/2,100 | **10.06 kW** |
| **€1,800/year gas** | Assumed fixed €180 and actual tariff €0.12/kWh; efficiency 0.90: (1,800−180)/0.12×0.90/2,100 | **5.79 kW** |
| **140 m², 1975** | Bosch original-condition area shortcut; interpolate 162 W/m² at 125 m² and 161 at 150 →161.4 | **22.60 kW**, area screen only |
| **200 m², 2005** | Bosch age/area factor 44 W/m²: 200×44/1,000 | **8.80 kW**, excluding separate DHW assessment |

For examples 1–3, analyst-selected 1,800–2,400 h sensitivity gives respectively **6.75–9.00**, **8.80–11.73**, and **5.06–6.75 kW**. These are scenario bounds, not confidence intervals. Methods: [BAFA](https://www.bafa.de/SharedDocs/Downloads/DE/Energie/ea_ermittlung_gesamtenergieverbrauch.pdf?__blob=publicationFile), [DIN Media](https://www.dinmedia.de/de/themenseiten/nachhaltiges-bauen/heizen/waermepumpen), [Bosch](https://www.bosch-homecomfort.com/de/de/wohngebaeude/wissen/heizungsratgeber/heizleistung-berechnen//).

## Implications for our product

- Keep `screeningEquivalentKw` separate from verified design heat load.
- Expose efficiency, heating-value basis and DHW convention.
- Obtain postcode, renovation and flow-temperature information before stronger recommendations.
- Store capacity curves and exact supply variants.
- Leave tanks provisional until hydraulic requirements are known.
- Calculate §14a from electrical requirements.
- Version subsidy rules by application date.
- Let deterministic calculations size; let the LLM explain.

## Open questions / uncertainty

- Universal boiler coefficients, age-only full-load hours and IWU W/m² defaults remain U.
- Several complete German phase/SKU maps remain U.
- Product-family inclusion does not establish market popularity.
- Paid standards were not inspected in full.
- Numerical screening ranges are not calibrated uncertainty.
- Future 2027 subsidy proposals are not current eligibility.

## Sources (numbered list: title — publisher — date — URL)

All accessed **2026-11-07**.

1. Dimensioning guide / calculator — BWP — current retrieved edition, date U — [Guide](https://www.waermepumpe.de/fileadmin/user_upload/waermepumpe/07_Publikationen/BWP_LF_WPDimensionierung.pdf), [API](https://api.waermepumpe.de/documentation/heatingLoad).
2. Energy conversion factors — BAFA — retrieved edition, date U — [URL](https://www.bafa.de/SharedDocs/Downloads/DE/Energie/ea_ermittlung_gesamtenergieverbrauch.pdf?__blob=publicationFile).
3. Heat-pump planning — DIN Media — undated — [URL](https://www.dinmedia.de/de/themenseiten/nachhaltiges-bauen/heizen/waermepumpen).
4. Climate map / bivalence — BWP — 2019 / undated — [Map](https://www.waermepumpe.de/presse/news/details/bwp-klimakarte-nach-postleitzahlen-fuer-normaussen-und-jahresmitteltemperaturen-ab-sofort-online/), [bivalence](https://www.waermepumpe.de/verbraucher/darum-waermepumpe/fragen-sie-die-experten/antwort-der-experten/sollte-ich-besser-eine-waermepumpe-mit-groesserer-heizleistung-nehmen-um-reserven-bei-tiefen-aussentemperaturen-zu-haben/).
5. Energieprofil — IWU — undated — [URL](https://energieprofil.iwu.de/).
6. Approximate heat-load table — Bosch — undated — [URL](https://www.bosch-homecomfort.com/de/de/wohngebaeude/wissen/heizungsratgeber/heizleistung-berechnen//).
7. WP-QS report/results — Fraunhofer ISE — 2025 — [Report](https://www.ise.fraunhofer.de/content/dam/ise/de/documents/projekte/WP-QS_Schlussbericht.pdf), [results](https://www.ise.fraunhofer.de/de/forschungsprojekte/wp-qs-im-bestand.html).
8. aroTHERM / DHW guidance — Vaillant — undated — [Product](https://www.vaillant.de/produkte/arothermplus/), [DHW](https://www.vaillant.de/ratgeber/technologie-verstehen/waermepumpe/warmwasserspeicher-waermepumpe/).
9. Vitocal 250-A — Viessmann — undated — [Modernization](https://www.viessmann.de/de/produkte/waermepumpe/vitocal-250-a.html), [small units](https://www.viessmann.de/de/produkte/waermepumpe/vitocal-250-a-neubau.html).
10. Altherma catalogues — Daikin — 2023/2026 — [Germany](https://www.daikin.de/content/dam/Internet-DAG/Broschueren/2023/DAIKIN%20Altherma%20W%C3%A4rmepumpen%20Prospekt%2004_2023%20430007.pdf), [Austria](https://www.daikin.at/content/dam/DACE-AT/document-library/catalogues/heat/Daikin_Katalog_Waermepumpen_2026.pdf).
11. Compress technical material — Bosch — undated / March 2025 — [Table](https://www.bosch-homecomfort.se/produkter/luftvattenvarmepumpar/compress-5800i-aw/teknisk-fakta/), [brochure](https://www.bosch-homecomfort.com/fr/media/country_pool/residential/service/brochures/pac/032025-bosch_brochure-compress5800aws-210x297.pdf).
12. WPL-A manual — Stiebel Eltron — date U — [URL](https://assets.stiebel-eltron.com/celum/Docs/originalFile/DOC-00126219.pdf).
13. Aquarea L — Panasonic — undated — [URL](https://www.aircon.panasonic.eu/DE_de/product/hydraulic-split-l-generation-1-phase-r290-1/).
14. CHA electrical guide — WOLF — February 2023 filename — [URL](https://static1.wolfeu.website.svc.wolf.eu/public/assets/editors/de-de/professionals/downloads/onepager-elektro-unterverteilung-02-23.pdf).
15. Outdoor specifications — Aira — undated — [URL](https://www.airahome.com/de-de/waermepumpen/ausseneinheiten).
16. EHS Mono R290 — Samsung UK — undated — [URL](https://samsung-climatesolutions.com/gb/b2c/products/ehs/mono/r290.html).
17. THERMA V announcement/brochure — LG — 2024 — [Announcement](https://www.lgcorp.com/media/release/27980), [brochure](https://www.lg.com/content/dam/channel/wcms/pl/business/download/airsolution/LG_2024_Therma-V-R290-Monobloc_20240321_221354458_.pdf).
18. §14a rules/guide — BNetzA/BWP — 2023/2026 — [Rules](https://www.bundesnetzagentur.de/993240), [guide](https://www.waermepumpe.de/fileadmin/user_upload/Praxisratgeber__14a_2026_WEB.pdf).
19. BEG changes / programme 458 — KfW — effective 2026-07-21 — [Changes](https://www.kfw.de/inlandsfoerderung/Bundesf%C3%B6rderung-f%C3%BCr-effiziente-Geb%C3%A4ude/Anpassungen-2026/), [458](https://www.kfw.de/inlandsfoerderung/Privatpersonen/Bestehende-Immobilie/F%C3%B6rderprodukte/Heizungsf%C3%B6rderung-f%C3%BCr-Privatpersonen-Wohngeb%C3%A4ude-(458)/).
