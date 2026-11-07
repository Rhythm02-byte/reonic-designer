"""Baseline installer policies (no learning beyond medians). Shared by the API and eval/.

B0   median bundle of the installer            -> median_bundle()
B0c  median bundle conditioned on simple rules -> conditioned()   (what /design serves as "baseline-0")
B1   rule of thumb from demand                 -> rule_of_thumb()
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping

import numpy as np
import pandas as pd

HP_SIZES = [5.0, 7.0, 10.0, 12.0]
HP_FULL_LOAD_HOURS = 2200.0
BUCKET_EDGES = [3500.0, 5000.0, 7000.0]  # kWh/year -> 4 demand buckets
FOSSIL = {"Gas", "Oil", "OtherNonRenewable"}
MIN_BUCKET_N = 8


@dataclass
class Pred:
    kwp: float
    battery_kwh: float
    wallbox: bool
    hp_kw: float


@dataclass
class Stats:
    installer_id: str
    n: int
    kwp: dict[int, tuple[float, float, float]]          # bucket (-1 = all) -> p10, p50, p90 (PV options only)
    battery: dict[int, tuple[float, float, float]]      # among options with a battery
    battery_share: dict[int, float]
    battery_sizes: list[float]                          # frequent installed battery sizes
    battery_step: float
    wallbox_share: float
    module_wp: float = 450.0
    extra: dict = field(default_factory=dict)


# Used only when no processed data is available at all (aggregates from PLAN section 2.5).
FALLBACK = Stats(
    installer_id="fallback", n=0,
    kwp={-1: (5.4, 9.0, 14.4)}, battery={-1: (5.0, 7.0, 14.0)}, battery_share={-1: 0.9},
    battery_sizes=[5.0, 7.0, 10.0, 14.0, 15.0], battery_step=2.5, wallbox_share=0.25,
)


def demand_bucket(demand_kwh: float) -> int:
    return int(np.digitize([demand_kwh], BUCKET_EDGES)[0])


def _q(x: pd.Series) -> tuple[float, float, float]:
    return tuple(float(v) for v in np.quantile(x.dropna(), [0.1, 0.5, 0.9]))  # type: ignore[return-value]


def fit_stats(df: pd.DataFrame, installer_id: str) -> Stats:
    """df: primary options joined with project inputs (needs demand_kwh, has_pv, kwp, has_battery, battery_kwh, has_wallbox)."""
    df = df.dropna(subset=["demand_kwh"])
    b = df.demand_kwh.map(demand_bucket)
    kwp, bat, share = {}, {}, {}
    for key, m in [(-1, pd.Series(True, index=df.index))] + [(k, b == k) for k in range(len(BUCKET_EDGES) + 1)]:
        pv, bt = df[m & df.has_pv], df[m & df.has_battery]
        if key == -1 or len(pv) >= MIN_BUCKET_N:
            kwp[key] = _q(pv.kwp)
        if key == -1 or len(bt) >= MIN_BUCKET_N:
            bat[key] = _q(bt.battery_kwh)
        if key == -1 or m.sum() >= MIN_BUCKET_N:
            share[key] = float(df[m].has_battery.mean())
    sizes = df.loc[df.has_battery, "battery_kwh"].round(1).value_counts(normalize=True)
    freq = sorted(float(s) for s in sizes[sizes >= 0.02].index)
    step = float(np.median(np.diff(freq))) if len(freq) > 1 else 1.0
    return Stats(installer_id, len(df), kwp, bat, share, freq or [float(bat[-1][1])], max(step, 1.0),
                 float(df.has_wallbox.mean()))


def pool_stats(dfs: list[pd.DataFrame], installer_id: str = "all") -> Stats:
    return fit_stats(pd.concat(dfs, ignore_index=True), installer_id)


def snap(value: float, options: list[float]) -> float:
    return float(min(options, key=lambda o: abs(o - value)))


def hp_rule(home: Mapping) -> float:
    """HP only with fossil heating and a known heat demand: kW = heat demand / full-load hours, snapped to catalog sizes."""
    heat = home.get("heat_demand_kwh")
    if home.get("heating_type") not in FOSSIL or heat is None or pd.isna(heat) or heat <= 0:
        return 0.0
    return snap(heat / HP_FULL_LOAD_HOURS, HP_SIZES)


def _pick(table: dict, bucket: int):
    return table.get(bucket, table[-1])


def median_bundle(s: Stats) -> Pred:
    return Pred(_pick(s.kwp, -1)[1], snap(_pick(s.battery, -1)[1], s.battery_sizes) if _pick(s.battery_share, -1) >= 0.5 else 0.0,
                s.wallbox_share >= 0.5, 0.0)


def conditioned(s: Stats, home: Mapping) -> Pred:
    k = demand_bucket(home["demand_kwh"])
    has_bat = _pick(s.battery_share, k) >= 0.5
    ev = bool(home.get("has_ev")) and not bool(home.get("has_existing_wallbox"))
    return Pred(_pick(s.kwp, k)[1], snap(_pick(s.battery, k)[1], s.battery_sizes) if has_bat else 0.0, ev, hp_rule(home))


def rule_of_thumb(s: Stats, home: Mapping) -> Pred:
    mwh = home["demand_kwh"] / 1000.0
    kwp = float(np.clip(round((1.5 * mwh + 2.5 + (2.0 if home.get("has_ev") else 0.0)) * 2) / 2, 4.0, 25.0))
    ev = bool(home.get("has_ev")) and not bool(home.get("has_existing_wallbox"))
    return Pred(kwp, snap(kwp * 1.0, s.battery_sizes), ev, hp_rule(home))
