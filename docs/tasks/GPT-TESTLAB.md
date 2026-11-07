# Task for ChatGPT / Codex: "Test Lab" (hidden evaluation view + run history per branch)

Paste everything below the line into a **new** Codex session opened on this repo. Start in plan mode (`/plan`), write the plan into `docs/tasks/GPT-TESTLAB-PLAN.md`, then implement it.

---

You are building the **Test Lab** for a hackathon repo (C:\Users\karim\Documents\Coding\thinc, Reonic challenge, deadline Sun 8 Nov 2026 15:00, feature freeze 11:00). Another agent (Claude) works on the engine at the same time, so stay strictly inside your files.

## Read first (only these)
AGENTS.md (hard rules: raw data never in git, docs or UI fixtures), docs/DESIGN.md (strict visual language: Reonic-style paper/ink, hairline cards, one gradient moment, no dashboards of KPI tiles), docs/PITCH.md §5 (what the numbers mean), eval/run.py and eval/results/latest.json (structure only; don't paste rows anywhere), apps/web/app/eval/page.tsx and apps/web/lib/api.ts (how the web reads /eval/summary).

## Goal
One hidden page, `/lab` (not linked in the nav; open it with the keyboard shortcut `g l` or `?lab=1`). It explains in plain words how good the engine is, and **stores every eval run so we can compare branches over time in a graph.** Keep it simple: a score, how long it took, and whether it got better.

## You own (create or edit only these)
- `eval/record.py`: after an eval run, append one compact record to `eval/history/runs.jsonl` (JSON Lines, committed to git; aggregates only).
- `eval/history/` (data + README)
- `apps/web/app/lab/**`, `apps/web/components/lab/**`, `apps/web/lib/lab.ts`
- Root `package.json`: add the scripts `eval:record` and `lab:seed` only. Add nothing else to anyone else's files.

## Do NOT touch
`services/engine/**`, `eval/run.py`, `eval/metrics.py`, `eval/select_model.py`, `apps/web` outside the paths above, `docs/` except your plan file. If you need a field that doesn't exist, read it defensively and list it as a request in your final report.

## Record format (one line per run)
`{ id, timestamp, git: {branch, commit, dirty} (via "git rev-parse"; if not a git repo: branch "local", commit null), engineVersion, policyConfig (copy of services/engine/config/policy.json), durationSec, splits: { temporal: { nTest, models: { B0, B1, M1?, composite?: { ems, wholeDesign, pv, battery, heatPump, wallbox, latencyP50ms } } }, ... }, selection?: {...}, oracle?: {...}, honesty?: {...} }`. Read everything from `eval/results/latest.json`. Tolerate missing blocks. Never include project IDs or inputs.
- `npm run eval:record` runs after `npm run eval`. Document it in `eval/history/README.md`.
- `lab:seed` creates one record from the current latest.json, so the graph isn't empty.

## Page content (top to bottom, nothing more)
1. **One headline:** "Expert match on unseen 2026 projects: **60.4**/100" (EMS of the selected model) plus "vs 61.1 for 'copy the installer's usual design'". Next to it, plain-language help (one sentence each):
   - **EMS** = average closeness to the expert design (100 = identical).
   - **Whole design** = share of homes where PV, battery, heat pump and wallbox are all within tolerance.
   - **PV/Battery within tolerance** = PV within ±20%, battery within ±25%.
2. **Run timeline graph:** x = run time, y = EMS (and a toggle for whole-design %). One line per git branch, the B0 baseline as a dashed reference line, points clickable to show commit, config and duration. Plain SVG or a tiny chart lib already in the project (check `apps/web/package.json`; add none unless essential, and justify it).
3. **Comparison table, latest run:** models as rows (rule of thumb, installer median, ours). Columns: EMS, whole design, PV, battery, latency. Best per column in bold. The help text is the column header tooltip.
4. **Honesty panel** (if present in the record): validation-vs-test protocol in one sentence, shuffled-label check, repeated-split mean ± sd, fuzz pass count, oracle table ("answering this question is worth +N points", roof marked UPPER BOUND).
5. **Run diff:** pick any two runs → per-metric delta with ▲/▼ and "within noise" when |Δ| < 2 points (n≈325).
6. **Duration** of each run, and a warning chip if latency p95 > 400 ms.
Empty and error states per DESIGN.md. Accessible: tables for every chart, keyboard navigation, no colour-only signals.

## Data access
A Next.js server component reads `eval/history/runs.jsonl` from disk (path relative to the repo root; resolve it robustly on Windows). No engine call is needed. In production, if the file is missing, show the empty state.

## Quality bar
- `pnpm lint` and `pnpm build` pass in apps/web. Add a tiny unit test for the record builder (Python, `pytest -q eval/test_record.py`) with a synthetic latest.json.
- No new dependency without a one-line justification in the plan.
- No feature creep: if an item isn't listed above, don't build it.

## Final report (≤200 words)
Files created, how to record a run, a screenshot description, field requests for the engine owner, open issues. Claude will review your diff against this spec.
