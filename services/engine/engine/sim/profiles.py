"""Bundled hourly resources: PV yield per kWp, ambient temperature, household load shapes.

All data comes from ``resources/sim_profiles.npz`` (built once by
``scripts/build_resources.py``; PVGIS v5_3 for Kassel, BDEW H0 via demandlib). Runtime is
offline and numpy-only. Hour 0 = 1 Jan 00:00 local clock; 8,760 h. Weekdays use the
calendar of 2023 (1 Jan = Sunday), the base year of the H0 profile.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

import numpy as np

HOURS = 8760
RES_DIR = Path(__file__).resolve().parents[2] / "resources"


@lru_cache(maxsize=1)
def load_resources() -> dict:
    """Return the cached arrays (float64, read-only) and the metadata dict under key ``meta``."""
    with np.load(RES_DIR / "sim_profiles.npz") as z:
        out = {k: z[k].astype(np.float64) for k in z.files}
    for v in out.values():
        v.setflags(write=False)
    out["meta"] = json.loads((RES_DIR / "sim_profiles_meta.json").read_text(encoding="utf-8"))
    return out


@lru_cache(maxsize=1)
def calendar() -> dict:
    """Hour-of-day, day index, weekday (0=Mon) and month (1-12) per hour of the reference year."""
    h = np.arange(HOURS)
    day = h // 24
    dow = (day + 6) % 7
    month = np.searchsorted(np.cumsum([31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]), day, side="right") + 1
    return {"hod": h % 24, "day": day, "dow": dow, "month": month}


def temperature() -> np.ndarray:
    """Hourly ambient temperature in degC (ERA5 via PVGIS, representative year)."""
    return load_resources()["temp"]


def _tilt_blend(az: str, tilt_deg: float) -> np.ndarray:
    r = load_resources()
    x = float(np.clip((tilt_deg - 10.0) / 25.0, 0.0, 1.0))  # 10 deg -> 0, 35 deg -> 1
    return (1 - x) * r[f"pv_{az}10"] + x * r[f"pv_{az}35"]


def pv_unit_profile(orientation="S", tilt_deg: float = 35.0, azimuth_deg: float | None = None) -> np.ndarray:
    """PV yield in kWh per kWp per hour (8760) for the Kassel reference year.

    ``orientation``: "S", "E", "W", "EW" (50/50 east/west split) or a dict like
    ``{"E": 0.5, "W": 0.5}`` (weights are normalised). ``tilt_deg`` is interpolated between the
    two PVGIS tilts (10 and 35 deg, clamped). ``azimuth_deg`` (0=S, -90=E, +90=W) overrides
    ``orientation`` and linearly interpolates between the E/S/W profiles; beyond +-90 deg the
    nearest of E/W is scaled down linearly to 60% at north (rough, not PVGIS-computed).
    """
    if azimuth_deg is not None:
        a = float(np.clip(azimuth_deg, -180, 180))
        side = "e" if a < 0 else "w"
        aa = abs(a)
        if aa <= 90:
            x = aa / 90.0
            return (1 - x) * _tilt_blend("s", tilt_deg) + x * _tilt_blend(side, tilt_deg)
        return _tilt_blend(side, tilt_deg) * (1.0 - 0.4 * (aa - 90.0) / 90.0)
    if isinstance(orientation, str):
        key = orientation.strip().upper()
        mix = {"EW": {"E": 0.5, "W": 0.5}}.get(key, {key: 1.0})
    else:
        mix = {str(k).upper(): float(v) for k, v in orientation.items()}
    tot = sum(mix.values())
    if tot <= 0 or any(k not in ("E", "S", "W") for k in mix):
        raise ValueError(f"bad orientation mix {orientation!r}")
    return sum(w / tot * _tilt_blend(k.lower(), tilt_deg) for k, w in mix.items())


def pv_profile(kwp: float, orientation="S", tilt_deg: float = 35.0, azimuth_deg: float | None = None) -> np.ndarray:
    """Hourly PV generation in kWh (= average kW) for an array of ``kwp``."""
    return float(kwp) * pv_unit_profile(orientation, tilt_deg, azimuth_deg)


# ---------------------------------------------------------------- load
# Multiplicative hour-of-day shape knobs applied on top of H0, then renormalised to the annual
# demand. These are SYNTHETIC, documented adjustments, not measured profiles. (Evidence for
# profile variety: HTW 74 household profiles, Schopfer 2018; see research/battery-and-simulations.md.)
# weekday rules / weekend rules: ((hour_from, hour_to), factor)
_FAMILIES = {
    "HomeOffice": {"wd": [((8, 17), 1.45), ((6, 8), 0.95), ((17, 22), 0.95)], "we": []},
    "Senior": {"wd": [((8, 18), 1.30), ((18, 23), 0.90)], "we": [((8, 18), 1.30), ((18, 23), 0.90)]},
    "FamilyOfFour": {"wd": [((9, 15), 0.80), ((6, 8), 1.15), ((17, 22), 1.15)], "we": [((9, 18), 1.15)]},
    "Working": {"wd": [((8, 17), 0.75), ((17, 22), 1.10)], "we": []},
}


def _family_key(name: str) -> str | None:
    n = (name or "H0").strip().lower()
    for k in _FAMILIES:
        if n.startswith(k.lower()):
            return k
    return None


def load_profile(annual_kwh: float, family: str = "H0", noise: float = 0.0, seed: int = 0) -> np.ndarray:
    """Hourly household load in kWh (8760) summing to ``annual_kwh``.

    ``family``: "H0" (BDEW dynamised H0, default), or prefixes "FamilyOfFour", "HomeOffice*"
    (more weekday daytime load), "Senior*" (more daytime, all days), "Working*" (empty house by day).
    Unknown names fall back to H0. ``noise`` > 0 multiplies each hour by a unit-mean lognormal
    (sigma = noise, seeded) to mimic the variability smooth H0 lacks (crude: it lowers
    self-consumption; real 1-s data would be better).
    """
    shape = load_resources()["h0"].copy()
    key = _family_key(family)
    if key:
        cal = calendar()
        f = np.ones(HOURS)
        wd = cal["dow"] < 5
        for mask, rules in ((wd, _FAMILIES[key]["wd"]), (~wd, _FAMILIES[key]["we"])):
            for (a, b), fac in rules:
                f[mask & (cal["hod"] >= a) & (cal["hod"] < b)] = fac
        shape *= f
    if noise > 0:
        shape *= np.random.default_rng(seed).lognormal(-0.5 * noise**2, noise, HOURS)
    return shape * (float(annual_kwh) / shape.sum())


def known_families() -> list[str]:
    """Names accepted by :func:`load_profile` (H0 plus prefixes)."""
    return ["H0", *_FAMILIES.keys()]
