# Codex: night shift as an independent teammate (2 workstreams)

Paste everything below the line into a **new** Codex session opened on `C:\Users\karim\Documents\Coding\thinc` (branch `next`). Start with `/plan`. Claude (the engine/eval lead's agent) reviews your work in the morning, re-runs your commands and checks your sources. You are trusted to choose methods. The goals, hard rules and deliverables are fixed.

---

## Who you are working with and why
Team of 4 at thinc! München 2026, Reonic challenge. **Feature freeze Sun 8 Nov 11:00, submission 15:00.** We are building **"Rhythm – Home Energy Designer"**:
- From a few facts about a German home, it proposes PV kWp, battery kWh, heat pump kW and wallbox the way the installer's own experts would. The model is learned from ~1,600 signed projects of 2 installers.
- An hourly simulation checks the design: PVGIS weather, BDEW H0 load, battery dispatch, EV, heat pump, 20-year economics.
- It shows the range experts chose for similar homes, flags unusual choices, and **asks the 1–3 questions that would change the design most** ("Ask next"; measured: real annual kWh instead of the 4,500 default lifts whole-design agreement from 12.3% to 20.9%).
- It ends in a planner workspace (customer sidebar, drafts, system cards) and a homeowner offer link/QR.
- Read first: `README.md`, `docs/PITCH.md` (all numbers + what they were measured on), `docs/BACKLOG.md`, `docs/PRODUCT.md`, `AGENTS.md`. Use CodeGraph (`codegraph explore "<symbols>"`, index at repo root) before reading code.

Honest state: we beat the installer's own median on PV sizing (59.7% vs 42.5% within ±20% on unseen 2026 homes). The whole design only ties it (20.9% vs 20.6%), because experts saw roof and budget, which the data lacks. Other teams have the same data. **We need to find what we're missing.**

## Hard rules (non-negotiable)
1. **The Reonic dataset never leaves this machine.** `dataset/`, `data/raw/`, `data/processed/` are not to be uploaded, pasted into prompts or web tools, or committed as derived rows. Aggregates from `docs/PITCH.md` are fine to reason with.
2. Edit only your folders: `data/external/**`, `eval/external/**`, `research/external/data/**`, `research/creative/**`, `docs/tasks/CODEX-*.md` (your status/plan files), plus root `package.json` script `x:external`. Need a change elsewhere? Write it as a request.
3. **Commit nothing.** Claude reviews the diff and commits.
4. Cite sources for every external fact (URL + date). If unsure, write UNVERIFIED. Never invent numbers, APIs or dataset fields.
5. No new UI. You produce data, code under your folders, and ranked research.

## Workstream A: external data pack + plausibility benchmark (long-running; start its downloads FIRST)
The full spec is in `docs/tasks/GPT-EXTERNAL-DATA.md`: follow it.
- **Sources:** MaStR (official German register of installations: PV and storage size distributions), WPuQ/OPSD measured load profiles, a triage of the other sets incl. Kaggle, the synthetic stress set, and `pnpm x:external` → `eval/external/benchmark.py`.
- Ask yourself what would let the planner trust a size: e.g. "your 9 kWp sits at the 62nd percentile of 2025 German home systems with batteries".

## Workstream B: blind-spot and creativity sweep ("what are we missing?")
**Goal:** a ranked, evidence-backed list of everything we could still do or say: approaches, model ideas, features, data sources, pipelines, demo moments, pitch angles, jury questions, risks. Include what other teams will likely do, so we can beat or differentiate from it.

Use methods that are known to make LLMs less generic:
1. **Diverge at the distribution level, not one answer at a time.** For each lens below, ask for ~10 candidate ideas *with an estimated probability that a typical team would think of it*. Keep the low-probability tail (< 10%) as candidates too. This is "Verbalized Sampling" (Zhang et al. 2025, arXiv 2510.01171), which counters mode collapse toward typical answers.
2. **Many lenses and personas:**
   - Reonic CTO; Reonic customer-success lead; a 15-year installer planner; a sceptical homeowner; an ML researcher on the jury; a VC; a PM at a competitor (Enpal, 1KOMMA5°, Aurora Solar, OpenSolar).
   - Analogies from other industries: radiology second reader, credit-scoring adverse-action reasons, car configurators, chess engines' "best move + eval bar", insurance underwriting with missing data.
3. **Structured frames:**
   - Assumption reversal (what if we don't predict sizes at all, but rank the installer's past packages?).
   - SCAMPER over our pipeline: inputs → model → simulation → UI → offer.
   - A morphological box (inputs × learner × objective × UX × proof).
   - Premortem: "it's 15:30, we lost; write the jury's three reasons".
   - "Accuracy is capped at ~25% whole-design. What wins anyway?"
4. **Debate before you converge.** A generator and a hard critic argue each shortlisted idea with a judge. Self-reflection alone tends to lock onto the first answer ("degeneration of thought", Liang et al., EMNLP 2024, arXiv 2305.19118).
5. **Converge with a pairwise tournament.** Compare ideas head-to-head and keep Elo-style scores, as in Google's AI co-scientist (Gottweis et al. 2025, arXiv 2502.18864).
   - Score axes: jury impact, evidence we can show, hours to build before 11:00, risk to the demo.
   - Note: LLM ideas tend to be rated *more novel but slightly less feasible* than experts' (Si, Yang, Hashimoto 2024, arXiv 2409.04109). So run a feasibility pass with CodeGraph on the actual repo.
6. **Protect diversity.** AI help makes outputs more similar to each other (Doshi & Hauser, Science Advances 2024). Keep 3 clearly-labelled wildcards in the final list, even if they lose the tournament.
7. If your environment lets you run parallel agents or subtasks, give each lens group its own agent and one agent the critic role. Otherwise run the lenses sequentially and keep their outputs separate until the tournament.

**Deliverables for B:** `research/creative/blindspots.md`:
- **Ranked table (top 25):** idea · category (model / data / feature / UX / pitch / risk) · why the jury cares · evidence or source · hours · risk · owner (Engine / Web / Eval / Pitch) · first concrete step.
- **Top 5 as mini-specs:** what, how, how we'd measure it without overfitting, demo moment, cut line.
- **Kill list:** tempting things we should NOT do, and why.
- **Questions** the jury will likely ask, and our best honest answers.
- **Appendix:** raw idea pool with lens, probability and Elo, so we can audit the process.

## How to work and communicate
- **Order:** start A's downloads → do B while they run → finish A. B's first full draft by **05:00**, A by **08:00**.
- **Progress:** append timestamped lines to `docs/tasks/CODEX-STATUS.md` (what's done, what's next, blockers).
- **Slack:** if `SLACK_BOT_TOKEN` is set, also post milestones to `#board` with `python tools/slack.py post board "[Codex] <what> · <need>"`, and read `#board` (`python tools/slack.py read board --since 2h`) at each milestone, because Claude may leave you instructions there.
- **Final report (≤300 words, in CODEX-STATUS.md):** the top 5 from B; A's key numbers; what you could not verify; requests for other owners.
