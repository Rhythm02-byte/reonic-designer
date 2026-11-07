**Research update (2026-11-07):** [TASK1-RESEARCH-COMPLETION.md](TASK1-RESEARCH-COMPLETION.md) resolves the Zolar company/software distinction. Read its correction before treating the original configurator as a current operating sales flow.

## Summary (≤150 words)

As of **2026-11-07**, the most useful documented patterns are editable recommendations, comparable alternatives, visible calculation assumptions, and a clear route to human advice. Pylon demonstrates a solar–battery sizing matrix and three battery comparisons; Aurora connects battery selection to simulated outcomes; Octopus exposes consumption assumptions and a shortest-payback recommendation. [Pylon](https://getpylon.com/battery-design/), [Aurora](https://help.aurorasolar.com/hc/en-us/articles/16533305716755-Adding-storage-in-Sales-Mode), [Octopus](https://octopus.energy/order/solar-new/estimate/)

For this build, prioritize consistent variant comparisons and an explanation of the additional value of the next battery size.

This is a public-documentation teardown, not an authenticated usability test. Exact screen counts, undisclosed controls and account-specific availability are **UNVERIFIED**. Vendor promises and individual reviews are not independent evidence of performance.

## Findings

**Table conventions:** stages are documented workflow stages, not counted screens. **U = UNVERIFIED**. Critiques are design judgments, not allegations of unlawful conduct.

### Homeowner-facing products

| Product | Entry and documented steps | Editable choices | Sizes, alternatives and economics | Visuals and trust devices |
|---|---|---|---|---|
| **Aurora Sales Mode** | Installer opens project; usage, roof, storage, financials and sharing areas. Exact count U. | Representative can change modules, battery quantity, reserve and permitted financial settings. Homeowner permissions U. | Simulated bill savings, self-sufficiency and backup potential; before/after bills. | 3D roof, irradiance, interactive proposal and optional signature. [Overview](https://help.aurorasolar.com/hc/en-us/articles/4406006770067-Sales-Mode-Overview), [storage](https://help.aurorasolar.com/hc/en-us/articles/16533305716755-Adding-storage-in-Sales-Mode) |
| **OpenSolar / Sales Machine** | Shared proposal; chapter-based Swipe or long Scroll layout. Exact count template-dependent, U. | System/payment choices; installer controls sections and disclosures. | Multiple designs and payment options; savings and cost comparisons. Applicable workflows permit up to six designs. | Interactive roof, product information, acceptance/payment and communication. [Product](https://www.opensolar.com/sales-machine-proposal/) |
| **Enpal** | Calculator/lead page → personalized planning. Exact questionnaire count U. | Storage/wallbox additions advertised; direct sizing controls U. | Public size/price illustrations and monthly financing; personalized comparison U. | Product imagery, customer stories, service and no-deposit claims. Package footnotes distinguish inclusions. [Calculator](https://www.info.enpal.de/) |
| **1KOMMA5°** | Landing page → offer request. Count U. | Integrated-system choices advertised; quote controls U. | Public amortization/generation-cost claims; personalized calculation interface U. | Equipment imagery, regional installers, warranties and customer stories. All are vendor representations. [Solar page](https://1komma5.com/de/solaranlage/) |
| **Zolar configurator** | Questionnaire → expert-prepared configuration → emailed configurator. Count U. | Module count, components, storage and wallbox. | Prepared design with energy balance and financial results. | Roof configuration and fixed-price planning proposition. **Current operational availability U.** [Configuration](https://zolar.de/beratung/photovoltaik-groesse-berechnen), [workflow](https://zolar.de/blog/so-funktioniert-zolar) |
| **Otovo** | Address-first estimate; advertises price before email and an offer in two minutes. Screen count U. | Storage/wallbox packages advertised; live sizing U. | Purchase versus monthly financing; personalized payback display U. | House imagery, installation promises and installation-count social proof. [Flow description](https://www.otovo.de/a/landingpage-de) |
| **Tesla Solar** | Five documented stages: start, solar size, Powerwall, payment/incentives, finalize. Not necessarily five screens. | Preferred/custom PV size, future demand, Powerwall count and payment. | Suggested size from address/bill; battery helper explains backup duration. Final design can change price. | Roof imagery, account progress and provisional-design disclosures. **US commercial flow.** [Ordering](https://www.tesla.com/support/energy/solar-panels/going-solar/how-to-order-solar-panels), [FAQ](https://www.tesla.com/support/energy/solar-panels/faqs/frequently-asked-questions) |
| **Octopus UK** | Solar estimate; count U. Heat pump: quote → advance payment → survey/design → final agreement → installation. | Solar panels, battery choice/size and consumption assumption; battery-free option. HP sizing controls U. | Solar recommendation identifies shortest payback; assumptions visible. | System illustrations, advisor contact and “think it over” path. HP survey precedes final design. [Solar](https://octopus.energy/order/solar-new/estimate/), [heat pump](https://octopus.energy/help-and-faqs/articles/what-s-the-process-to-get-a-heat-pump-with-octopus-energy/) |
| **SolarEdge mySolarEdge** | Installed-system app, not an offer configurator. Navigation count U. | Monitoring and supported device controls. | Production, consumption and import/export depend on metering. Proposal/payback controls U. | Energy-flow view; documentation explains missing-meter limitations. [Monitoring](https://solaredge.com/en/support/system-owner/track-energy-production-and-consumption) |
| **Enphase App** | Installed-system Energy tab; navigation count U. | Time period and supported operating profiles. | Energy production, consumption, charging and grid flows; these are not automatically a utility bill. | Hourly bars/flows; consumption monitoring needs appropriate CTs. [Energy view](https://support.enphase.com/s/article/how-to-monitor-energy-data-in-the-enphase-app) |
| **Sunrun** | Consultation → assessment/design confirmation → approval → permitting/install. Proposal screen count U. | Discuss goals and approve design; self-service controls U. | Consultation covers layout, production and options; standardized interactive payback U. | Mapping, expert guidance, installation partners and homeowner approval. [Consultation](https://www.sunrun.com/go-solar-center/solar-terms/definition/solar-consultation) |

### Installer-facing products

| Product | Entry and documented stages | Planner controls | Alternatives/economics | Visuals and trust devices |
|---|---|---|---|---|
| **Reonic** | Contact/Offers → creation; five areas: Basics, Plan, Simulate, Price, Finalise. | Scope/packages, components, address and planning mode; duplicate variants. | Numbered variants. Quick planning has no yield calculation and consequently no economic calculation. | 3D/2D roof planning; internal notes excluded from customer PDF. [Documentation](https://docs.reonic.com/docs/en/offers-overview-create-an-offer) |
| **Aurora AutoDesigner** | Existing roof design → run automation. Count U. | Energy target, maximum roof fill and design constraints. | Generates modules/inverter design; economics downstream. | Editable roof layout. Rerunning can replace existing design content. [API documentation](https://docs.aurorasolar.com/reference/autodesigner) |
| **OpenSolar Ada** | Open design → imagery/facets → automatic systems → optional edits. | Templates configure components, placement restrictions, pricing and control schemes. | Multiple generated systems and BOM; manual editing retained. | 3D roofs and shade views; inadequate imagery needs manual work. [Workflow](https://support.opensolar.com/hc/en-us/articles/13780099656719-Designing-using-Ada-Auto-Design) |
| **Solar Monkey** | Design/calculate → compare → share; exact screens U. | PV, storage and HP planning; exact proposal knobs U. | Documents hourly battery modelling, degradation, efficiency and alternatives. | Online quotations and digital approval. Accuracy/conversion claims remain vendor claims. [Battery product](https://solarmonkey.io/solutions/solar-monkey-for-batteries/) |
| **autarc** | Inquiry through planning, installation and maintenance. Count U. | Heating planning, dimensioning, balancing and PV planning advertised. | Exact homeowner variant/payback UI U. | LiDAR room capture, technical planning and funding assistance. [Platform](https://www.autarc.energy/) |
| **Enerflow** | **Identity U.** Enerflo was found, but cannot be silently substituted. | Exact requested product U. | Enerflo separately documents branded proposals/custom pricing. | Disambiguation lead only. [Enerflo FAQ](https://enerflo.com/about/faq) |
| **SurgePV** | Site → design → generation → storage → financials → proposal shown publicly; exact count U. | Battery purpose, critical appliances, reserve, tariff and metering assumptions. | Distinguishes financial optimization from backup objectives; documents incremental storage savings. | 3D design, battery decision cards and backup/load concepts. [Storage design](https://www.surgepv.com/solar-storage-design) |
| **Pylon** | Design/battery tool; count U. | Solar/battery combinations, usage and tariff scenarios. | Matrix and small/medium/large comparisons: bills, payback, self-sufficiency, backup and cycling. | Solar-kW × battery-kWh heat map and aerial roof imagery. [Battery design](https://getpylon.com/battery-design/) |

### Ten patterns worth copying

These are recommendations based on documented examples, not experimentally ranked findings.

1. **Start with an editable draft:** Zolar’s expert-prepared configuration. [Source](https://zolar.de/beratung/photovoltaik-groesse-berechnen)
2. **Provide value before contact capture:** Otovo’s price-before-email proposition. [Source](https://www.otovo.de/a/landingpage-de)
3. **Represent future demand explicitly:** Tesla includes future EV/home changes. [Source](https://www.tesla.com/support/energy/solar-panels/going-solar/how-to-order-solar-panels)
4. **Use identical comparison rows:** Pylon’s battery alternatives. [Source](https://getpylon.com/battery-design/)
5. **Connect an edit to recalculation:** Aurora’s battery simulation. [Source](https://help.aurorasolar.com/hc/en-us/articles/16533305716755-Adding-storage-in-Sales-Mode)
6. **Expose the consumption assumption:** Octopus’s estimate. [Source](https://octopus.energy/order/solar-new/estimate/)
7. **Name the objective:** shortest payback versus backup capability. [Octopus](https://octopus.energy/order/solar-new/estimate/), [SurgePV](https://www.surgepv.com/solar-storage-design)
8. **Retain manual control after automation:** Ada’s editable output. [Source](https://support.opensolar.com/hc/en-us/articles/13780099656719-Designing-using-Ada-Auto-Design)
9. **Explain subsequent checks:** Octopus’s heat-pump survey. [Source](https://octopus.energy/help-and-faqs/articles/what-s-the-process-to-get-a-heat-pump-with-octopus-energy/)
10. **Keep sharing and human advice accessible:** OpenSolar proposals. [Source](https://www.opensolar.com/proposals/)

### Ten anti-patterns to avoid

1. **Losing previous edits:** Aurora documents order-dependent clearing of storage during automatic roof design. [Source](https://help.aurorasolar.com/hc/en-us/articles/16533305716755-Adding-storage-in-Sales-Mode)
2. **Displaying incomplete zero prices:** Aurora documents a storage-price snapshot issue; incomplete quotes should be blocked. [Source](https://help.aurorasolar.com/hc/en-us/articles/16533305716755-Adding-storage-in-Sales-Mode)
3. **Unexplained engineering metrics:** cycling/autonomy require translation for homeowners. Pylon supplies an example of the terminology. [Source](https://getpylon.com/battery-design/)
4. **Excessive initial choices:** OpenSolar permits more designs than this project’s intended maximum. Three is our scope choice, not a universal optimum. [Source](https://www.opensolar.com/sales-machine-proposal/)
5. **Monthly price without package context:** Enpal’s PV-only and add-on distinctions belong beside the headline. [Source](https://www.info.enpal.de/)
6. **Generic percentage savings presented as personal:** Otovo’s broad claims need household assumptions. [Source](https://www.otovo.de/a/landingpage-de)
7. **Initial estimate appearing final:** Tesla explicitly retains design-dependent pricing. [Source](https://www.tesla.com/support/energy/solar-panels/faqs/frequently-asked-questions)
8. **Economics without generation modelling:** Reonic explains the quick-planning limitation. [Source](https://docs.reonic.com/docs/en/offers-overview-create-an-offer)
9. **Missing measurements shown as zero:** SolarEdge documents metering prerequisites. [Source](https://solaredge.com/en/support/system-owner/track-energy-production-and-consumption)
10. **Acceptance as the only obvious action:** retain Octopus’s defer-and-consider path alongside integrated checkout. [Source](https://octopus.energy/order/solar-new/estimate/)

### Review complaints

**Planners:** inspected Aurora Capterra reviews include learning effort, memory use and getting stuck. The explicit memory/autosave complaint dates to **2019**, so current behavior is U. OpenSolar’s App Store includes a reliability complaint alongside positive feedback. Pylon reviews contain conflicting price opinions. These are anecdotes, not comparative failure rates. [Aurora](https://www.capterra.com/p/191094/Aurora-Solar/), [OpenSolar](https://apps.apple.com/us/app/opensolar/id1410085935?platform=ipad), [Pylon](https://www.capterra.com/p/217697/Pylon/reviews/)

**Homeowners:** Enpal Trustpilot reviews inspected from **2026-11-04–06** include changing contacts, slow support and mismatches between sales expectations and technical constraints, alongside positive installation experiences. Allegations were not independently verified. [Reviews](https://de.trustpilot.com/review/enpal.de)

### Explaining battery size

Pylon provides the clearest inspected public comparison; Octopus names a payback objective; Aurora shows recalculated outcomes; Tesla explains backup duration. An explicit homeowner-facing **marginal €/additional-kWh curve** was **UNVERIFIED** across the inspected products. [Pylon](https://getpylon.com/battery-design/), [Octopus](https://octopus.energy/order/solar-new/estimate/), [Aurora](https://help.aurorasolar.com/hc/en-us/articles/16533305716755-Adding-storage-in-Sales-Mode), [Tesla](https://www.tesla.com/support/energy/solar-panels/going-solar/how-to-order-solar-panels)

## Implications for our product

- Compare three variants with consistent cost and energy rows; treat three as a product constraint.
- Explain the selected battery through a smaller alternative and the next size’s incremental benefit.
- Separate backup value from financial value.
- Place consumption/tariff assumptions beside savings.
- Preserve overrides and preview regeneration changes.
- Label preliminary estimates and unresolved checks.
- Keep “save”, “ask installer” and “decide later” visible.

These recommendations follow the documented patterns above; their effectiveness in our product still needs testing.

## Open questions / uncertainty

- Exact authenticated screen counts and permissions remain U.
- Zolar’s current operational availability and Enerflow’s identity remain U.
- US/UK commercial terms cannot be transferred directly to Germany.
- Review sampling was opportunistic; complaint prevalence is U.
- Accessibility, mobile performance and live interaction quality were not tested.

## Sources (numbered list: title — publisher — date — URL)

All accessed **2026-11-07**; undated unless specified.

1. Sales Mode Overview / Adding storage — Aurora Solar — updated July/August 2026 — [Overview](https://help.aurorasolar.com/hc/en-us/articles/4406006770067-Sales-Mode-Overview), [storage](https://help.aurorasolar.com/hc/en-us/articles/16533305716755-Adding-storage-in-Sales-Mode).
2. Sales Machine / Dynamic Proposals — OpenSolar — undated — [Sales Machine](https://www.opensolar.com/sales-machine-proposal/), [proposals](https://www.opensolar.com/proposals/).
3. Solar calculator — Enpal — undated — [URL](https://www.info.enpal.de/).
4. Solaranlage — 1KOMMA5° — undated — [URL](https://1komma5.com/de/solaranlage/).
5. Configuration and workflow — Zolar — undated — [Configuration](https://zolar.de/beratung/photovoltaik-groesse-berechnen), [workflow](https://zolar.de/blog/so-funktioniert-zolar).
6. Address-first offer — Otovo — undated — [URL](https://www.otovo.de/a/landingpage-de).
7. Ordering / FAQ — Tesla — undated — [Ordering](https://www.tesla.com/support/energy/solar-panels/going-solar/how-to-order-solar-panels), [FAQ](https://www.tesla.com/support/energy/solar-panels/faqs/frequently-asked-questions).
8. Solar estimate / HP process — Octopus Energy — undated — [Solar](https://octopus.energy/order/solar-new/estimate/), [HP](https://octopus.energy/help-and-faqs/articles/what-s-the-process-to-get-a-heat-pump-with-octopus-energy/).
9. Energy monitoring — SolarEdge — undated — [URL](https://solaredge.com/en/support/system-owner/track-energy-production-and-consumption).
10. Energy monitoring — Enphase — date U — [URL](https://support.enphase.com/s/article/how-to-monitor-energy-data-in-the-enphase-app).
11. Solar consultation — Sunrun — updated 2026-04-28 — [URL](https://www.sunrun.com/go-solar-center/solar-terms/definition/solar-consultation).
12. Create an offer — Reonic — undated — [URL](https://docs.reonic.com/docs/en/offers-overview-create-an-offer).
13. AutoDesigner — Aurora Solar — undated — [URL](https://docs.aurorasolar.com/reference/autodesigner).
14. Designing using Ada — OpenSolar — updated 2026-07-24 — [URL](https://support.opensolar.com/hc/en-us/articles/13780099656719-Designing-using-Ada-Auto-Design).
15. Battery software — Solar Monkey — undated — [URL](https://solarmonkey.io/solutions/solar-monkey-for-batteries/).
16. Platform — autarc — undated — [URL](https://www.autarc.energy/).
17. FAQ — Enerflo — undated — [URL](https://enerflo.com/about/faq).
18. Solar storage design — SurgePV — undated — [URL](https://www.surgepv.com/solar-storage-design).
19. Battery design — Pylon — undated — [URL](https://getpylon.com/battery-design/).
20. Planner reviews — Capterra / Apple — review dates vary — [Aurora](https://www.capterra.com/p/191094/Aurora-Solar/), [OpenSolar](https://apps.apple.com/us/app/opensolar/id1410085935?platform=ipad), [Pylon](https://www.capterra.com/p/217697/Pylon/reviews/).
21. Homeowner reviews — Trustpilot — cited November 2026 — [Enpal](https://de.trustpilot.com/review/enpal.de).
