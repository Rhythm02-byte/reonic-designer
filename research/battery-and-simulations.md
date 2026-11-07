# Battery sizing and simulation design for a German residential PV + battery + heat pump + EV engine

Research date: 2026-11-07. Evidence tags: **[P]** = primary source text read (PDF/abstract page opened); **[S]** = secondary or search-snippet only (verify before citing); **[A]** = my inference/engineering judgement, not from a source.
Quotes are kept under 15 words. All URLs were returned by searches or opened in this session.

---

## 0. Executive summary

1. **"Smallest battery that gets most of the benefit" is, in effect, what the German literature recommends, but it is not one formal standard.** HTW's normalized sizing (Weniger 2013) says self-sufficiency saturates beyond about 1-1.5 kWh/MWh because large batteries are "not empty by the next morning" [P]. Economic optima are smaller still (0.5-1.1 kWh/MWh depending on battery price) [P]. Recommended engine rule: size to the knee of the marginal-value curve, cap by nightly (sunset-to-sunrise) load, and report max-autarky as an alternative, clearly labelled as uneconomic.
2. **EV:** smart surplus charging beats a bigger home battery for the car (HTW 2025: +25 pp solar share from surplus control vs +9 pp from a battery) [S, HTW PDF opened but figures come from the abstract text]. An EV does not justify a proportionally larger stationary battery. Bidirectional V2H can substitute for part of a stationary battery, but evidence is Australian and weak for Germany [S].
3. **Dynamic tariffs/arbitrage** add modest value for households; modest storage is enough and over-investing is warned against [S]. The Solarspitzengesetz (negative-price quarter-hours unpaid, 60% cap without smart meter) makes forecast-based charging a first-class battery function and shifts value from "store for evening" to "avoid zero-paid midday feed-in" [P for pv-magazine article, S for HTW claims].
4. **Chemistry/aging:** assume LFP, ~92-95% usable of nominal, 2-3 pp capacity loss per year in the field (RWTH Nature Energy 2024) [P for abstract], AC-AC roundtrip about 85-90% plus standby of ~13 W average (HTW 2024) [P].
5. **Heat pump:** it raises annual load (+3200 kWh, +80% in a 730-household sample) but mostly in winter when PV is scarce, so it lowers autarky (59% vs 73%) rather than raising it; it increases optimal PV but not the optimal battery proportionally [S/P mix, see section A5].
6. **Simulations:** hourly resolution is enough for sizing/ranking (Beck 2016: 60 min fine for sizing PV and storage capacity) [P], but self-consumption and autarky numbers shown to a user are biased high at hourly resolution and with smooth H0 profiles; use a bias correction or 15-min profiles built from HTW's 74 load profiles. Top upgrades by value-for-effort: (1) load-profile variety + resolution bias handling, (2) forecast-based charging + feed-in rules (negative-price hours, 60% cap), (3) battery degradation and standby in the 20-year model, (4) inverter clipping / E-W split, (5) Heizstab/DHW surplus.

---

## PART A: Battery sizing

### A1. State of the art for sizing; is "knee" the standard?

**Evidence**

- HTW Berlin (Weniger, Tjaden, Quaschning, IRES 2013 / Energy Procedia 2014) normalize PV (kWp/MWh) and usable battery (kWh/MWh) by annual demand so results are household-size independent [P: https://solar.htw-berlin.de/wp-content/uploads/WENIGER-2013-Sizing-and-Grid-Integration-of-Residential-PV-Battery-Systems.pdf].
  - With 1 kWp/MWh and no battery: self-consumption and autarky about 30%.
  - Adding 1 kWh/MWh: self-consumption 59%, autarky 56%.
  - Beyond 1.5 kWh/MWh "only leads to insignificant raises"; reason given: large batteries are only partly discharged at night and not empty next morning. The paper therefore says the average load between sunset and sunrise is the benchmark for demand-matched sizing. This directly supports your "battery should be empty in the morning" intuition.
  - Cycles: 1 kWp/MWh with 1 kWh/MWh gives about 270 cycles/yr; small PV with battery gives under 150 cycles/yr; highest cycle count occurs with small batteries.
  - Cost-optimal results depend on price scenario: at about 1500 EUR/kWh only up to 0.5 kWh/MWh pays; in their mid-term (1000 EUR/kWh) 1 kWp/MWh with 0.75 kWh/MWh is only 2 ct/kWh above the optimum; in their long-term scenario (600 EUR/kWh) the optimum is 0.8 kWp/MWh with 1.1 kWh/MWh, and the cost curve is flat around the optimum ("a broad range of system configurations will be profitable").
- HTW 2014 economics paper: battery size has a larger effect on mean electricity cost than PV size; at their reference prices only batteries below 0.6 kWh/MWh reached the retail price; interest rate is the dominant economic parameter, then PV price, retail price, feed-in tariff [P: https://solar.htw-berlin.de/wp-content/uploads/WENIGER-2014-Economics-of-Residential-PV-Battery-Systems-in-the-Self-Consumption-Age.pdf]. Assumptions there: 20-yr life, 5000 cycle life, 1.5% O&M.
- HTW Stromspeicher-Inspektion 2024 recommends: usable capacity "maximal 1,5 kWh pro kW PV-Leistung" (max 1.5 kWh per kWp) and uses cap of 8 kWh (5 kW PV, 5010 kWh/a demand) and 16 kWh (10 kW PV, 9363 kWh/a with heat pump and wallbox) in its reference cases [P: https://solar.htw-berlin.de/wp-content/uploads/HTW-Stromspeicher-Inspektion-2024.pdf]. It values grid feed-in at 8 ct and grid purchase at 40 ct.
- Field data (same Inspektion 2024, 100+ systems, Eigensonne/Kostal): PV alone cuts grid purchase by ~2000 kWh/a; a battery halves the remaining purchase to ~1500 kWh/a; mean autarky 70%; battery adds 18-38 pp autarky in 9 of 10 households; strongest effect in low-consumption households [P].
- Schopfer, Tiefenbeck, Staake (Applied Energy 223, 2018): with 4190 Swiss households, battery profitable for only 0.1% of households at current costs but 99.9% at the most optimistic costs; profitability varies strongly even at equal annual demand because of load-profile shape [P abstract: https://cris.fau.de/publications/227854435/ ; open full text https://fis.uni-bamberg.de/handle/uniba/44370]. Implication: the sizing criterion is heterogeneous across households; a single rule of thumb hides large variance.
- Other: Hesse et al. 2017, Energies 10(7):835, cost-optimal component sizing with linear optimization [S: https://econpapers.repec.org/RePEc:gam:jeners:v:10:y:2017:i:7:p:835-:d:102334]; von Appen and Braun, Applied Energy 229 (2018): self-sufficiency desire plus storage investment incentive lead to larger PV [S: https://ideas.repec.org/a/eee/appene/v229y2018icp1140-1151.html]; Uhlemeyer et al. (175 German buildings, grid-supporting vs economic sizing) [S: https://zenodo.org/records/3243423/files/4B_6_CRET19_011_paper_Bj%C3%B6rn_Uhlemeyer.pdf].

**I did not find a peer-reviewed review that formally standardizes a "knee-point" criterion** for residential batteries. "Knee" is my framing of HTW's saturation observation and diminishing-returns results. State this honestly in the product.

**Criteria compared (what to implement)**

| Criterion | Where it comes from | Behaviour | Use in engine |
|---|---|---|---|
| Max self-sufficiency | HTW autarky curves; Unabhängigkeitsrechner | Always bigger; saturates > ~1.5 kWh/MWh | Show as "max independence" variant, flag marginal EUR/kWh |
| Max NPV / min mean electricity cost | Weniger 2014, Schopfer 2018 | Optimum small (0.5-1.1 kWh/MWh) and flat; very sensitive to battery price, interest rate | Primary ranking criterion |
| Min LCOS | generic | Favours high cycle count, small battery | Report as secondary KPI |
| Knee of autarky curve | HTW saturation (A1) | Where marginal autarky pp per kWh falls below threshold | Use as recommended default; suggested threshold [A]: stop when added kWh yields < ~1 pp autarky or < X EUR/yr per installed EUR |
| Nightly consumption match | Weniger 2013 (sunset-to-sunrise benchmark); HTW 2025 forecast charging | Caps useful capacity at average nightly load | Hard sanity cap: usable kWh <= ~1.0-1.3 x mean (sunset-to-sunrise load) [A] |
| Full-cycle equivalents | Weniger 2013: ~270 at 1/1; Agora 2015 says ~250/yr achievable [S: https://www.agora-energiewende.org/fileadmin/Projekte/2015/PV-Speicher-Rollout/Agora_Speicherdurchbruch_2015-10-08_web_EN.pdf]; pv magazine assumes 300 [S] | FCE < ~150 signals oversizing | Plausibility check: flag designs with FCE < 150 or > 400 |
| HTW max kWh per kWp | Inspektion 2024: 1.5 kWh/kWp | Simple guard | Guard rail |

**Practical answer:** yes, "smallest battery with most of the benefit" is the closest thing to a standard, defensible via HTW's saturation and economic-optimum results. Implement as: compute autarky and NPV on a grid of capacities; pick the capacity at the economic optimum, constrained by (a) nightly load cap and (b) 150-350 FCE/yr band; show the max-autarky option separately.

### A2. EV: night charging vs solar charging vs home office

**Evidence (HTW Berlin + Fronius, "Solares Laden von Elektrofahrzeugen", April 2025, 730 households)** [P: https://solar.htw-berlin.de/wp-content/uploads/HTW-Solares-Laden-von-Elektrofahrzeugen.pdf; text extracted locally; headline figures also confirmed in S: https://www.energiezukunft.eu/mobilitaet/e-autos-mit-mehr-solarstrom-laden]
- Mean solar share of EV charging energy: 53%.
- A home battery raises the EV solar share by only about 9 pp on average (for 3 of 4 households under 15 pp; some >30 pp).
- Dynamic surplus charging ("Überschussregelung") raises solar share by about 25 pp on average versus uncontrolled charging.
- Household autarky with PV + battery + EV: 73% on average; without battery 47%; with heat pump added 59%.
- Charging losses are large at low power: at 1.4 kW only 76% of solar energy reaches the car battery, at 11 kW 90% (vehicle standby consumption dominates).
- Qualitative guidance in the study: use surplus charging and choose the wallbox by PV size; the study also reports that EVs are plugged in at home on >3 days per week in 68% of households.
- Earlier HTW text (in the same study) quotes strategy ranges for solar share of driving energy: uncontrolled 5-15%, wallbox manual 10-50%, automatic surplus 20-70%, threshold charging 25-90% (typical 15,000 km/yr EV).

**Interpretation**
- Home office/day availability is the strongest lever for solar share (car at home when PV produces). The battery is a weak substitute for this.
- Night charging at home from a battery is inefficient: a 10 kWh battery is drained by the car in one night and the car's 10-15 kWh/day demand (about 40 kWh/week at 15,000 km) is larger than typical nightly household load, so it breaks the "battery empty by morning" balance. [A] Therefore do not size the battery up for the EV; instead (i) model the EV as a controllable load with a plug-in schedule, (ii) give the engine a priority order: house load, EV surplus above a threshold, battery, feed-in [A, matches HTW "Schwellwertladen"].
- V2H: Australian simulation (Flinders/Murdoch, IET Renewable Power Generation 2025) found V2H can remove the need for a dedicated battery, with about 5% bill reduction relative to PV+battery+EV without V2H, and a 13 kWh battery needed to match V2H performance [S: https://researchnow.flinders.edu.au/en/publications/optimal-sizing-of-photovoltaic-and-battery-energy-storage-for-res/ ; press https://www.pv-magazine-australia.com/2026/04/16/evs-with-vehicle-to-home-technology-reduce-need-for-large-home-batteries/]. Different tariff/export setting; treat as indicative. Germany V2H legal/tariff conditions (double network charges, wallbox support) are not covered here.

**Default for engine:** EV adds consumption (see parameter table) with weekday schedules (home office share as parameter), surplus charging enabled by default; battery size recommendation computed on non-EV nightly load plus a modest uplift (e.g., +0-2 kWh) only if EV is plugged at night and surplus-charging is not possible [A].

### A3. Dynamic tariffs, Solarspitzengesetz, forecast-based charging

**Dynamic tariffs**
- Since 1 Jan 2025 all suppliers must offer dynamic tariffs (§41a EnWG) [S, from pv magazine/EPJ PV search summary: https://www.pv-magazine.com/2025/06/06/germany-registers-130-hours-of-negative-day-ahead-power-prices-in-may/ for negative price counts].
- Negative day-ahead hours in Germany: 457 h in 2024; 250 h by end of May 2025 [S, same source].
- A 2026 Energy Informatics study (Ameling et al.) with German load profiles finds dynamic tariffs plus modest storage give substantial savings and warns against over-investing in capacity [S: https://doaj.org/article/961fc222aaa8433499fcabbbef2eb912; page returned 403 to fetch, abstract only via search snippet].
- EPJ Photovoltaics 17, 20 (2026) (Berrian et al.): standalone PV shows value erosion with negative prices, hybrid PV+BESS more resilient; up to ~10% PV curtailment losses under high negative-price scenarios; gains come from battery revenue [S: https://www.epj-pv.org/10.1051/epjpv/2026012 ; page 403 on fetch, snippet only].
- Conclusion for engine [A]: for households, arbitrage from grid charging rarely changes the optimal battery size materially because spreads net of ~85-90% round-trip efficiency, standby, and cycle wear are limited and the household load is small; treat price-aware charging as an operating-strategy toggle that raises the value of a given battery and adds ~1-2 kWh willingness-to-pay for oversize at most. Do not let arbitrage justify a large battery on its own.

**Solarspitzengesetz (in force 25 Feb 2025)** [P: https://www.pv-magazine.de/2025/12/22/keine-angst-vor-dem-solarspitzengesetz-wir-erlaeutern-die-neue-erloessituation/]
- New plants: no feed-in tariff for electricity fed in during negative-price quarter-hours; lost compensation is appended to the end of the support period (plant-specific). Requires smart meter for quarter-hour billing.
- Plants under 100 kWp: until a smart meter with tested control is installed, feed-in capped at 60% of peak power.
- Example (10 kWp south, 2024 weather): 60% cap costs 6083 -> 5726 kWh (about EUR 28/yr); HTW estimate: 9% yield loss for south-facing full-feed, 1.1% for east-west. Negative hours: about 1322 kWh/yr unpaid (18% of that plant's 2024 output fell in negative hours), feed-in revenue 483 -> 351 EUR/yr; forecast-based battery control (empty before negative periods) reduces the 20-yr shortfall to about 115 EUR; a simple surplus-charging controller still hits the cap; a 10 kWh battery captures only part of long negative stretches.
- HTW claim: an intelligently operated 10 kWh battery cuts curtailment of a 10 kW system at 5 kW feed-in cap to about 1% [S: pv-magazine summary; and Weniger quote "unter 2 Prozent" in https://www.solarserver.de/2025/02/07/neues-testverfahren-fuer-energiemanagement-von-pv-speichern/]. HTW 2016 "Klug gespeichert statt abgeregelt": forecast-based charging reduced curtailment by about 6 pp relative to simple charging under the then 50% cap [S: https://solar.htw-berlin.de/wp-content/uploads/WENIGER-2016-Klug-gespeichert-statt-abgeregelt.pdf ; snippet].
- Feed-in tariff today (Teileinspeisung <=10 kWp): 7.78 ct/kWh from 1 Feb 2026, 1% semiannual degression; August 2026 value 7.70-7.71 ct/kWh, to verify on BNetzA [S: https://reduco.ai/blog/solar/einspeiseverguetung-2026-saetze]. Discussion of further EEG changes from 2027 is unconfirmed; keep a scenario switch.
- Older/pre-Feb-2025 plants are grandfathered [S: https://www.enpal.de/blog/wirkleistungsbegrenzung].

**Forecast-based charging ("prognosebasiertes Laden")**
- HTW Stromspeicher-Inspektion 2025 (HTW + KIT) [P, PDF read locally: https://solar.htw-berlin.de/wp-content/uploads/HTW-Stromspeicher-Inspektion-2025.pdf]:
  - Typical aging-optimal behaviour: delay charging to the afternoon, store only what the following night needs plus a safety reserve, stop charging once target SoC is reached.
  - Measured on a system over 10 days: time at 90-100% SoC cut from 99 h to 43 h; mean SoC reduced where early charging gave 64% for 7 kWh LFP systems.
  - Cited modelling result (Li and Danzer): time above 85% SoC cut from 70 days/yr to 19 days/yr [secondary citation inside the Inspektion].
  - Statement that LFP and NMC both have higher calendar aging at higher SoC.
- HTW campaign "Dein Stromspeicher kann mehr": midday charging increased mean market value of fed-in solar power by 28% in 2024 simulation [S: https://www.solarserver.de/2025/04/04/neue-initiative-dein-stromspeicher-kann-mehr].
- Engine implication: S1 needs at least two dispatch modes: greedy (reference, what most legacy systems do) and forecast-based (target-SoC from next-night load, charge late, respect negative hours and 60% cap). The value difference between them is a central, defensible product insight.

### A4. Chemistry, aging, usable capacity, efficiency

**Evidence**
- HTW Inspektion 2024 [P]: mean battery (DC) efficiency of 20 lithium systems 95.7% (lowest 87.9%); mean inverter discharge path (BAT2AC) efficiency 95.2%; standby draw at empty battery: average 13 W (19 W in 2023; 16 of 20 systems <3 W; worst 64 W; Varta 2 W). Example: 40 W for 2000 h/a empty = 80 kWh/a; 10 W gives 10-30 kWh/a. Partial-load: at 200 W output the best inverter has 92% efficiency, worst 71%; nightly loads are mostly low (28-household ISFH data: on average 72% of night power flows are under 300 W). Datasheet capacity claims often deviate (e.g., a claimed 15 kWh gave 13.3 kWh usable on the bench).
- HTW SPI (System Performance Index) compares real system to a lossless one at 5 kW/10 kW reference cases; top systems reach about 92.6% (5 kW class) and 95.4% (10 kW class) [S: https://pv.de/en/news/energy-storage-inspection-2024-rct-power-byd-fronius-and-kostal-on-the-winners-podium/].
- Field degradation: RWTH ISEA (Figgener et al., Nature Energy 9, 1438-1447, 2024): 21 home storage systems in Germany, up to 8 years (106 system-years), lose about 2-3 percentage points usable capacity per year; most met warranties thanks to capacity buffers [P abstract: https://ideas.repec.org/a/nat/natene/v9y2024i11d10.1038_s41560-024-01620-9.html ; press https://www.pv-magazine.com/?p=38326]. Caveat: the sample is first-generation products, many NMC; LFP-era systems likely age slower [A].
- Market (RWTH market review, status 2023): about 220,000 systems installed in 2022, stock about 650,000, average capacity stable at 8.8 kWh, average power 5.3 kW [P/S: https://arxiv.org/pdf/2203.06762 text extracted but those exact lines are from search summary].
- Aging physics [P via Inspektion 2025]: high SoC, high temperature, high power, and deep cycles accelerate aging; calendar aging depends mostly on SoC and temperature; end of life is typically 80% (sometimes 70% or 60%) of initial capacity. Limiting maximum SoC below 100% helps NMC and LFP but loses usable capacity; forecast-based dwell reduction avoids that trade-off. Teesside lab: fully charged BYD cells aged almost twice as fast as cells stored at 20% SoC over 17 months.
- LFP model references: Naumann et al., J. Energy Storage 17 (2018) 153-169 (calendar), J. Power Sources (2020) (cycle) [S: https://portal.fis.tum.de/en/publications/analysis-and-modeling-of-calendar-aging-of-a-commercial-lifeposub/]. A search summary says LFP calendar aging is less SoC-sensitive than NMC [S, unverified at paper level].

**Defaults** (see table in section C): LFP, DoD/usable 90-95% of nominal (Inspektion 2024 shows many systems with reserve), DC battery efficiency 95.7%, bat-to-AC 95.2%, so one-way charge from PV via DC-coupled about 97% x 95.7% etc. Use system-level AC-AC round trip of about 85-88% for AC-coupled and 88-92% for DC-coupled [A, composition of Inspektion path efficiencies]. Standby 13 W average (when discharged) as default, with 5 W (good) / 30 W (bad) sensitivity. Degradation 2%/yr capacity loss (range 1-3%), end-of-life 70-80%, replace-or-not decision at year 12-15 in the 20-yr model.

### A5. Heat pump coupling

**Evidence**
- HTW/Fronius sample (730 households): a heat pump raises household electricity use by more than 3200 kWh or 80% on a 4100 kWh median; mean autarky with PV+battery+EV is 73% and 59% with a heat pump; battery adds >13 pp autarky in 7 of 10 cases... (from HTW Solares Laden text, exact wording in Bild 6/7) [P: https://solar.htw-berlin.de/wp-content/uploads/HTW-Solares-Laden-von-Elektrofahrzeugen.pdf]. In winter, when heat pump runs and PV is scarce, solar surplus is rare; surplus-charging helps the EV less in winter.
- HTW Inspektion 2024 reference case 2: 10 kW PV, 9363 kWh/a (heat pump + wallbox), battery cap 16 kWh [P].
- Older HTW (Tjaden 2015/16) autarky for simple PV-HP system about 20-30% [S: https://solar.htw-berlin.de/wp-content/uploads/TJADEN-2016-Solarspeichersysteme-zur-autarken-Strom-und-Waermeversorgung-von-Gebaeuden-in-Niederspannungsnetzen.pdf ; value via https://cms.ueberlingen.de/mediamanager/2024/07/13_warmepumpe_web_september_2023.pdf].
- Fraunhofer ISE (mixed-integer, 2017): electrical and thermal storage sizing is demand-driven with little interdependence [S: https://publica.fraunhofer.de/handle/publica/247410]. Applied Energy 188 (2017): optimal heat pump size hardly depends on scenario, PV size depends strongly on load profile [S: https://econpapers.repec.org/RePEc:eee:appene:v:188:y:2017:i:c:p:604-619].
- Heat pump performance data (Fraunhofer ISE field tests): WPsmart im Bestand: average SPF about 3.1 (air-water) and 4.1 (ground); follow-up WP-QS im Bestand, 77 units: about 3.4 air-water, 4.3 ground, overall range 2.6-5.4 [S: https://www.ise.fraunhofer.de/en/research-projects/wpsmart-im-bestand-heat-pump-field-trial-focus-existing-buildings-and-smart-control.html ; numbers via https://www.energie-fachberater.de/heizung-lueftung/heizung/waermepumpe/effizienter-als-gedacht-waermepumpe-auch-im-altbau-zuverlaessig.php].
- Full-load hours by building standard (BürgerNetzwerkSolar guide, approximate): passive house 500-800 h, KfW40/new 900-1200 h, renovated old 1300-1600 h, unrenovated old 1800-2200 h [S: https://www.worms.de/neu-de-wAssets/docs/zukunft-gestalten/klima-umwelt/Energie/BuergerSolarBeratung/_BNS_Waermepumpe-Praxisleitfaden-im-Einfamilienhaus.pdf].

**Conclusions**
- A heat pump increases the sensible PV size (more kWh to produce, especially shoulder months) and the value of a PV system (high load, partly daytime in spring/autumn), but additional battery capacity has diminishing value because winter demand outstrips PV even with a big battery, while summer demand is small (DHW only). So optimal battery grows weakly; optimal PV grows more [A, consistent with Fraunhofer finding of weak storage interdependence and HTW autarky drop].
- Highest-value coupling is not battery: it is thermal flexibility (buffer tank, SG-Ready/DHW boost, Heizstab) [A; modulating HP with SG-Ready raises self-consumption per https://www.verbraucherzentrale-rlp.de/node/108337 [S]].

### A6. ML / data-driven sizing papers

- **Schopfer, Tiefenbeck, Staake, "Economic assessment of photovoltaic battery systems based on household load profiles", Applied Energy 223 (2018) 229-248, DOI 10.1016/j.apenergy.2018.03.185. Confirmed to exist.** 4190 Zurich-area households, techno-economic optimization of PV-battery configuration per load profile, plus ML predictor of optimal configuration, profitability and self-sufficiency from limited smart-meter features and short timeframes; main finding: profitability is dominated by load-profile heterogeneity [P abstract: https://cris.fau.de/publications/227854435/ ; https://econpapers.repec.org/RePEc:eee:appene:v:223:y:2018:i:c:p:229-248]. A follow-up "Profitability assessment of photovoltaic battery systems based on household load profiles" is listed [S: https://cris.fau.de/publications/237636979].
- Khezri, Razmi et al., IEEE Trans. Sustainable Energy 14(2) 837-848 (2023), feed-forward NN sizing of renewable-battery system with fast-charging EV [S: https://research.chalmers.se/en/publication/533977].
- Gschwind et al., "SolarFit" neural-network surrogate for PV+storage sizing in EV homes (seminar listing only, not a verified paper) [S: https://talks.cam.ac.uk/talk/index/232144/].
- Elmali and Altin 2026, ML surrogate for solar plant sizing trained on HOMER outputs [S: https://avesis.bozok.edu.tr/yayin/7ad1e1bd-0469-4984-a84e-7b64543ffd00/machine-learning-driven-rapid-optimization-of-solar-power-plant-sizing-using-homer-generated-synthetic-scenarios].
- Takeaway for hackathon [A]: train a surrogate (e.g., gradient boosting or small MLP) on your own S1 results over randomized (load shape, PV, battery) inputs; use it to produce instant curves in the UI and for Monte Carlo (S6). That mirrors Schopfer's predictor idea without needing their data.

---

## PART B: Simulations

General resolution evidence (applies to S1-S3):
- Beck, Kondziella, Huard, Bruckner, Applied Energy 173 (2016) 331-342: 10 s smart-meter data from 25 German households; load resolution matters more than PV resolution; for PV-only 15-min irradiation is accurate; 60 s load data suits all profiles, 15 min suffices if little power above 2 kW; with battery the resolution effect is less pronounced, 5-60 min give good self-consumption; 60 min is sufficient for sizing PV and storage capacity; battery inverter power sizing needs at least 300 s [P: https://econpapers.repec.org/RePEc:eee:appene:v:173:y:2016:i:c:p:331-342].
- Summaries reporting larger errors when resolution is coarse: Sun et al. 2020 (UK 15 s data): low resolution overstates PV-battery benefit [S: https://durham-repository.worktribe.com/OutputFile/1268684]; Burgio et al., Energies 2020: storage reduces resolution-induced error by factor ~8-10 [S: https://doaj.org/article/486af13fe4e94cc39d9bdebb3986a380]; Jimenez-Castillo et al.: about 9% difference between hourly and 10 s [S: https://rujapre.ujaen.es/bitstreams/157dad1e-ff8f-4085-9063-626f71dfd99e/download]; Polish MATEC 2018 study: 5 and 15 min can give >15% error on some days, avoid >15 min [S: https://www.matec-conferences.org/10.1051/matecconf/201824004003]; NZ study: median profiles overestimated self-consumption by ~5% [S: https://hdl.handle.net/10092/15210].
- HTW provides 74 German single-family household profiles in 1 s resolution (Tjaden, Bergner, Weniger, Quaschning) [P: https://pvspeicher.htw-berlin.de/wp-content/uploads/Repr%C3%A4sentative-elektrische-Lastprofile-f%C3%BCr-Wohngeb%C3%A4ude-in-Deutschland-auf-1-sek%C3%BCndiger-Datenbasis.pdf ; data page https://pvspeicher.htw-berlin.de/daten-und-simulation-links]. Their 15-min mean over all 74 profiles is nearly identical to the standard load profile H0 (per search summary of the same paper), while individual households differ widely [S].
- Self-sufficiency varies by up to 23% across households at equal relative PV and storage size [S, cited in search summary of arXiv https://pdf.arxiv.org/pdf/2003.00741].
- HTW explicit: Inspektion says household load profiles differ strongly especially in daytime, and the night load is mostly base load [P].

### S1. Hourly energy balance (PV x load x greedy dispatch)

- **Method/resolution:** hourly is adequate for ranking and for capacity sizing (Beck 2016) but biases self-consumption/autarky upward [S evidence above]. Use 15-min if profile data allow; otherwise hourly with a calibration factor (e.g., apply a per-household "intra-hour variance" correction that lowers direct consumption) [A].
- **Key parameters/defaults:** PV specific yield 900-1050 kWh/kWp (HTW assumes 1050 in economics paper [P]; Germany typically 850-1000 for real fleet [A]); system efficiency chain: PV inverter ~97% max, battery DC 95.7%, bat-to-AC 95.2% (HTW 2024); standby 13 W; usable fraction 90-95%.
- **Pitfalls:** (1) H0 or smooth profiles overestimate PV direct use; (2) ignoring partial-load inverter efficiency and standby overstates battery value (HTW: worst system loses 588 kWh/yr more grid purchase than an ideal one); (3) ignoring power limits (battery charge/discharge kW, inverter limit) -- HTW calls them "Dimensionierungsverluste"; (4) greedy dispatch is not what to compare against after Solarspitzengesetz.
- **Better variants:** forecast-based dispatch (target SoC from next-night load; midday charging; respects negative hours and 60% cap); price-aware dispatch (day-ahead prices) via simple rule or LP over 24 h; separate PV inverter clipping step; 15-min resolution.

### S2. Heat pump (fuel -> heat demand -> heat load via full-load hours -> hourly via temperature -> COP(T))

- **Method:** annual heat = fuel x boiler efficiency (see defaults); heating load = heat / full-load hours (BNS table above); hourly heat = distribute by degree-hours of outdoor temperature below heating limit (typ. 15 C [A, not found in sources]) plus separate DHW base; electricity = heat / COP(T, flow temp). Calibrate COP curve so seasonal SPF equals field values: 3.1-3.4 air-water existing buildings, 4.1-4.3 ground (Fraunhofer ISE) [S].
- **Pitfalls:** oversizing (full-load hours too low), COP at design point instead of seasonal, forgetting defrost/heating-rod backup at <-7 C, DHW share (about 15-20% in efficient buildings [A]), double counting when fuel bills include DHW; underestimating winter peaks drives §14a decisions.
- **Better variants:** two-zone (space + DHW) with different flow temps/COPs; thermal buffer/SG-Ready flexibility; weather file consistent with PV (same TMY/year) so winter correlations are real; check against HTW Inspektion reference (HP + wallbox household = 9363 kWh/a).

### S3. EV charging profiles

- **Method:** annual km -> kWh (15,000 km typical in HTW sources [P]; consumption 15-20 kWh/100 km [A]); plug-in schedule (weekday/weekend, home office share); charging modes: uncontrolled, timer, surplus (+25 pp solar, HTW) and threshold; charging power effect on losses (76% at 1.4 kW vs 90% at 11 kW, HTW) [P].
- **Pitfalls:** assuming 100% home charging (survey: 70-75% of charged energy at home [S per HTW citation]); using flat nightly charging profile; ignoring vehicle standby and min current (6 A) at low surplus; 1-phase vs 3-phase.
- **Better variants:** Markov / trip-based plug-in profiles; home-office vs commuter archetypes; wallbox min-power threshold logic; optional V2H as scenario.

### S4. Existing PV/storage incremental value (AC-coupled retrofit, post-EEG)

- **Method:** compute baseline of existing system (PV-only or PV+old storage with degraded capacity), then incremental delta of added battery/HP/EV; for post-EEG plants (Ausförderung) feed-in is market value or EEG Anschlussvergütung; for plants grandfathered pre-Feb 2025 no 60% cap, no negative-hour rule [S: https://www.enpal.de/blog/wirkleistungsbegrenzung]; voluntary switch to smart-meter regime gives +0.6 ct but loses negative hours [P pv-magazine article].
- **Parameters:** AC-coupled adds double conversion: HTW notes AC-coupled systems A1/B1 have extra standby of the PV inverter in real operation [P]; older existing batteries: capacity -2-3 pp/yr [P abstract].
- **Pitfalls:** treating retrofit as a new system (no sunk PV cost); applying new-plant EEG rules to old plants; incremental value of a battery is higher when feed-in tariff is low; AC retrofit shares inverter clipping behaviour differently (clipped energy can be recaptured by AC-coupled battery).
- **Better variants:** marginal analysis (NPV with/without each add-on), battery-replace-vs-keep decision.

### S5. 20-year economics

- **Defaults/benchmarks:** HTW 2014: 20-yr life, 1.5% O&M of investment, interest 4%, retail price escalation 2%/yr [P]. Retail price 2025 average 39.6 ct/kWh for 3500 kWh/yr (BDEW), 2026 about 37.0 ct/kWh YTD per BDEW August 2026 edition [S: https://www.bdew.de/media/documents/BDEW_Strompreisanalyse_102025.pdf ; https://www.bdew.de/media/documents/BDEW_Strompreisanalyse_082026.pdf]. Feed-in 7.78 ct (<=10 kWp, Feb 2026). HTW SPI uses 40 ct and 8 ct [P]. Interest rate is the most influential economic parameter [P].
- **Pitfalls:** no degradation; ignoring negative-hours rule and 60% cap for new plants; ignoring battery replacement; flat prices; using nominal not usable capacity; ignoring VAT (0% VAT on PV since 2023, [A] verify); ignoring inverter replacement at year ~12-15.
- **Better variants:** battery degradation 2%/yr plus inverter replacement; price scenarios (retail growth, dynamic tariffs); IRR/payback plus NPV; discount rate range 2-6%.

### S6. Monte Carlo uncertainty / robustness

- **Method:** sample load profile (HTW 74 profiles or generated), weather year, retail price growth, interest, battery price, degradation, feed-in regime; report distribution of NPV and probability(NPV>0). Schopfer 2018 shows household heterogeneity is dominant, so profile sampling must be a first-class dimension [P].
- **Pitfall:** sampling only price parameters and one smooth profile; correlated variables (high retail price with high interest).
- **Better variants:** surrogate model (A6) to make 10k+ draws fast; tornado chart from one-at-a-time sensitivity (HTW: interest > PV price > retail price > feed-in) [P].

### S7. Backtest

- **Method:** compare simulated vs measured: (a) HTW Inspektion field aggregates: mean autarky 70%, grid purchase reduction 3400 kWh/yr, battery adds 18-38 pp in 9/10 households, PV alone 2000 kWh/yr reduction [P]; (b) HTW/Fronius 730-household stats: EV solar share 53%, autarky 47/73/59 [S/P]; (c) HTW Weniger 2013 normalized results (30%/59%/56%, ~270 cycles) [P]. Use these as acceptance bands for S1-S3.
- **Pitfalls:** field samples are early adopters (HTW notes this) and skew towards larger PV; single-year weather.
- **Better variants:** per-household backtest if user provides monitoring data (smart meter, inverter portal); report error in autarky pp.

---

## PART C: Missing simulations, ranked by value for effort (20-hour hackathon)

| Rank | Addition | Why valuable | Effort | Evidence |
|---|---|---|---|---|
| 1 | **Load-profile variety + resolution bias** (HTW 74 profiles at 15 min or archetype library: low/mid/high daytime load, night base load) | Biggest source of error and household variance; H0 hides it | Medium (data download + resampling) | Schopfer 2018; HTW profiles; resolution studies [P/S] |
| 2 | **Forecast-based vs greedy dispatch + Solarspitzengesetz rules** (60% cap, negative-price hours, EEG regime switch) | Changes revenue and battery value for new plants; low code (rules over hourly arrays) | Low-medium | pv-magazine 2025; HTW 2025 [P] |
| 3 | **Battery aging + standby in S1/S5** (2%/yr capacity loss, 13 W standby, SoC-dwell proxy) | Prevents overoptimistic 20-yr NPV; trivial to add | Low | RWTH 2024; HTW 2024/2025 [P] |
| 4 | **Plausibility guards**: FCE/yr band (150-350), kWh/kWp <= 1.5, usable <= nightly load, battery kW vs peak load | Keeps designs physically sensible; cheap | Very low | Weniger 2013; HTW 2024 [P] |
| 5 | **Inverter clipping / DC-AC ratio** | Real losses at DC/AC > 1.2; interacts with feed-in cap and AC-coupled battery | Low | not found in HTW sources; standard engineering [A] |
| 6 | **Orientation: E/W split vs south** | E/W raises self-consumption (Azaioud et al. Energies 2020: +14 pp SCI) and cuts 60%-cap loss (1.1% vs 9%) | Low if you already have PVGIS-like per-orientation curves | HTW poster [S: https://solar.htw-berlin.de/wp-content/uploads/TJADEN-2014-Poster-Impact-of-the-PV-Generators-Orientation.pdf]; pv-magazine [P] |
| 7 | **DHW/Heizstab PV surplus diversion** | Cheap flexible sink when no battery; relevant for HP homes | Low | [A]; SG-Ready note [S] |
| 8 | **§14a EnWG curtailment** (HP, wallbox >4.2 kW; Modul 1 flat discount, Modul 2 reduced work price, Modul 3 time-variable) | Affects HP/EV economics and peak design; implement as discount + 4.2 kW curtailment window | Low-medium | Utility pages [S: https://www.vattenfall.de/steuerbare-verbrauchseinrichtungen-14a-enwg ; https://www.yello.de/wissen/energiemarkt/14a-enwg-netzentgelt/]; verify BNetzA text |
| 9 | **Surrogate model for S6** | Instant UI curves, many MC draws | Medium | A6 |
| 10 | **Emergency backup sizing** (blackout days, critical load, backup-capable inverter) | Differentiator but separate objective | Medium | none sourced [A] |
| 11 | **Grid connection limits** (feed-in cap kW, 3-phase imbalance) | Rare binding; partially covered by 60% rule | Low | [A] |
| 12 | **V2H** | Interesting, weak German evidence | Medium-high | Flinders [S] |

---

## Default parameter table (Germany)

| Parameter | Default | Range for sensitivity | Source / tag |
|---|---|---|---|
| Battery type | LFP | LFP / NMC | HTW 2025 [P]; market [S] |
| Usable capacity / nominal | 0.92 | 0.85-0.98 | Inspektion 2024 shows deviations (claimed 15 vs 13.3 kWh) [P]; [A] |
| DC battery efficiency | 95.7% | 88-97% | HTW 2024 [P] |
| Bat-to-AC conversion efficiency (avg) | 95.2% | 85-97% | HTW 2024 [P] |
| System AC-AC round trip | 86-88% | 80-92% | derived [A] |
| Standby when discharged | 13 W | 2-64 W | HTW 2024 [P] |
| Capacity fade | 2%/yr | 1-3%/yr | RWTH Nature Energy 2024 [P abstract] |
| End of life | 70-80% of initial | | Inspektion 2025 [P] |
| Calendar life / replace | 15-20 yr | 10-20 | HTW 2014 assumes 20 yr / 5000 cycles [P] |
| FCE per year plausible | 150-350 (typ. 250-300) | | Weniger 2013 (~270) [P]; Agora ~250, pv magazine 300 [S] |
| Battery size rule | 0.5-1.1 kWh/MWh economic; <=1.5 kWh/MWh and <=1.5 kWh/kWp cap | | Weniger 2013 [P]; Inspektion 2024 [P] |
| PV size rule | ~0.8-1.0 kWp/MWh baseline; larger with HP/EV | | Weniger 2013 [P] |
| PV specific yield | 950 kWh/kWp (south, 30 deg) | 850-1050 | HTW 1050 in 2014 paper [P]; [A] fleet avg |
| Battery system price | market-based, 2022: HSS about 1200 EUR/kWh | check current | RWTH market review [S: https://arxiv.org/pdf/2203.06762]; HTW 2014 scenarios 1500/1000/600 EUR/kWh [P] |
| Retail electricity price | 37-40 ct/kWh | +/- 3%/yr | BDEW 2025 39.6; 2026 YTD 37.0 [S] |
| Feed-in (Teileinspeisung <=10 kWp) | 7.78 ct/kWh (Feb 2026), 7.70-7.71 from Aug 2026 | 0-8 | reduco summary [S] |
| Negative-hour feed-in | 0 ct for plants after 25 Feb 2025 | 0.4-18% of PV output in negative hours (18% in 2024 example) | pv-magazine 2025 [P] |
| 60% cap without smart meter | on for new <100 kWp | off with smart meter | [P] |
| Interest/discount rate | 4% | 2-6% | HTW 2014 [P] |
| O&M | 1.5% of investment/yr | 1-2% | HTW 2014 [P] |
| Electricity price escalation | 2%/yr | 0-4% | HTW 2014 [P] |
| Household load median | 4100 kWh/yr (HTW/Fronius sample); 5010 kWh reference | 2000-6000 | HTW [P] |
| Night load | 72% of night power under 300 W | household-specific | HTW 2024 [P] |
| EV annual km | 15,000 | 8,000-25,000 | HTW [P] |
| EV charge efficiency | 76% at 1.4 kW, 90% at 11 kW | | HTW 2025 [P] |
| EV solar share ranges | uncontrolled 5-15%, surplus 20-70%, threshold 25-90% | | HTW 2025 [P] |
| HP SPF existing buildings | 3.1-3.4 air, 4.1-4.3 ground | 2.6-5.4 | Fraunhofer ISE [S] |
| HP full-load hours | 1300-1600 renovated, 1800-2200 unrenovated | 500-2200 | BNS guide [S] |
| HP electricity add to household | +3200 kWh/yr (median in sample, +80%) | | HTW 2025 [P] |
| Feed-in reference (SPI) | 8 ct sell / 40 ct buy | | HTW 2024 [P] |
| Temporal resolution | 15 min preferred; 60 min for sizing; battery inverter sizing needs <=5 min | | Beck 2016 [P] |
| Heating limit temperature | 15 C | 12-17 | [A] not sourced |

---

## Sources

HTW Berlin
- Stromspeicher-Inspektion 2024: https://solar.htw-berlin.de/wp-content/uploads/HTW-Stromspeicher-Inspektion-2024.pdf
- Stromspeicher-Inspektion 2025: https://solar.htw-berlin.de/wp-content/uploads/HTW-Stromspeicher-Inspektion-2025.pdf
- Solares Laden von Elektrofahrzeugen (2025): https://solar.htw-berlin.de/wp-content/uploads/HTW-Solares-Laden-von-Elektrofahrzeugen.pdf
- Weniger et al. 2013, Sizing and grid integration: https://solar.htw-berlin.de/wp-content/uploads/WENIGER-2013-Sizing-and-Grid-Integration-of-Residential-PV-Battery-Systems.pdf
- Weniger et al. 2014, Economics: https://solar.htw-berlin.de/wp-content/uploads/WENIGER-2014-Economics-of-Residential-PV-Battery-Systems-in-the-Self-Consumption-Age.pdf
- Weniger 2016, Klug gespeichert statt abgeregelt: https://solar.htw-berlin.de/wp-content/uploads/WENIGER-2016-Klug-gespeichert-statt-abgeregelt.pdf
- Tjaden 2014 poster, PV orientation: https://solar.htw-berlin.de/wp-content/uploads/TJADEN-2014-Poster-Impact-of-the-PV-Generators-Orientation.pdf
- Tjaden 2016, Solarspeichersysteme autark Strom und Wärme: https://solar.htw-berlin.de/wp-content/uploads/TJADEN-2016-Solarspeichersysteme-zur-autarken-Strom-und-Waermeversorgung-von-Gebaeuden-in-Niederspannungsnetzen.pdf
- 74 load profiles (1 s): https://pvspeicher.htw-berlin.de/wp-content/uploads/Repr%C3%A4sentative-elektrische-Lastprofile-f%C3%BCr-Wohngeb%C3%A4ude-in-Deutschland-auf-1-sek%C3%BCndiger-Datenbasis.pdf ; page: https://pvspeicher.htw-berlin.de/daten-und-simulation-links
- Press on Inspektion 2024: https://pv.de/en/news/energy-storage-inspection-2024-rct-power-byd-fronius-and-kostal-on-the-winners-podium/
- Solarserver on HTW forecast-based management: https://www.solarserver.de/2025/02/07/neues-testverfahren-fuer-energiemanagement-von-pv-speichern/ ; https://www.solarserver.de/2025/04/04/neue-initiative-dein-stromspeicher-kann-mehr
- Energiezukunft on solar charging: https://www.energiezukunft.eu/mobilitaet/e-autos-mit-mehr-solarstrom-laden

Papers
- Schopfer, Tiefenbeck, Staake, Applied Energy 223 (2018): https://cris.fau.de/publications/227854435/ ; https://econpapers.repec.org/RePEc:eee:appene:v:223:y:2018:i:c:p:229-248 ; https://fis.uni-bamberg.de/handle/uniba/44370
- Beck, Kondziella, Huard, Bruckner, Applied Energy 173 (2016): https://econpapers.repec.org/RePEc:eee:appene:v:173:y:2016:i:c:p:331-342
- Figgener et al., Nature Energy 9 (2024): https://ideas.repec.org/a/nat/natene/v9y2024i11d10.1038_s41560-024-01620-9.html ; https://www.pv-magazine.com/?p=38326 ; https://zenodo.org/records/12091223
- Figgener et al., battery storage market review: https://arxiv.org/pdf/2203.06762
- Naumann et al. (LFP calendar aging): https://portal.fis.tum.de/en/publications/analysis-and-modeling-of-calendar-aging-of-a-commercial-lifeposub/
- Hesse et al. Energies 10(7) 835: https://econpapers.repec.org/RePEc:gam:jeners:v:10:y:2017:i:7:p:835-:d:102334
- von Appen and Braun, Applied Energy 229 (2018): https://ideas.repec.org/a/eee/appene/v229y2018icp1140-1151.html
- Applied Energy 188 (2017) heat pump/PV: https://econpapers.repec.org/RePEc:eee:appene:v:188:y:2017:i:c:p:604-619
- Fraunhofer mixed-integer HP/storage: https://publica.fraunhofer.de/handle/publica/247410
- Uhlemeyer et al.: https://zenodo.org/records/3243423/files/4B_6_CRET19_011_paper_Bj%C3%B6rn_Uhlemeyer.pdf
- Khezri et al. 2023: https://research.chalmers.se/en/publication/533977
- Resolution: https://durham-repository.worktribe.com/OutputFile/1268684 ; https://doaj.org/article/486af13fe4e94cc39d9bdebb3986a380 ; https://rujapre.ujaen.es/bitstreams/157dad1e-ff8f-4085-9063-626f71dfd99e/download ; https://www.matec-conferences.org/10.1051/matecconf/201824004003 ; https://hdl.handle.net/10092/15210 ; https://arxiv.org/pdf/2003.00741 ; https://arxiv.org/pdf/1905.09498 (review of small-scale PV-battery energy management)
- V2H: https://researchnow.flinders.edu.au/en/publications/optimal-sizing-of-photovoltaic-and-battery-energy-storage-for-res/ ; https://www.pv-magazine-australia.com/2026/04/16/evs-with-vehicle-to-home-technology-reduce-need-for-large-home-batteries/
- Dynamic tariffs/negative prices: https://doaj.org/article/961fc222aaa8433499fcabbbef2eb912 ; https://www.epj-pv.org/10.1051/epjpv/2026012 ; https://www.pv-magazine.com/2025/06/06/germany-registers-130-hours-of-negative-day-ahead-power-prices-in-may/
- Agora Speicherdurchbruch (2015): https://www.agora-energiewende.org/fileadmin/Projekte/2015/PV-Speicher-Rollout/Agora_Speicherdurchbruch_2015-10-08_web_EN.pdf

Policy / market
- Solarspitzengesetz impact analysis: https://www.pv-magazine.de/2025/12/22/keine-angst-vor-dem-solarspitzengesetz-wir-erlaeutern-die-neue-erloessituation/
- Wirkleistungsbegrenzung overview: https://www.enpal.de/blog/wirkleistungsbegrenzung
- Feed-in tariff rates: https://reduco.ai/blog/solar/einspeiseverguetung-2026-saetze
- BDEW electricity price: https://www.bdew.de/media/documents/BDEW_Strompreisanalyse_102025.pdf ; https://www.bdew.de/media/documents/BDEW_Strompreisanalyse_082026.pdf
- §14a EnWG: https://www.vattenfall.de/steuerbare-verbrauchseinrichtungen-14a-enwg ; https://www.yello.de/wissen/energiemarkt/14a-enwg-netzentgelt/
- Heat pump field tests: https://www.ise.fraunhofer.de/en/research-projects/wpsmart-im-bestand-heat-pump-field-trial-focus-existing-buildings-and-smart-control.html ; https://www.energie-fachberater.de/heizung-lueftung/heizung/waermepumpe/effizienter-als-gedacht-waermepumpe-auch-im-altbau-zuverlaessig.php
- BNS heat pump guide: https://www.worms.de/neu-de-wAssets/docs/zukunft-gestalten/klima-umwelt/Energie/BuergerSolarBeratung/_BNS_Waermepumpe-Praxisleitfaden-im-Einfamilienhaus.pdf

## Gaps and caveats

- No peer-reviewed review standardizing a "knee point" criterion was found; presented as my synthesis.
- Heating-limit temperature, DHW share, VAT treatment of PV, current battery prices, and EV consumption are not sourced here; confirm before shipping.
- The HTW Unabhängigkeitsrechner itself and the HTW Weniger-Energy Procedia 2014 full text were not opened; figures come from the IRES 2013 paper by the same authors.
- Energy Informatics 2026 and EPJ-PV 2026 pages returned 403; their claims rest on search snippets.
- Several figures (HP SPF, §14a details, HTW curtailment quotes) are from secondary pages; verify against Fraunhofer ISE reports and Bundesnetzagentur before citing.
- Inverter clipping, backup power, and grid-connection-limit items have no sourced German studies in this pass.
