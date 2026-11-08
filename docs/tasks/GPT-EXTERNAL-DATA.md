# Task for Codex: external data pack + plausibility benchmark

Paste everything below the line into a **new** Codex session opened on `C:\Users\karim\Documents\Coding\thinc` (branch `next`). Start with `/plan`, write your plan to `docs/tasks/GPT-EXTERNAL-DATA-PLAN.md`, then implement. You have a lot of freedom in *how*; the goals, the hard rules and the done-checks below are fixed. Claude reviews your diff and re-runs your numbers at the end.

---

## Why this matters (read this first)
We are building an AI planner for German home energy systems (Reonic challenge, thinc! München; feature freeze Sun 8 Nov 2026 11:00). From a few facts about a home it proposes PV kWp, battery kWh, heat pump kW and wallbox the way the installer's own experts would, checks it with an hourly simulation (PVGIS weather, BDEW H0 load profile, battery dispatch, EV, heat pump, 20-year economics), and asks the 1–3 questions that would change the design most.

Our only labelled data is a private export of ~1,600 signed projects from 2 installers. It is small, and two facts limit any model:
- Experts sized near-identical homes anywhere from 5.4 to 12.6 kWp: they saw the roof and the budget, we don't.
- 29% of projects carry a 4,500 kWh placeholder instead of the real annual consumption.

Today the model matches the expert's PV within ±20% in ~60% of 2026 test homes (the installer's own median: 42.5%), but whole-design agreement only ties that median (~21%). We want **independent outside evidence** to (1) check that our designs are plausible for German homes beyond our two installers, (2) give priors that might improve the model, and (3) calibrate the simulator with real measured load profiles. You are the one person on the team doing this.

## Hard rules (non-negotiable)
1. **The Reonic dataset (`dataset/`, `data/raw/`, `data/processed/`) never leaves this machine.** Don't upload it, paste it into any tool or prompt, or commit derived row-level data. You may *run the engine* locally; you don't need to read the private data at all for this task.
2. Commit **aggregates only** (distributions, quantiles, counts, small calibrated profiles), each file < 5 MB. Raw downloads go to `data/external/raw/` (gitignored: add the rule).
3. Every source gets: URL, version/date, licence, SHA-256 of what you downloaded, and what each used column means **as verified in the source's own documentation**. Don't guess column semantics; if unsure, say UNVERIFIED.
4. External data cannot replace the expert-match test: no public dataset contains installer-chosen bundles. Never claim it measures "accuracy vs experts".
5. Use CodeGraph before reading our code: `codegraph explore "<symbols>"` (index at repo root). Don't edit files outside your folders.

## You own (create/edit only these)
`data/external/**`, `eval/external/**`, `research/external/data/**`, `docs/tasks/GPT-EXTERNAL-DATA-PLAN.md`, plus one root `package.json` script `x:external`. Need something elsewhere (an engine field, a config)? List it as a request in your report.

## Goals
### G1. MaStR (Marktstammdatenregister): German PV + storage size distributions
- Get it via `open-mastr` (bulk download → local DB; tables `EinheitenSolar`, `EinheitenStromSpeicher`) or the Zenodo snapshot (record 14843222). Verify column meaning in the MaStR data model docs (gross vs net power, usable storage capacity, units kW vs kWh, commissioning date, status, Gemeinde/postcode, unit vs installation IDs).
- Scope: residential-like rooftop PV, in operation, commissioned 2018–2026, sizes ~1–30 kWp; storage linked to PV **only via the register's own references** (e.g. shared installation/operator/location IDs, whichever the docs define). Postcode proximity is not a link: if you can't link, report storage distributions separately and say so.
- Produce: kWp distribution by commissioning year; battery attach rate and kWh/kWp ratio by year (linked subset); p5/p25/p50/p75/p95; regional splits (federal state) if cheap. Output `data/external/mastr_summary.json` + a short `research/external/data/mastr.md` with charts or tables.

### G2. Measured load profiles → simulator calibration
- WPuQ (Zenodo 5642902; 38 single-family homes near Hameln 2018–2020, household and heat pump metered separately, 10 s–60 min): build hourly normalized profiles (household; heat pump vs outdoor temperature if available).
- OPSD household data incl. the residential EV channel (`DE_KN_residential4_ev`) if usable.
- Compare with what our simulator assumes (BDEW H0 via demandlib; heat pump and EV models in `services/engine/engine/sim/`): self-consumption and autarky for a few reference systems. Report the gap; ship the profiles as compact `.npz`/`.json` under `data/external/profiles/` with a loader in `eval/external/profiles.py`. Don't edit the engine; tell us what to change.

### G3. Other public sets: triage
From `research/external/R2-public-datasets.md` and `TASK1-RESEARCH-COMPLETION.md` (incl. Kaggle candidates, LBNL "Tracking the Sun" which has PV DC kW + battery kWh, PVGIS): for each, usable yes/no, why, licence, the one thing it would give us. Pull at most 2 more if clearly valuable.

### G4. Synthetic stress set
Implement `research/external/TASK2-SYNTHETIC-TEST-SPEC.md` as `eval/external/stress.py`: edge-case homes (tiny/huge demand, existing PV/storage, heat pump with no heat demand, EV without wallbox, etc.) with the **expected rule outcome** per case. Run them through our engine (`services/engine`, `Designer` / the `/design` API on localhost:8000, whichever you prefer) and report violations.

### G5. Plausibility benchmark
`eval/external/benchmark.py` (run via `pnpm x:external`): generate N realistic German homes (sample demand/household/EV/heating from public stats you cite), get our engine's designs, and score:
- share of PV sizes inside the MaStR p5–p95 for that year,
- distance of our battery/PV ratio distribution to MaStR's (e.g. Wasserstein),
- stress-set rule violations (G4).
Write the result to `eval/external/results.json` (aggregates). Keep it deterministic (fixed seeds) and offline after the first download.

## Done when
- `pnpm x:external` runs end-to-end offline from cached downloads and prints the benchmark.
- `data/external/README.md` lists every source with licence + SHA + verified column meanings.
- `git status` shows no raw data and no Reonic-derived rows staged; all committed files < 5 MB.
- Tests: `pytest -q eval/external` (unit tests for parsers/linkers using tiny synthetic fixtures you write).

## Final report (≤ 300 words)
What you got from each source (with the key numbers), what was unusable and why, benchmark results for our engine, **three concrete, testable ideas** for improving the model or simulator (e.g. "use MaStR kWh/kWp by year as a prior for the battery step"), requests for the engine owner, and anything you're unsure about. Claude will re-run your commands and check units against the docs.
