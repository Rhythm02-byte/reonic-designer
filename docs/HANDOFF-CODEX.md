# Handoff prompt for Codex (paste as-is)

You are continuing a hackathon repo at C:\Users\karim\Documents\Coding\thinc (Reonic challenge, deadline **Sun 8 Nov 2026 15:00**, feature freeze 11:00). Read first, in order: AGENTS.md (owners, hard rules: raw data never leaves the team or enters git/docs; no LLM sizing; offline eval), docs/BACKLOG.md (status of everything), PLAN.md §0, §6.3–6.9, §10, docs/PITCH.md, docs/DESIGN.md. Don't re-research what's in research/*.md.

## State (Sat night)
- Engine `services/engine` (FastAPI): ETL, baselines, learned policy (engine/policy), hourly simulator (engine/sim, offline PVGIS + BDEW H0 resources), endpoints /design /simulate /validate /meta /eval/summary /holdout. 85 tests pass (`npm run test`). Run `npm run engine:dev`.
- Web `apps/web` (Next.js, pnpm, Reonic-style design from Faris): planner, offer page, 3D house, lock pins, diff bar, QR share, battery curve. `npm run web:install && npm run web:dev`.
- Eval `eval/run.py` (`npm run eval`, `--select` for validation-based selection). Honest test numbers are in docs/PITCH.md §5.
- Two jobs may have been mid-flight when Claude stopped. Check whether they finished:
  1. Frontend ↔ live engine integration (field mapping in apps/web/lib/api.ts, tolerances in /eval/summary, provenance, /holdout warm-up).
  2. Per-component model selection on validation + conformal intervals (look for research/model-selection.md and a "selection" block in eval/results/latest.json; config in services/engine/config/policy.json).
  If unfinished, finish them with the same rules: select on validation only, score the 2026 test once.

## Do next (in order, stop each at "works")
1. Verify end-to-end: engine + web, planner → change input → diff bar → share → offer opens → variant switch. Fix breakages. Keep tests, lint and build green.
2. Reconcile external research: read research/external/HANDOFF.md and the reports it links. Merge only decision-relevant findings into PLAN.md and docs/PITCH.md. Keep UNVERIFIED labels. Add **compatibility** as a small supporting point, separating (a) verified manufacturer pairings (with source) from (b) what our engine actually implements (currently: installer catalog snapping, not pairing checks).
3. Standout "Ask next" (PLAN §6.9): rank missing/placeholder inputs by design/price change and show the top ≤3 questions in the planner. Add the oracle experiment in eval (placeholder demand, hidden EV flag, roof cap = expert module count, labelled as an upper bound).
4. BOM generator: installer line-item templates → parts list + CSV in the Reonic `project_options_parts` schema.
5. Pitch: update docs/PITCH.md numbers from the final eval, build the deck outline, record the fallback demo video, finish the README (setup, approach, limitations).
6. Deployment for the QR demo: web on Vercel, engine on a small host or a `cloudflared` tunnel, `DEMO_HOLDOUT=0` on anything public.

## Extra statistics worth doing (cheap, honest)
- Bootstrap 95% confidence intervals for the EMS / whole-design difference vs B0 on the test set (paired bootstrap by project). Report them in the pitch.
- Per-segment table (installer, demand band, EV, heating, no-PV), with n.
- Calibration plot for the battery/PV include probabilities. Interval coverage before/after conformal.
- Noise ceiling: agreement among near-identical homes (already ~55% for PV in research/rhythm-findings.md), to frame "how good can anyone get".
- Ablation: learned vs physics vs installer median, per component.

## Inspiration (1KOMMA5°, others), only if time
- 1KOMMA5° Heartbeat: one energy manager for PV, battery, HP and EV with dynamic-tariff optimisation. Pitch line: our simulator already models smart EV charging. Dynamic tariffs barely change battery size (research/battery-and-simulations.md), so we keep them out of sizing.

## Public / synthetic data (ChatGPT task R2 covers this)
- Use research/external R2 results if present. Kaggle has no installer-design labels (rhythm-findings), so external data is for load/HP profiles and realism checks only. A synthetic generator exists in services/engine/tests/policy_synth.py and _incoming/reonic-designer/src/reonic/simulate.py.
