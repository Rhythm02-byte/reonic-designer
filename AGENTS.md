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

## Docs lookup (no hallucinated APIs)

Before using a library API you are not sure about, fetch current docs from Context7's public API with WebFetch or curl:
- search: `https://context7.com/api/v1/search?query=<lib>` → library id (e.g. `/vercel/next.js`)
- docs: `https://context7.com/api/v1/<id>?type=txt&topic=<topic>&tokens=5000`
UI work follows [docs/DESIGN.md](docs/DESIGN.md) strictly.

## Code search (CodeGraph)

Before Grep/Read, use `codegraph_explore` (projectPath = repo root) or `codegraph explore "<symbols>"`; don't re-read files it showed you.

## Board protocol (Slack, `tools/slack.py`, stdlib only; setup in [tools/README.md](tools/README.md))

Setup, once per machine: `cp .env.example .env`, put the bot token in it (ask @Kian738, never commit or paste it), then `python tools/slack.py setup`. No token = every command is a harmless no-op, so never block on it. Your name: `SLACK_AGENT=<Name>` or git user.name.

**Every agent, every task:**
1. **Start:** `python tools/slack.py start` — one digest of #board, open claims, mentions of you, #changelog. Act on anything that names you or your folders. Don't continue into an area someone has claimed.
2. **Claim** a folder before a multi-file edit: `python tools/slack.py claim apps/web/components/` (`release` it when done). Only the folder owner may be edited anyway; claims stop two agents of the same owner colliding.
3. **Post** when you finish something another owner depends on, when blocked, when the contract changes, or when you decide something others must follow: `python tools/slack.py post board "<what changed> · <what I need> @owner" --kind done|blocked|ask|decision|contract` (auto-prefixes `[Name's agent]`). Specific channel for detail: `#engine #web #eval #pitch`. Keep posts to 1-2 lines, aggregates only, never secrets or raw data rows.
4. **Finish:** `python tools/slack.py done "<area>: <change>"` — one line to `#changelog` (adds the commit). Only @Kian738's agent edits `docs/BACKLOG.md` from `#changelog`; everyone else posts and never edits docs, so there are no write races (Slack is append-only).
5. **Blocked/need a decision?** Post with `--kind blocked|ask`, tag the owner, then continue with other work instead of waiting.

`#runs` gets automatic eval results (`notify_run`). `@all` only for contract changes, feature freeze, and demo-critical breakage.
