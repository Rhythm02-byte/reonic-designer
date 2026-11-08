"""Joint PV + battery decision (idea 2).

Default chain: PV = coverage/median size, then battery given that PV, each maximised on its own. Here, for every PV
candidate c (the nine predicted PV quantiles), the battery quantiles are predicted WITH PV = c, the battery size b(c) is
the coverage size, and the pair maximising P(PV hit) * P(battery hit) wins (P = share of the quantile samples within
tolerance). `samples_gate` also decides battery inclusion jointly: max(p_bat * hit_b(c), 1 - p_bat).
Include decisions for PV, heat pump and wallbox stay the default's; rules + snapping run on the result.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from engine.policy.chain import COVERAGE_QUANTILES, SIZE_TOLERANCE, coverage_size
from research.lib import TARGETS, apply_rules, predictor, train_designer

KIND = "post-processor"
SETTINGS = {"samples": {"gate": False}, "samples_gate": {"gate": True}}
COV = {"sizing": {"coverage": ["pv", "battery"]}}


def _q(model, t, Xc):
    cols = model.steps[t][4]
    return np.sort(np.clip(np.column_stack([m.predict(Xc[cols]) for m in model.quants[t]]), 0, None), axis=1)


def fit(train: pd.DataFrame, setting: dict, ctx):
    dz = train_designer(train, config=COV)  # same default config + PV quantile models
    base = predictor(dz)
    m = dz.model
    tp, tb = SIZE_TOLERANCE["pv_kwp"], SIZE_TOLERANCE["battery_kwh"]
    bcat = np.asarray(dz.catalog.get("battery_kwh") or [], float)

    def predict(test: pd.DataFrame):
        sizes, extra = base(test)
        if "pv_kwp" not in m.quants or "battery_kwh" not in m.quants:
            return sizes, extra
        Xc = dz._X(test)[m.cols].copy()
        Xc["heat_pump_kw"] = sizes["heat_pump_kw"].to_numpy(float)
        S = _q(m, "pv_kwp", Xc)                                     # (n, 9) plausible expert PV sizes
        n, K = S.shape
        best = np.full(n, -1.0)
        pv, bat = sizes["pv_kwp"].to_numpy(float).copy(), sizes["battery_kwh"].to_numpy(float).copy()
        p_bat = extra["p_battery_kwh"].to_numpy(float)
        inc_pv = pv > 0
        inc_bat = bat > 0
        for j in range(K):
            c = S[:, j]
            hp = ((c[:, None] >= S * (1 - tp) - 1e-12) & (c[:, None] <= S * (1 + tp) + 1e-12)).mean(axis=1)
            Xc["pv_kwp"] = c
            B = _q(m, "battery_kwh", Xc)
            b = coverage_size(B, tb, bcat if len(bcat) else None)
            hb = ((b[:, None] >= B * (1 - tb) - 1e-12) & (b[:, None] <= B * (1 + tb) + 1e-12)).mean(axis=1)
            if setting["gate"]:
                with_b, without = p_bat * hb, 1 - p_bat
                score = hp * np.maximum(with_b, without)
                choose_b = np.where(with_b >= without, b, 0.0)
            else:
                score = hp * np.where(inc_bat, hb, 1.0)
                choose_b = np.where(inc_bat, b, 0.0)
            better = inc_pv & (score > best + 1e-12)
            best = np.where(better, score, best)
            pv = np.where(better, c, pv)
            bat = np.where(better, choose_b, bat)
        out = sizes.copy()
        out["pv_kwp"], out["battery_kwh"] = pv, bat
        return apply_rules(test, out[list(TARGETS)], dz.catalog), extra
    return predict
