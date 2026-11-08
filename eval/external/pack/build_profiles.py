"""Extract public measured profiles; strict full-year windows, no gap imputation.

HDF5 adapter uses h5py only (optional acquisition-time dependency).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import DATA, RAW, quantiles, write_json
from profiles import normalized


def complete_hourly(index, values, year):
    """Reindex explicit UTC timestamps; never silently trim gaps or leap days."""
    expected = pd.date_range(f"{year}-01-01", f"{year + 1}-01-01", freq="h", inclusive="left", tz="UTC")
    s = pd.Series(np.asarray(values, dtype=float), index=pd.DatetimeIndex(index))
    if s.index.has_duplicates:
        raise ValueError("Duplicate timestamps")
    s = s.reindex(expected)
    if not np.isfinite(s).all() or (s < 0).any():
        raise ValueError("Incomplete or negative year")
    # For leap years drop Feb 29 only, preserving month/day alignment, then renormalize later.
    s = s.loc[~((s.index.month == 2) & (s.index.day == 29))]
    if len(s) != 8760:
        raise ValueError("Expected 8760 hours after leap-day removal")
    return s.to_numpy()


def wpuq():
    import h5py
    arrays, rows, excluded = {}, [], []
    with h5py.File(RAW / "wpuq_2019_data_60min.hdf5", "r") as f:
        # NO_PV avoids uncertain PV reconstruction. HOUSEHOLD excludes separately metered HP.
        for house in sorted(f["NO_PV"]):
            for feed in ("HOUSEHOLD", "HEATPUMP"):
                key = f"NO_PV/{house}/{feed}"
                a = f[key + "/table"][:]
                try:
                    values = complete_hourly(pd.to_datetime(a["index"], unit="s", utc=True), a["P_TOT"] / 1000, 2019)
                    arrays[f"wpuq_{house.lower()}_{feed.lower()}"] = normalized(values)
                    rows.append({"public_id": key, "feed": feed, "annual_kwh": float(values.sum()),
                                 "daytime_share_08_18": float(values.reshape(-1, 24)[:, 8:18].sum() / values.sum())})
                except ValueError as e:
                    excluded.append({"public_id": key, "reason": str(e), "finite_fraction": float(np.isfinite(a["P_TOT"]).mean())})
    # Weather is at ~5 min, aggregate within each UTC hour; no gap fill.
    with h5py.File(RAW / "wpuq_2019_weather.hdf5", "r") as f:
        group = f["WEATHER_SERVICE/IN/WEATHER_TEMPERATURE_TOTAL"]
        a = group["table"][:]
        # Unlike electrical feed seconds, weather retains pandas datetime64 nanoseconds.
        if group["table"].attrs["index_kind"] != b"datetime64":
            raise ValueError("Unrecognized weather time encoding")
        unit = str(group.attrs["unit"])
        weather = pd.Series(a["TEMPERATURE:TOTAL"], index=pd.to_datetime(a["index"], unit="ns", utc=True)).resample("h").mean()
    bins = []
    for lo, hi in [(-20, -5), (-5, 0), (0, 5), (5, 10), (10, 15), (15, 20), (20, 40)]:
        mask = ((weather >= lo) & (weather < hi)).reindex(pd.date_range("2019-01-01", periods=8760, freq="h", tz="UTC"), fill_value=False).to_numpy()
        # Shapes are individually normalized: statistic is hourly share, not thermal COP.
        vals = [float(v[mask].mean() * 8760) for k, v in arrays.items() if k.endswith("heatpump") and mask.any()]
        bins.append({"temperature_c_low": lo, "temperature_c_high": hi, "hours": int(mask.sum()),
                     "relative_hp_electricity_vs_annual_hourly_mean": quantiles(vals)})
    return arrays, {"retained_profile_n": len(arrays), "retained_household_n": sum(x["feed"] == "HOUSEHOLD" for x in rows),
                    "excluded": excluded, "public_profile_statistics": rows,
                    "hp_temperature_bins": bins,
                    "temperature_unit": unit + "; verified in HDF5 group unit attribute; time alignment provisional, bins disabled as model calibration",
                    "scope": "2019 NO_PV cohort only; nonrepresentative single-family homes with heat pumps; no new imputation"}


def opsd():
    d = pd.read_csv(RAW / "opsd_household_data_60min_singleindex.csv")
    d.index = pd.to_datetime(d.utc_timestamp, utc=True)
    arrays, rows = {}, []
    # Complete residential2 grid-only load and residential4 submeter/reconstruction in leap 2016.
    # Published channels are cumulative kWh meter readings, NOT interval energy.
    # Upstream processing.ipynb resamples cumulative values with .last(), so
    # counter[t]-counter[t-1] belongs to the hour labelled t (approximately hh:59).
    numeric = [c for c in d if c.startswith("DE_")]
    energy = d[numeric].diff()
    g = energy.loc[energy.index.year == 2016]
    candidates = {
        "opsd_residential2_household": g.DE_KN_residential2_grid_import,
        "opsd_residential4_ev": g.DE_KN_residential4_ev,
        "opsd_residential4_heatpump": g.DE_KN_residential4_heat_pump,
        "opsd_residential4_household": g.DE_KN_residential4_grid_import + g.DE_KN_residential4_pv
        - g.DE_KN_residential4_grid_export - g.DE_KN_residential4_ev - g.DE_KN_residential4_heat_pump,
    }
    for key, s in candidates.items():
        try:
            # Independently metered channels can yield small negative reconstruction residuals;
            # exclude instead of clipping undocumented boundaries.
            a = complete_hourly(s.index, s.to_numpy(), 2016)
            arrays[key] = normalized(a)
            rows.append({"name": key, "status": "retained", "annual_kwh_excluding_feb29": float(a.sum()),
                         "upstream_interpolated_hour_n": int(d.loc[d.index.year == 2016].interpolated.fillna("").str.contains("residential" + ("2" if "residential2" in key else "4"), case=False).sum())})
        except ValueError as e:
            rows.append({"name": key, "status": "excluded", "reason": str(e), "negative_hours": int((s < 0).sum())})
    return arrays, {"year": 2016, "leap_day": "24 hours dropped, retained shapes renormalized", "profiles": rows,
                    "upstream_interpolation": "present, published flags counted; no new imputation",
                    "conversion": "Backward differences of cumulative kWh. Upstream processing.ipynb uses hourly .last(); diff belongs to current hour label. Counters at both boundaries required. Minute-level boundary approximation and clock shifts disclosed.",
                    "boundary": "residential4 import+PV-export minus HP/EV is provisional accounting; negative residuals exclude full profile"}


def calibration(arrays):
    from engine.sim.profiles import load_profile, pv_profile, temperature
    from engine.sim.battery import flows
    from engine.sim.heatpump import hp_electric
    from engine.sim.ev import ev_load
    reference = load_profile(4500)
    out = []
    for pv_kwp, battery_kwh in [(5, 0), (9, 5), (12, 10)]:
        pv = pv_profile(pv_kwp)
        for kind, suffix, annual, model in [("household", "household", 4500, reference),
                                            ("heatpump", "heatpump", 5000, hp_electric(temperature(), 17000)["elec"]),
                                            ("ev", "_ev", 1512, ev_load(12000))]:
            baseline = flows(pv, model, battery_kwh)
            results = []
            for key, value in arrays.items():
                if not key.endswith(suffix):
                    continue
                # Timing-only comparison: equal annual component energy in both alternatives.
                for shift in (0, 1):
                    measured = np.roll(value, shift) * annual
                    r = flows(pv, measured, battery_kwh)
                    results.append({"public_profile": key, "utc_to_clock_shift_hours": shift,
                                    "self_consumption_delta_pp": 100 * float(r["self_consumption"][0] - baseline["self_consumption"][0]),
                                    "autarky_delta_pp": 100 * float(r["autarky"][0] - baseline["autarky"][0])})
            out.append({"pv_kwp": pv_kwp, "battery_nominal_kwh": battery_kwh, "component": kind,
                        "component_annual_kwh": annual, "n_profile_clock_scenarios": len(results),
                        "self_consumption_delta_pp": quantiles([r["self_consumption_delta_pp"] for r in results]),
                        "autarky_delta_pp": quantiles([r["autarky_delta_pp"] for r in results])})
    combined = []
    for pv_kwp, battery_kwh in [(5, 0), (9, 5), (12, 10)]:
        pv = pv_profile(pv_kwp)
        for kind in ("household_plus_hp", "household_plus_ev"):
            extra = hp_electric(temperature(), 17000)["elec"] if kind.endswith("hp") else ev_load(12000)
            baseline = flows(pv, reference + extra, battery_kwh)
            measurements = []
            for key, value in arrays.items():
                if kind.endswith("hp") and key.startswith("wpuq_") and key.endswith("_household"):
                    hp = arrays.get(key.removesuffix("_household") + "_heatpump")
                    if hp is None:
                        continue
                    measured = value * 4500 + hp * 5000
                elif kind.endswith("ev") and key == "opsd_residential4_ev":
                    measured = reference + value * 1512
                else:
                    continue
                for shift in (0, 1):
                    # Shift only the measured component for EV; both for paired WPuQ.
                    load = np.roll(measured, shift) if kind.endswith("hp") else reference + np.roll(value, shift) * 1512
                    r = flows(pv, load, battery_kwh)
                    measurements.append((100 * float(r["self_consumption"][0] - baseline["self_consumption"][0]),
                                         100 * float(r["autarky"][0] - baseline["autarky"][0])))
            combined.append({"pv_kwp": pv_kwp, "battery_nominal_kwh": battery_kwh, "load_scenario": kind,
                             "n_profile_clock_scenarios": len(measurements),
                             "self_consumption_delta_pp": quantiles([x[0] for x in measurements]),
                             "autarky_delta_pp": quantiles([x[1] for x in measurements])})
    return {"interpretation": "Timing-only fixed-design sensitivity, component-isolation and coupled household systems. Same engine dispatch/weather, equal annual energy; not independent physics validation or error against observed autarky. WPuQ 2019/OPSD2016 calendar vs H0 2023 and Kassel weather confound representativeness. 0/1h clock shifts bracket UTC/fixed-CET alignment; DST convention unresolved. Source statistical percentiles summarize selected profile/clock scenarios, not population confidence intervals.", "systems": out, "coupled_systems": combined}


def main():
    a, wm = wpuq()
    b, om = opsd()
    arrays = {**a, **b}
    folder = DATA / "profiles"
    folder.mkdir(exist_ok=True)
    np.savez_compressed(folder / "measured.npz", **arrays)
    write_json(folder / "metadata.json", {"schema_version": 1, "sources": ["https://zenodo.org/records/5642902", "https://data.open-power-system-data.org/household_data/2020-04-15/"],
                                         "license": "CC-BY-4.0", "units": "hourly fractions summing to 1", "wpuq": wm, "opsd": om})
    write_json(DATA / "profile_calibration.json", calibration(arrays))
    print(json.dumps({"profiles": len(arrays), "wpuq_households": wm["retained_household_n"], "opsd": om["profiles"]}))


if __name__ == "__main__":
    main()
