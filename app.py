"""Planner UI:  streamlit run app.py"""
import json
import os
from pathlib import Path

import pandas as pd
import streamlit as st

from reonic import data, synth
from reonic.engine import Designer
from reonic.model import ORDER
from reonic.schema import HEATING_TYPES, LABEL, LOAD_PROFILES, TARGETS, UNIT, HomeInputs

DATA = Path(os.environ.get("REONIC_DATA", data.default_data_path()))
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
    st.warning("Running on SYNTHETIC data. Put the Reonic export in data/raw/ for real results.")

with st.sidebar:
    st.header("The home")
    unknown = "unknown"
    heating = st.selectbox("Current heating", (unknown,) + HEATING_TYPES)
    inp = HomeInputs(
        annual_consumption_kwh=st.number_input("Annual consumption (kWh)", min_value=0.0, value=4500.0, step=100.0),
        electricity_price_eur_kwh=st.number_input("Electricity price (€/kWh)", min_value=0.0, value=0.35, step=0.01, format="%.3f"),
        energy_price_increase=st.number_input("Expected price increase per year", min_value=0.0, value=0.03, step=0.01, format="%.2f"),
        has_ev=st.checkbox("Electric car (now or planned)"),
        ev_km_per_year=st.number_input("EV km per year", min_value=0.0, value=None, step=1000.0, placeholder=unknown),
        has_flexible_tariff=st.checkbox("Dynamic / flexible tariff"),
        load_profile=st.selectbox("Load profile", LOAD_PROFILES),
        heating_type=None if heating == unknown else heating,
        heating_demand_kwh=st.number_input("Heating demand (kWh/yr)", min_value=0.0, value=None, step=500.0, placeholder=unknown),
        existing_pv_kwp=st.number_input("Existing PV (kWp)", min_value=0.0, value=0.0, step=0.5),
        existing_battery_kwh=st.number_input("Existing battery (kWh)", min_value=0.0, value=0.0, step=0.5),
        has_existing_wallbox=st.checkbox("Already has a wallbox"),
    )

tab_plan, tab_check, tab_eval = st.tabs(["Design", "Validate & compare", "Evaluation"])

with tab_plan:
    st.caption("Override any component; everything downstream re-plans around it.")
    locked = {}
    for col, t in zip(st.columns(len(ORDER)), ORDER):
        with col:
            if st.checkbox(f"Override {LABEL[t].lower()}", key=f"lock_{t}"):
                locked[t] = st.number_input(f"{LABEL[t]} ({UNIT[t]})", min_value=0.0, value=0.0, step=0.5, key=f"val_{t}")

    d = designer.design(inp, locked)
    for col, t in zip(st.columns(len(ORDER)), ORDER):
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
    c = st.columns(len(TARGETS))
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
