"""Expert-match metrics (PLAN section 10.2). Pure functions over predictions and ETL option rows."""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.metrics import f1_score, fbeta_score, precision_score, recall_score

from engine.baseline import HP_SIZES, Pred


def closeness(pred: float, expert: float, scale: float) -> float:
    return float(max(0.0, 1.0 - abs(pred - expert) / scale))


def kwp_closeness(p: Pred, o) -> float:
    if not o.has_pv:
        return 1.0 if p.kwp == 0 else 0.0
    return closeness(p.kwp, o.kwp, 0.2 * o.kwp)


def battery_closeness(p: Pred, o) -> float:
    return closeness(p.battery_kwh, o.battery_kwh, max(2.0, 0.3 * o.battery_kwh))


def hp_closeness(p: Pred, o) -> float:
    if o.hp_kw <= 0 or p.hp_kw <= 0:
        return 1.0 if (o.hp_kw <= 0) == (p.hp_kw <= 0) else 0.0
    return closeness(p.hp_kw, o.hp_kw, max(2.0, 0.3 * o.hp_kw))


def bundle_match(p: Pred, o) -> float:
    return float((p.battery_kwh > 0) == bool(o.has_battery) and p.wallbox == bool(o.has_wallbox) and (p.hp_kw > 0) == (o.hp_kw > 0))


def expert_match(p: Pred, o) -> float:
    """0-100: mean of bundle match, kWp, battery and heat-pump closeness."""
    return 100.0 * float(np.mean([bundle_match(p, o), kwp_closeness(p, o), battery_closeness(p, o), hp_closeness(p, o)]))


def _size_idx(kw: float) -> int:
    return int(np.argmin([abs(kw - s) for s in HP_SIZES]))


def evaluate(projects: pd.DataFrame, options: pd.DataFrame, preds: dict, steps: dict, runtimes_ms: list[float]) -> dict:
    """projects: one row per test project; options: all options of those projects (is_primary flagged).
    preds: project_id -> Pred; steps: project_id -> battery tolerance (installer step, kWh)."""
    prim = options[options.is_primary].set_index("project_id")
    by_proj = {pid: g for pid, g in options.groupby("project_id")}
    ids = [pid for pid in projects.project_id if pid in preds and pid in prim.index]
    P = [preds[i] for i in ids]
    T = [prim.loc[i] for i in ids]

    ems_primary = [expert_match(p, o) for p, o in zip(P, T)]
    ems_any = [max(expert_match(preds[i], o) for o in g.itertuples()) for i in ids for g in [by_proj[i]]]

    out: dict = {"nProjects": len(ids), "expertMatchPrimary": _m(ems_primary), "expertMatchAny": _m(ems_any),
                 "bundleExactMatch": _m([bundle_match(p, o) for p, o in zip(P, T)])}
    for name, pf, tf in (("battery", lambda p: p.battery_kwh > 0, lambda o: bool(o.has_battery)),
                         ("wallbox", lambda p: p.wallbox, lambda o: bool(o.has_wallbox)),
                         ("heatPump", lambda p: p.hp_kw > 0, lambda o: o.hp_kw > 0)):
        y, yh = [tf(o) for o in T], [pf(p) for p in P]
        out[name] = {"accuracy": _m([a == b for a, b in zip(y, yh)]), "f1": float(f1_score(y, yh, zero_division=0)),
                     "nPositive": int(sum(y)), "nPredicted": int(sum(yh))}

    pv = [(p, o) for p, o in zip(P, T) if o.has_pv]
    d = np.array([p.kwp - o.kwp for p, o in pv])
    ex = np.array([o.kwp for _, o in pv])
    out["kwp"] = {"n": len(pv), "mae": _m(np.abs(d)), "medianAbsError": float(np.median(np.abs(d))) if len(d) else None,
                  "within10pctOr2Modules": _m(np.abs(d) <= np.maximum(0.1 * ex, 0.9))}
    bt = [(p, o, steps[i]) for i, p, o in zip(ids, P, T) if o.has_battery]
    bd = np.array([p.battery_kwh - o.battery_kwh for p, o, _ in bt])
    out["batteryKwh"] = {"n": len(bt), "mae": _m(np.abs(bd)), "withinOneStep": _m([abs(x) <= s + 1e-9 for x, (_, _, s) in zip(bd, bt)])}
    hp = [(p, o) for p, o in zip(P, T) if o.hp_kw > 0]
    out["heatPumpKw"] = {"n": len(hp), "withinOneSize": _m([p.hp_kw > 0 and abs(_size_idx(p.hp_kw) - _size_idx(o.hp_kw)) <= 1 for p, o in hp])}
    out["runtimeMs"] = {"p50": float(np.percentile(runtimes_ms, 50)), "p95": float(np.percentile(runtimes_ms, 95))} if runtimes_ms else None
    return out


def _m(x) -> float | None:
    x = np.asarray(list(x), dtype=float)
    return float(x.mean()) if len(x) else None


# ---- teammate's metrics (reonic-designer evaluate.py), ported ---------------------------------------------------------
# A size counts as "matches the expert" within this relative tolerance (and both agree on include/exclude).
# Wallbox: only include/exclude counts (11 vs 22 kW is a customer choice, not design skill).
TOLERANCE = {"pv_kwp": 0.20, "battery_kwh": 0.25, "heat_pump_kw": 0.25, "wallbox_kw": float("inf")}
TARGETS = ("pv_kwp", "battery_kwh", "heat_pump_kw", "wallbox_kw")


def pred_frame(preds: dict, ids: list) -> pd.DataFrame:
    """project_id -> Pred  ->  target columns (wallbox: 11 kW when included)."""
    return pd.DataFrame({"pv_kwp": [preds[i].kwp for i in ids], "battery_kwh": [preds[i].battery_kwh for i in ids],
                         "heat_pump_kw": [preds[i].hp_kw for i in ids], "wallbox_kw": [11.0 if preds[i].wallbox else 0.0 for i in ids]},
                        index=ids)


def policy_metrics(pred: pd.DataFrame, truth: pd.DataFrame, lo: pd.DataFrame | None = None, hi: pd.DataFrame | None = None) -> dict:
    """whole_design_within_tolerance (PV +-20%, battery +-25%, HP +-25%, wallbox include only), per-component
    within_tolerance, include F1/F2, size MAE, and (when lo/hi given) p10-p90 coverage of the expert size.
    NaN truth = offered but size unknown: only include/exclude is scored."""
    out, all_ok = {}, np.ones(len(truth), dtype=bool)
    for t in TARGETS:
        y, p = truth[t].to_numpy(float), pred[t].to_numpy(float)
        known = ~np.isnan(y)
        has_y, has_p = (y > 0) | ~known, p > 0
        both = has_y & has_p & known
        rel = np.abs(p - np.nan_to_num(y)) / np.where(y > 0, y, 1)
        ok = np.where(has_y, has_p & (~known | (rel <= TOLERANCE[t])), ~has_p)
        all_ok &= ok
        m = {
            "includeAccuracy": float((has_y == has_p).mean()),
            "includePrecision": float(precision_score(has_y, has_p, zero_division=0)),
            "includeRecall": float(recall_score(has_y, has_p, zero_division=0)),
            "includeF1": float(f1_score(has_y, has_p, zero_division=0)),
            "includeF2": float(fbeta_score(has_y, has_p, beta=2.0, zero_division=0)),
            "sizeMae": float(np.abs(p - y)[both].mean()) if both.any() else None,
            "expertIncludeRate": float(has_y.mean()),
            "withinTolerance": float(ok.mean()),
        }
        if lo is not None and hi is not None and t != "wallbox_kw":
            sized = has_y & known & (y > 0)
            m["p10p90Coverage"] = float(((y >= lo[t].to_numpy()) & (y <= hi[t].to_numpy()))[sized].mean()) if sized.any() else None
            m["nCoverage"] = int(sized.sum())
        out[t] = m
    out["wholeDesignWithinTolerance"] = float(all_ok.mean())
    return out
