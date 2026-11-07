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
python -m reonic synth                          # fake data -> data/synthetic.csv (until the real data arrives)
python -m reonic eval  --data data/synthetic.csv   # held-out metrics vs baseline -> reports/
python -m reonic train --data data/synthetic.csv   # -> models/designer.joblib (used by the app if present)
streamlit run app.py                            # planner UI (REONIC_DATA=path selects the dataset)
pytest -q
```

Real data: put it in `data/` (gitignored; never commit it), fill `COLUMN_MAP` in `src/reonic/data.py`, then use `--data data/<file>`.

## Approach

A chain of gradient-boosting models decides, per component, whether it is included and how large it is,
in physical order (heat pump → PV → battery). Each step sees the upstream decisions, so the design is coherent
and planner overrides propagate. Deterministic rules then enforce hard constraints and snap sizes to the sizes
installers actually use. Explanations combine model confidence, what the most similar past projects received,
and simple physics and economics.

## Known limitations

- Physics and cost constants are rough German defaults, not yet calibrated.
- Heat pump fuel savings are not modelled; payback covers PV and battery only.
- All results so far are on synthetic data.
