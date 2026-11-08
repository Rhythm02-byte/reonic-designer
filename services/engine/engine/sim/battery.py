"""Vectorised greedy battery dispatch (S1) across many battery sizes in one pass over 8,760 h.

Order (Reonic): PV -> household load -> battery -> grid; battery -> load when PV is short.
Defaults (research/battery-and-simulations.md): LFP, usable 92% of nominal, AC->stored 0.957,
stored->AC 0.952, standby 13 W (grid-drawn), power 0.5 C but at least 2.5 kW, fade 2%/yr.
SoC is tracked in usable kWh (0..usable). The optional feed-in cap (60% of kWp without smart meter,
Solarspitzengesetz) curtails the surplus left after the battery has taken its share.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class BatteryParams:
    usable: float = 0.92
    eta_charge: float = 0.957
    eta_discharge: float = 0.952
    standby_kw: float = 0.013
    c_rate: float = 0.5
    min_power_kw: float = 2.5
    fade_per_year: float = 0.02


DEFAULT = BatteryParams()


def dispatch(net: np.ndarray, nominal_kwh, p: BatteryParams = DEFAULT):
    """Greedy dispatch. ``net`` = pv - load, shape (T,) shared by all sizes or (T, B) per size.

    Returns (charge_ac, discharge_ac, soc), each (T, B): AC energy taken from the surplus, AC
    energy delivered to the load, and usable-kWh state of charge at the end of each hour.
    """
    nom = np.atleast_1d(np.asarray(nominal_kwh, float))
    B = nom.size
    U = p.usable * nom
    P = np.where(nom > 0, np.maximum(p.c_rate * nom, p.min_power_kw), 0.0)
    kc, kd = 1.0 / p.eta_charge, p.eta_discharge
    ec, ird = p.eta_charge, 1.0 / p.eta_discharge
    T = net.shape[0]
    C = np.zeros((T, B))
    D = np.zeros((T, B))
    S = np.zeros((T, B))
    s = np.zeros(B)
    if not np.any(nom > 0):  # no battery: nothing to dispatch
        return C, D, S
    mn = np.minimum
    if net.ndim == 1:
        for h, n in enumerate(net.tolist()):
            if n > 0.0:
                c = mn(mn(P, n), (U - s) * kc)
                s = s + c * ec
                C[h] = c
            elif n < 0.0:
                d = mn(mn(P, -n), s * kd)
                s = s - d * ird
                D[h] = d
            S[h] = s
    else:
        npos = np.maximum(net, 0.0)
        nneg = np.maximum(-net, 0.0)
        for h in range(T):
            c = mn(mn(P, npos[h]), (U - s) * kc)
            d = mn(mn(P, nneg[h]), s * kd)
            s = s + c * ec - d * ird
            C[h] = c
            D[h] = d
            S[h] = s
    return C, D, S


def flows(pv: np.ndarray, load: np.ndarray, nominal_kwh, feed_in_cap_kw=None,
          p: BatteryParams = DEFAULT, hourly: bool = False) -> dict:
    """Annual energy flows per battery size.

    ``pv``/``load``: (T,) or (T, B) in kWh per hour; ``nominal_kwh``: scalar or (B,) (0 = no battery).
    ``feed_in_cap_kw``: None, scalar or (B,) maximum export power; excess is curtailed.
    Returns dict of (B,) arrays: pv, load, import_kwh (incl. standby), grid_to_load, export,
    curtailed, self_consumed, self_consumption, autarky, cycles, empty_share_06, charge_ac,
    discharge_ac, standby_kwh, battery_loss_kwh, delta_soc; plus ``hourly`` dict of (T, B) arrays
    when ``hourly=True``.
    """
    pv = np.asarray(pv, float)
    load = np.asarray(load, float)
    nom = np.atleast_1d(np.asarray(nominal_kwh, float))
    B = nom.size
    net = pv - load
    C, D, S = dispatch(net, nom, p)
    pv2 = pv if pv.ndim == 2 else pv[:, None]
    load2 = load if load.ndim == 2 else load[:, None]
    npos = np.maximum(net, 0.0)
    nneg = np.maximum(-net, 0.0)
    if net.ndim == 1:
        npos, nneg = npos[:, None], nneg[:, None]
    export_raw = npos - C
    grid_to_load_h = nneg - D
    has_bat = nom > 0
    standby_h = np.where(has_bat, p.standby_kw, 0.0)
    if feed_in_cap_kw is None:
        curt_h = np.zeros_like(export_raw)
    else:
        curt_h = np.maximum(export_raw - np.asarray(feed_in_cap_kw, float), 0.0)
    export_h = export_raw - curt_h
    T = net.shape[0]
    pv_sum = np.broadcast_to(pv2.sum(0), (B,)).copy()
    load_sum = np.broadcast_to(load2.sum(0), (B,)).copy()
    export = export_h.sum(0)
    curt = curt_h.sum(0)
    g2l = grid_to_load_h.sum(0)
    standby = standby_h * T
    U = p.usable * nom
    ch, dis = C.sum(0), D.sum(0)
    with np.errstate(divide="ignore", invalid="ignore"):
        # fractions are 0..1 by definition; clip float noise (no PV gave autarky -2e-16, which broke recommend_battery)
        sc = np.clip(np.where(pv_sum > 0, (pv_sum - export - curt) / pv_sum, 0.0), 0.0, 1.0)
        aut = np.clip(np.where(load_sum > 0, 1.0 - g2l / load_sum, 0.0), 0.0, 1.0)
        cycles = np.where(U > 0, dis / p.eta_discharge / U, 0.0)
        empty = np.where(U > 0, (S[5::24] <= 0.02 * U).mean(0), 1.0)
    out = {
        "pv": pv_sum, "load": load_sum, "import_kwh": g2l + standby, "grid_to_load": g2l,
        "export": export, "curtailed": curt, "self_consumed": pv_sum - export - curt,
        "self_consumption": sc, "autarky": aut, "cycles": cycles, "empty_share_06": empty,
        "charge_ac": ch, "discharge_ac": dis, "standby_kwh": standby,
        "battery_loss_kwh": ch - dis - S[-1], "delta_soc": S[-1],
    }
    if hourly:
        out["hourly"] = {"charge": C, "discharge": D, "soc": S, "import": grid_to_load_h + standby_h,
                         "export": export_h, "curtailed": curt_h}
    return out
