# Pitch notes (single source for deck, demo and Q&A)

> Keep every number here with **what it was measured on**. Update the tables when `pnpm eval` changes. Never put raw project rows in the deck.

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
- **Near-identical homes get 5.4–12.6 kWp** (p10–p90, n=216, 4–5 MWh, no EV). Roof size and budget aren't in the data, a big source of disagreement (Rhythm's deviation analysis). Not a proven ceiling: an optimistic same-input bound is 62% (`research/creative/ceiling/REPORT.md`), so don't say "ceiling".
- Wallboxes: 24.6% of homes get one, but only 9% of those have an EV flag.

## 4. How it works (one diagram)
`inputs → learned installer policy (gradient boosting chain, kNN similar homes) → hourly simulation (PVGIS + BDEW H0, battery dispatch, EV, heat pump, 20-year €) → rules + catalog snap → design + reasons + flags + "ask next"`
- Claude Haiku only phrases text and turns "family buys an EV next year" into a visible input patch. **It never sizes anything.** Everything works with no API key.

## 5. Proof (fill from `eval/results/latest.json` → `served.test`; selection on validation)
**Protocol:** train offers ≤ 2025-09-30, choose on validation (Q4 2025, n=232), refit ≤ 2025-12-31, score the 2026 test: never used to choose a model; scored in 3 recorded runs so far (the /lab counter shows every look).

| Test 2026 (n=325) | EMS | Whole design | PV ±20% | Battery ±25% |
|---|---|---|---|---|
| Rule of thumb (B1) | 55.0 | 14.8% | 32.9% | 40.0% |
| Installer median (B0) | 61.1 | 20.6% | 42.5% | 47.4% |
| **Ours (composite + battery coverage over catalogue sizes)** | 61.2 | **22.2%** | **59.7%** | **48.9%** |

Source: `pnpm eval` run of 2026-11-08 (eval/history, kind "all"). Previous config (before battery coverage sizing): 60.4 / 20.9% / 59.7% / 49.2%; the swap was chosen on validation (+0.4 pt, noise-level) and is reported as such.
Final run 2026-11-08 ~08:10 (`pnpm eval`, kind "all"; config adopted from the research tournament, combo C, before this look). Honesty (same run): shuffled labels 22.2% vs real 24.1% whole design (validation); 20 random splits ours − B0 = +2.1 ± 2.3 pts (not distinguishable from zero); fuzz 0 / 2,000 broken.

- Validation (n=232) chose: learned PV, battery and heat pump; installer-conditioned wallbox. Physics features and installer PV prior help, and shallow trees (depth 3, leaf ≥40) win, so the data is small and noisy.
- **Claim we can defend:** +17 pts PV within tolerance vs the installer's own median, equal on whole design. Equal on EMS (61.0 vs 61.1): the median gets battery/wallbox habits right by construction. 1–2 pt differences are noise at this n.
- The simulator's economic battery matches experts worst (23% on validation). So it is an *explanation and second opinion*, not the sizing source. That is evidence that experts size batteries by habit, not economics.
- **Confidence ranking (`eval/selective.py`, 2025 time folds, n=921, score fixed in advance):** the most confident quarter of homes is fully right 25.2% of the time vs 16.0% for all homes (B0 on the same homes: 13.9% / 9.1%). Useful for ordering the review queue, **not** good enough to auto-approve designs. Don't pitch "auto-approve".
- **Per 2025 quarter (train on earlier offers only):** whole design ours vs B0 = 10.4/7.9, 11.4/4.8, 18.2/5.9, 24.1/17.7%. Caveat: the served config was chosen on Q4, so this is retrospective, not fresh evidence.
- Size ranges after conformal calibration: PV 10–90% range covers 85.5% of 2026 experts (target 80%), battery 83.6%.
- /design latency on a laptop under load (08 Nov 04:40, same input, n=15): median ~350 ms; distinct inputs up to ~1.2 s while other jobs ran. Say "under a second", not a p95.
- Robust: sensitivity over the signed-option guess × module wattage stays within ~1.5 pts. Blanking 60% of inputs costs ~2 EMS points.
- **Honest reading:** we clearly beat baselines on PV sizing. Battery choice is installer habit, so we reproduce it and add the physics view on top.

## 6. Standout: "it knows what it doesn't know"
Three faces of one idea, all from the same engine (no extra features):
1. **Ask next.** The engine ranks missing or placeholder inputs by how much they would change the design or price, e.g. "How many modules fit the roof?", "Is an EV planned?", "Real annual kWh? (4,500 looks like a default)". It fits the planner's qualification call and turns the data's biggest weakness into the workflow. *Measured (oracle, 2026 test, n=325, selected model, no tuning):*

| Question answered | Whole design: unknown → answered | PV ±20% |
|---|---|---|
| Real annual kWh (instead of the 4,500 placeholder) | **+10.8 pts** (11.4% → 22.2%) | 46.5% → 59.7% (previous config) |
| Roof capacity in modules (**upper bound**: cap = expert's module count) | 22.2% → **33.2%** | 59.7% → **82.5%** |
| EV yes/no | 21.2% → 22.2% | ~equal |

Slide line: **"One question about the roof is worth more than any model we could train: +11 points whole-design (upper bound)."** Real consumption roughly doubles whole-design agreement versus a placeholder.
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
- **Parts list is preliminary:** products are picked from the installer's catalogue by size; compatibility (inverter ↔ battery, string layout) is not checked.
- Two installers only. The heat pump appears in ~2% of designs, so HP sizing is physics-led (full-load hours), not learned.
- No roof size in the data → PV size uncertainty (we ask for it instead of guessing).
- Single reference weather site (Kassel). Hourly H0 smooths load (self-consumption slightly optimistic).
- Prices are 2026 market ranges with sources and dates; inverter replacement, O&M, gas/oil prices are placeholders.

## 10. Likely jury questions
- *Isn't the installer-median baseline already good?* Yes, and that is a finding: battery choice is habit. On the whole design we are **slightly ahead but within noise** (22.2% vs 20.6%; +0.6 ± 2.0 over 20 splits); we win clearly on PV (+17 pts) and add what the median can't: coupling, physics, explanations, flags, "ask next".
- *Does a stricter metric change that?* Yes, and we say so: with an absolute ±1-module PV tolerance instead of ±20%, the median beats us on validation (7.3% vs 13.4%); "any offered option" changes little (`research/creative/ceiling/REPORT.md`). 87 development projects have a PV line without a readable size, so they count PV presence only.
- *Is the planner demo on unseen data?* Yes: the served model is trained on offers up to 2025-12-31 (`pnpm x:train`), the same cutoff as the held-out projects in Evidence.
- *Overfitting?* Selection on a validation window, 2026 test never used to choose a model; scored in 3 recorded runs so far (the /lab counter shows every look), temporal + leave-one-installer-out, sensitivity and masking tests, shallow models.
- *Why not just an LLM?* The brief rules it out, and our numbers show habit plus physics. The LLM only writes text and parses intent.
