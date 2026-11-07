# thinc! x Reonic

Expert-quality PV + battery + heat-pump (+ wallbox) designs from a few facts about a home. Plan: [PLAN.md](PLAN.md). Rules: [AGENTS.md](AGENTS.md). Design language: [docs/DESIGN.md](docs/DESIGN.md).

Raw data (`dataset/<installer_id>/*.csv`) stays local and gitignored. Only `engine/etl` reads it; everything else uses `data/processed/`.

## Setup (Windows, Git Bash)

```bash
# engine (Python 3.11+)
npm run setup:engine              # venv at services/engine/.venv + editable install
# or by hand:
python -m venv services/engine/.venv
services/engine/.venv/Scripts/python -m pip install -e services/engine

# web
pnpm --dir apps/web install
npm --prefix packages/contracts install
```

## Commands

| Command | What it does |
|---|---|
| `npm run etl` | `dataset/` -> `data/processed/{projects,options}.parquet` + `catalog_<installer>.json` |
| `npm run engine:dev` | FastAPI on http://localhost:8000 (`GET /health`, `POST /design`, docs at `/docs`) |
| `npm run test` | engine tests (synthetic CSVs only) |
| `npm run eval` | offline backtest -> `eval/results/latest.json` + table (re-runs the ETL first) |
| `npm run report:correlations` | regenerates `research/data-correlations.md` (aggregates only) |
| `npm run contracts` | dumps `packages/contracts/openapi.json`, the example fixtures and `src/api.d.ts` |
| `npm run web:dev` | Next.js on http://localhost:3000 (planner `/`, offer `/offer#...`, `/eval`; proxies `/engine/*` to :8000 and shows labelled demo data while the engine is down) |

## Layout

```
services/engine/   engine package: etl/ (normalize), models/ (pydantic schemas), baseline.py, design.py, api/
eval/              run.py (splits + baselines), metrics.py, results/
packages/contracts openapi.json, fixtures/, src/api.d.ts (generated)
apps/web/          Next.js app (App Router, Tailwind v4, shadcn/ui)
research/          derive_features.py prototype, data_correlations.py, data-correlations.md
```

`/design` currently serves `baseline-0`: the installer's median bundle conditioned on demand bucket, EV and fossil heating. No simulation or learned model yet.
