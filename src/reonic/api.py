"""JSON API for the web frontend:  uvicorn reonic.api:app --port 8000

Local only (uvicorn binds to 127.0.0.1 by default). The model artifact contains training
data, so this must never be exposed beyond the machine running the demo.
"""
import json
import math
from functools import cache
from pathlib import Path

import pandas as pd
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route
from threadpoolctl import threadpool_limits

from . import data, physics
from .engine import Designer
from .schema import (BOOL_FIELDS, HEATING_TYPES, INPUT_FIELDS, LABEL, LOAD_PROFILES, NUMERIC_FIELDS, TARGETS,
                     UNIT, HomeInputs)

MODEL = Path("models/designer.joblib")
REPORTS = Path("reports")
CHOICES = {"heating_type": HEATING_TYPES, "load_profile": LOAD_PROFILES}
MAX_SIZE = 1_000.0  # sanity bound for locked sizes (kWp / kWh / kW)


@cache
def designer() -> Designer:
    return Designer.load(MODEL) if MODEL.exists() else Designer.train(data.load(data.default_data_path()))


# -- input validation (trust boundary) ----------------------------------------------------------
def _number(name: str, v, upper: float = math.inf) -> float:
    if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) or not 0 <= v <= upper:
        raise ValueError(f"{name} must be a number between 0 and {upper:g}")
    return float(v)


def parse_inputs(raw) -> HomeInputs:
    if not isinstance(raw, dict):
        raise ValueError("inputs must be an object")
    if unknown := set(raw) - set(INPUT_FIELDS):
        raise ValueError(f"unknown input fields: {sorted(unknown)}")
    out = {}
    for k, v in raw.items():
        if v is None:  # unknown stays unknown
            continue
        if k in NUMERIC_FIELDS:
            out[k] = _number(k, v)
        elif k in BOOL_FIELDS:
            if not isinstance(v, bool):
                raise ValueError(f"{k} must be true, false or null")
            out[k] = v
        elif v not in CHOICES[k]:
            raise ValueError(f"{k} must be one of {CHOICES[k]}")
        else:
            out[k] = v
    return HomeInputs(**out)


def parse_sizes(raw, name: str) -> dict[str, float]:
    if not isinstance(raw, dict) or set(raw) - set(TARGETS):
        raise ValueError(f"{name} must be an object with keys from {TARGETS}")
    return {t: _number(f"{name}.{t}", v, MAX_SIZE) for t, v in raw.items()}


# -- economics shown next to every design --------------------------------------------------------
def economics(inp: HomeInputs, v: dict[str, float]) -> dict:
    """Rough cost and savings. Heat pump fuel savings are not modelled (see physics.py)."""
    cost = physics.capex_eur(v["pv_kwp"], v["battery_kwh"], v["heat_pump_kw"])
    cost += physics.CAPEX["wallbox"] if v["wallbox_kw"] > 0 else 0.0
    gen = physics.pv_yield_kwh(v["pv_kwp"])
    out = {"cost_eur": cost, "pv_yield_kwh": gen, "demand_kwh": None, "self_use_share": None,
           "solar_share_of_demand": None, "savings_eur": None, "payback_years": None}
    base = physics.num(inp.annual_consumption_kwh)
    if not base:  # unknown consumption: no savings estimate rather than a guessed one
        return out
    ev = physics.ev_demand_kwh(inp.has_ev, inp.ev_km_per_year)
    hd = physics.num(inp.heating_demand_kwh) or physics.heat_demand_kwh(inp.heated_area_m2)
    demand = base + ev + (physics.heat_pump_electricity_kwh(hd) if v["heat_pump_kw"] > 0 and hd else 0.0)
    sc = physics.self_consumption_ratio(demand, gen, v["battery_kwh"])
    save = physics.annual_pv_savings_eur(demand, v["pv_kwp"], v["battery_kwh"], inp.electricity_price_eur_kwh)
    pv_cost = physics.capex_eur(v["pv_kwp"], v["battery_kwh"], 0)
    return {**out, "demand_kwh": demand, "self_use_share": sc, "solar_share_of_demand": gen * sc / demand,
            "savings_eur": save, "payback_years": pv_cost / save if save > 0 else None}


# -- endpoints -------------------------------------------------------------------------------------
def meta(_body) -> dict:
    return {
        "fields": [{"name": f, "kind": "number" if f in NUMERIC_FIELDS else "bool" if f in BOOL_FIELDS else "choice",
                    "choices": list(CHOICES.get(f, ()))} for f in INPUT_FIELDS],
        "targets": [{"name": t, "label": LABEL[t], "unit": UNIT[t], "catalog": designer().catalog[t]} for t in TARGETS],
        "synthetic": not MODEL.exists() and data.default_data_path().endswith("synthetic.csv"),
    }


def design(body) -> dict:
    inp = parse_inputs(body.get("inputs", {}))
    locked = parse_sizes(body.get("locked", {}), "locked")
    d = designer().design(inp, locked)
    alts = {}
    for t in TARGETS:  # spec alternatives-confidence: one flip per component the planner hasn't locked
        sizes = sorted(designer().catalog[t])
        if t in locked or (getattr(d, t) == 0 and not sizes):
            continue
        alt = 0.0 if getattr(d, t) > 0 else sizes[len(sizes) // 2]
        a = designer().design(inp, {**locked, t: alt})
        alts[t] = {"value": alt, "values": a.values(), "flags": a.flags, "economics": economics(inp, a.values())}
    return {"values": d.values(), "probability": d.probability, "explanation": d.explanation,
            "rules_applied": d.rules_applied, "flags": d.flags, "economics": economics(inp, d.values()),
            "alternatives": alts}


def validate(body) -> dict:
    inp, values = parse_inputs(body.get("inputs", {})), parse_sizes(body.get("values", {}), "values")
    if set(values) != set(TARGETS):
        raise ValueError(f"values needs all of {TARGETS}")
    return {"flags": designer().validate(inp, values), "economics": economics(inp, values)}


def evaluation(_body) -> dict:
    path = REPORTS / "eval.json"
    return json.loads(path.read_text()) if path.exists() else {}


def holdout(_body) -> dict:
    path = REPORTS / "test_predictions.csv"
    if not path.exists():
        return {"rows": []}
    df = pd.read_csv(path, index_col=0)
    recs = df.astype(object).where(df.notna(), None).to_dict("records")
    typed = {f: bool if f in BOOL_FIELDS else float if f in NUMERIC_FIELDS else str for f in INPUT_FIELDS}
    return {"rows": [{
        "project_id": r["project_id"], "installer_id": r["installer_id"],
        "inputs": {f: None if r[f] is None else typed[f](r[f]) for f in INPUT_FIELDS},
        **{who: {t: r[f"{t}_{who}"] for t in TARGETS} for who in ("expert", "ours", "baseline")},
    } for r in recs]}


def _endpoint(fn):
    async def run(request: Request) -> JSONResponse:
        try:
            body = await request.json() if request.method == "POST" else {}
            if not isinstance(body, dict):
                raise ValueError("body must be a JSON object")
            with threadpool_limits(1):  # single-row predicts are ~13x faster without OpenMP fan-out
                return JSONResponse(fn(body))
        except ValueError as e:  # includes malformed JSON
            return JSONResponse({"error": str(e)}, status_code=400)
    return run


app = Starlette(routes=[
    Route("/api/meta", _endpoint(meta)),
    Route("/api/design", _endpoint(design), methods=["POST"]),
    Route("/api/validate", _endpoint(validate), methods=["POST"]),
    Route("/api/eval", _endpoint(evaluation)),
    Route("/api/holdout", _endpoint(holdout)),
])
