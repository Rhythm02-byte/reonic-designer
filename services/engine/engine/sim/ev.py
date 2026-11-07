"""EV charging model (S3).

Energy: km/yr x 0.18 kWh/km (incl. charging losses) x 70% charged at home.
Availability: weekdays the car is home 18:00-07:30, weekends all day ("homeoffice": all days).
Modes:
  "evening"    - plug in at 18:00, charge at wallbox power until the day's need is met (dumb charging).
  "solar"      - surplus-first (PV minus other load) while the car is home; the remainder is
                 charged just before the 07:30 departure, so the daily need is met by 07:30.
  "homeoffice" - like "solar" but the car is home all day, every day.
Each day's need is energy/365. EV load is served before the battery (surplus-first wallbox
priority); surplus ignores the battery.
"""
from __future__ import annotations

import numpy as np

from .profiles import HOURS, calendar

KWH_PER_KM = 0.18
HOME_SHARE = 0.70
MODES = ("evening", "solar", "homeoffice")


def ev_annual_kwh(km_per_year: float, home_share: float = HOME_SHARE, kwh_per_km: float = KWH_PER_KM) -> float:
    """Home-charged EV energy per year (kWh), incl. charging losses."""
    return float(km_per_year) * kwh_per_km * home_share


def ev_load(km_per_year: float, mode: str = "evening", pv: np.ndarray | None = None,
            other_load: np.ndarray | None = None, wallbox_kw: float = 11.0) -> np.ndarray:
    """Hourly EV charging energy (kWh, 8760). ``pv``/``other_load`` (kWh/h) drive the solar modes."""
    if mode not in MODES:
        raise ValueError(f"unknown EV mode {mode!r}; use one of {MODES}")
    out = np.zeros(HOURS)
    need = ev_annual_kwh(km_per_year) / 365.0
    P = float(wallbox_kw)
    if need <= 0 or P <= 0:
        return out
    if mode == "evening" or pv is None:
        per_hour = np.clip(need - P * np.arange(48), 0.0, P)
        per_hour = per_hour[per_hour > 0]
        n = len(per_hour)
        for j, e in enumerate(per_hour):
            idx = (np.arange(365) * 24 + 18 + j) % HOURS
            out[idx] += e
        return out
    cal = calendar()
    hod, weekend = cal["hod"], cal["dow"] >= 5
    cap = np.full(HOURS, P)
    if mode == "solar":
        cap[(~weekend) & (hod >= 8) & (hod < 18)] = 0.0  # car away
        cap[(~weekend) & (hod == 7)] = 0.5 * P  # leaves 07:30
    surplus = np.clip(pv - (other_load if other_load is not None else 0.0), 0.0, None)
    sur = np.minimum(surplus, cap)
    for d in range(365):
        idx = (np.arange(d * 24 + 8, d * 24 + 32)) % HOURS  # day d 08:00 .. day d+1 07:59
        s = sur[idx]
        tot = s.sum()
        if tot >= need:  # surplus in time order until the need is met
            c = np.cumsum(s)
            out[idx] += np.minimum(s, np.clip(need - (c - s), 0.0, None))
            continue
        out[idx] += s
        rem = need - tot
        room = cap[idx] - s
        for j in range(len(idx) - 1, -1, -1):  # top up as late as possible before the deadline
            if room[j] <= 0:
                continue
            x = min(room[j], rem)
            out[idx[j]] += x
            rem -= x
            if rem <= 1e-12:
                break
    return out
