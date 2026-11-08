# AGENTS.md — rules every coding agent reads first

Project: Reonic challenge at thinc! München 2026. Master plan: [PLAN.md](PLAN.md). Submission: **Sun 8 Nov 2026, 15:00**. Feature freeze: **Sun 11:00**.

## Owners (only the owner's agent edits these folders)

| Owner (GitHub) | Role | Folders |
|---|---|---|
| @Kian738 | UX & product glue, contracts, docs | `packages/contracts/`, `docs/`, `AGENTS.md`, `PLAN.md` |
| @Rhythm02-byte | Engine (ETL, simulation, models, optimizer, BOM, API) | `services/engine/` |
| @faris-el-mokhtari-svg | Frontend + Blender house renders | `apps/web/` (except `apps/web/e2e/`) |
| @iemko23 | Evaluation, tests, public data sources | `eval/`, `data/external/`, `apps/web/e2e/` |

Shared read-only: `research/`. Nobody edits another owner's folder. To get a change there, ask on the board.

## Hard rules

1. **Data never leaves the team.** `dataset/`, `data/raw/` and `data/processed/` are gitignored. No uploads to public tools, no raw rows in issues, PRs or the board. Aggregates are fine.
2. **Contract first.** Engine ↔ web talk only through `packages/contracts` (OpenAPI + generated TS + fixtures). Announce contract changes on the board *before* merging and tag the affected owners.
3. **LLM never sizes the system.** Claude Haiku only phrases explanations, parses free text into a JSON patch, or extracts bill fields. Everything must work with no API key (template fallback).
4. **Eval is offline and deterministic.** `OFFLINE=1` disables live PVGIS/LLM calls. Never tune on the test split.
5. **Units:** the CSV labels lie (`*_kwh` columns hold Wh, `*_kw` hold W; battery and inverter columns are swapped in parts). Only `services/engine/etl` reads raw CSVs. Everything downstream uses kWh, kW, kWp and €/kWh.
6. **Anti-clutter:** a new UI control needs a demo-story reason or goes behind "More". See PLAN §9.1 kill list.
7. Small PRs. Run `pnpm test` (and `pnpm eval` if you touched the engine or eval) before pushing. Use pnpm, never npm.

## Bad habits (don't)

- Looking at or tuning on the 2026 test; "one more try" after seeing a test number. Decide on 2025 folds/splits; `/lab` counts every test look.
- Adopting a change from one split, or reporting the best of many settings without a fresh confirmation (seeds never used to choose).
- Features from the future: rolling stats over all rows, a customer's later offers, anything not known when the offer was created.
- Claims without a source: every number in pitch, README or slides comes from `eval/results/latest.json` (say which block) or is labelled an assumption. No "ceiling", no "scored once".
- Grep/Read loops instead of CodeGraph; re-reading files; reports longer than needed.
- npm instead of pnpm; editing another owner's folder; committing data, models, `.env` or secrets.
- "Done" without a check: run `pnpm test`, and look at the page in a browser (full reload: a `#hash` change doesn't reload the code).

## Docs lookup (no hallucinated APIs)

Before using a library API you are not sure about, fetch current docs from Context7's public API with WebFetch or curl:
- search: `https://context7.com/api/v1/search?query=<lib>` → library id (e.g. `/vercel/next.js`)
- docs: `https://context7.com/api/v1/<id>?type=txt&topic=<topic>&tokens=5000`
UI work follows [docs/DESIGN.md](docs/DESIGN.md) strictly.

## Code search (CodeGraph)

Before Grep/Read, use `codegraph_explore` (projectPath = repo root) or `codegraph explore "<symbols>"`; don't re-read files it showed you.

## Board protocol (Slack, `tools/slack.py`; setup: [tools/README.md](tools/README.md))

Set `SLACK_BOT_TOKEN` in your gitignored `.env` (ask @Kian738; never paste it). Run `python tools/slack.py setup` once. No token = harmless no-op. Identity: `SLACK_AGENT=<Name>` or git user.name.

1. **Start once per task:** `python tools/slack.py start`. Compact digest: recent board/changelog, additional mentions, open claims from 12h history. Decisions, contracts, blockers and requests stay visible; `start --full` shows all fetched messages. Act on your mentions/folders; respect claims.
2. **Claim before multi-file edits:** `python tools/slack.py claim <folder>`; `release <folder>` when done. Ownership rules still apply.
3. **Post only new, actionable information:** `python tools/slack.py post board "<change or blocker> · <needed action> @owner" --kind done|blocked|ask|decision|contract`. One or two lines. No repeated status, mirrored posts or acknowledgements. Details belong in the area channel or a linked file. Ask/block once, then continue independent work. Aggregates only; no secrets or raw data.
4. **Markdown changes:** promptly commit and push your own `.md` edits, then send one board post with branch, commit, changed paths and a pull request to affected agents (`git pull --ff-only origin <branch>` in their clean checkout). Do not bundle anyone else's uncommitted work. This notification also serves as the dependency/decision post; do not post it twice.
5. **Finish once per shipped change:** `python tools/slack.py done "<area>: <change>"` adds the commit to `#changelog`. Add a board post only for a dependency/action, not another completion summary. Only @Kian738's agent updates `docs/BACKLOG.md`.

`#runs` receives automatic eval summaries (`notify_run`). `@all` only for contract changes, feature freeze and demo-critical breakage.
