"""Planner UI:  streamlit run app.py"""
import json
import os
from pathlib import Path

import pandas as pd
import streamlit as st

from reonic import data, synth
from reonic.engine import Designer
from reonic.schema import HEATING_TYPES, LABEL, TARGETS, UNIT, HomeInputs

DATA = Path(os.environ.get("REONIC_DATA", "data/synthetic.csv"))
MODEL = Path("models/designer.joblib")
REPORTS = Path("reports")


@st.cache_resource
def get_designer() -> Designer:
    if MODEL.exists():
        return Designer.load(MODEL)
    if not DATA.exists() and DATA.name == "synthetic.csv":
        synth.generate().to_csv(DATA, index=False)
    return Designer.train(data.load(DATA))


st.set_page_config(page_title="Home Energy Designer", layout="wide")
st.title("Home energy designer")
designer = get_designer()
if DATA.name == "synthetic.csv" and not MODEL.exists():
    st.warning("Running on SYNTHETIC data. Set REONIC_DATA=path/to/reonic.csv for real results.")

with st.sidebar:
    st.header("The home")
    inp = HomeInputs(
        annual_consumption_kwh=st.number_input("Annual consumption (kWh)", min_value=0.0, value=4500.0, step=100.0),
        household_size=st.number_input("People in household", min_value=1, value=3, step=1),
        heating_type=st.selectbox("Current heating", HEATING_TYPES),
        has_ev=st.checkbox("Electric car (now or planned)"),
        ev_km_per_year=st.number_input("EV km per year", min_value=0.0, value=None, step=1000.0, placeholder="unknown"),
        electricity_price_eur_kwh=st.number_input("Electricity price (€/kWh)", min_value=0.0, value=0.35, step=0.01, format="%.3f"),
        feed_in_tariff_eur_kwh=st.number_input("Feed-in tariff (€/kWh)", min_value=0.0, value=0.08, step=0.005, format="%.3f"),
        budget_eur=st.number_input("Budget (€)", min_value=0.0, value=None, step=1000.0, placeholder="unknown"),
        roof_area_m2=st.number_input("Usable roof area (m²)", min_value=0.0, value=None, step=5.0, placeholder="unknown"),
        heated_area_m2=st.number_input("Heated living area (m²)", min_value=0.0, value=None, step=10.0, placeholder="unknown"),
    )

tab_plan, tab_check, tab_eval = st.tabs(["Design", "Validate & compare", "Evaluation"])

with tab_plan:
    st.caption("Override any component; everything downstream re-plans around it.")
    locked = {}
    for col, t in zip(st.columns(3), ("heat_pump_kw", "pv_kwp", "battery_kwh")):
        with col:
            if st.checkbox(f"Override {LABEL[t].lower()}", key=f"lock_{t}"):
                locked[t] = st.number_input(f"{LABEL[t]} ({UNIT[t]})", min_value=0.0, value=0.0, step=0.5, key=f"val_{t}")

    d = designer.design(inp, locked)
    for col, t in zip(st.columns(3), TARGETS):
        v = getattr(d, t)
        col.metric(LABEL[t], f"{v:g} {UNIT[t]}" if v > 0 else "none",
                   "planner override" if t in locked else f"{d.probability[t]:.0%} likely", delta_color="off")
    st.subheader("Why")
    st.markdown("\n".join(f"- {line}" for line in d.explanation))
    if d.rules_applied:
        st.subheader("Rules applied")
        st.markdown("\n".join(f"- {r}" for r in d.rules_applied))
    for f in d.flags:
        st.warning(f)

with tab_check:
    st.subheader("Validate a planner's own design")
    c = st.columns(3)
    own = {t: c[i].number_input(f"{LABEL[t]} ({UNIT[t]})", min_value=0.0, value=0.0, step=0.5, key=f"own_{t}")
           for i, t in enumerate(TARGETS)}
    flags = designer.validate(inp, own)
    if flags:
        for f in flags:
            st.warning(f)
    else:
        st.success("In line with what experts did for similar homes.")

    st.subheader("Held-out projects: ours vs expert")
    path = REPORTS / "test_predictions.csv"
    if not path.exists():
        st.info("Run `python -m reonic eval` first.")
    else:
        df = pd.read_csv(path, index_col=0)
        pid = st.selectbox("Project", df.index[:500])
        row = df.loc[pid]
        st.dataframe(pd.DataFrame({k: [row[f"{t}_{k}"] for t in TARGETS] for k in ("expert", "ours", "baseline")},
                                  index=[f"{LABEL[t]} ({UNIT[t]})" for t in TARGETS]))
        st.json({k: v for k, v in row.items() if not any(k.endswith(s) for s in ("_expert", "_ours", "_baseline"))})

with tab_eval:
    path = REPORTS / "eval.json"
    if not path.exists():
        st.info("Run `python -m reonic eval` first.")
    else:
        r = json.loads(path.read_text())
        st.caption(f"Trained on {r['n_train']} projects, tested on {r['n_test']} unseen projects.")
        st.metric("Whole design within tolerance", f"{r['model']['whole_design_within_tolerance']:.0%}",
                  f"baseline {r['baseline']['whole_design_within_tolerance']:.0%}", delta_color="off")
        rows = [{"component": LABEL[t], "metric": k, "model": r["model"][t][k], "baseline": r["baseline"][t][k]}
                for t in TARGETS for k in r["model"][t]]
        st.dataframe(pd.DataFrame(rows), hide_index=True)
