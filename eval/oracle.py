"""Oracle experiment ("Ask next", PLAN 6.9): what is answering one question worth?

Test split (2026), the SELECTED model (config/policy.json, refit on train <= 2025-12-31, as in the selection test phase),
scored once, nothing tuned. For every askable field the same model designs the same test homes twice:
  unknown   the field is hidden / replaced by its placeholder
  answered  the real value (the unmodified test inputs)
Fields:
  demand  every demand replaced by the 4,500 kWh tool default                      (answer = the true demand)
  ev      the EV flag and distance blanked (unknown)                               (answer = the true flag)
  ev*     the EV flag set to "no" (what a planner who skips the question sends)   (extra row, same answer)
  heat    heat demand blanked for Gas / Oil homes                                  (answer = the true heat demand)
  roof    no roof cap                                                              (answer = cap at the expert's module count)
The roof row is an UPPER BOUND: the cap equals the expert's own kWp, so PV can never exceed the expert's size. A real answer
(a measured roof) is a looser cap and is worth less.

    python eval/run.py --oracle        (updates only the "oracle" block of eval/results/latest.json)
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from engine.policy.designer import Designer

KEYS = ("ems", "wholeDesign", "pv", "battery", "heatPump", "wallbox")


def _hide_ev(t: pd.DataFrame) -> pd.DataFrame:
    return t.assign(has_ev=None, ev_km=np.nan)


def _assume_no_ev(t: pd.DataFrame) -> pd.DataFrame:
    return t.assign(has_ev=False, ev_km=np.nan)


def _demand_placeholder(t: pd.DataFrame) -> pd.DataFrame:
    from engine.etl.normalize import DEFAULT_DEMAND_KWH
    return t.assign(demand_kwh=DEFAULT_DEMAND_KWH)


def _hide_heat(t: pd.DataFrame) -> pd.DataFrame:
    return t.assign(heat_demand_kwh=np.where(t["heating_type"].isin(["Gas", "Oil"]), np.nan, t["heat_demand_kwh"]))


def _roof_cap(t: pd.DataFrame) -> pd.DataFrame:
    kwp = pd.to_numeric(t["pv_kwp"], errors="coerce")
    return t.assign(roof_max_kwp=kwp.where(kwp > 0))


FIELDS = {  # name -> (unknown transform, applies to, note)
    "demand": (_demand_placeholder, None, "demand replaced by 4,500 kWh"),
    "ev": (_hide_ev, None, "EV flag and km blanked"),
    "evAssumedNo": (_assume_no_ev, None, "EV flag set to no"),
    "heat": (_hide_heat, lambda t: t["heating_type"].isin(["Gas", "Oil"]), "heat demand blanked (Gas/Oil homes)"),
    "roof": (None, None, "UPPER BOUND: cap = expert's module count; unknown = no cap"),
}


def run(R, P, O, D) -> dict:
    jobs = R.splits_temporal(P, O, D)
    train = pd.concat([j.train for j in jobs])
    dz = Designer.train(train)  # default config = config/policy.json (the selected composite)
    R.VARIANTS["ORC"] = lambda d: d

    def score(transform=None, subset=None):
        js = jobs
        if subset is not None:
            js = [R.Job(j.inst, j.train, j.test[subset(j.test)], j.stats) for j in jobs]
            js = [j for j in js if len(j.test)]
        r = R.run_split(js, O, models=("ORC",), designer=dz, transform=transform)
        return {**R.scores(r, "ORC"), "n": r["nTest"]}

    out = {"split": "temporal (test = offers after 2025-12-31)", "model": "composite (selected on validation), refit on train <= 2025-12-31",
           "nTest": int(sum(len(j.test) for j in jobs)), "fields": {}}
    for name, (unknown, subset, note) in FIELDS.items():
        if name == "roof":
            hidden, answered = score(None, subset), score(_roof_cap, subset)
            kind = "upperBound"
        else:
            hidden, answered = score(unknown, subset), score(None, subset)
            kind = "answer"
        out["fields"][name] = {"note": note, "kind": kind, "n": answered["n"], "unknown": hidden, "answered": answered,
                               "gain": {k: answered[k] - hidden[k] for k in KEYS}}
        print(f"oracle {name:<12} n={answered['n']:<4} EMS {hidden['ems']:.1f} -> {answered['ems']:.1f}  whole {100 * hidden['wholeDesign']:.1f} -> "
              f"{100 * answered['wholeDesign']:.1f}%  PV {100 * hidden['pv']:.1f} -> {100 * answered['pv']:.1f}%", flush=True)
    return out
