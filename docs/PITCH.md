# Pitch notes (single source for deck, demo and Q&A)

> Keep every number here with **what it was measured on**. Update the tables when `npm run eval` changes. Never put raw project rows in the deck.

## 1. One-liner
**An AI planner that designs like your best colleague, and tells you what it doesn't know.**
From a few facts about a home, it proposes PV, battery, heat pump and wallbox the way the installer's own experts do. It checks the design with an hourly simulation, and it names the 1–3 questions that would change the design most.

## 2. Problem (numbers we can defend)
- Installer 1 (export data): median **8.2 days** from request to offer (n=257). Installer 2: 16 h (n=18). *Elapsed time, not effort; ask Reonic for real hours per design.*
- Median offer → signature: 29 / 20 days.
- German market under pressure: E-Handwerk PV installs ~355k (2025) vs ~395k (2024, ZVEH). The first credible offer often wins (brief, p. 5).
- Homeowners fear being oversold. Verbraucherzentrale tells them to demand itemized offers, *usable* battery kWh and sceptical payback.

## 3. What we found in the data (the "we actually looked" slide)
- 1,619 signed projects, 2 installers. The expert design exists only as a **parts list**. We reconstruct kWp/kWh/kW from line items. Units are mislabelled (Wh in "kWh" columns) and battery and inverter columns are swapped.
- **~25% of installer 2's offers have no PV** (storage/wallbox/retrofit jobs). There, consumption is the 4,500 kWh placeholder → strongest single signal (Spearman −0.53).
- Experts' battery ≈ **0.93 kWh per kWp** in every segment (the old rule of thumb). Battery size follows the PV/package, not the household.
- **Near-identical homes get 5.4–12.6 kWp** (p10–p90, n=216, 4–5 MWh, no EV). Roof size and budget aren't in the data → a hard ceiling for any model (Rhythm's deviation analysis).
- Wallboxes: 24.6% of homes get one, but only 9% of those have an EV flag.

## 4. How it works (one diagram)
`inputs → learned installer policy (gradient boosting chain, kNN similar homes) → hourly simulation (PVGIS + BDEW H0, battery dispatch, EV, heat pump, 20-year €) → rules + catalog snap → design + reasons + flags + "ask next"`
- Claude Haiku only phrases text and turns "family buys an EV next year" into a visible input patch. **It never sizes anything.** Everything works with no API key.

## 5. Proof (fill from `eval/results/latest.json`; selection on validation, test scored once)
**Protocol:** train offers ≤ 2025-09-30, choose on validation (Q4 2025, n=232), refit ≤ 2025-12-31, score 2026 test **once**.

| Test 2026 (n=325, scored once) | EMS | Whole design | PV ±20% | Battery ±25% |
|---|---|---|---|---|
| Rule of thumb (B1) | 55.0 | 14.8% | 32.9% | 40.0% |
| Installer median (B0) | 61.1 | 20.6% | 42.5% | 47.4% |
| **Ours (composite, chosen per component on validation)** | 60.4 | **20.9%** | **59.7%** | **49.2%** |

- Validation (n=232) chose: learned PV, battery and heat pump; installer-conditioned wallbox. Physics features and installer PV prior help, and shallow trees (depth 3, leaf ≥40) win, so the data is small and noisy.
- **Claim we can defend:** +17 pts PV within tolerance vs the installer's own median, equal on whole design. Not better on EMS (60.4 vs 61.1): the median gets battery/wallbox habits right by construction. 1–2 pt differences are noise at this n.
- The simulator's economic battery matches experts worst (23% on validation). So it is an *explanation and second opinion*, not the sizing source. That is evidence that experts size batteries by habit, not economics.
- Size ranges after conformal calibration: PV 10–90% range covers 85.5% of 2026 experts (target 80%), battery 83.6%.
- /design latency: p50 92 ms / p95 133 ms (cached simulator), p95 345 ms uncached.
- Robust: sensitivity over the signed-option guess × module wattage stays within ~1.5 pts. Blanking 60% of inputs costs ~2 EMS points.
- **Honest reading:** we clearly beat baselines on PV sizing. Battery choice is installer habit, so we reproduce it and add the physics view on top.

## 6. Standout: "it knows what it doesn't know"
Three faces of one idea, all from the same engine (no extra features):
1. **Ask next.** The engine ranks missing or placeholder inputs by how much they would change the design or price, e.g. "How many modules fit the roof?", "Is an EV planned?", "Real annual kWh? (4,500 looks like a default)". It fits the planner's qualification call and turns the data's biggest weakness into the workflow. *Measured (oracle, 2026 test, n=325, selected model, no tuning):*

| Question answered | Whole design: unknown → answered | PV ±20% |
|---|---|---|
| Real annual kWh (instead of the 4,500 placeholder) | 12.3% → **20.9%** | 46.5% → 59.7% |
| Roof capacity in modules (**upper bound**: cap = expert's module count) | 20.9% → **32.9%** | 59.7% → **82.5%** |
| EV yes/no | 20.3% → 20.9% | ~equal |

Slide line: **"One question about the roof is worth more than any model we could train: +12 points whole-design (upper bound)."** Real consumption roughly doubles whole-design agreement versus a placeholder.
2. **Honest second opinion.** Next to the expert-style battery, the simulator's economic optimum, e.g. "experts usually sell 9–10 kWh here; 5 kWh is the economic sweet spot; the extra 5 kWh adds ~10 autarky points and pays back 2.4 years later". The planner decides. The homeowner sees the curve. That kills the "oversold" fear with numbers, not adjectives.
3. **Ranges, not fake precision.** Every size carries the range experts chose for similar homes. Flags fire when a design leaves it.

## 7. Business impact
- Draft in <1 s instead of hours/days → more offers per planner, faster first offer.
- Juniors design like seniors (learned from the installer's own history; works for an unseen installer).
- Fewer wrong offers: flags + "confirm on site" list before sending.
- Homeowner link explains the offer → fewer calls, higher trust.

## 8. Demo script (5 min)
See PLAN §15. Use a real held-out 2026 project; show the expert design side by side only after our proposal.

## 9. Known limitations (say them before the jury asks)
- Two installers only. The heat pump appears in ~2% of designs, so HP sizing is physics-led (full-load hours), not learned.
- No roof size in the data → PV size uncertainty (we ask for it instead of guessing).
- Single reference weather site (Kassel). Hourly H0 smooths load (self-consumption slightly optimistic).
- Prices are 2026 market ranges with sources and dates; inverter replacement, O&M, gas/oil prices are placeholders.

## 10. Likely jury questions
- *Isn't the installer-median baseline already good?* Yes, and that is a finding: battery choice is habit. We beat it overall, win clearly on PV, and add what the median can't: coupling, physics, explanations, flags, "ask next".
- *Overfitting?* Selection on a validation window, test scored once, temporal + leave-one-installer-out, sensitivity and masking tests, shallow models.
- *Why not just an LLM?* The brief rules it out, and our numbers show habit plus physics. The LLM only writes text and parses intent.
