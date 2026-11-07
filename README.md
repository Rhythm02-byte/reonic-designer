# Home Energy Designer (Reonic challenge, thinc! München 2026)

Proposes PV, battery and heat pump designs for a home the way an expert planner would, explains why,
lets the planner override any part, and measures how close it gets to real expert designs.

Team context, plan and decisions are in [CONTEXT.md](CONTEXT.md).

## Setup

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

## Run

```bash
python -m reonic build                          # data/raw/ (Reonic export) -> data/projects.csv, one row per project
python -m reonic eval                           # held-out metrics vs baseline -> reports/  (add --group-col installer_id)
python -m reonic train                          # -> models/designer.joblib (used by the app if present)
streamlit run app.py                            # planner UI
python -m reonic synth                          # fake data -> data/synthetic.csv, used automatically if data/raw/ is absent
pytest -q
```

Real data: copy the Reonic export folders (`<installer_id>/projects_status_quo.csv` + `project_options_parts.csv`) into `data/raw/`. It is gitignored; never commit it. See CONTEXT.md §7 for the export's quirks.

## Approach

The expert design for each project is rebuilt from the offer's line items. A chain of gradient-boosting
models then decides, per component, whether it is included and how large it is, in physical order
(heat pump → PV → battery → wallbox). Each step sees the upstream decisions, so the design is coherent
and planner overrides propagate. Deterministic rules then enforce hard constraints and snap sizes to the sizes
installers actually use. Explanations combine model confidence, what the most similar past projects received,
and simple physics and economics.

## Known limitations

- Physics and cost constants are rough German defaults, not yet calibrated.
- Heat pump fuel savings are not modelled; payback covers PV and battery only.
- The export doesn't mark which option was signed; we use the lowest option number (configurable).
- PV size at one installer is rebuilt from module counts × an assumed 450 Wp.
- Heat pumps are almost never offered in the data (0.3%), so heat pump sizing can't really be learned.
