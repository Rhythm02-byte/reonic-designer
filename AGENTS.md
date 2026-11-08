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

## Board protocol (Slack, via `tools/slack.py`; setup in [tools/README.md](tools/README.md))

- **Channels:** `#board` (status only), `#engine`, `#web`, `#eval`, `#pitch`, `#runs` (automatic eval results).
- **Post format:** `[Who's agent] what changed · what I need @owner` — `python tools/slack.py post board "<text>"`.
- **When to post:** when you finish something another owner depends on, when you're blocked, or when the contract changes.
- **Reading:** read `#board` at the start of a task: `python tools/slack.py read board --since 2h`.
- `@all` only for contract changes, feature freeze, and demo-critical breakage. Never post secrets or raw data rows.
