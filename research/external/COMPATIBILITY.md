# Component compatibility: evidence and pitch note

**Current supplement:** [TASK3-COMPATIBILITY-VERIFIED.md](TASK3-COMPATIBILITY-VERIFIED.md) adds exact manufacturer conditions and source-inspected engine implementation. Read it before making pitch or pairing-enforcement claims.

## Summary (≤150 words)

Checked **2026-11-07** against manufacturer documentation. Selected inverter–battery combinations are documented, subject to exact models, module counts and firmware. This is a desk verification of component families, **not** an inspection of the application, a completed home design, or installation approval. No private data was accessed.

Pitch wording usable now: **“Our research identifies manufacturer-documented component pairings and the constraints a buildable design must respect.”**

Only after implementation and tests, stronger wording could be: **“The engine checks supported inverter–battery pairings, valid module counts and required accessories before producing the parts list.”** That implementation claim is currently **UNVERIFIED**. Treat compatibility as a supporting credibility point, not the central pitch.

## Findings

### Documented inverter–battery pairings

The BYD rows below refer specifically to **Premium HVS/HVM BCU2.0**, matrix **V2.22, 2026-10-10**, single tower. They do not establish compatibility for HVS+, HVM+, HVB or arbitrary firmware. [BYD matrix](https://site.bydbatterybox.com/uploads/downloads/BCU2.0_261010_BYD_Battery_Box_Premium_HVS%26HVM_Compatible_Inverter_List_V2.22-6ac9cfeb73807.pdf)

| Inverter family | HVS modules | HVM modules | Minimum inverter firmware shown | Battery BMU / BMS shown |
|---|---:|---:|---|---|
| Fronius Symo GEN24 Plus | 2–5 | 4–8 | 1.9.7-0 | 3.13 / 3.19 |
| GoodWe ET 5–10 kW / BT | 2–5 | 4–8 | ARM 11 | 3.13 / 3.19 |
| SMA STP 5.0–10.0 Smart Energy | 2–5 | 4–8 | 3.00.02.R | 3.16 / 3.24 |
| KOSTAL PLENTICORE G3 | 2–5 | 3–8 | 3.03.20 | 3.13 / 3.19 |

Those are matrix minimums, not a recommendation to install old firmware. Check current manufacturer requirements and both sides' exact variants before enabling a catalogue pair.

HVS modules provide **2.56 kWh usable DC** each; HVM modules **2.76 kWh**. Thus the matrix permits HVM **8.28 kWh** on PLENTICORE G3, but the other listed families begin at **11.04 kWh**. These are capacity/count examples, not complete installation designs. [HVS datasheet](https://site.bydbatterybox.com/uploads/downloads/BCU2.0_BBOX_HVS_Datasheet_EN_V1.0_250328-67ee42d4ced21.pdf), [HVM datasheet](https://site.bydbatterybox.com/uploads/downloads/BCU2.0_BBOX_HVM_Datasheet_EN_V1.0_250328-67ee3a426f6ce.pdf)

Additional documented ecosystem checks:

| Pairing | Evidence | Boundary |
|---|---|---|
| Huawei SUN2000-5/6/8/10/12K-MAP0 + LUNA2000-5/10/15-S0 or 7/14/21-S1 | Manufacturer datasheet explicitly lists these battery families. | Local SKU, current firmware and exact battery configuration still need confirmation; whole-home backup requires the stated SmartGuard arrangement. [Huawei sheet](https://solar.huawei.com/admin/asset/v1/pro/view/1895ef0ef0a64bd5ae353e422fbd4af4.pdf) |
| SolarEdge SE5K/8K/10K-RWB48 + BAT-05K48 | European sheet lists 1–5 battery modules and a 40–62 V battery range. | This is the 48 V family, not proof that a SolarEdge 400 V battery can be substituted. Backup has additional local/component/firmware conditions. [SolarEdge sheet](https://www.solaredge.com/sites/default/files/se-solaredge-home-hub-inverter-three-phase-backup-datasheet-de.pdf) |

### Remaining whole-system checks

The following are **proposed validation requirements**, not claims that this repository already performs them:

- **PV to inverter:** exact module/string count, cold-corrected open-circuit voltage, hot operating voltage against MPPT range, input and short-circuit current, tracker allocation, connectors and regional limits. Matching kWp and inverter kW alone is insufficient evidence of a complete pairing. Huawei's sheet provides separate voltage/current/tracker limits; no site/string configuration was supplied here. [Huawei sheet](https://solar.huawei.com/admin/asset/v1/pro/view/1895ef0ef0a64bd5ae353e422fbd4af4.pdf)
- **Battery:** revision, module count, controller, firmware, usable energy definition, charging/discharging limits and parallel-tower restrictions. A single-tower approval must not be generalized to parallel towers. [BYD matrix](https://site.bydbatterybox.com/uploads/downloads/BCU2.0_261010_BYD_Battery_Box_Premium_HVS%26HVM_Compatible_Inverter_List_V2.22-6ac9cfeb73807.pdf)
- **Backup:** include the required switching/interface equipment and identify supported circuits and power limits; storage capacity alone does not establish backup functionality. [Huawei sheet](https://solar.huawei.com/admin/asset/v1/pro/view/1895ef0ef0a64bd5ae353e422fbd4af4.pdf), [SolarEdge sheet](https://www.solaredge.com/sites/default/files/se-solaredge-home-hub-inverter-three-phase-backup-datasheet-de.pdf)
- **Wallbox/EMS:** distinguish ordinary charging from verified PV-surplus control. The latter needs the supported meter/controller/protocol arrangement. No all-brand interoperability has been established. [go-e integration options](https://go-e.com/de-de/produkte/go-e-charger-gemini-flex-2-0)
- **Heat pump:** check output at design temperatures, modulation, hydraulic flow/volume, emitters, DHW recovery and separate outdoor/indoor/heater electrical supplies. See [R3-heat-pump-sizing.md](R3-heat-pump-sizing.md) for sourced sizing limits. No whole-house heat-pump design is approved by this compatibility note.
- **BOM:** include approved controllers, bases, cables, meters, activation licences and backup accessories rather than pricing just headline components. This is a proposed completeness check.

### Catalogue disposition

- **Documented, conditional candidates:** the pairings above, under their stated conditions.
- **UNVERIFIED until exact matrix/installation documentation is checked:** FoxESS ECS/H3 generation combinations, SAJ BU2/B2 revision combinations, Sigenergy tower/controller revisions, EcoFlow cross-generation combinations, Enphase whole-system limits and Tesla expansion/backup packages.
- **No conclusion:** compatibility across every product in R4, a particular home's complete electrical/hydraulic design, or existing application enforcement.

## Implications for our product

- Use an explicit allowlist of exact pairings and conditions; unknown pairings should need planner review.
- Represent module-count ranges per inverter–battery pairing, not only per battery family.
- Add source URL, document revision, firmware conditions and required accessories to compatibility records.
- Demonstrate a valid and rejected module-count example if the rule is implemented; otherwise show this as researched design work.
- Include one modest compatibility sentence in the pitch, using the implementation status distinction in the Summary.

## Open questions / uncertainty

- Application implementation and enforcement are **UNVERIFIED**: no engine, API, frontend or generated BOM was inspected in this follow-up.
- Full catalogue and site-specific compatibility remain unfinished; current firmware/SKU/region checks still apply.
- Regional release and replacement products may differ from the cited families. Do not silently apply these rows to newer revisions.
- No field installation or hardware test was performed.
- Phase 2 R7–R9 has not run; it requires the user-supplied review materials described in PROMPTS.md.

## Sources (numbered list: title — publisher — date — URL)

All reopened or discovered **2026-11-07**.

1. HVS/HVM BCU2.0 Compatible Inverter List V2.22 — BYD — 2026-10-10 — [PDF](https://site.bydbatterybox.com/uploads/downloads/BCU2.0_261010_BYD_Battery_Box_Premium_HVS%26HVM_Compatible_Inverter_List_V2.22-6ac9cfeb73807.pdf); [manufacturer downloads](https://site.bydbatterybox.com/downloads).
2. HVS BCU2.0 datasheet V1.0 — BYD — 2025-03-28 filename — [PDF](https://site.bydbatterybox.com/uploads/downloads/BCU2.0_BBOX_HVS_Datasheet_EN_V1.0_250328-67ee42d4ced21.pdf).
3. HVM BCU2.0 datasheet — BYD — 2025-03-28 download filename; internal title differs — [PDF](https://site.bydbatterybox.com/uploads/downloads/BCU2.0_BBOX_HVM_Datasheet_EN_V1.0_250328-67ee3a426f6ce.pdf).
4. SUN2000-MAP0 technical specification — Huawei — version 02-202406 displayed on reopened PDF — [PDF](https://solar.huawei.com/admin/asset/v1/pro/view/1895ef0ef0a64bd5ae353e422fbd4af4.pdf); [product page](https://solar.huawei.com/en/products/sun2000-5-12k-map0/).
5. Home Hub Three Phase for Europe, DS-000112-DE — SolarEdge — 2024-02-01 — [PDF](https://www.solaredge.com/sites/default/files/se-solaredge-home-hub-inverter-three-phase-backup-datasheet-de.pdf).
6. Gemini flex 2.0 integration options — go-e — undated, accessed 2026-11-07 — [Product](https://go-e.com/de-de/produkte/go-e-charger-gemini-flex-2-0).
