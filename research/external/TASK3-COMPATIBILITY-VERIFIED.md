## Summary (≤150 words)

Evidence audited **2026-11-07**; manufacturer documents below were actually opened. Selected German-demo inverter–battery families have documented pairings with model, module-count and firmware conditions. This does not certify a site's installation. The inspected engine implements numeric catalogue snapping, general sizing rules and a minimal catalogue-based BOM; its inspected design/validation paths do **not** implement these manufacturer pairing rules.

**Pitch NOW:** “We snap proposed sizes to installer catalogue steps and have researched manufacturer-documented inverter–battery pairings for the next validation layer.”

**Only after implementation and tests:** “Our engine checks supported inverter–battery combinations, module counts, firmware requirements and required accessories before producing the parts list.”

This note supplements, and does not overwrite, R4 or COMPATIBILITY.md. No private rows or raw data were accessed.

## Findings

### 1. Conditional pairings suitable for a narrow demo allowlist

**BYD Battery-Box Premium HVS/HVM, BCU2.0:** the manufacturer's V2.22 matrix, updated **2026-10-10**, gives these **single-tower** conditions. Columns are minimum inverter/BMU/BMS firmware; retain their exact version strings. These rows do not cover HVS+/HVM+/HVB or every inverter sharing the same brand. [Matrix, pp.1–2](https://site.bydbatterybox.com/uploads/downloads/BCU2.0_261010_BYD_Battery_Box_Premium_HVS%26HVM_Compatible_Inverter_List_V2.22-6ac9cfeb73807.pdf)

| Exact matrix inverter family | HVS modules | HVM modules | Inverter minimum | BMU / BMS minimum |
|---|---:|---:|---|---|
| Fronius Symo GEN24 Plus | 2–5 | 4–8 | 1.9.7-0 | 3.13 / 3.19 |
| GoodWe ET (5–10 kW) / BT | 2–5 | 4–8 | ARM 11 | 3.13 / 3.19 |
| SMA STP 5.0–10.0 SE | 2–5 | 4–8 | 3.00.02.R | 3.16 / 3.24 |
| KOSTAL PLENTICORE G3 | 2–5 | 3–8 | 3.03.20 | 3.13 / 3.19 |

Use the single-tower subset for this demo; parallel installations have separate conditions. Minimum versions are evidence fields, not a recommendation to install old firmware. Exact local inverter SKU and current commissioning instructions remain installer checks.

HVS steps are **5.12/7.68/10.24/12.80 kWh**, from 2–5 modules at 2.56 kWh. HVM steps are **8.28/11.04/13.80/16.56/19.32/22.08 kWh**, from 3–8 modules at 2.76 kWh. BYD calls these **DC usable energy**, measured at 100% DoD, 0.2C and 25°C; system usable energy can vary with inverter. They are not guaranteed AC-delivered energy. [HVS sheet, p.2](https://site.bydbatterybox.com/uploads/downloads/BCU2.0_BBOX_HVS_Datasheet_EN_V1.0_250328-67ee42d4ced21.pdf), [HVM sheet, p.2](https://site.bydbatterybox.com/uploads/downloads/BCU2.0_BBOX_HVM_Datasheet_EN_V1.0_250328-67ee3a426f6ce.pdf)

**Concrete rule example:** PLENTICORE G3 + three HVM modules is matrix-listed; Symo GEN24 Plus + three HVM modules is outside the listed count range. That is a pairing-specific difference, even though both are sold within the HVM family. This is a proposed rejection example, not a current engine behavior.

**Accessories/region:** BYD supplies an EU service contact, but the matrix is not a German installation approval. Budget controller/base/cables against the exact kit quotation; complete accessory SKUs are **UNVERIFIED** here. KOSTAL's German page separately identifies battery activation and power-extension codes: battery operation is an explicit BOM/licence consideration. Fronius' opened UK product guide requires a Smart Meter and switching equipment for Full Backup; German switching SKU approval remains **UNVERIFIED**, so the demo should promise ordinary grid-connected storage only. [KOSTAL activation](https://www.kostal-solar-electric.com/de/service-support/aktivierungscode/), [Fronius guide](https://www.fronius.com/en-gb/uk/solar-energy/installers-partners/service-support/tech-support/how-to-install/installation-guide-gen24?filter=3524&productid=e4c97f84-dd97-44a0-b4d3-b49f5ae83c6c)

### 2. Two additional ecosystems, with narrower verification status

**Huawei SUN2000-5/6/8/10/12K-MAP0 + LUNA2000 S1:** the MAP0 datasheet explicitly lists **7/14/21-S1**, and also **5/10/15-S0**. For a simple S1 demo use one LUNA2000-10KW-C1 controller and 1–3 **7-E1** modules. The S1 manual Issue09 identifies 6.9 kWh designed initial energy/module (derived totals 6.9/13.8/20.7); do not relabel the 7/14/21 names as exact measured usable AC energy. Its inverter table requires MAP0 **SUN2000MA V200R024C00SPC100 or later**. The newer **5-E1** option requires ESS **LUNA2000A V200R025C00SPC100 or later**; exclude it from the simplest allowlist. Battery-side minimum for the pure 7-E1 combination is **UNVERIFIED** here. [MAP0 sheet, p.2](https://solar.huawei.com/admin/asset/v1/pro/view/1895ef0ef0a64bd5ae353e422fbd4af4.pdf), [S1 manual §§2.1, 2.3, 9](https://info.support.huawei.com/Energy/info/en_US/solar/docView/EDOC1100339927)

MAP0 backup requires **SmartGuard-63A-T0** in the cited sheet. Local German SKU/release, meter/network topology and commissioning requirements still need confirmation; a global datasheet alone does not clear those. S0 is a documented pairing but its current firmware/accessory completeness is **UNVERIFIED** in this audit; do not silently apply S1 rules to it. [MAP0 sheet](https://solar.huawei.com/admin/asset/v1/pro/view/1895ef0ef0a64bd5ae353e422fbd4af4.pdf)

**SolarEdge European three-phase SE5K/8K/10K-RWB48 + BAT-05K48:** the inverter sheet explicitly permits **1–5 modules**. The 2025 German battery sheet specifies **BAT-05K48M0B-0***, **4.6/4.85 kWh usable/module**; 4.85 applies to new installations from **2025-01-01** with a three-phase Home Hub and Home Battery 48V. Five-module derived totals therefore depend on eligibility, rather than a universal 25 kWh claim. Neither opened sheet supplies a numeric minimum firmware; record **UNVERIFIED**, not “none required.” Backup may require additional components and firmware. This evidence concerns the **48V** ecosystem; the 400V battery is separate. [EU inverter sheet, p.2](https://www.solaredge.com/sites/default/files/se-solaredge-home-hub-inverter-three-phase-backup-datasheet-de.pdf), [battery sheet, p.2](https://knowledge-center.solaredge.com/sites/kc/files/se-solaredge-home-battery-48V-datasheet-de.pdf)

### 3. What this repository actually implements

Read-only audit of both design branches, learned policy/rules, simulator attachment, validation, BOM and contract. Source links are absolute workspace paths; line numbers describe the inspected checkout.

- `/design` delegates to `design`; the latter selects baseline or learned policy. Learned design calls `Designer.design`, then builds the numeric system and attaches simulation. [API:68](C:/Users/karim/Documents/Coding/thinc/services/engine/engine/api/main.py:68), [dispatch:310](C:/Users/karim/Documents/Coding/thinc/services/engine/engine/design.py:310), [policy service:396](C:/Users/karim/Documents/Coding/thinc/services/engine/engine/design.py:396).
- The learned catalogue comprises frequent numeric target sizes; `_run` applies `rules.apply_one`, which snaps unlocked sizes and applies general PV/battery/heating rules. Baseline likewise snaps battery sizes. This is not an allowlist of manufacturer pairs. [training:140](C:/Users/karim/Documents/Coding/thinc/services/engine/engine/policy/designer.py:140), [rule invocation:213](C:/Users/karim/Documents/Coding/thinc/services/engine/engine/policy/designer.py:213), [rules:47](C:/Users/karim/Documents/Coding/thinc/services/engine/engine/policy/rules.py:47), [baseline:105](C:/Users/karim/Documents/Coding/thinc/services/engine/engine/baseline.py:105).
- The contract permits optional inverter and battery product IDs, but has no module-count/firmware compatibility record. The proposal constructors set sizes without selecting an inverter or battery product ID. `/validate` reduces the system to numeric targets and checks R01–R05 plus neighbor statistics. Thus manufacturer pairing enforcement is **not implemented in these inspected request paths**. [schema:102](C:/Users/karim/Documents/Coding/thinc/services/engine/engine/models/schemas.py:102), [OpenAPI inverter:1359](C:/Users/karim/Documents/Coding/thinc/packages/contracts/openapi.json:1359), [constructor:378](C:/Users/karim/Documents/Coding/thinc/services/engine/engine/design.py:378), [validation:427](C:/Users/karim/Documents/Coding/thinc/services/engine/engine/design.py:427), [policy validation:285](C:/Users/karim/Documents/Coding/thinc/services/engine/engine/policy/designer.py:285).
- `_bom` picks nearest-sized battery/wallbox/heat-pump catalogue products and common service lines; it does not construct a verified inverter–battery/accessory bundle. Simulation attachment works with numeric energy sizes and can replace alternative battery sizes. Neither establishes hardware compatibility. [BOM:121](C:/Users/karim/Documents/Coding/thinc/services/engine/engine/design.py:121), [alternatives:274](C:/Users/karim/Documents/Coding/thinc/services/engine/engine/design.py:274).
- Energy semantics need reconciliation before importing these rules: current R05 uses a blanket **0.9 usable fraction**. Applying that to an already-usable BYD capacity would double-discount energy. [rules:20](C:/Users/karim/Documents/Coding/thinc/services/engine/engine/policy/rules.py:20).

## Implications for our product

- Start with one single-tower BYD family; store exact inverter family, BCU generation, module counts, firmware and source revision from the matrix.
- Keep nominal, manufacturer-usable DC and simulated AC energy distinct; eliminate blanket conversions where a manufacturer gives usable energy.
- Require explicit review for unknown product IDs, regional release or missing firmware evidence. Unknown does not mean incompatible or approved.
- Attach controller/base/cable/meter/licence requirements to exact kits; treat backup as a separate verified feature.
- After implementing rules, test the HVM three-module G3/Symo difference and unknown-pair behavior through `/design`, `/validate` and all alternatives.
- Use the NOW pitch sentence until that implementation and its tests exist; the sources support researched pairings, not installed-system certification.

## Open questions / uncertainty

FoxESS ECS/H3 revisions, SAJ B2/BU2/H2 revisions, Sigenergy controller/tower revisions, EcoFlow cross-generation products, Enphase system limits and Tesla expansion/backup configurations remain **UNVERIFIED** for this task. R4 catalogue presence is not compatibility evidence. Availability, exact German commissioning approvals and complete accessory quantities remain supplier/installer checks. No hardware, site/string design, firmware installation or runtime integration test was performed. No claim is made that every brand interoperates or that any home is installation-ready.

## Sources (numbered list: title — publisher — date — URL)

All successful sources below opened **2026-11-07**; pages/sections are identified above.

1. HVS/HVM BCU2.0 compatible inverter list V2.22 — BYD — 2026-10-10 — [PDF](https://site.bydbatterybox.com/uploads/downloads/BCU2.0_261010_BYD_Battery_Box_Premium_HVS%26HVM_Compatible_Inverter_List_V2.22-6ac9cfeb73807.pdf).
2. HVS BCU2.0 datasheet V1.0 — BYD — 2025-03-28 filename — [PDF](https://site.bydbatterybox.com/uploads/downloads/BCU2.0_BBOX_HVS_Datasheet_EN_V1.0_250328-67ee42d4ced21.pdf).
3. HVM datasheet — BYD — 2025-03-28 download filename; PDF metadata title instead says 241212 V1.4 — [PDF](https://site.bydbatterybox.com/uploads/downloads/BCU2.0_BBOX_HVM_Datasheet_EN_V1.0_250328-67ee3a426f6ce.pdf).
4. SUN2000-MAP0 technical specification — Huawei — 02-202406 — [PDF](https://solar.huawei.com/admin/asset/v1/pro/view/1895ef0ef0a64bd5ae353e422fbd4af4.pdf).
5. LUNA2000-S1 User Manual Issue09 — Huawei — 2026-06-30; page release 2026-07-28 — [Manual](https://info.support.huawei.com/Energy/info/en_US/solar/docView/EDOC1100339927).
6. Home Hub three-phase Europe DS-000112-DE — SolarEdge — 2024-02-01 — [PDF](https://www.solaredge.com/sites/default/files/se-solaredge-home-hub-inverter-three-phase-backup-datasheet-de.pdf).
7. Home Battery 48V DS-000141-DE — SolarEdge — 2025-02-17 — [PDF](https://knowledge-center.solaredge.com/sites/kc/files/se-solaredge-home-battery-48V-datasheet-de.pdf).
8. Aktivierungscodes für Produkterweiterungen — KOSTAL — undated — [German page](https://www.kostal-solar-electric.com/de/service-support/aktivierungscode/).
9. GEN24 & GEN24 Plus Product guide — Fronius — undated; UK regional page — [Guide](https://www.fronius.com/en-gb/uk/solar-energy/installers-partners/service-support/tech-support/how-to-install/installation-guide-gen24?filter=3524&productid=e4c97f84-dd97-44a0-b4d3-b49f5ae83c6c).
