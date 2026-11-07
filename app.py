"""Planner UI:  streamlit run app.py

The model here is trained on the training split only (the same 80/20 split as `python -m reonic eval`).
The example homes in the sidebar come from the 20% it has never seen, so what you see is an honest comparison.
"""
import json
import os
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

from reonic import data, evaluate, synth
from reonic.baseline import rule_of_thumb
from reonic.engine import Designer
from reonic.model import ORDER
from reonic.schema import HEATING_TYPES, LABEL, LOAD_PROFILES, TARGETS, UNIT, HomeInputs

DATA = Path(os.environ.get("REONIC_DATA", data.default_data_path()))
REPORTS = Path("reports")
UNKNOWN = "unknown"
CUSTOM = "Enter your own home"
TOLERANCE = {"pv_kwp": 0.20, "battery_kwh": 0.25, "heat_pump_kw": 0.25}


def _num(v):
    return None if v is None or (isinstance(v, float) and np.isnan(v)) or v is pd.NA else float(v)


def _flag(v) -> bool:
    return bool(v) if v is not None and not (isinstance(v, float) and np.isnan(v)) and v is not pd.NA else False


def agrees(t: str, expert: float, ours: float) -> bool:
    """Same include/exclude, and for sized components within the evaluation tolerance."""
    if np.isnan(expert):  # offered, size unknown
        return ours > 0
    if expert > 0:
        return ours > 0 and (t not in TOLERANCE or abs(ours - expert) / expert <= TOLERANCE[t])
    return ours == 0


@st.cache_resource
def get_demo():
    """Designer trained on the training split, plus the held-out homes and its predictions on them."""
    if not DATA.exists() and DATA.name == "synthetic.csv":
        synth.generate().to_csv(DATA, index=False)
    df = data.load(DATA)
    train, test = evaluate.split(df, 0.2, 0, None)
    designer = Designer.train(train)
    return designer, len(train), test, designer.design_batch(test)


def pick_examples(test: pd.DataFrame, pred: pd.DataFrame) -> dict[str, int]:
    """A few held-out homes that tell the story, including one where we disagree with the expert."""
    ok = pd.DataFrame({t: [agrees(t, e, o) for e, o in zip(test[t], pred[t])] for t in TARGETS}, index=test.index)
    demand = test["annual_consumption_kwh"]
    not_placeholder = demand != 4500  # 4,500 kWh looks like a default value in the export
    ev = test["has_ev"].astype(float).fillna(0) == 1
    ex: dict[str, int] = {}

    typical = test[ok.all(axis=1) & demand.between(3000, 8000) & not_placeholder & ~ev & (test["existing_pv_kwp"] == 0)]
    if len(typical):
        ex["Typical home: we match the expert"] = (typical["annual_consumption_kwh"] - 5000).abs().idxmin()
    ev_homes = test[ev & (test["wallbox_kw"] > 0) & ok["pv_kwp"] & ok["battery_kwh"]]
    if len(ev_homes):
        ex["Home with an EV and a wallbox"] = ev_homes.index[0]
    hp = test[test["heat_pump_kw"] > 0]
    hp_idx = hp.index[0] if len(hp) else None
    has_pv = test[(test["existing_pv_kwp"] > 0) & (test.index != hp_idx)]  # keep each example a different home
    if len(has_pv):
        ex["Home that already has PV"] = has_pv.index[0]
    if hp_idx is not None:
        ex["Where we disagree: expert chose a heat pump"] = hp_idx
    return ex


def load_example(test: pd.DataFrame, examples: dict[str, int]) -> None:
    """Callback: copy a held-out home's inputs into the sidebar widgets."""
    choice = st.session_state["example"]
    if choice == CUSTOM:
        return
    r = test.loc[examples[choice]]
    ss = st.session_state
    ss["heating"] = r["heating_type"] if isinstance(r["heating_type"], str) else UNKNOWN
    ss["consumption"] = _num(r["annual_consumption_kwh"])
    ss["price"] = _num(r["electricity_price_eur_kwh"]) or 0.35
    ss["increase"] = _num(r["energy_price_increase"]) or 0.03
    ss["has_ev"] = _flag(r["has_ev"])
    ss["ev_km"] = _num(r["ev_km_per_year"])
    ss["flex"] = _flag(r["has_flexible_tariff"])
    ss["profile"] = r["load_profile"] if r["load_profile"] in LOAD_PROFILES else LOAD_PROFILES[0]
    ss["heat_demand"] = _num(r["heating_demand_kwh"])
    ss["pv_existing"] = _num(r["existing_pv_kwp"]) or 0.0
    ss["bat_existing"] = _num(r["existing_battery_kwh"]) or 0.0
    ss["wb_existing"] = _flag(r["has_existing_wallbox"])


st.set_page_config(page_title="Home Energy Designer", layout="wide")
st.title("Home energy designer")
designer, n_train, test, test_pred = get_demo()
examples = pick_examples(test, test_pred)
if DATA.name == "synthetic.csv":
    st.warning("Running on SYNTHETIC data. Put the Reonic export in data/raw/ for real results.")

for key, default in {"heating": UNKNOWN, "consumption": 4500.0, "price": 0.35, "increase": 0.03, "has_ev": False,
                     "ev_km": None, "flex": False, "profile": LOAD_PROFILES[0], "heat_demand": None,
                     "pv_existing": 0.0, "bat_existing": 0.0, "wb_existing": False}.items():
    st.session_state.setdefault(key, default)

with st.sidebar:
    st.header("The home")
    st.caption(f"Model trained on {n_train:,} projects. The examples below are from {len(test):,} projects it has never seen.")
    st.selectbox("Start from an example", [CUSTOM] + list(examples), key="example",
                 on_change=load_example, args=(test, examples))
    heating = st.selectbox("Current heating", (UNKNOWN,) + HEATING_TYPES, key="heating")
    inp = HomeInputs(
        annual_consumption_kwh=st.number_input("Annual consumption (kWh)", min_value=0.0, step=100.0, value=None,
                                               placeholder=UNKNOWN, key="consumption"),
        electricity_price_eur_kwh=st.number_input("Electricity price (€/kWh)", min_value=0.0, step=0.01, format="%.3f", key="price"),
        energy_price_increase=st.number_input("Expected price increase per year", min_value=0.0, step=0.01, format="%.2f", key="increase"),
        has_ev=st.checkbox("Electric car (now or planned)", key="has_ev"),
        ev_km_per_year=st.number_input("EV km per year", min_value=0.0, step=1000.0, value=None, placeholder=UNKNOWN, key="ev_km"),
        has_flexible_tariff=st.checkbox("Dynamic / flexible tariff", key="flex"),
        load_profile=st.selectbox("Load profile", LOAD_PROFILES, key="profile"),
        heating_type=None if heating == UNKNOWN else heating,
        heating_demand_kwh=st.number_input("Heating demand (kWh/yr)", min_value=0.0, step=500.0, value=None,
                                           placeholder=UNKNOWN, key="heat_demand"),
        existing_pv_kwp=st.number_input("Existing PV (kWp)", min_value=0.0, step=0.5, key="pv_existing"),
        existing_battery_kwh=st.number_input("Existing battery (kWh)", min_value=0.0, step=0.5, key="bat_existing"),
        has_existing_wallbox=st.checkbox("Already has a wallbox", key="wb_existing"),
    )

tab_plan, tab_check, tab_eval = st.tabs(["Design", "Validate & compare", "Evaluation"])

with tab_plan:
    st.caption("Override any component; everything downstream re-plans around it. The wallbox follows a fixed rule: a wallbox if the home has an EV.")
    locked = {}
    for col, t in zip(st.columns(len(ORDER)), ORDER):
        with col:
            if st.checkbox(f"Override {LABEL[t].lower()}", key=f"lock_{t}"):
                locked[t] = st.number_input(f"{LABEL[t]} ({UNIT[t]})", min_value=0.0, value=0.0, step=0.5, key=f"val_{t}")

    d = designer.design(inp, locked)
    for col, t in zip(st.columns(len(ORDER)), ORDER):
        v = getattr(d, t)
        if t in locked:
            note = "planner override"
        elif t == "wallbox_kw":
            note = "rule: has an EV" if v > 0 else "rule: no EV"
        else:
            note = f"{d.probability[t]:.0%} likely"
        col.metric(LABEL[t], f"{v:g} {UNIT[t]}" if v > 0 else "none", note, delta_color="off")
    st.subheader("Why")
    st.markdown("\n".join(f"- {line}" for line in d.explanation))
    if d.rules_applied:
        st.subheader("Rules applied")
        st.markdown("\n".join(f"- {r}" for r in d.rules_applied))
    for f in d.flags:
        st.warning(f)

with tab_check:
    example = st.session_state.get("example", CUSTOM)
    st.subheader("Compare with what the installer delivered")
    if example == CUSTOM:
        st.info("Pick an example home in the sidebar to see our design next to the expert's. "
                "Change any input and the design updates; the expert's design stays fixed.")
    else:
        idx = examples[example]
        expert = test.loc[idx]
        base = rule_of_thumb(test.loc[[idx]]).iloc[0]
        rows = []
        for t in TARGETS:
            e, o = float(expert[t]), float(getattr(d, t))
            rows.append({"Component": f"{LABEL[t]} ({UNIT[t]})",
                         "Expert": "unknown size" if np.isnan(e) else f"{e:g}",
                         "Ours (live)": f"{o:g}", "Baseline": f"{float(base[t]):g}",
                         "Agrees": "yes" if agrees(t, e, o) else "no"})
        st.dataframe(pd.DataFrame(rows), hide_index=True)
        st.caption("The expert's design is for the home as it was loaded. If you change an input, differences from the expert are expected.")
        st.caption(f"Installer {expert['installer_id']}. 'Agrees' means the same include/exclude and, for PV, battery and heat pump, "
                   "a size within the evaluation tolerance (PV ±20%, battery and heat pump ±25%). "
                   "This home was not used to train the model.")

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

with tab_eval:
    path = REPORTS / "eval.json"
    if not path.exists():
        st.info("Run `python -m reonic eval` first.")
    else:
        r = json.loads(path.read_text())
        st.caption(f"Trained on {r['n_train']} projects, tested on {r['n_test']} unseen projects (random split).")
        st.metric("Whole design within tolerance", f"{r['model']['whole_design_within_tolerance']:.0%}",
                  f"baseline {r['baseline']['whole_design_within_tolerance']:.0%}", delta_color="off")
        rows = [{"component": LABEL[t], "metric": k, "model": r["model"][t][k], "baseline": r["baseline"][t][k]}
                for t in TARGETS for k in r["model"][t]]
        st.dataframe(pd.DataFrame(rows), hide_index=True)
        if "by_installer" in r:
            st.caption("Whole design per installer: " + ", ".join(f"{k}: {v:.0%}" for k, v in r["by_installer"].items()))
