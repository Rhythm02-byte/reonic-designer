# Claude bug hunt: find, prove and fix everything before the 11:00 freeze

You are the team's quality owner for the next ~4 hours. Your job: **find every real bug in `next`, prove each one with a failing test or a reproducible check, fix it minimally, and prove the fix.** You report on Slack. Kian's main Claude session coordinates; you do the work.

## Situation (Sun 8 Nov 2026, ~05:30; freeze 11:00, submission 15:00)
- **Repo:** `C:\Users\karim\Documents\Coding\thinc`, branch `next` (the team's main, pushed to origin).
  - Read `AGENTS.md` first (owners, hard rules, **bad habits**, Slack protocol), then `README.md`, `docs/PITCH.md`, `docs/demo-script.md`.
- **Stack:**
  - `services/engine`: FastAPI on :8000, sklearn chain + kNN + rules + hourly simulator + Ask-next + parts list.
  - `apps/web`: Next 16 / React 19, Faris's UI plus our adapter `lib/api.ts` → `lib/engine.ts`; `/pitch` deck, `/lab`, `/offer`, `/new-customer`, `proxy.ts` tunnel guard.
  - `packages/contracts`: OpenAPI + generated TypeScript.
  - `eval/`: offline evaluation.
  - The engine and web dev servers may already be running (uvicorn `--reload` on :8000, Next on :3000). Don't start duplicates; check `curl localhost:8000/health` and `curl localhost:3000`.
- **Commands (pnpm, never npm):**
  - `pnpm test`: engine pytest, eval pytest, web lint, web typecheck;
  - `pnpm x:web-build`;
  - `pnpm x:train`: the served model, offers ≤ 2025-12-31;
  - `pnpm x:external`: Codex's stress / plausibility suite;
  - `node scripts/py.mjs <script>` runs the venv python.
- **Other agents working right now; don't touch their files:**
  - Research tournament session: `eval/research*`, `research/experiments.md`, `eval/history/runs.jsonl`, the root `package.json` `x:research` line.
  - Kian's main session: will change `services/engine/config/policy.json` and run the final `pnpm eval` around 09:00. **You never edit `policy.json`, never run `pnpm eval` (it scores the 2026 test), never retrain unless a fix requires it (then say so on Slack first).**
  - Codex deliverables (uncommitted; Kian's session commits them): `eval/external/**`, `data/external/**`, `research/creative/**`, `research/jury/**`, `research/external/data/**`, `docs/tasks/CODEX-*.md`. Read them; don't edit them. Exception: if a fix needs a test fixture from there, copy it into `services/engine/tests/`.
- **Hard rules:**
  - Data (`dataset/`, `data/raw`, `data/processed`) never leaves the machine, is never committed, and never appears in Slack, files or test fixtures (synthetic fixtures only).
  - No secrets in commits (`.env` is gitignored).
  - The 2026 test is off limits.
  - Don't change the model's decisions to make a test pass. Don't relax a tolerance or a timing limit to make a test pass.

## Known bugs to fix first (evidence already exists)
From Codex's stress suite (`research/external/data/benchmark.md`, `research/creative/ceiling/STRESS.md`, `eval/external/stress.py`, `eval/external/results.json`):
1. **Negative PV:** a negative roof cap gives a negative PV size (case `dev-boundary-0049`).
   - Fix the input validation (schema: `roofMaxModules ≥ 0`, or treat < 0 as invalid → 422) **and** clamp the output ≥ 0.
   - Add a regression test.
2. **Simulation metrics missing:** 8 of 347 required metrics are missing (grid import / feed-in / PV yield / autarky, twice each).
   - The engine logs a caught `recommend_battery` empty-candidate exception, so `/design` returns without metrics.
   - Find the root cause (empty battery candidate list?), fix it, and add a test that `/design` always returns those metrics for valid homes.
3. **Module arithmetic:** 39/70 responses fail `modules × moduleWp ≈ kWp`, probably because kWp is serialized with 2 decimals.
   - Decide the honest fix: kWp derived from `modules × moduleWp`, or more precision.
   - Make the planner, the 3D house, the parts list and the offer show **one** consistent panel count.
   - Test it.
4. **Missing review warnings:** 120 of 186 predeclared review cases get no warning (58 blocked by the adapter).
   - These are **not** 120 defects. Triage them: which ones are real missing flags (e.g. an implausible input the planner should be warned about) and which are the checker's expectations.
   - Fix only the real ones, with tests. List the rest as "by design" in your report.
5. **One demand-monotonic diagnostic fails:** more demand gives a smaller PV in one pair. Investigate; fix only if it's a bug, not a learned habit.
6. **Latency:** 3 timing tests fail even on retry: warm/cold `/design` and the 12-size battery sweep (`services/engine/tests/test_hybrid_api.py` and others).
   - Find out whether this is CPU contention (other agents train models) or a real regression.
   - Measure with the machine idle if you can, and **profile** `/design` (cProfile or pyinstrument) to find the hot path.
   - Fix a real regression. Don't touch the limits.

## Then hunt for more (use parallel Sonnet subagents)
Launch **up to 4 Sonnet subagents in parallel** (Agent tool, `model: "sonnet"`), each with one area and a CodeGraph-only brief (`codegraph_explore`, projectPath = repo root; no grep/read loops). Each returns **only confirmed findings** with a reproduction:
- **A, engine correctness:** locks (a locked part never changes; downstream re-plans), rules R01–R07, Ask-next (never asks for an entered field; answers change the design), the parts list (`design._bom`: module count, inverter sized to PV, battery, wallbox, heat pump), existing-PV handling, NaN/None paths, unit conversions (Wh vs kWh, the swapped columns; see `AGENTS.md` rule 5).
- **B, web adapter and UI logic:**
  - `apps/web/lib/api.ts` `toWire`/`toFlat`/`toDesign` (flat inputs ↔ engine HomeInputs; every field mapped; provenance "entered" only for fields the planner filled);
  - the offer link encode/decode (`lib/copy.ts`; malformed links must yield null);
  - `Planner.tsx` drafts/undo/save/preview;
  - `/pitch` stepping (`components/pitch/*`, `lib/pitch.ts`);
  - `/offer` option switching;
  - `/new-customer` (`lib/workspace.ts`);
  - the HiddenMenu triple tap.
- **C, API contract and robustness:**
  - fuzz `/design`, `/simulate`, `/validate`, `/holdout`, `/meta` with schema-valid edge cases (zero demand, huge demand, all unknowns, an existing PV larger than the roof, a locked 0 battery with PV, every heating type and load profile);
  - responses must match `packages/contracts` (regenerate types only if the contract really changed; `pnpm x:contracts`);
  - no 500s, no NaN in JSON.
- **D, security and data:**
  - `apps/web/proxy.ts` (holdout, lab/run and the paid Google routes are refused through a tunnel: `cf-connecting-ip` or a non-local Host);
  - no data rows or secrets in the git history of `next` (`git log --all --name-only`);
  - `.gitignore` coverage;
  - the CORS origins;
  - the `/lab/run` spawn arguments.

## "Claude testing": end-to-end in the browser (you do this yourself)
Use the built-in browser (`mcp__Claude_Browser__*`; load the `anthropic-skills:built-in-browser` skill first). **Always do a full reload; a `#hash` change does not reload the code.**
1. Planner `/`:
   - edit an input → the diff bar and undo work;
   - lock a battery at 20 kWh → R05/R06 flags show, no fake "Experts pick 20 kWh";
   - answer an Ask-next question → the design updates;
   - Evidence → load a held-out project → compare.
2. Offer: Share → open the link → switch options → the panel count matches the planner; savings show only for the recommended option.
3. `/pitch`, slides 5.1 → 5.5 and 6 with PageDown; then `/pitch?demo=1` with the engine **stopped** (or simulated) → the labelled demo data, no crash.
4. `/new-customer` → create → empty facts, Ask-next asks. Afterwards remove the test customer from localStorage (key `rhythm.workspace.v1`).
5. `/lab` loads; the "Run all tests" button shows on localhost. **Don't click it** (it scores the 2026 test).
6. Mobile width (375 px): the planner, the offer, the QR code; no horizontal scroll.
7. Console: no errors on any page.

## How to work
- **For each bug:**
  1. write a failing test (pytest under `services/engine/tests/` or `eval/`; for the web, a pure-function test only if a test runner exists, otherwise a reproducible browser check written in your report);
  2. make the minimal fix;
  3. the test passes;
  4. `pnpm test` stays green;
  5. commit locally on `next`, one commit per bug, with a clear message ending with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
  - **Don't push.** Kian pushes.
- **Faris owns `apps/web`.** Keep his components verbatim where you can; mark your edits `// ours: <why>`.
- Fix root causes, not symptoms. If a fix would change model numbers (sizes), stop and post an `ask` on Slack instead.
- **Time box:** known bugs 1–3 by 07:30; the hunt and the browser tests by 09:30; final report by 10:00. Cut from the bottom of the list, never the tests.

## Slack (`tools/slack.py`, token is in `.env`)
- At the start, and every ~45 min: `SLACK_AGENT=Claude-QA python tools/slack.py start`. Act on anything that mentions you or QA.
- **Claim** before multi-file edits: `SLACK_AGENT=Claude-QA python tools/slack.py claim services/engine/engine/` (`release` after).
- **Per fixed bug:** `SLACK_AGENT=Claude-QA python tools/slack.py done "engine: <bug> fixed + test · <commit>"`.
- **Blocked, or a model-changing decision:** `SLACK_AGENT=Claude-QA python tools/slack.py post board "<what> · <need> @Kian738" --kind blocked|ask`.
- **Final:** `post board "QA report: docs/tasks/QA-REPORT.md · <one line> @Kian738" --kind done`.
- Posts are 1–2 lines, aggregates only, never rows or secrets.

## Deliverable: `docs/tasks/QA-REPORT.md` (≤ 400 words)
- A table: bug · severity (demo-breaking / wrong number / cosmetic) · status (fixed + test / by design / open) · commit.
- The browser checklist with pass/fail per item.
- `pnpm test` and `pnpm x:web-build` results; `pnpm x:external` before vs after (same DEV suite, no tuning).
- **What you did not verify, explicitly.**
