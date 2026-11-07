# thinc! × Reonic — Master Plan

> Goal: an engine that turns a few facts about a home into a complete PV + battery + heat-pump (+ wallbox) design **the way an experienced planner would**, a planner Design Studio to refine it in seconds, a measured proof against expert designs, and (stretch) a homeowner preview via link/QR.
>
> Deadline: **Sun 8 Nov 2026, 15:00**. Data stays inside the team (brief, p. 8): raw CSVs are never committed, uploaded, or pasted into public tools.

---

## 0. TL;DR (read this if nothing else)

1. **The data is two installers' signed projects** (342 + 1,277 projects; 2,395 + 19,257 BOM line items). Inputs live in `projects_status_quo.csv`; the "expert design" is a **parts list** in `project_options_parts.csv`. Sizes (kWp, kWh, kW) are **not given directly**. We reconstruct them from line items. Units and two columns are mislabelled (see §2.3).
2. **What we predict:** which components a home gets (battery, wallbox, heat pump) and how large each one is (kWp, battery kWh, HP kW, inverter kW), then the **full parts list** with the installer's own products and services.
3. **How:** a hybrid of three parts. (a) A **learned installer policy** (small gradient-boosted models plus a "similar homes" lookup) reproduces what experts do. (b) An **hourly physics and economics simulation** keeps designs plausible and explains them. (c) A **joint optimizer** scores complete candidate systems with both, so the design is coupled, not three separate guesses. Claude Haiku only phrases explanations and turns free text ("buying an EV next year") into input changes. It never sizes anything.
4. **Simulations we need (plain language):** "if this home had *this* system, hour by hour across a year, how much solar does it use itself, how much does it buy and sell, and what does it save?" We run that for many candidate systems. We add sub-simulations for the **heat pump** (turns gas/oil use into a winter-heavy electricity curve), the **EV** (evening charging vs. solar charging), **existing PV/storage** (only the *added* value counts), **20-year money**, and **uncertainty** (what if consumption is 20% off?). §6.3 lists each one and the decision it informs.
5. **Proof:** a backtest on unseen projects (split by time, and leave-one-installer-out) against 4 baselines, with one **Expert Match Score (0–100)**, a runtime figure, and calibrated confidence bands. It is shown on a simple `/eval` page.
6. **UX:** the planner gets a finished draft immediately and edits by exception (lock a component, the rest re-optimizes, a diff bar shows what changed and why). The homeowner gets **at most 3 variants**, a house picture, one sentence of outcome, and a "why this size" curve that answers the fear of being oversold.
7. **Protect order if time runs short:** planner view + eval (minimum result), then validation flags, then the homeowner link/QR.

---

## 1. What the judges will score (map every feature to this)

| Criterion (brief p. 8) | What wins it | Where in plan |
|---|---|---|
| Technical depth | Reproduce expert decisions + convincing measurement | §6, §10 |
| User fit | Planner refines & understands; homeowner explores | §9 |
| Business impact | Time per offer, consistency, win rate | §9.1, §15 |
| Execution & demo | End-to-end, 5-minute story | §14, §15 |

**Minimum** (must ship): proposal with short explanation → measured vs. expert on unseen projects → planner changes ≥1 input/component and gets an updated design.
**Stretch** (in this order): deviation analysis, alternatives + confidence, validation view, homeowner view.

---

## 2. Dataset deep dive

### 2.1 Files

```
dataset/<installer_id>/projects_status_quo.csv     one row per project = INPUTS
dataset/<installer_id>/project_options_parts.csv   one row per BOM line = EXPERT DESIGN
```

| | Installer `23c108b7` | Installer `2a8ba8e2` |
|---|---|---|
| Projects | 342 (336 with parts) | 1,277 (1,257 with parts) |
| Options (variants) | 357 | 1,637 |
| Line items | 2,395 | 19,257 |
| Countries | DE | DE (+1 SI) |
| Period | Jun 2025 – Apr 2026 | Jun 2024 – Apr 2026 |
| Style | **Package-driven** (e.g. "Complete Package 2 Sigenergy 10.8kWp + 9kWh") | Itemised (Huawei / EcoFlow / SAJ…), many service lines |
| Lines per option (median) | 8 | 13 |

**All projects are signed** (`first_signed_at` filled), so the data shows *designs that sold*, not all proposals. That is survivorship bias. We learn the policy of a successful offer.

### 2.2 Columns — status quo (36)

| Group | Columns | Fill rate | Notes |
|---|---|---|---|
| IDs/time | project_id, customer_contact_id, request/offer/first_signed_at | 81–100% (request only 1% at inst. 2) | Some customers have several projects. Group CV by customer. |
| Demand | energy_demand_wh, load_profile, load_profile_editor_id | 100% | **4,500 kWh in 20–31% of rows** looks like a tool default. 82–86% are multiples of 500 kWh, so these are estimates, not readings. `H0` 92%. |
| Tariff | energy_price_per_wh, energy_price_increase, flexible_tariff, base_price(+increase) | 100% / 100% / 44%·5% / ≤20% | 0.00032 €/Wh in 71% of inst. 2 looks like a default. Escalation of 3% is the installer default. |
| EV | has_ev, ev_annual_drive_distance_km | 100% / 3–6% | EV share 3–6% |
| Existing PV | has_solar, solar_size_kwp, angle, orientation, built_year, feedin, feedin_post_eeg | 0% inst. 1, 1.4% inst. 2 | Only 18 projects |
| Existing storage | has_storage, storage_size_kwh, storage_built_year | 11 projects | **Trap:** build years 2025/2026 ≈ sold battery size (see §3.2) |
| Wallbox | has_wallbox, wallbox_charge_speed_kw | 4 projects | |
| Heating | heating_existing_type, cost_per_year, cost_increase, electricity_demand_kwh, heating_demand_wh | 12–14% | Types: Heatpump (171), Gas (18), Oil (8), OtherRenewable/NonRenewable (2) |
| Building | house_size_sqm, house_built_year, num_inhabitants | **0.4–0.6%** | Unusable for training. Optional input only. |

**Missing entirely:** address/postcode, roof area/orientation/tilt (except existing PV), shading, **any prices**, which option was signed, the module count limit of the roof, and the planner's time spent.

### 2.3 Columns — parts (15) and the traps in them

`project_id, option_id, option_number, technology {solar, ses (storage), wallbox, heatpump}, line_item_function, component_type, component_name, component_brand, quantity, quantity_units, module_watt_peak, inverter_power_kw, battery_capacity_kwh, wb_charging_speed_kw, heatpump_nominal_power_kw`

| Trap | Evidence | Fix in ETL |
|---|---|---|
| **Unit lies**: "_kwh/_kw/_kwp" are W/Wh | `storage_size_kwh=10000`, `solar_size_kwp=10000`, `wallbox_charge_speed_kw=11000` | divide by 1,000 |
| `energy_demand_wh` is Wh, `energy_price_per_wh` is €/Wh | 4,500,000 Wh, 0.00039 €/Wh = 0.39 €/kWh | convert to kWh and €/kWh |
| **Swapped columns**: battery capacity sits in `inverter_power_kw`; inverter power sits in `battery_capacity_kwh` | "Battery 7kWh" → inverter_power_kw=7000; "Hybrid Inverter 10kW" → battery_capacity_kwh=10000 | remap by component_type |
| Rounded spec values | "PV Module 463W" → 450; "Heat Pump 12.5kW" → 12000 | parse the **name** first (regex), the column as fallback |
| Module lines almost absent at inst. 2 (4 rows!) | | module count = qty of `Substructure …` or `DC Install …` (both per-module); kWp = count × Wp (450 W default, flagged) |
| Packages carry sizes in the name | "10.8kWp + 9kWh" | regex `(\d+(\.\d+)?)kWp \+ (\d+(\.\d+)?)kWh` |
| Mixed `heating_existing_cost_per_year` | values 0.76–1.53 next to 1,000–4,000 | <10 means a unit price, not an annual cost |
| Encoding | `°` breaks UTF-8 | read with `latin1` |
| Derived, not measured | existing-HP rows: heat demand = **exactly 3.5 ×** electricity; gas rows: cost ≈ 0.122 €/kWh × demand | treat as one signal, never two features |
| Non-component lines | ServiceFee, InstallationFee, "All-Inclusive Package", "Optional PV Insurance" | keep for BOM templates, exclude from sizing |

### 2.4 Hidden signals we can mine from part names (free features)

- **Roof type** from substructure/DC lines: concrete tile ≈ 45%, clay tile ≈ 25%, flat (incl. E/W) ≈ 8–10%, metal/trapezoid/standing seam, bitumen, slate, beaver tail. Pitch hints: ">30°", "<30°", "<15°". This drives the homeowner house picture and the mounting BOM.
- **Shading proxy**: power optimizers per module (285 options at inst. 2).
- **Backup preference**: "Emergency Power Gateway", "Transfer Switch", "EPS Box".
- **Old electrics**: "Meter Cabinet Replacement" (cost driver, 30%+ of inst. 2).
- **Building height**: scaffolding m².
- **Existing solar thermal**: "Removal of Solar Thermal System".
- **HP bundle** (always together): heat pump + 200 L buffer + 300 L hot-water tank + hydraulic station + smart controller.

> Leakage rule: anything mined from parts is **output** information. Roof type is the one exception, because the planner knows it at design time (site visit/3D). We use it as an *optional planner input* and report metrics with and without it.

### 2.5 What experts actually do (first findings)

| Finding | Inst. 1 | Inst. 2 | Implication |
|---|---|---|---|
| Median kWp | 10.8 | 9.0 | |
| Median battery | 9 kWh | 7 kWh | |
| Battery attach rate | 97% | 88% | "No battery" is rare but real. It must be predictable. |
| Wallbox attach | 22% | 27% | 54–67% if EV |
| Heat pump attach | 0% | 1.9% | Only with **Gas/Oil** heating: ~40% of those (n≈23) |
| corr(demand, kWp) | 0.24 | 0.45 | **Demand explains little.** Roof size and packages dominate. |
| kWp per MWh demand | 2.25 | 1.93 | Installers fill roofs (HTW's economic optimum is lower) |
| Battery kWh per kWp (median) | 0.93 | 0.93 | The classic "1 kWh per kWp" rule. Above HTW's guidance (≤1 kWh/kWp, ≤1–1.5 kWh per MWh demand). That is an explainable expert-vs-physics gap. |
| Multi-option projects | 6% | 22% | Variants differ in **battery (46–55%)** more than **kWp (24–40%)**. That is the template for our homeowner variants. |
| Existing PV (n=18) | – | mostly **battery-only retrofit** (~5 kWh, 4 lines) or extension | dedicated "retrofit mode" |
| Existing HP (n=171) | bigger battery (12 vs 9) | bigger kWp (10.35 vs 9.0) and battery (10 vs 7) | the coupling is visible in the data |
| HP size vs heat demand | – | kW ≈ heat demand ÷ 2,000–2,500 h, snapped to {5, 7, 10, 12} | matches the full-load-hours rule from literature |
| **No PV at all** (primary option) | 5% | **~25%** | battery-only / wallbox-only / retrofit offers. At inst. 2, 245 of 391 projects with exactly 4,500 kWh are PV-less: the planner didn't enter demand because it wasn't a PV job. **`demand_is_default` vs has_pv: Spearman −0.53, the strongest signal.** We need a P(PV) gate and a "retrofit / storage-only" intent |
| Wallbox without recorded EV | – | ~75% of wallboxes | EV flag misses most wallbox buyers. The wallbox stays a rule plus an explicit planner question ("EV planned?") |
| Request → offer (median) | **8.2 days** (n=257) | 16 h (n=18) | business-impact number |
| Offer → signed (median) | 29 days | 20 days | |

---

## 3. Answers to your open questions

### 3.1 "Which option was signed — does it matter?"
**Yes, medium importance, not a blocker.** About 1 in 5 projects at installer 2 has 2–10 options (e.g. the same PV with a 5, 10 or 15 kWh battery). For those projects "the expert design" is ambiguous. Plan:
- **Primary metric:** compare against the option with the lowest `option_number` (likely the main one; verify with Reonic).
- **Secondary metric:** "any-option match", meaning we count a hit if we match *any* option the installer offered. That is fair, because the installer considered all of them valid.
- **Bonus:** multi-option projects are our **training data for variants**. They show how this installer spreads alternatives, e.g. "same PV, battery ±5 kWh".
- Ask Reonic (one question, §17). If they know the signed option, it becomes the primary truth.

### 3.2 "If it has a build year, it's existing?"
Usually yes, but the data contradicts it here. At installer 1, all 5 "existing storage" rows were built in **2025/2026**, have no existing PV, and the battery sold has the **same size** (10→10, 10→9, 5→5, 9→9). That looks like the *planned* system was typed into the status quo, or the battery was installed by this same project. If we trust it, the model "cheats" (data leakage).
**Rule:** `existing = built_year < offer_year` → trusted. `built_year ≥ offer_year` → flagged "ambiguous". These are dropped from training features and evaluated both ways. Same rule for `solar_built_year`. Ask Reonic.

### 3.3 "Will cached data be outdated? Can it break on their private test?"
Layered resolver, **cache first, live second, bundled fallback third**:

```
request PV profile (lat, lon, tilt, azimuth)
 → memory cache → disk cache (.cache/pvgis/…json)
 → live PVGIS (3 s timeout)               [skipped when OFFLINE=1]
 → bundled reference profile (committed)  ← always works, flagged source="fallback"
```

- **Their test cannot break on missing location data:** the dataset has **no address**, so evaluation always uses the bundled German reference profile anyway. `OFFLINE=1` makes eval deterministic (same input, same score).
- **Staleness by data type:**
  - *Solar irradiance* (PVGIS TMY = typical year built from 2005–2023 climate). It does not go stale in any way that matters.
  - *Load shapes* (BDEW H0, HTW). Structural, stable.
  - *Tariffs and prices* **do** go stale. They live in `config/market.json` with an `as_of` date and a source link. The project's own price (in the data) always wins. Installers override in their library, and the UI shows "prices as of Nov 2026".
  - *Rules* (feed-in rate, Solarspitzengesetz, §14a) live in the same config with dates.
- **Robust to schema drift:** pydantic input models with defaults. Unknown columns are ignored, missing columns are imputed with a provenance flag. A hidden test set with the same schema runs through `eval/run.py --data <dir>` unchanged.

**Other data sources we need** (all free, all cached): PVGIS TMY (PV hourly), BDEW H0 profile (demandlib / R `standardlastprofile`, CC0), When2Heat (hourly heat demand + COP curves, OPSD), DWD/PVGIS temperature (in the TMY), Stromspiegel (kWh by household size, for missing demand), EEG feed-in rates, KfW 458 subsidy rules, market price ranges (§9.6). Optional for testing: MaStR, WPuQ, HTW load profiles (§11).

### 3.4 "What exactly do we simulate, and why?"
See §6.3. In one line: **we simulate so the engine can see what a planner sees in their head.** A bigger battery helps less if the family is home all day. A heat pump adds load mostly in winter, when solar is weak. An EV charged at 19:00 needs a battery or smart charging. Without simulation, the ML can only copy averages. With it, the engine can say *why*, and stay sane for homes unlike the training data.

### 3.5 "Claude/Haiku JSON or our own ML?"
**Both, with strict roles.** The brief says a single ungrounded prompt "will not reproduce expert decisions reliably". So:

| Job | Tool | Why |
|---|---|---|
| Component decisions + sizes | Gradient boosting (LightGBM) + kNN, trained on the CSVs | small tabular data; fast; measurable; monotone constraints |
| Plausibility, coupling, savings | Our numpy hourly simulation | physics, not guesses |
| Choosing the final bundle | Joint optimizer (exhaustive over catalog, ~500 candidates, <100 ms) | GA unnecessary: the search space is small enough to enumerate |
| Explanation text | Claude Haiku, fed only our reason-code JSON; numbers checked after generation; template fallback | plain language without invented facts |
| Free-text refinement ("EV next year") | Claude Haiku with structured output → **JSON patch on inputs**, shown before applying | natural language, but the engine still decides |
| Bill / notes extraction (stretch) | Claude Haiku (vision) → input fields with "extracted" provenance | removes typing |

---

## 4. Stakeholders — wants, needs, fears → design answers

| Who | Wants | Needs | Fears | Our answer |
|---|---|---|---|---|
| **Planner** (primary user) | a solid first design *right away* | full override; final say; speed between site visits (mobile) | a black box they can't justify; looking stupid in front of the customer; rework | instant draft; every number has a "why" + similar past projects; lock and edit; validation flags before sending; export in Reonic's own BOM format |
| **Installer company** (buyer) | more offers per planner, higher win rate | consistency junior↔senior; their products and margins | margin erosion; wrong offers → complaints; one more tool to learn | learns *their* catalog and style; margin per category; plugs into Reonic workflow; zero setup (catalog inferred from history) |
| **Homeowner** | understand the offer; try variants | plain language; safety; fixed home data | being **oversold**; wrong system; hidden costs; tech jargon; regret | max 3 variants; diminishing-returns curve; "homes like yours"; robustness note; transparent 4-line price breakdown; no datasheets unless asked |
| **Reonic** (jury + platform) | AI that fits their OS | data contract compatibility | demo-ware | same input schema, same BOM output schema, honest metrics and limitations |

Conflict rule (brief asks us to state it): **We favour the planner.** The homeowner only sees and changes what the planner allows, and home data stays fixed.

---

## 5. Research base

### 5.1 Reonic's product (public docs, docs.reonic.com)
- Planning: 3D roof from Google Solar / drone photogrammetry / OSM; **"Optimize Layout" fills 80–90% of the final layout**; shading heat-map per panel ("Reonic Score 0–10").
- Simulation: dispatch **PV → household → battery → grid** in short intervals (15-min synthetic load curve), typically 20-year horizon; defaults **€0.30/kWh, 5% escalation**; feed-in override per offer (e.g. post-EEG).
- Heat pump: heat-load methods (simple simulation, indication, room-by-room DIN EN 12831), dimensioning table, **bivalence temperature with heating rod**, existing-heating card (type + kWh or €/yr; fuel price defaults in settings).
- EV: demand only if the variant has **wallbox + vehicle**; assumes solar-surplus charging; one vehicle for residential.
- Offers: **variants**; "Quick Planning" (price-only offer from a few inputs); PV packages with **linked amounts**; AI features: read consumption from a bill, **check a project against company rules before sending**, compare a competitor offer, AI circuit plan.
- No public Reonic code repository was found.

**Implication:** our engine is the missing "Quick Planning, but expert-quality" step *before* 3D planning. Our validation view mirrors their "check before sending". We reuse their conventions (load-profile names, variants, linked amounts) so it feels native.

### 5.1b How installers actually work (full evidence: [research/installer-workflow.md](research/installer-workflow.md))
- **Pipeline:** lead → call → data collection (bill, photos, meter cabinet) → site visit or remote roof → design → offer → follow-up → signing → grid registration / MaStR / meter cabinet → procurement → install → commissioning. **The slowest steps come after signing:** grid review up to 8 weeks, meter change 4–12 weeks.
- **Market pressure:** E-Handwerk PV installs ~355k (2025) vs ~395k (2024, ZVEH). 2024 interviews report price dumping. Speed and clarity of offers matter more than ever.
- **Evidence gap:** no independent German numbers on hours per offer or conversion rate (only vendor claims: ~4 h manual, Reonic "30 min"). **Ask the Reonic experts and any installer on site.** This is the impact slide.
- Consumer guidance (Verbraucherzentrale NRW) tells homeowners to demand an itemized offer, *usable* battery kWh, a site visit and sceptical payback assumptions. Our homeowner view should pass that checklist by design.
- One finding to double-check: the agent read Reonic's docs as "simulation is PV-only, HP/wallbox only priced". That contradicts the Reonic simulation articles on HP and EV demand (§5.1). Treat it as unverified.

**New requirements from this research (added to scope):**
1. **Meter cabinet (Zählerschrank) as an explicit input + cost line** (default "unknown → flagged"), since it is a top delay and cost driver (it's in 30%+ of inst. 2 options).
2. **"Confirm on site" checklist** generated from low-provenance inputs (roof capacity, meter cabinet, shading, heat-load basis).
3. **Usable battery kWh** shown, not just nominal.
4. **Conservative assumptions by default** (escalation, yield) with visible values. The homeowner sees them under "Annahmen".
5. **Grid-registration data package** (kWp, inverter, storage, wallbox/HP §14a) as an export. Stretch: pre-filled form fields.
6. Brand/availability constraint: the engine only proposes products the installer has in the library.

### 5.2 Competitors (what to steal, what to avoid)

| Product | Strength | Weakness / lesson |
|---|---|---|
| Aurora Solar (US) — Sales Mode, AutoDesigner | guided iPad flow; auto design from **energy offset target or max fit**; 4 ways to enter consumption | heavy; US-centric; add-ons |
| OpenSolar — Ada | AI auto-designs **multiple systems**; customer-driven interactive proposal (explore options and payment plans with live savings) | proposal can overwhelm |
| autarc (Berlin, YC S24) | LiDAR heat-load scan; vendor claims 10–12 h saved per HP project | HP-only focus |
| Zolar / Otovo | enquiry/address → auto design → configurator link by email (Otovo address-based; Zolar flow unconfirmed) | consumer-led, little installer control |
| SolarEdge Designer / PV*SOL | deep engineering | slow, expert-only |
| 1KOMMA5° Heartbeat, Enpal | consumer apps with live energy-flow visuals | post-sale; but the energy-flow metaphor is familiar to homeowners |
| Productivity tools (Linear, Figma, Superhuman) | command palette, keyboard-first, instant feedback, property panels, undo | apply to the Design Studio |

**Idea crossover (the "genetic" pass):**
- Aurora's *target-based auto design* + OpenSolar's *multiple systems* + data-learned installer style = **3 expert-like variants auto-generated in that installer's style.**
- Reonic's *linked amounts* + Figma's *property panel* + **lock pins** = edit one thing, the rest follows, nothing jumps unexpectedly.
- OpenSolar's *size switcher* + HTW's *diminishing-returns research* = the homeowner **"why this size" curve** with the recommended point marked.
- Reonic's *check before sending* + kNN *example-based explanation* = **validation flags with "5 similar homes you designed"**.
- Linear's *Cmd+K* + Claude structured output = **"Tell the engine what changed"** command bar that shows a JSON-patch preview.

### 5.3 Science and standards we use

| Topic | Finding | Use |
|---|---|---|
| Battery sizing (HTW Berlin, Weniger/Quaschning) | normalize by demand: p = kWp/MWh, s = kWh/MWh (Weniger et al., EU PVSEC 2014); usable storage ≤1 kWh/kWp and ≤1–1.5 kWh per MWh demand; beyond ~1.5 kWh/MWh the autarky gain is insignificant (Weniger 2013) | physics prior + validation flag "unusually large battery" |
| Self-consumption simulation | hourly/15-min energy balance is standard (Reonic, PV*SOL, HTW) | §6.3 S1 |
| HP sizing from consumption | heat load kW = (fuel kWh × boiler efficiency) ÷ full-load hours; 1,300–1,600 h renovated, 1,800–2,200 h unrenovated, ~2,000 typical; oil ≈ 10 kWh/l | §6.3 S2; matches data (÷2,000–2,500) |
| HP efficiency (Fraunhofer ISE "WP-QS im Bestand", final report Nov 2025, 77 systems) | 61 air-water: mean SPF **3.4** (2.6–4.9); heating rod 1.3% of electrical work; many systems oversized | SCOP default 3.4; Reonic data uses 3.5 |
| HP hourly shape | When2Heat: hourly heat demand + COP time series for DE | §6.3 S2 |
| Household demand when missing (Stromspiegel) | single-family home: 1p 1,800 · 2p 2,700 · 3p 3,500 · 4p 3,800 · 5p 4,500 kWh (+ elec. hot water ≈ +17–33%) | imputation |
| EV | 13.4–29.7 kWh/100 km (ADAC); charging losses: 11 kW wallbox 5–10%, household socket 10–30% (EnBW) | 18 kWh/100 km incl. losses default; home share 70% |
| Feed-in 2026 | ≤10 kWp partial feed-in **7.70 ct/kWh from Aug 2026** (Bundesnetzagentur); −1%/half-year; draft to end the fixed tariff for <25 kWp from 2027 (not law yet) | config with `as_of` |
| Solarspitzengesetz (since 25 Feb 2025) | no remuneration during negative prices for new systems; 60% feed-in cap without smart meter | battery + EMS value; simulated curtailment |
| §14a EnWG | controllable HP/wallbox get reduced grid fees; module 2 = −60% energy rate with a separate meter (~€240/yr at 5,000 kWh HP) | HP economics |
| KfW 458 | Merkblatt 09/2026: 30% base + 16% speed bonus (−4 pts from 01.02.2027) + income bonus 40/30/10% (≤€30k/40k/50k); cap 70% (80% at ≤€30k income); eligible costs €28,000 first unit | HP net price |
| Defaults (Jachimowicz 2019 meta-analysis, 58 studies) | defaults shift choices strongly, d = 0.68 | strong pre-filled defaults for the planner; **ethical** defaults for the homeowner |
| Choice overload (Chernev et al. 2015, contested effect) | overload grows with set complexity and preference uncertainty | ≤3 variants for homeowners |
| Compromise effect (Simonson 1989, JCR) | middle option gains share | "recommended" goes in the middle **only if it truly is our recommendation**, otherwise it is manipulation and feeds the oversold fear |
| Explanations (Chen, Liao, Vaughan, Bansal 2023; exploratory, n=26) | **example-based** explanations reduced over-reliance; feature-based ones didn't | "similar homes" panel |
| Cognitive forcing (Buçinca 2021) | reduces over-reliance but users dislike it | use only for red flags (one-tap reason to override) |
| Response time (Doherty & Thadani 1982; secondary sources) | <400 ms keeps users in flow | recompute <300 ms; optimistic UI |
| Conformal / quantile regression (Romano 2019, MAPIE) | calibrated prediction intervals | confidence bands that are honest |

---

## 6. Engine design

### 6.1 Pipeline

```
raw CSV ─► ETL normalize ─► canonical Project + Option tables (+ derived sizes, roof, flags)
                                │
inputs (planner) ─► impute w/ provenance ─► features ─► Policy models (P(component), size quantiles, kNN)
                                │                              │
                                └──► Simulator (hourly, 20y) ◄─┘
                                              │
                         Joint optimizer over catalog candidates (locks/constraints)
                                              │
                         Proposal + 2 alternatives + confidence + flags
                                              │
                    BOM generator (installer templates)  ─►  Explanation (reason codes → Haiku/template)
```

### 6.2 ETL (owner: Rhythm; prototype in `research/derive_features.py`)
Per option: `n_modules, module_wp, kwp, battery_kwh, inverter_kw, has_wallbox, wallbox_kw, hp_kw, has_buffer, has_dhw_tank, roof_type, pitch_hint, has_optimizers, has_backup, has_meter_cabinet, n_lines, technologies[]`. Per project: unit-fixed inputs, `demand_is_default`, `existing_*_trusted`, `fuel_kwh`, `heat_demand_kwh`, `hp_elec_existing_kwh`. Output: `data/processed/*.parquet` (gitignored) + `catalog_<installer>.json` (products actually used, with frequency).

### 6.3 Simulations: what, how, and the decision each one informs

| # | Simulation | How (default assumptions) | Decision it informs |
|---|---|---|---|
| **S1** | **Hourly household energy balance** (8,760 h) | PV profile (PVGIS TMY, reference DE location, south 35° unless known; E/W ≈ 85% yield) × kWp; load = BDEW H0 (or profile family) scaled to annual kWh; battery greedy dispatch (Reonic order), usable 90%, 95% one-way efficiency, 0.5C | battery yes/no and size; kWp returns; self-consumption & autarky for explanations |
| **S2** | **Heat pump** | fuel kWh × efficiency (gas cond. 0.95, old 0.80, oil 0.85; oil l × 10) → heat demand; heat load = demand ÷ full-load hours (2,000 h default, building-age adjusted); hourly heat from temperature (When2Heat shape); COP(T) curve normalized to SCOP 3.4; hot water 18% flat; heating rod below bivalence −7 °C | HP size (snap to catalog); HP vs gas running cost; **how the HP changes PV/battery** (winter load → less PV gain than expected) |
| **S3** | **EV** | km/yr × 18 kWh/100 km × 70% home; weekday arrival 18:00 / departure 07:30; modes: dumb (evening), **solar-surplus** (smart wallbox), home-office | wallbox; battery +; PV +; value of smart charging |
| **S4** | **Existing systems** | existing PV & storage included in the *baseline*; new system evaluated **incrementally** (AC-coupled retrofit, extension); EEG end = built_year + 20 → post-EEG value | retrofit mode: battery-only vs PV extension vs nothing; no double counting |
| **S5** | **20-year economics** | project's price & escalation; feed-in from config; negative-price hours; 60% cap without smart meter; §14a for HP/wallbox; PV degradation 0.5%/yr; battery capacity fade; market prices (§9.6) | savings/yr, payback, NPV (explanations, homeowner view, "fair size" check) |
| **S6** | **Uncertainty / scenarios** | Monte Carlo (n≈64) over uncertain inputs: demand ±20% if default-like, escalation 2–5%, EV adoption, HP later | **robust choice** (minimax regret) + confidence; "still a good choice if…" sentence |
| **S7** | **Backtest replay** | run every held-out project through the engine | the proof (§10) + deviation analysis (where experts ≠ physics) |

**Upgrades from research** (evidence: [research/battery-and-simulations.md](research/battery-and-simulations.md)), ranked by value for effort:

| # | Upgrade | Why |
|---|---|---|
| U1 | **Load variety:** run S1 over a set of realistic profiles (HTW 74 households, aggregated to hourly) instead of one smooth H0 curve | a smooth H0 *overstates* self-consumption; hourly resolution itself is fine for sizing (Beck 2016) |
| U2 | **Dispatch modes:** greedy vs forecast-based charging; negative-price hours unpaid; 60% feed-in cap without smart meter | Solarspitzengesetz; forecast charging also halves time at 90–100% SoC (less aging) |
| U3 | **Battery reality in S5:** LFP, ~92% usable, DC efficiency ~95.7%, discharge path ~95.2%, standby ~13 W (HTW Inspektion 2024), fade ~2–3 pp/yr (RWTH, Nature Energy 2024), inverter replacement ~year 12–15 | honest 20-year money |
| U4 | **Plausibility guards:** full cycles/yr (target 150–350, <150 = oversized), usable kWh ≤ 1.5 × kWp, battery ≤ sunset-to-sunrise load | validation flags with physics behind them |
| U5 | **Inverter clipping + orientation split** (E/W clips ~1.1% vs south ~9% at the cap) | inverter sizing, E/W roofs |
| U6 | **Heating rod / hot-water surplus** | cheap self-consumption lever, a "no bigger battery needed" explanation |
| U7 | **§14a curtailment** for HP/wallbox | rule compliance |
| U8 | Surrogate model for fast Monte Carlo | only if S6 is too slow |
| U9 | Backup power, grid connection limits, V2H | last; flag as "talk to your installer" |

**Battery sizing method (answer to "isn't it smallest size that does the job?"):** there is no formal "knee standard", but HTW's results support it:
- 1 kWh of battery per MWh of demand lifts autarky from ~30% to ~56%. Beyond ~1.5 kWh/MWh the gain is insignificant, because a big battery is "not empty by the next morning" (Weniger 2013).
- The *economic* optimum is smaller, ~0.5–1.1 kWh/MWh depending on battery price.
- Our rule: **economic optimum, capped by the nightly (sunset→sunrise) load and a 150–350 cycles/yr band. Max autarky is shown as a separate variant**, never as the default.
- **EV:** solar-surplus charging adds ~25 pp solar share vs ~9 pp from a battery (HTW/Fronius 2025, 730 households). So **don't upsize the battery for the car**; propose smart charging first.
- **Dynamic tariffs:** arbitrage does not materially change household battery size. Model them only in economics.
- **Heat pump:** lowers autarky (≈59% vs 73%) and raises optimal **PV** more than optimal battery.
- Schopfer et al. 2018 (Applied Energy 223) confirm that load-profile shape drives profitability most, and they trained an ML predictor of optimal configuration. That is a direct precedent for our approach.
- **Expert-vs-physics:** installers in our data sit at ~0.93 kWh/kWp (≈1.7–2 kWh/MWh), above the economic optimum. The engine reproduces the expert by default (that's the brief) and flags the marginal value honestly. This is our deviation-analysis story.

Performance: vectorize S1 across battery sizes (one pass over 8,760 h for a candidate vector) → ~500 candidates in <100 ms in numpy. Cache by input hash.

### 6.4 Learned installer policy (the "decides like an expert" part)
- **Component gates** (classification, calibrated): `P(battery)`, `P(wallbox)`, `P(heat pump)` — HP gate is *structural*: only if heating ∈ {Gas, Oil, OtherNonRenewable} and not existing HP.
- **Sizes** (quantile regression p10/p50/p90, conformalized): kWp, battery kWh, HP kW. Chain them: the battery model sees predicted kWp; the kWp model sees EV/HP flags.
- **Features (small, on purpose):** demand_kwh, demand_is_default, load_profile, has_ev, ev_km, heating_type, heat_demand_kwh, hp_elec_kwh, existing PV kWp/age (trusted only), existing storage (trusted only), price, escalation, flex_tariff, **installer_id**, optional roof_type, + **physics features** (S1 economically optimal kWp/battery for this home) = physics-informed ML.
- **Anti-overfit:** shallow trees (depth ≤4, ≥20 samples/leaf), monotone constraints (kWp ↑ demand, battery ↑ demand/EV/HP), grouped CV by customer, time split, leave-one-installer-out; installer as a categorical "style offset" with shrinkage to the global model.
- **kNN case base** (standardized features, k=7): "similar homes this installer designed" → example-based explanation + validation percentiles + OOD detector (large neighbor distance → lower confidence, weight physics more).

### 6.5 Joint optimizer (the coupling)
Candidates = catalog-feasible bundles {kWp in module steps (≤ roof max), battery ∈ installer battery steps ∪ {0}, HP ∈ catalog ∪ {0} if gate, wallbox ∈ {0,1}}, honoring **locks** and constraints (inverter DC/AC 1.0–1.3, battery ≤1.5 kWh/kWp, HP covers heat load at bivalence).

```
score(c) = log P_expert(c | home)        # how expert-like (from policy distributions)
         + λ · z(NPV(c), autarky(c))     # physics/economics from S1–S5 (+S6 robust)
         − penalties(rule violations)
```
- Proposal = argmax. **Alternatives** = best distinct candidates along the installer's typical variant axes (battery −/+ one step, PV max-fit), giving "Value / Recommended / More independence".
- λ is tuned on validation for match. Ablation λ=0 (pure imitation) vs λ→∞ (pure economics) is a great slide.
- Refinement: an input change re-runs everything except locked components; the response includes a **diff with reasons**.

### 6.6 BOM generator (the parts list)
Per installer, learn line-item templates from co-occurrence:
- **Always** lines (≥80% of options: e.g. grid registration, delivery, planning).
- **Per-module** lines × n_modules (substructure *of the roof type*, DC install, optimizers if shading flag).
- **Per-component** bundles (battery → install battery; wallbox → install wallbox + cable; HP → buffer 200 L + DHW 300 L + hydraulic station + controller).
- **Package mode** (inst. 1): if a package matches the size within one step, use the package line.
Output both as UI groups and as **CSV in exactly Reonic's `project_options_parts` schema** (integration story: our output is their input).

### 6.7 Explanations
Engine emits reason codes, e.g.
`{"code":"BATTERY_EVENING_LOAD","component":"battery","value":9,"evidence":{"evening_share":0.41,"autarky_gain_pts":18,"next_step_gain_pts":3}}`.
Haiku turns 3 codes into 2–3 sentences for planner (technical) or homeowner (plain German, "Sie"). A post-check ensures every number in the text exists in the JSON, otherwise the template is used. Cached by hash.

### 6.8 Missing / uncertain data
Imputation chain with **provenance** on every field: `entered > extracted(bill) > derived(other field) > installer default > national default`. Examples: persons → kWh (Stromspiegel); gas €/yr → kWh (fuel price); existing HP elec × 3.5 → heat; no roof info → installer's median module count as soft cap. Low-provenance inputs widen S6 ranges, and the UI marks them "estimated". **Minimum input for a good design:** annual kWh (or persons), heating type (+ bill), EV y/n, existing PV/storage. Everything else improves confidence.

---

### 6.9 Standout: "knows what it doesn't know" (pitch: docs/PITCH.md §6)
Why this one: the data's ceiling is *missing information* (near-identical homes get 5.4–12.6 kWp because roof and budget aren't recorded; 4,500 kWh placeholders; wallboxes without an EV flag). Every team will fight that with a bigger model. We turn it into the planner's workflow. No new screens: it is one list on the Studio and one curve on the offer.

**Ask next (value of information)**
1. Askable inputs: annual kWh (missing or placeholder-detected), roof capacity (modules), EV planned (y/n, year), heating fuel use (if fossil), existing PV/storage details, meter cabinet state.
2. For each one, take 3 plausible values from the installer's training distribution (p25/p50/p75 or yes/no) and re-run the policy (no simulation: ~20 ms each).
3. Score = how often the proposal changes (component set or ≥1 catalog step) × the price swing. Show the top ≤3 above a threshold: *"Ask: is an EV planned? It changes wallbox and battery (+€1,900)."*
4. Each item shows one question, one sentence of impact, and inline answer buttons. Answering re-designs with a diff bar.

**Oracle experiment (makes it measurable):** in the eval, replace a known answer by its "unknown" state, then restore it.
- Demand: swap real values with the 4,500 placeholder.
- EV: hide the flag.
- Roof: give the expert's module count as a *cap* — an upper bound, labelled as such.
The EMS / PV-within-tolerance gain per answered question is the pitch slide: "answering this one question is worth +N points".

**Honest second opinion:** expert-style battery + the simulator's economic optimum + the marginal value (already in /design via `physics` and R06). The planner chooses. The homeowner sees the curve.

## 7. Canonical data model (fields we need)

```ts
HomeInputs {                       // provenance: {source, confidence} on each
  installerId
  demandKwh, loadProfile ("H0"|"FamilyOfFour"|"HomeOfficeOnePerson"|…), persons?, homeOffice?
  priceEurKwh, priceEscalation, flexTariff?, basePriceMonth?
  ev: {has, kmPerYear?, plannedYear?, smartCharging?}
  existingPv?: {kwp, tiltDeg, azimuthDeg, builtYear, feedInEurKwh, trusted}
  existingStorage?: {kwh, builtYear, trusted}
  existingWallbox?: {kw}
  heating: {type: "Gas"|"Oil"|"Heatpump"|"OtherRenewable"|"OtherNonRenewable"|"Unknown",
            fuelKwh?, costEurYear?, hpElecKwh?, heatDemandKwh?, plannedSwitch?}
  building?: {sqm?, builtYear?, roofType?, roofMaxModules?, orientation?}
  location?: {lat, lon} | {postcode}
}
SystemDesign {
  pv: {modules, moduleWp, kwp, productId}?      inverter: {kw, productId}?
  battery: {kwh, productId}?                    wallbox: {kw, productId}?
  heatPump: {kw, productId, bufferL?, dhwL?}?
  locks: ("pv"|"battery"|"heatPump"|"wallbox")[]
}
Metrics { pvYieldKwh, selfConsumption, autarky, gridImportKwh, feedInKwh,
          savingsEurYear, paybackYears, npv20, priceEur, co2t?, hourlyTypicalDays }
DesignResponse {
  proposal: SystemDesign, alternatives: SystemDesign[], metrics: Record<id, Metrics>,
  confidence: {component: {p10,p50,p90, probIncluded}}, reasons: ReasonCode[],
  flags: Flag[] /* severity, message, percentile, similarIds */, similar: SimilarHome[],
  bom: BomLine[] /* Reonic schema */, provenance, engineVersion, latencyMs
}
SharePolicy { variantsVisible: id[], homeownerKnobs: {battery: "off"|"toggle"|"steps", wallbox, heatPump},
              houseStyle: "gable"|"hip"|"flat"|"shed", showPrices, expiresAt }
```

## 8. API contract (FastAPI, OpenAPI → `openapi-typescript` for the web)

| Endpoint | Purpose |
|---|---|
| `POST /design` | inputs + locks → DesignResponse (<300 ms p95 target) |
| `POST /simulate` | inputs + fixed system → Metrics (used by homeowner knobs) |
| `POST /validate` | inputs + planner's own system → flags + percentiles |
| `POST /intent` | free text + inputs → JSON patch preview (Haiku) |
| `GET/PUT /catalog/{installer}` | product library |
| `POST /share` / `GET /share/{token}` | homeowner-safe projection (no editable home data) |
| `GET /eval/latest` | eval results JSON for `/eval` page |

**Contract first:** agree on these schemas in the first hour. The frontend builds against JSON fixtures in `packages/contracts/fixtures/` while the engine catches up.

---

## 9. UX / UI

### 9.1 Principles (the anti-clutter contract)
1. **Draft first, edit by exception.** The planner never starts from a blank form.
2. **One primary action per screen, ≤3 headline numbers visible**; everything else is progressive disclosure.
3. **Everything explainable in one hover/tap**: value → why → similar homes.
4. **Nothing moves unless asked**: locks + diff bar + undo.
5. **<300 ms feedback** on every change (optimistic UI, skeletons never longer than 1 s).
6. **Feature budget:** if a control isn't used in the demo story or by ≥50% of planner sessions, it goes behind "More" or gets cut. Kill list: free 3D roof editor, CRM, chat bot, product search engine, PDF designer.
7. **Risk reduction is a feature:** flags before sending, provenance chips, data the homeowner can't break.

### 9.2 Planner views

**P1 — New project (Intake), 1 screen, ~6 fields**
`Annual consumption` (or persons) · `Heating` (segmented: Gas/Oil/Heat pump/Other + bill € or kWh) · `EV` (toggle + km) · `Existing PV/battery` (toggle reveals 3 fields) · `Roof type` (4 icons) · `Roof fits ≈ __ modules` (optional). Defaults pre-filled from installer history; each field shows a provenance chip (*entered / estimated / default*). Stretch: drop a bill photo or paste notes → fields fill in (Haiku), highlighted until confirmed. **CTA: "Design"** (Enter).

**P2 — Design Studio (the core, desktop 3-column)**
- **Left · Home facts** (compact, inline-editable; changing any → instant redesign).
- **Center · System cards** (PV, Battery, Heat pump, Wallbox). Each card has: value + stepper, on/off, **lock pin**, and a **"range rail"**: the slider track shows the p10–p90 expert band plus faint dots for the 7 most similar past projects ("ghost dots"). The planner sees at a glance whether a value is normal. Unusual value → amber/red rail.
- **Right · Impact**: autarky, savings/yr, price, payback (+ tiny typical-day chart), then **"Why"** (3 reason sentences), then **Similar homes** (expandable list, link to project).
- **Bottom · Diff bar** after every change: "Battery 9 → 12 kWh · +€1,150 · autarky +3 pts · because EV adds 2,400 kWh mostly in the evening". Undo/Redo (⌘Z / ⇧⌘Z), change history.
- **Scenario chips**: `+ EV next year` `+ Heat pump` `Home office` `+1 person` → one tap, animated diff.
- **Command bar (⌘K)**: "family is buying an EV next year" → preview "EV: yes · 15,000 km · from 2027 · smart charging" → Apply.
- **Flags tray** (validation): e.g. "Battery larger than 95% of similar homes (n=41); +6 kWh adds only +2 pts autarky." Actions: *Use suggestion* / *Keep — reason ▾* (backup power, customer wish, future EV). The reason is stored with the offer.
- **Tabs:** Design · **Parts list** (grouped, quantities linked to kWp, unit price, margin, export CSV/Reonic) · **Variants & sharing**.

**P3 — Variants & sharing**: pick 2–3 variants (auto-suggested), set the **homeowner knobs** (battery: off/toggle/steps; wallbox toggle; HP toggle; show prices y/n), pick the **house style** (Satteldach/gable, Walmdach/hip, Flachdach/flat, Pultdach/shed; preselected from the roof type in the BOM), preview in a phone frame, **Generate link + QR**.

**P4 — Validation mode**: same studio, opened on a planner-made design (import CSV / enter sizes) → flags first.

**P5 — Product library** (§9.6). **P6 — `/eval`** (§10.4).

### 9.3 Mobile planner (installer on site)
- Bottom tab bar: **Home · System · Impact · Share**. Sticky bottom summary (price · autarky · savings).
- System = horizontally **swipeable component cards** (snap). Large steppers (≥44 px), **long-press = lock**, tap value = bottom-sheet editor with a range rail.
- Gestures always duplicate a visible button (discoverability). No hidden swipe-only actions.
- **Haptics (`web-haptics`)** as progressive enhancement: `nudge` on stepper snap, `success` on link generated, `error` on a red flag. Never on every tap. Vibration API is unsupported on iOS Safari, so it degrades silently.
- Offline-tolerant: last design cached; recompute queued.

### 9.4 Homeowner preview (link/QR, stretch)
Order of the page, phone-first:
1. **House picture** of the chosen style with the system layered in (panels, battery, wallbox, HP appear/disappear with toggles). Pre-rendered Blender layers (WebP) are the robust default; GLB/three.js is the stretch.
2. **One sentence**: "Covers about 68% of your electricity and saves about €1,420 a year. Pays for itself in about 11 years."
3. **Variant switcher** (max 3 cards, installer-chosen, recommended highlighted *with the reason*), price + monthly saving each. Allowed knobs only (e.g. battery on/off).
4. **"Why this size?"** — the **diminishing-returns curve** (battery or PV size vs autarky/savings, the offer marked, "beyond this each extra kWh adds little"). This directly answers "am I being oversold?".
5. **"A day with your system"** — 24 h scrubber (summer/winter) animating sun → home → battery → evening. This is how homeowners grasp *why* a battery matters.
6. **"Homes like yours"** (aggregate, anonymized): "Most similar homes chose 8–10 kWh."
7. **"Still a good choice if…"** (S6 robustness): "…you use 20% more or less electricity."
8. **Price in 4 lines** (PV, battery, installation & services, subsidy), with "What's included" disclosure.
9. **"Ask your installer"** button (pre-filled question to the planner). No chatbot.
Language: German first ("Sie"), English toggle. No datasheets unless "Technical details" is opened. **Home data is shown read-only.**

### 9.4b Homeowner Q&A assistant ("Fragen zum Angebot"), stretch after 9.4
**Yes, but tightly grounded.** Its value: homeowners ask the same 10 questions (battery worth it? blackout? more consumption? lifespan? subsidy?). Answering them at 22:00 without the installer removes friction. Each question also tells the installer what this customer worries about.

- **Entry:** not the front door. A "Fragen?" button at the bottom of the preview plus 3 suggested chips ("Lohnt sich der Speicher?", "Was passiert bei Stromausfall?", "Was, wenn ich mehr Strom brauche?").
- **Model:** Claude Haiku with tool use, cached system prompt, temperature 0, max 6 tool calls per turn, cost cap per share link.
- **Tools (read-only except the last):**
  | Tool | Returns |
  |---|---|
  | `get_offer()` | the share projection: variants, sizes, prices (if shown), metrics, assumptions |
  | `simulate_variant(changes)` | metrics for a change **within the installer's allowed knobs only** (e.g. battery off/9/14 kWh). Rejects anything else. |
  | `marginal_value(component)` | the diminishing-returns data, rendered inline as the `MarginalCurve` |
  | `explain(metric)` | definition + how it was computed for this home (autarky, self-consumption, payback) |
  | `assumptions()` | inputs with provenance (what's measured vs estimated) and `as_of` dates for prices/rules |
  | `faq(topic)` | curated, dated snippets: backup power, battery lifespan/warranty, EEG/feed-in, Solarspitzengesetz, KfW 458, §14a, maintenance |
  | `ask_installer(question)` | forwards the question to the planner (shows "Ihr Planer antwortet in der Regel innerhalb von …") |
- **Guardrails:**
  - Every number in an answer must come from a tool result in the same turn. A post-check strips the answer back to a template if a number doesn't match.
  - No margins, internal notes, other customers' data or competitor talk. No legal, tax or investment advice beyond the offer's own numbers; those go to `ask_installer`.
  - It can't change the offer and can't promise discounts.
  - Homeowner text is untrusted input. Tool scopes, not the prompt, enforce what is possible.
  - The installer can switch the assistant off per share link.
- **Installer side:** questions asked appear in the planner's project as "Kundenfragen" (with consent text in the preview). This is a sales insight, e.g. "asked 3× about blackout → offer the backup gateway".
- **Same tool layer powers the planner's ⌘K bar**, so it is one implementation, two surfaces.
- **Eval:** 20 scripted questions incl. 5 adversarial ("give me a discount", "ignore your rules", "what's the installer's margin?"); pass = grounded numbers + correct refusals.

### 9.5 Explaining decisions without upselling
- Always show the **smaller honest option** (e.g. "Without battery") when the installer allows it, with what you lose.
- The recommended badge needs a reason code. No reason, no badge.
- The marginal-value number (next step adds X pts / €Y) is shown next to every size choice.

### 9.6 Product library and prices
- **Seeded automatically** from the installer's history (brands, battery steps, packages, typical service lines) plus **generic market items** with a price **range**, `as_of` date and source:
  PV turnkey ~€1,100–1,400/kWp (5–10 kWp, 2026) · battery €300–700/kWh installed (Verbraucherzentrale) · air-water HP ~€15,000–31,000 installed before KfW 458 (ADAC, via cleanthinking), more in old buildings · wallbox (to source). *(All 2026 web ranges, mostly vendor-published, so they are shown as ranges.)*
- UX: each item shows a **range bar (market low–high) with the installer's price as a pin**; one tap "use market median"; **bulk margin % per category** (installers think in margins); stale badge after 90 days.
- **No real-product search engine** (scope creep, can't verify). Stretch: "paste a datasheet/product name" → Haiku extracts specs into a draft item the planner confirms.

---

## 10. Testing & evaluation system (owner: iemko23)

### 10.1 Splits
1. **Temporal**: train on offers ≤ 2025-12-31, test 2026 (realistic deployment).
2. **Grouped 5-fold** by `customer_contact_id` (no duplicate homes across folds).
3. **Leave-one-installer-out** (cold start for a new installer: global model + inferred catalog).

### 10.2 Metrics
- Components: accuracy, F1, Brier score per component; **bundle exact match** (same set of components).
- Sizes: MAE & median abs. error (kWp, kWh, kW); **within tolerance** (kWp ±10% or ±2 modules; battery within one catalog step; HP within one size).
- Calibration: coverage of p10–p90 (target ≈80%).
- **Expert Match Score (0–100)** per project = 100 × mean(bundle match, kWp closeness, battery closeness, HP closeness), with closeness = max(0, 1 − |Δ|/tolerance-scale). Reported for primary option and any-option.
- Plausibility: % proposals violating physical rules (also run on the *expert* designs: "experts violate X in 7%").
- Speed: p50/p95 latency of `/design`.
- **Baselines**: B0 installer median bundle · B1 rule of thumb (kWp = 1.0–1.5×MWh, 1 kWh/kWp) · B2 physics-optimal NPV · B3 kNN · M1 GBM · **M2 hybrid (ours)**.

### 10.3 Test types
- **Golden cases** (10 hand-picked homes incl. no-battery, retrofit, HP, EV, huge demand) with expected ranges.
- **Property/invariant tests**: more demand never gives smaller kWp (unlocked); adding an EV never lowers wallbox probability; HP never proposed with existing HP; locked components never change; BOM quantities consistent with kWp.
- **Robustness**: missing columns, all-default inputs, extreme values, Slovenian row, public/synthetic homes (§11). No crash and plausible output.
- **E2E** (Playwright): intake → design → change input → share link opens.

### 10.4 Visualization (keep simple)
`make eval` → `eval/results/<git-sha>.json` + `latest.json` → `/eval` page: **big score** + **runtime** + n projects + delta vs previous run and vs best baseline; a small table per component; calibration bar; **worst 10 projects** (click → opens them in the Design Studio side by side with the expert design). That last one is the "analysis of where and why we deviate" stretch goal.

---

## 11. Public data to generalize and test (port to our schema with `source`)

| Dataset | What it gives | Use |
|---|---|---|
| **MaStR** (open-mastr, Zenodo dumps, DL-DE-BY-2.0) | every German PV unit (kWp, date, postcode) and storage unit (kWh) | market distribution priors; "are our sizes realistic for 2025/26?"; regional yields via postcode |
| **PVGIS** (JRC API / pvlib `get_pvgis_hourly`) | hourly PV per location/tilt/azimuth | S1; per-address live fetch |
| **BDEW H0** (demandlib / R `standardlastprofile`, CC0) | standard household profile, 15 min | S1 load |
| **HTW Berlin 74 profiles** (1 s, single-family homes) | realistic load variety | S6 scenarios; validate H0 assumptions |
| **WPuQ** (Schlemminger et al. 2022, 38 homes, HP + household separately, 2018–20) | real HP load curves | validate S2 HP shape |
| **When2Heat** (OPSD, Ruhnau) | hourly heat demand + COP for DE | S2 |
| **Tracking the Sun** (LBNL, US) | PV+storage sizes & prices | price/size sanity, out-of-market stress test only |
| **Synthetic generator** | sample homes from Stromspiegel/MaStR/heating-type shares | fuzz & plausibility tests (no labels needed) |

---

## 12. Architecture & repo layout

```
apps/web/                 Next.js (App Router), Tailwind, shadcn/ui, Recharts, framer-motion, web-haptics   [faris]
  app/(planner)/projects, /design/[id], /library, /eval
  app/(share)/s/[token]   homeowner preview
  public/house/<style>/<layer>.webp                                                                  [faris: Blender]
services/engine/          Python 3.12, FastAPI, pydantic v2, numpy, pandas, lightgbm, scikit-learn     [rhythm]
  etl/  sim/  models/  optimize/  bom/  explain/  api/  config/market.json  resources/(pvgis, h0, when2heat)
packages/contracts/       OpenAPI schema, generated TS types, JSON fixtures                             [kian]
eval/                     run.py, metrics.py, baselines.py, golden/, results/                           [iemko]
data/raw/ (gitignored)  data/processed/ (gitignored)  data/external/ (public, scripts only)             [iemko for external]
research/                 notebooks/scripts (derive_features.py)                                       [all, read-only for others]
docs/                     README, decisions, pitch deck outline, demo script                            [kian]
tools/board               agent board script (from hackathon-agent-board template)
AGENTS.md                 owners + rules (every agent reads this)
```

**Backend merge decision (Sat evening, after audit of `reonic-designer`):**
- **Kept/ported:** learned chain HP → PV → battery with teacher forcing and lock propagation; rules R01–R04 with IDs (locks are flagged, never changed); kNN validation + explanations; wallbox = EV rule (their CV showed no model gain); synthetic data for tests; sensitivity (option choice × module Wp), default-demand check, masked-input robustness; findings digest → `research/rhythm-findings.md`.
- **Replaced:** Streamlit UI (→ Next.js); empirical self-consumption curve (→ hourly simulator `engine/sim`); their ETL (→ ours, which also parses names, roof, trusted-existing, AC-coupling exclusion); guessed capex constants (→ sourced `config/market.json`).
- **Their recorded baseline to beat:** whole design within tolerance 13.5% (random split) vs rule of thumb 3.8%; unseen installer 18.5% / 9.8%.

**First real model results (Sat night, `npm run eval`):** EMS / PV within ±20%

| Split | B0 installer median | M1 learned chain | **H1 = learned PV + installer's usual battery** |
|---|---|---|---|
| temporal (2026 test) | 61.1 / 42.5% | 58.2 / 56.3% | **62.0 / 56.3%** |
| random 80/20 | 55.3 / 38.9% | 55.2 / 47.3% | **56.6 / 47.3%** |
| unseen installer 23c108b7 | 57.4 / 46.4% | 58.7 / 42.0% | **59.2 / 42.0%** |
| unseen installer 2a8ba8e2 | 51.2 / 33.3% | 51.4 / 37.1% | 50.9 / 37.1% |

Reading: the learned model clearly wins on **PV size** (+8–14 pts within tolerance). Battery choice is installer habit/packages (always included, usual size), and inputs barely move it (flat masking curve). **H1 is the engine default**, and battery *economics* come from the simulator as the explanation and the validation flag. Next model work: simulator features in M1 (S1 optimum), threshold tuning on a validation split, conformal calibration (PV interval coverage 64–75% vs 80% target).

**Merging the teammates' existing backend + frontend (incl. its rendering):**
1. Clone both into `_incoming/backend/` and `_incoming/frontend/` (gitignored, never imported directly).
2. Audit each file against a scorecard: *correct? tested? matches the contract? matches DESIGN.md? needed for the demo story?* → **Keep** (port as-is), **Port** (rewrite cleanly into the scaffold), **Inspire** (idea only), **Drop**.
3. Port only Keep/Port items into `services/engine` / `apps/web`, behind the §8 contract and the design tokens. The 3D/house rendering gets its own decision: if it renders reliably on mobile, it becomes the homeowner hero. Otherwise its Blender assets become pre-rendered WebP layers.
4. Delete `_incoming/` once ported. No parallel old/new code paths after Saturday evening.
5. Every port gets a test or a fixture, otherwise it's not "kept".

**Deployment & share links (gap found on review):** the QR code must open on a phone, so `localhost` won't do.
- Web on Vercel. Engine on one small container host (Render/Fly/Railway), or a `cloudflared` tunnel from a laptop as the backup plan.
- **Share = snapshot.** On "Generate link" the engine precomputes metrics for *every allowed knob combination* (e.g. battery off/9/14 × wallbox on/off = 6 combos, ms each) and stores one JSON. The homeowner page then needs **no engine at runtime**: fast, cheap, and the demo can't break on the jury's phone. Only the optional Q&A assistant calls the backend.
- Tokens are unguessable (128-bit), links expire, there is no customer name in the URL or page title, and `noindex` is set.
- No auth for the demo. An installer switcher (2 tenants) in the header stands in for login.
- **Override log:** every planner override + reason is stored. That is the future training signal ("the engine learns your style"), a strong business-impact line.

LLM: Claude Haiku (`claude-haiku-5-5`), structured outputs, prompt caching, temperature 0, response cache by hash, timeout 4 s → template fallback. **The demo must work with the API key removed.**

---

## 13. Team, ownership, agent board

| Person | Owns (folders) | First deliverable |
|---|---|---|
| **@Kian738** — UX & product glue | `packages/contracts`, `docs/`, AGENTS.md, demo script, deck | contracts v1 + fixtures (hour 1); UX copy; flow reviews |
| **@Rhythm02-byte** — engine | `services/engine` | ETL + baselines (hour 3); `/design` v1 (hour 6) |
| **@faris-el-mokhtari-svg** — frontend + Blender | `apps/web`, `apps/web/public/house` | Studio shell on fixtures (hour 4); house layers (Sun AM) |
| **@iemko23** — eval, tests, data sources | `eval/`, `data/external/`, `apps/web/e2e` | eval harness + baselines table (hour 6); `/eval` JSON |

Board protocol (from the Notion template): one pinned GitHub issue; every agent posts `[Name's Claude] what changed · what I need from @who`; each agent runs `tools/board wait` and acts only on its own tag or on posts touching its folders. Contract changes are announced on the board **before** merging.

---

## 14. Timeline (now → Sun 15:00)

| Window | Milestone | Done when |
|---|---|---|
| Sat → 19:00 | **M0 Foundations** | repo + AGENTS.md + board; contracts + fixtures; ETL normalized; B0/B1 baselines scored; Studio shell on fixtures |
| 19:00 → 24:00 | **M1 Minimum result** | S1 simulation; GBM gates + size quantiles; `/design` live; Studio wired; one input change → new design; eval v1 with temporal split |
| 00:00 → 06:00 (shifts) | **M2 Depth** | joint optimizer + locks + diff; S2 HP, S3 EV, S4 retrofit, S5 money; BOM generator + Reonic CSV export; reason codes + templates; flags |
| 06:00 → 11:00 | **M3 Delight** | homeowner share + QR + house layers; mobile layout + haptics; ⌘K intent (Haiku); `/eval` page; S6 robustness |
| 11:00 → 13:30 | **M4 Freeze** | feature freeze 11:00; final eval run; README (setup, approach, limitations); deck; **record fallback video** |
| 13:30 → 15:00 | Buffer | rehearse the 5-min demo twice; submit by 14:30 |

---

## 15. Demo script (5 minutes)

1. **(0:00) Problem:** "At installer 1, the median time from request to offer was 8 days." (That is elapsed time, not pure planner effort. Get the real hours from Reonic, §17 Q10.) One planner, many homes.
2. **(0:30) Describe a home** (pick a real held-out project for the demo): e.g. 4,800 kWh, gas heating 18 MWh, no EV, concrete-tile roof. Enter.
3. **(1:00) Complete system appears** in <1 s (sizes illustrative until the engine runs): PV, battery, heat pump, no wallbox; 3 reasons; similar homes; parts list in the installer's own products.
4. **(1:45) Refine:** ⌘K "family is buying an EV next year" → patch preview → apply → battery +, wallbox added, diff bar explains. Lock PV, change heating → only the unlocked parts move.
5. **(2:45) Validate:** planner bumps the battery to 20 kWh → red flag with similar homes and marginal value.
6. **(3:15) Homeowner:** generate QR → phone shows house, one sentence, 3 variants, "why this size" curve.
7. **(4:00) Reality check:** the same project's expert design side by side; then `/eval`: Expert Match Score on unseen 2026 projects vs baselines, calibration, runtime, worst cases with reasons.
8. **(4:40) Impact:** minutes instead of hours/days per offer, consistent junior designs, a homeowner who understands. Limitations, honestly stated.

---

## 16. Risks & known limitations

| Risk | Mitigation |
|---|---|
| Heat-pump data tiny (~23 fossil-heated projects, 31 HP lines) | structural gate + physics sizing (full-load hours) + catalog snap; report HP metrics with n and wide CIs |
| No roof size → kWp mostly roof-driven | optional "roof fits ≈ N modules" input; default from installer history; report error with/without roof type |
| Two installers only → style overfit | leave-one-installer-out; global model + style offset; physics weight for OOD |
| Defaults masquerading as data (4,500 kWh) | `demand_is_default` feature; wider uncertainty; UI says "estimated" |
| Module Wp unknown at inst. 2 | 450 W assumption flagged; evaluate in modules *and* kWp |
| Leakage (planned systems in status quo) | trusted-existing rule (§3.2) |
| LLM latency/outage | everything works without it; templates |
| Feature creep | §9.1 kill list; feature freeze 11:00 |
| Market prices uncertain | ranges + `as_of` + installer override; prices never used to *train* sizing |
| Data sharing rule | raw data gitignored; no public uploads; demo uses held-out projects |

---

## 17. Questions for the Reonic experts (ask first, cheap, high value)

1. Projects with several options: **which one was signed?** Is `option_number` 1 the main proposal? Do gaps in numbering mean deleted options?
2. `has_storage`/`has_solar` with `built_year` ≥ offer year: **existing, or the planned system** entered in the status quo?
3. `heating_existing_type = Heatpump`: is that an existing HP? Is `heating_existing_heating_demand_wh` derived with a fixed COP of 3.5?
4. Confirm the parts columns: battery capacity in `inverter_power_kw`, inverter power in `battery_capacity_kwh`, all in W/Wh?
5. Is 4,500 kWh (and 0.32 €/kWh, 3% increase) a **tool default** when the planner doesn't enter a value?
6. Can we get **prices** per line/option, **postcode**, or **roof capacity / module count limit** for some projects?
7. Installer 2 has almost no module lines: what module wattage do they typically use?
8. Is "All-Inclusive Package" a price line? Is a "Complete Package" the full system?
9. Will you evaluate on **hidden projects** with the same schema? From the same installers?
10. How long does a planner *really* spend per design today (for the impact slide)?

---

## 18. Sources

Reonic: [planning product page](https://reonic.com/en-gb/product/360h/planning) · [docs home](https://docs.reonic.com/) · [Offers topic](https://docs.reonic.com/docs/en/topic/offers) · [Energy consumption](https://docs.reonic.com/docs/en/category/offers-plan-energy-consumption) · [Plan PV](https://docs.reonic.com/docs/en/category/offers-plan-pv) · [Offers overview](https://docs.reonic.com/docs/en/category/offers-overview) · [Simulation](https://docs.reonic.com/docs/en/category/offers-simulation-cat) · [Energy flows](https://docs.reonic.com/docs/en/offers-simulation-cat-energy-flows) · [HP demand](https://docs.reonic.com/docs/en/offers-simulation-cat-demand-hp) · [EV demand](https://docs.reonic.com/docs/en/offers-simulation-cat-demand-ev) · [Existing heating](https://docs.reonic.com/docs/en/offers-plan-heat-pump-existing-heating) · [Heat pump planning](https://docs.reonic.com/docs/en/category/offers-plan-heat-pump)

Competitors: [Aurora Sales Mode](https://help.aurorasolar.com/hc/en-us/articles/4406006770067-Sales-Mode-Overview) · [Aurora consumption entry](https://help.aurorasolar.com/hc/en-us/articles/15684820148627-Entering-Customer-Energy-Usage-in-Sales-Mode) · [OpenSolar OS 3.0 notes](https://www.opensolar.com/?p=14518) · [OpenSolar Ada](https://support.opensolar.com/hc/en-us/articles/13785730896911-Using-Ada-Chat-and-Voice) · [autarc (pv magazine)](https://www.pv-magazine.de/2025/03/18/start-up-des-monats-autarc-software-legt-waermepumpen-und-photovoltaik-aus-und-erstellt-angebote/) · [1KOMMA5 Heartbeat](https://1komma5.com/en/offer/energymanager-heartbeat) · [Zolar](https://www.zolar.de/en) · [Aurora transparency research](https://aurorasolar.com/solar-sales-transparency-turns-skeptics-into-customers-research/)

Science/standards: [HTW storage sizing slides](https://solar.htw-berlin.de/wp-content/uploads/ZOLL-2023-PPT-Empfehlungen-zur-Speicherauslegung-im-Gewerbe.pdf) · [HTW Energy Storage Inspection 2022](https://cdn.shopify.com/s/files/1/0628/8041/5974/files/HTW-Energy-Storage-Inspection-2022.pdf) · [HTW load profiles](https://pvspeicher.htw-berlin.de/wp-content/uploads/Repräsentative-elektrische-Lastprofile-für-Wohngebäude-in-Deutschland-auf-1-sekündiger-Datenbasis.pdf) · [HTW solar EV charging](https://solar.htw-berlin.de/wp-content/uploads/HTW-Solares-Laden-von-Elektrofahrzeugen.pdf) · [Fraunhofer ISE HP field test](https://www.ise.fraunhofer.de/de/forschungsprojekte/wp-qs-im-bestand.html) · [Heizlast aus Verbrauch](https://www.haustechnikdialog.de/SHKwissen/1411/Heizlasten-in-Altbauten) · [greenox HP sizing](https://www.greenox-group.de/waermepumpe-dimensionieren-gasverbrauch/) · [WPuQ dataset](https://www.nature.com/articles/s41597-022-01156-1) · [When2Heat](https://data.open-power-system-data.org/when2heat/) · [open-mastr](https://open-mastr.readthedocs.io/en/develop/dataset/) · [MaStR quality](https://arxiv.org/html/2304.10581v2) · [pvlib PVGIS](https://pvlib-python.readthedocs.io/en/stable/reference/generated/pvlib.iotools.get_pvgis_hourly.html) · [BDEW profiles (R)](https://cran.r-universe.dev/standardlastprofile/standardlastprofile.pdf) · [Tracking the Sun](https://emp.lbl.gov/index.php/tracking-sun-2024-edition) · [MAPIE](https://mapie.readthedocs.io/) · [Romano et al. 2019 CQR](https://arxiv.org/abs/1905.03222)

Regulation/prices: [Einspeisevergütung 2026 (ADAC)](https://www.adac.de/rund-ums-haus/energie/spartipps/einspeiseverguetung-pv-anlagen) · [Solarspitzengesetz](https://ema-energiewelt.de/wissen/solarspitzengesetz-negative-preise-einspeiseverguetung) (60% cap: see ADAC link, §9 EEG) · [Feed-in rates (BNetzA)](https://www.bundesnetzagentur.de/) · [§14a EnWG](https://ema-energiewelt.de/wissen/netzentgelte-paragraph-14a-steuerbare-verbraucher-2026) · [PV costs 2026](https://42watt.de/magazin/photovoltaik-kosten) · [Storage retrofit](https://42watt.de/magazin/pv-speicher-nachruesten) · [HP costs 2026](https://www.cleanthinking.de/waermepumpe-kosten/) · [HP after subsidy](https://www.enter.de/blog/was-kostet-eine-waermepumpe-nach-foerderung) · [Stromspiegel values](https://www.co2online.de/energie-sparen/strom-sparen/strom-sparen-stromspartipps/stromverbrauch-im-haushalt/) · [EV consumption](https://www.enbw.com/blog/elektromobilitaet/wie-hoch-ist-der-stromverbrauch-von-elektroautos/)

Behaviour/UX: [Default effects meta-analysis](https://collaborate.princeton.edu/en/publications/when-and-why-defaults-influence-decisions-a-meta-analysis-of-defa/) · [Choice overload meta-analysis (Chernev et al. 2015)](https://doi.org/10.1016/j.jcps.2014.08.002) · [Compromise effect](https://doi.org/10.1086/209205) · [Cognitive forcing](https://arxiv.org/pdf/2102.09692) · [Example-based explanations](https://arxiv.org/html/2301.07255) · [web-haptics](https://dev.to/jqueryscript/webhaptics-haptic-feedback-for-the-mobile-web-3bc6)
