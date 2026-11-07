# How German residential PV / storage / heat-pump installers work: evidence and product implications

Date: 2026-11-07. Method: web search + page fetches (German and English). Evidence grading: **[I]** installer/trade voice or association data, **[G]** government/statutory/consumer-protection source, **[R]** consumer-advice portal (secondary, often lead-gen), **[V]** single-vendor claim (marketing, unverified), **[F]** forum anecdote.

## 0. Honest limits (read first)
- The search tool did NOT surface photovoltaikforum.com, Reddit, or YouTube content. Forum evidence is thin (one akkudoktor.net delay thread, one akkudoktor heat-pump sizing thread; a haustechnikdialog thread returned 403).
- **No independent German data found** for: hours per offer, offers per day/week, offer-to-sign conversion, share lost to price. Numbers on these are vendor claims or US/India vendor benchmarks, marked as such.
- Many "process" facts come from consumer-guide portals (photovoltaik.info, reduco.ai) that are lead-gen/vendor content: [R]/[V]. The installer's own voice is mostly inferred from trade-press interviews and association surveys.
- Recommended before the demo: 3-5 installer-planner interviews for time per offer, win rate, brand/margin selection rules.

---

## 1. End-to-end pipeline

| # | Step | Who (typical) | Typical time | Tools | Failure points | Evidence |
|---|------|---------------|--------------|-------|----------------|----------|
| 1 | Lead intake | Marketing / inside sales; portal leads (matched to up to 3 installers) | minutes | Lead portals, website configurators, CRM | Customer compares 2-3 offers; configurator number is only an "invitatio ad offerendum" | [R] photovoltaik.info (configurator, first-contact pages) |
| 2 | Qualification call | Sales / Energieberater | not quantified | CRM, phone | Lead forms capture building type, roof shape/covering/age (<30, 30-70, >70 y), ownership, timing, address; non-owners/WEG leads wasted | [R] photovoltaik.info |
| 3 | Data collection | Customer + sales | not quantified | Annual electricity bill, property plan, photos | No bill/plan; Zaehlerschrank unknown | [R] photovoltaik.info |
| 4 | Site visit or remote | Sales rep / technician | **1-2 h** visit (guide claim) | Compass, tape, camera, tablet; remote: aerial/LiDAR/Google Solar | Checks: roof covering+condition, rafters/load, skylights/dormers/chimney, shading, Zaehlerschrank vs VDE-AR-N 4100, fuses, cable routes, inverter location. VZ NRW calls a pre-offer visit "unerlaesslich"; aerial-only planning is called a warning sign | [R] photovoltaik.info vor-ort-termin-solarteur-checkliste; [G] VZ NRW via Solarserver; [R] solaranlage-tipps checklist |
| 5 | Design (roof, strings, inverter, battery, wallbox, HP heat load) | Planner / sales / technician | **Unknown for DE.** Vendor claims: manual quote 4 h (Surge glossary example); Reonic "preliminary planning, detailed simulation and quote within 30 minutes"; manual heat load "several hours" (Reonic press release) | Reonic, Solar Monkey, PV*SOL, SolarEdge Designer, Sunny Design, Excel | Rework when site data differs | [V] surgepv.com/de/glossar/solarangebot; [V] reonic.com product/360b (commercial page); [V] pv-magazine press release |
| 6 | Pricing / offer | Sales + back office | One unnamed Reonic customer: 3-5 variants in 10-15 min [V] | Offer tool/CRM; wholesaler prices | Missing line items (scaffolding, Zaehlerschrank, Netzanmeldung, MaStR) | [G] VZ NRW; [V] Reonic |
| 7 | Follow-up / negotiation | Sales | first contact to binding offer 1-2 weeks (guide) | CRM, phone | Comparison with 2-3 offers; online kits near wholesale price | [R] photovoltaik.info; [I] pv magazine 2024 |
| 8 | Signing | Customer | -- | E-signature (Reonic docs) | Signed variant is locked; changes need new variant + re-sign | [V] docs.reonic.com |
| 9 | Netzanmeldung / MaStR / TAB | Installer files grid request; MaStR within 1 month of commissioning | Grid review 8 weeks (EEG), 1 month for <=30 kW; online portal duty for <=30 kW since 1.1.2025 | Grid-operator portals, MaStR | Incomplete documents = "most common self-inflicted delay"; installer must be in Netzbetreiber directory; regional backlogs of months | [R] reduco.ai (cites EEG/NAV/MsbG); [R] photovoltaik.info timeline |
| 10 | Zaehlerschrank rebuild / meter change | Registered electrician + Messstellenbetreiber | cabinet hours-days; meter change 4-12 weeks after completion in practice | -- | Old cabinet = "classic Termin-Killer"; cost cited 1,500-3,500 EUR (reduco.ai headline, [V]) | [R] reduco.ai; [F] akkudoktor |
| 11 | Procurement | Installer purchasing -> wholesaler | Contract to install date 6-16 weeks (reduco) / 4-12 (photovoltaik.info); extreme 4 weeks-6 months | Wholesaler portals | Inverters and storage most constrained; regional dealers have limited stock | [R] photovoltaik.info timeline |
| 12 | Installation | Montage crew + electrician | 1-3 days (reduco), 2-5 days (photovoltaik.info) | -- | Scaffolding skipped to cut price; BG reports rise in serious roof accidents | [I] pv magazine 2024-08-01 |
| 13 | Commissioning + documentation | Electrician / installer | -- | Commissioning protocol, MaStR | Feed-in cannot start until grid approval even if install is done | [R] photovoltaik.info |

Overall contract-to-commissioning: "4 to 12 months" (photovoltaik.info, [R]); reduco.ai headline "3-6 months" [V].

---

## 2. How planners size systems

Caveat: nearly all rules come from consumer/advice sites, not verified installer interviews. They likely mirror installer practice but this is inference.

- **Battery vs PV:** about 1 kWh per kWp; economical 0.9-1.3; upper limit 1.5 (photovoltaik.info verhaeltnis-pv-anlage-speicher, [R]).
- **Battery vs consumption:** about 1 kWh per 1,000 kWh/yr; with heat pump 1.2-1.5; or (annual kWh/365) x 1.3-1.6 ([R] search summaries).
- **PV vs demand:** ~1,000 kWh/kWp; yield about 1.3x consumption (example 14-15 kWp for 11,100 kWh). 4,500 kWh -> 5-7 kWp; 7,000 kWh with EV -> 9-11 kWp ([R]).
- **"Dach voll machen":** not directly evidenced in sources found. Hypothesis from domain knowledge; verify in interviews.
- **Winter:** do not size the battery for winter; optimize the annual average ([R] photovoltaik.info).
- **Inverter oversizing:** DC/AC 1.1-1.3 common, datasheets often allow up to 1.5; Fraunhofer ISE: German mean DC ~10 % above AC ([R]/[V] reduco.ai via search summary).
- **Heat pump:** Heizlast (kW) = useful heat energy / full-load hours (1,800-2,000 h standard; 1,500-1,800 partly renovated; 1,800-2,200 unrenovated); boiler efficiency 0.70-0.80 old, 0.90-0.95 condensing; subtract DHW; only an estimate, DIN EN 12831 is the proper method ([R] BNS Praxisleitfaden, haustechnikdialog via search summary). A real thread: installer's building-based calc ~30 kW, offered 35 kW; owner's fuel-based estimate ~24.5 kW; mixed DHW/solar/wood/pool made fuel data unreliable ([F] akkudoktor wp-auslegung). A heat pump adds ~3,000-6,000 kWh/yr electricity ([R] snippet).
- **Packages / variants:** Eturnity co-founder (pv magazine 2020) argues for pre-built bundles of modules+inverter+battery+services ([V]). Reonic offers: several variants per offer under one signature link; optional components chosen at signature; "additional components" priced but not simulated; simulation covers PV only ([V] docs.reonic.com).
- **Manufacturer partnerships / margin:** NO evidence found on how installers choose brands or set margins. Only indirect: inverter/storage availability at wholesalers constrains plans ([R]); price war from overstock ([I] Claussen). Gap.
- **Quality gap:** HTW Berlin: only 12 of 21 systems reached SPI >90 %; badly configured systems can lose >600 EUR/yr (as cited by photovoltaik.info; HTW original not read). HTW Stromspeicher-Inspektion 2024: least efficient storage costs 270 EUR/yr more; datasheets often omit efficiency; check usable vs nominal capacity ([R] search summary).
- **Solarspitzengesetz:** systems without smart meter cap feed-in at 60 % of kWp; HTW simulation: loss 1.1 % (E-W) to 9.0 % (S) without storage; another source claims ~21 % loss of remuneration incl. negative-price stops (conflicting). ZVEH asks that the 60 % limit refer to the generator only, not storage ([I] solarserver 2025-10-21, energiezukunft.eu).

---

## 3. Daily life and pain points

**Market data:**
- E-Handwerk installed ~355,000 PV systems in 2025 vs 395,000 in 2024; rooftop 360k -> 325k; storage 260k -> 235k; share of firms installing PV 57.1 % -> 52.1 %; PV+storage only 6 % of E-Handwerk revenue; E-Handwerk involved in ~72 % of 450,000 rooftop systems. ZVEH blames inconsistent energy policy (incl. proposed end of small-system feed-in tariff) ([I] solarserver 2026-03-20).
- 2025: ~17.5 GW vs 17.7 GW in 2024 (BSW, via search summary [I]).
- 2024 (wholesaler VEH, pv magazine 2024-08-01 [I]): own sales ~40 % lower; installer order declines 20-50 %; "price dumping" is the main problem; components sold near wholesale price online; ~220,000 balcony systems registered in H1 2024.
- pv magazine 2024-07-22 [I]: installers report residential demand down 60 %, order intake down 45 % (one report); quote "Orders are not in short supply, but profitability is"; "Consolidation is in full swing".
- Europe: residential installs about -20 % y/y in 2024; >24,000 installers; 69 % of DACH installers offer HEMS (EUPD via pv magazine 2025-08-19 [I]/[V]).
- Heat pumps: SHK orders and utilization falling in 2025/26; skills shortage mainly on-site assembly/service (ZVSHK, Fraunhofer ISE survey, search summary [I]).

**Per-planner metrics:**
- Germany: no independent data.
- Vendor/US benchmarks: manual quote 4 h (Surge [V]); US close rates 3-5 % of leads, 15-25 % of qualified leads, 20-35 % proposal-to-sign; speed-to-proposal "most correlated" with close rate; proposal within 24 h of visit best (rework.com, surgepv, quickestimate [V], partly India/US, unsourced).
- Eturnity: up to 50 % consulting-time saving ([V], pv magazine 2020 comment).
- A claimed "8-12 h/week manual entry (SEIA)" could not be verified; do not use.

**Pain points evidenced:**
- Same data re-entered across several programs; admin effort high; low margins; skilled labor ~50 % of system cost (Eturnity author, pv magazine 2020 [V]/[I]).
- Regulatory churn: installers and grid operators interpret Solarspitzengesetz differently; possible customer-installer disputes ([I] ZVEH/energiezukunft).
- Grid operators: "largest bureaucratic bottleneck" (photovoltaik.info [R]); forum: 7 months (installer not accredited), >1 year at a large operator, 1-2 weeks at a municipal one ([F] akkudoktor).
- Installer insolvency feared by customers ([F]).
- Scaffolding skipped, accident rise ([I]); balcony PV eats small rooftop sales ([I]).
- Big players (1KOMMA5, Enpal, E.ON Solar) lead via bundles, financing, service (EUPD [I]/[V]). 1KOMMA5 field-sales ads mention "prequalified leads" ([V] snippet). Anonymous Enpal criticism of guideline-driven sales and churn ([F], unverified).

---

## 4. Missing information at offer time and defaults

- Online configurators use standardized data (average irradiation, typical roof pitches, common module sizes); result is a "qualified cost estimate"; binding only after visit ([R] photovoltaik.info configurator page).
- Typical post-visit additions: meter-cabinet replacement, roof renovation, detailed shading adjustments, building rules, access ([R]). No percentages published.
- Consumption: from last electricity bill; time-of-day profile usually not available, though storage need depends on it ([R]).
- Heat load: estimated from old fuel use / area when no calculation exists; offers without a heat-load calc are a warning sign ([R]).
- Roof: remote LiDAR/aerial fine for qualification and early proposals; weak on obstructions, overhanging neighbours, outdated Street View ([R] Solar Power World; [V] surge/arka360). NREL-cited test (81 locations, +/-1.95 solar-access points) concerns Sighten, not Google API, second-hand ([V]).
- Zaehlerschrank: unknown until visit; added as separate line ([R]).
- Not found: the actual default assumptions planners apply (e.g. household load profile, EV km, electricity-price path).

---

## 5. Tools and complaints

- **Reonic** (Augsburg; "over 1,300 customers" in its 2025-07 press release, "over 3,000" elsewhere, inconsistent [V]): lead -> offer -> install in one project; roof planning with auto module placement, strings, inverter sizing, circuit diagrams, BOM; 20-year yield projection; variants; e-signature; LiDAR heat-load scan (needs iPhone with LiDAR), DIN EN 12831, hydraulic balancing, KfW documentation; free tier 4 projects/month ([V]).
- **autarc Pro** (LiDAR building scan, 15 min, App Store listing [V]); **WaermePilot** (DIN EN 12831 + LiDAR [V]); Fraunhofer **WESPE** (snippet only).
- **Eturnity, Solar Monkey, PV*SOL, SolarEdge Designer, Sunny Design, Aurora, OpenSolar:** no independent user complaints reached. Only generic "double entry / revisions don't propagate / tools don't know each other" claims from Payaca/Sunbase-type vendor blogs ([V], UK/US).
- **Excel/CRM:** assumed, not evidenced.
- Reonic limitation (their docs): simulation covers PV only; heat pump, wallbox, additional components are priced but not simulated -> gap for a combined design AI.
- Job ads (hellosun, PEC) show split roles: electrical planning (Stromlaufplaene) vs detailed planning to release only buildable projects ([R] snippets); WBS "Projektplaner Solarenergie- und Waermepumpensysteme" course covers planning, legal framework, subsidies, profitability ([R]).

---

## 6. Homeowner side

- **Questions/fears evidenced:** payback and yield assumptions (VZ NRW: vendor return calcs often use unrealistic assumptions); hidden costs (scaffolding, cabinet, registration); usable vs nominal battery capacity; warranty (calendar life for batteries); installer insolvency and time to commissioning; grid-operator delays; lump-sum price without breakdown plus time pressure as red flags ([G] VZ NRW via solarserver/reduco).
- **Consumer shopping rules:** 2-3 offers; offer lists kWp, inverter, usable storage and its cost, all labor; compute price per kWp excluding storage; on-site visit before offer ([G] VZ NRW).
- **Why deals are lost (indirect):** price competition from online kits and low-price installers; balcony PV substitution; policy uncertainty; trust. US vendor data stress speed to proposal ([V], unverified for DE).
- **What convinces (mixed):** itemized offer; transparent yield basis (Fraunhofer: install errors up to 10 % yield loss); references; one fixed contact; clear process/timeline ([R] photovoltaik.info). EUPD lists financing, reviews, after-sales, sector coupling for market leaders.
- Gap: no independent German survey of consultation questions.

---

## 7. Implications: 14 product requirements

1. **Output an installer-grade, itemized offer**, not just a sizing: kWp, inverter model, usable battery kWh, wallbox, HP, scaffolding, Zaehlerschrank, Netzanmeldung, MaStR, labor. [G VZ NRW; R configurator page]
2. **Make the Zaehlerschrank an explicit input and cost line** (age, free slots, APZ, rebuild needed) with flagged default and price range. [R reduco; R configurator; F akkudoktor]
3. **HP sizing via heat-load path**: DIN EN 12831 when data exists, otherwise fuel-consumption method (DHW removed, boiler efficiency, full-load hours) with stated method and uncertainty band; avoid oversizing. [R BNS guide; F 30 vs 24.5 kW; V Reonic scan]
4. **Co-optimize PV + battery + HP + wallbox in one simulation** (Reonic's own docs: simulation covers PV only; HP adds 3-6 MWh/yr). [V docs.reonic.com; R]
5. **Encode rules of thumb as transparent, editable defaults** (1 kWh/kWp; 1.2-1.5 kWh per MWh with HP; DC/AC 1.1-1.3; ~1,000 kWh/kWp) and show the reasoning. [R photovoltaik.info; R reduco]
6. **Auto-generate Good/Better/Best variants** (PV only / +battery / +battery+HP+wallbox, battery size ladder) with delta-price and delta-savings. [V Reonic variants; R]
7. **Confidence-tagged defaults plus "confirm on site" list** per offer (roof condition, shading, cabinet, cable route, heat load). [R configurator; V remote-design sources]
8. **Remote-first design (satellite/LiDAR) with shading/obstruction risk flag** and a 1-2 h field-verification checklist. [R Solar Power World; V surge/arka; R site-visit checklist]
9. **Model Solarspitzengesetz explicitly** (60 % cap without smart meter, negative-price no-remuneration, effect on orientation/storage), showing assumptions because published loss estimates conflict (1-9 % vs ~21 %). [I ZVEH; R]
10. **Respect real constraints**: brand/partner catalog, wholesaler availability, bundles. Evidence thin; validate via interviews. [R photovoltaik.info timeline; V Eturnity]
11. **Price/margin controls first-class** (margin, discount guardrail, price per kWp excl. storage, competitor sanity view) given price war and 2-3 offer comparison. [I Claussen 2024; G VZ NRW]
12. **Conservative, visible payback/yield assumptions** (electricity price path, degradation, usable capacity) in plain language; trust differentiator. [G VZ NRW; R photovoltaik.info]
13. **Netzanmeldung-ready data package** (circuit diagram, BOM, grid-operator fields, MaStR data) plus realistic timeline (grid review up to 8 weeks, meter change 4-12 weeks, install 1-3 days). [R reduco; F akkudoktor]
14. **Minimal-input first proposal** (address + bill + a few toggles), progressive refinement, no double entry across CRM/design/offer. [V rework/surge speed claims; V Payaca; V Reonic 30-min claim]

---

## Sources

Fetched and read:
- https://www.photovoltaik.info/zeitplaene-wartezeiten-pv-anbieter/
- https://www.photovoltaik.info/erstgespraech-pv-installateur-wichtige-fragen/
- https://www.photovoltaik.info/verhaeltnis-pv-anlage-speicher/
- https://www.photovoltaik.info/vor-ort-termin-solarteur-checkliste/
- https://www.photovoltaik.info/photovoltaik-online-konfigurator-verbindlichkeit/
- https://reduco.ai/blog/solar/photovoltaik-lieferzeit-installation-2026
- https://akkudoktor.net/t/welche-verzoegerungen-koennen-kommen-bis-die-dach-pv-anlage-laeuft/29107
- https://akkudoktor.net/t/wp-auslegung-abgetrennt/39107
- https://www.pv-magazine.de/2020/03/20/steigerung-der-wettbewerbsfaehigkeit-in-der-photovoltaik-branche-es-ist-zeit-fuer-effiziente-und-kundenfreundliche-beratungsprozesse/
- http://www.pv-magazine.com/2024/07/22/germanys-solar-market-faces-price-wars-consolidation/
- https://www.pv-magazine.de/2024/08/01/die-balkonanlagen-gehen-eindeutig-zu-lasten-der-klassischen-privaten-dachanlagen/
- https://www.solarserver.de/2026/03/20/zveh-fruehjahrkonjunkturumfrage-e-handwerk-zieht-sich-aus-photovoltaik-zurueck/
- https://www.solarserver.de/2025/01/16/verbraucherzentrale-nrw-mehr-durchblick-bei-pv-angeboten/
- https://docs.reonic.com/docs/en/offers-overview-overview-offer-characteristics
- https://reonic.com/en-gb/product/360b
- https://www.pv-magazine.de/unternehmensmeldungen/reonic-revolutioniert-waermepumpensektor-mit-kostenloser-heizlastberechnung-nach-din-en-12831/
- http://www.pv-magazine.com/2025/08/19/residential-solar-shifts-from-surge-to-strategy-eupd-report-spotlights-market-leaders/

Seen only in search results (summaries; weaker):
- https://www.surgepv.com/de/glossar/solarangebot
- https://resources.rework.com/libraries/solar-home-energy-growth/in-home-sales-funnel
- https://surge-website.pages.dev/blog/solar-proposal-win-rate-benchmarks
- https://quickestimate.co/blog/solar-proposal-conversion-rate
- https://www.surgepv.com/blog/solar-close-rate
- https://www.solaranlage-tipps.de/blog/warmepumpe-mit-pv-anlage-richtig-dimensionieren-2026-kwp-speichergrosse-stromertrag-berechnen
- https://reduco.ai/blog/solar/wechselrichter-dimensionierung-ueberbelegung
- https://reduco.ai/blog/solar/photovoltaik-angebot-pruefen
- https://www.worms.de/neu-de-wAssets/docs/zukunft-gestalten/klima-umwelt/Energie/BuergerSolarBeratung/_BNS_Waermepumpe-Praxisleitfaden-im-Einfamilienhaus.pdf
- https://www.haustechnikdialog.de/SHKwissen/1411/Heizlasten-in-Altbauten
- https://www.haustechnikdialog.de/Forum/t/292804/Auslegung-Waermepumpe-Heizungsbauer-und-Eigene-Rechnung (403 on fetch)
- https://www.solarserver.de/2025/10/21/zveh-fordert-in-positionspapier-klaerung-zum-solarspitzengesetz
- https://www.energiezukunft.eu/erneuerbare-energien/solarenergie/handwerksbetriebe-und-netzbetreiber-in-der-praxis-uneins
- https://docs.reonic.com/docs/en/app-heat-load-scan
- https://apps.apple.com/de/app/autarc-pro/id6505113634
- https://www.solarserver.de/2026/01/06/bsw-solar-photovoltaik-ausbau-in-2025-stagniert/
- https://www.solarserver.de/2025/10/16/abschwung-im-photovoltaik-markt-2025/
- https://www.zvshk.de/fileadmin/zvshk.de/user_upload/Redaktion/Bilder_Presse/12_PM_SHK_Bilanz_2025.pdf
- https://solar.htw-berlin.de/wp-content/uploads/HTW-Stromspeicher-Inspektion-2024.pdf
- https://www.pv-magazine.de/wp-content/uploads/sites/4/2025/04/0020_Reonic_PVMagazine_final.pdf (fetch 404; mentioned in a search summary)
- https://www.solarpowerworldonline.com/2024/09/why-solar-shade-analysis-is-so-subjective-how-to-fix-it/
- https://www.nrel.gov/docs/fy18osti/71313.pdf
- https://www.wbstraining.de/kurse/weiterbildung/projektplaner-in-fuer-solarenergie-und-waermepumpensysteme.pdf
- https://pro-ec.de/wp-content/uploads/2023/09/PEC-Stellenangebot-Planer-fuer-Photovoltaikanlagen.pdf
- https://rejobs.org/de/erneuerbare-energien-jobs/120997-elektrikerin-technikerin-elektroingenieurin-fur-die-elektrische-planung-von-pv-anlagen-und-warmepumpen-hellosun-gesellschaft-fur-solarbau-mbh
- https://www.hausbau-forum.de/posts/694071/
- https://payaca.com/blog/why-solar-installers-replacing-generic-crms
- https://verbraucherzentrale.nrw/node/84212
