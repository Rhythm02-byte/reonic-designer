"""Physics-informed pieces for the learned policy: simulator-derived features, the simulator's economic battery, and the
installer-specific PV size prior. Pure functions over canonical input rows (see features.row_from_inputs).

Everything here is computed from the HOME INPUTS only (never from a target), so it can be used as a feature without leakage.
"""
from __future__ import annotations

import pickle
from pathlib import Path
from typing import Mapping

import numpy as np
import pandas as pd

from engine import baseline as bl
from engine import sim

PV_GRID = (2.0, 3.0, 4.0, 5.0, 6.0, 8.0, 10.0, 12.0, 14.0, 16.0, 20.0)
PHYSICS_COLS = ("sim_pv_opt_kwp", "sim_battery_opt_kwh")
_FAMILY = {"family": "FamilyOfFour", "home_office": "HomeOffice", "senior": "Senior"}
_CACHE: dict[str, tuple[float, float]] = {}
_BAT_CACHE: dict[str, float] = {}


def _f(x):
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    return None if np.isnan(v) else v


def sim_home(row: Mapping) -> dict:
    """Canonical input row -> the simulator's home dict (camelCase). Unknown stays absent (simulator defaults apply)."""
    home: dict = {"demandKwh": _f(row.get("demand_kwh")) or 4500.0, "loadProfile": _FAMILY.get(row.get("load_family"), "H0")}
    if _f(row.get("price_eur_kwh")) is not None:
        home["priceEurKwh"] = _f(row["price_eur_kwh"])
    if _f(row.get("price_escalation")) is not None:
        home["priceEscalation"] = _f(row["price_escalation"])
    if row.get("has_ev") is True or _f(row.get("has_ev")) == 1.0:
        home["ev"] = {"has": True, **({"kmPerYear": _f(row["ev_km"])} if _f(row.get("ev_km")) else {})}
    pv = _f(row.get("existing_pv_kwp")) or 0.0
    if row.get("has_existing_pv") and pv > 0:
        home["existingPv"] = {"kwp": pv}
    st = _f(row.get("existing_storage_kwh")) or 0.0
    if row.get("has_existing_storage") and st > 0:
        home["existingStorage"] = {"kwh": st}
    if row.get("has_existing_wallbox") is True:
        home["existingWallbox"] = {"kw": 11.0}
    ht = row.get("heating_type")
    if isinstance(ht, str) and ht != "Unknown":
        h: dict = {"type": ht}
        if _f(row.get("heat_demand_kwh")):
            h["heatDemandKwh"] = _f(row["heat_demand_kwh"])
        if ht == "Heatpump" and _f(row.get("hp_elec_existing_kwh")):
            h["hpElecKwh"] = _f(row["hp_elec_existing_kwh"])
        home["heating"] = h
    return home


def _key(*parts) -> str:
    import json
    return json.dumps(parts, sort_keys=True, default=str, separators=(",", ":"))


def economic_battery(row: Mapping, pv_kwp: float, sizes, hp_kw: float = 0.0) -> float:
    """The simulator's economic-optimum battery (kWh, 0 = none pays back) for this home with `pv_kwp` new PV, chosen among `sizes`."""
    home = sim_home(row)
    system: dict = {}
    if pv_kwp and pv_kwp > 0:
        system["pv"] = {"kwp": float(pv_kwp)}
    if hp_kw and hp_kw > 0:
        system["heatPump"] = {"kw": float(hp_kw)}
    sizes = tuple(sorted({float(s) for s in sizes}))
    k = _key(home, system, sizes)
    if k not in _BAT_CACHE:
        try:
            _BAT_CACHE[k] = float(sim.recommend_battery(home, system, sizes)["economic"]["batteryKwh"])
        except Exception:  # simulator failure must never break a design
            _BAT_CACHE[k] = 0.0
    return _BAT_CACHE[k]


def _physics_one(row: Mapping) -> tuple[float, float]:
    """(NPV-optimal new kWp with no battery, economic battery kWh at that kWp) for this home."""
    home = sim_home(row)
    k = _key(home)
    if k not in _CACHE:
        try:
            rows = sim.sweep_pv(home, {}, PV_GRID)
            kwp = float(PV_GRID[int(np.argmax([r["npv20"] for r in rows]))])
            bat = float(sim.recommend_battery(home, {"pv": {"kwp": kwp}}, sim.DEFAULT_SIZES)["economic"]["batteryKwh"])
            _CACHE[k] = (kwp, bat)
        except Exception:
            _CACHE[k] = (np.nan, np.nan)
    return _CACHE[k]


def warm(rows, executor=None) -> None:
    """Fill the physics cache for homes not seen yet; with an executor (process pool) the ~60 ms simulations run in parallel."""
    todo: dict[str, Mapping] = {}
    for r in rows:
        todo.setdefault(_key(sim_home(r)), r)
    todo = {k: r for k, r in todo.items() if k not in _CACHE}
    if executor is None:
        for r in todo.values():
            _physics_one(r)
        return
    futures = {k: executor.submit(_physics_one, r) for k, r in todo.items()}
    for k, f in futures.items():
        try:
            _CACHE[k] = f.result()
        except Exception:  # noqa: BLE001 - a broken pool only means the features are computed in-process later
            pass


def physics_features(df: pd.DataFrame) -> pd.DataFrame:
    vals = [_physics_one(r) for r in df.to_dict("records")]
    return pd.DataFrame(vals, columns=list(PHYSICS_COLS), index=df.index, dtype=float)


def save_cache(path: str | Path) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as f:
        pickle.dump((_CACHE, _BAT_CACHE), f)


def load_cache(path: str | Path) -> None:
    p = Path(path)
    if p.exists():
        try:
            with open(p, "rb") as f:
                c, b = pickle.load(f)
            _CACHE.update(c)
            _BAT_CACHE.update(b)
        except Exception:
            pass


# ---- installer-specific PV size prior -------------------------------------------------------------------------------
class PvPrior:
    """Median installed kWp of the installer for homes in the same demand bucket (fallback: installer, then everyone).
    Training rows get an out-of-fold value so the feature never contains the row's own target."""
    MIN_N = 8

    def fit(self, df: pd.DataFrame) -> "PvPrior":
        d = df[df["pv_kwp"] > 0].copy()
        d["_b"] = d["demand_kwh"].map(_bucket)
        self.all = float(d["pv_kwp"].median()) if len(d) else np.nan
        inst = d.get("installer_id", pd.Series("", index=d.index)).astype(str)
        self.by_inst = {k: float(g["pv_kwp"].median()) for k, g in d.groupby(inst) if len(g) >= self.MIN_N}
        self.by_bucket = {(k, b): float(g["pv_kwp"].median()) for (k, b), g in d.groupby([inst, d["_b"]]) if len(g) >= self.MIN_N}
        return self

    def transform(self, df: pd.DataFrame) -> pd.Series:
        inst = df["installer_id"].astype(str) if "installer_id" in df else pd.Series("", index=df.index)
        b = df["demand_kwh"].map(_bucket) if "demand_kwh" in df else pd.Series(1, index=df.index)
        out = [self.by_bucket.get((i, k), self.by_inst.get(i, self.all)) for i, k in zip(inst, b)]
        return pd.Series(out, index=df.index, dtype=float)

    @classmethod
    def oof(cls, df: pd.DataFrame, folds: int = 5, seed: int = 0) -> pd.Series:
        rng = np.random.default_rng(seed)
        fold = rng.integers(0, folds, len(df))
        out = pd.Series(np.nan, index=df.index)
        for k in range(folds):
            m = fold == k
            if m.all() or not m.any():
                continue
            out[m] = cls().fit(df[~m]).transform(df[m])
        return out


def _bucket(demand) -> int:
    d = _f(demand)
    return bl.demand_bucket(4500.0 if d is None else d)
