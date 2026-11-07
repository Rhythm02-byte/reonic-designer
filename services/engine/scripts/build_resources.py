"""Build the offline resource files (run once, commit the output).

    services/engine/.venv/Scripts/python services/engine/scripts/build_resources.py

Needs network + `pip install demandlib` (build time only; the runtime engine uses
numpy/pandas only).  Writes services/engine/resources/{sim_profiles.npz,sim_profiles_meta.json}.

* PV: PVGIS v5_3 `seriescalc` (PVGIS-SARAH3 radiation, ERA5 temperature), 2005-2023,
  pvcalculation=1, peakpower=1 kWp, loss=14 %, Kassel 51.32N 9.50E.  A single
  *representative real year* is picked (closest to the 19-year mean in annual yield of
  S35 and in heating degree hours), so PV and temperature stay physically consistent.
  Times are UTC in PVGIS; converted to Europe/Berlin local clock, Feb 29 dropped,
  DST gap/overlap hours repaired -> 8760 naive local hours.
* Load: BDEW H0 *dynamised* (h0_dyn) via demandlib 0.2.2 (MIT), year 2023 (Sun 1 Jan,
  German national holidays), 15 min -> hourly, normalised to 1000 kWh/yr.
No data is fabricated: if PVGIS is unreachable the script aborts.
"""
from __future__ import annotations

import datetime as dt
import json
import sys
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "resources"
API = "https://re.jrc.ec.europa.eu/api/v5_3/seriescalc"
LAT, LON = 51.32, 9.50
YEARS = (2005, 2023)
# PVGIS azimuth: 0 = south, -90 = east, +90 = west
ORIENTS = {"s35": (35, 0), "e35": (35, -90), "w35": (35, 90),
           "s10": (10, 0), "e10": (10, -90), "w10": (10, 90)}


def fetch(angle: int, aspect: int) -> pd.DataFrame:
    params = dict(lat=LAT, lon=LON, peakpower=1, loss=14, pvcalculation=1, angle=angle,
                  aspect=aspect, startyear=YEARS[0], endyear=YEARS[1], outputformat="json",
                  usehorizon=1, mountingplace="building")
    for attempt in range(3):
        try:
            with urllib.request.urlopen(API + "?" + urllib.parse.urlencode(params), timeout=180) as r:
                j = json.loads(r.read())
            break
        except Exception as e:  # noqa: BLE001
            print("retry", attempt, e, file=sys.stderr)
            time.sleep(3)
    else:
        sys.exit("PVGIS unreachable - aborting (no fabricated data).")
    df = pd.DataFrame(j["outputs"]["hourly"])
    df["time"] = pd.to_datetime(df["time"], format="%Y%m%d:%H%M", utc=True).dt.floor("h")
    return df.set_index("time"), j["inputs"]


def to_local_8760(s: pd.Series, year: int) -> np.ndarray:
    loc = s.tz_convert("Europe/Berlin").tz_localize(None)
    loc = loc[~loc.index.duplicated(keep="first")]
    full = pd.date_range(f"{year}-01-01", f"{year}-12-31 23:00", freq="h")
    loc = loc.reindex(full).interpolate(limit_direction="both")
    loc = loc[~((loc.index.month == 2) & (loc.index.day == 29))]
    assert len(loc) == 8760, len(loc)
    return loc.to_numpy(dtype=np.float32)


def build_h0() -> np.ndarray:
    warnings.simplefilter = lambda *a, **k: None  # demandlib sets simplefilter("error"); pandas 3.1 deprecations would raise
    warnings.filterwarnings("ignore")
    import demandlib
    from demandlib import bdew
    hol = [dt.date(2023, 1, 1), dt.date(2023, 4, 7), dt.date(2023, 4, 10), dt.date(2023, 5, 1),
           dt.date(2023, 5, 18), dt.date(2023, 5, 29), dt.date(2023, 10, 3), dt.date(2023, 12, 25),
           dt.date(2023, 12, 26)]
    slp = bdew.ElecSlp(2023, holidays=hol)
    q = slp.get_scaled_profiles({"h0_dyn": 1000.0})["h0_dyn"]  # kWh per 15 min
    h = q.groupby(q.index.floor("h")).sum().to_numpy()
    assert len(h) == 8760
    return (h / h.sum() * 1000.0).astype(np.float32), demandlib.__version__


def main() -> None:
    OUT.mkdir(exist_ok=True)
    raw, temps, inputs0 = {}, None, None
    for name, (ang, asp) in ORIENTS.items():
        df, inp = fetch(ang, asp)
        raw[name] = df["P"] / 1000.0  # W per kWp -> kWh per kWp per hour
        if name == "s35":
            temps, inputs0 = df["T2m"], inp
        print(name, "annual mean kWh/kWp/yr", round(raw[name].sum() / 19, 1), flush=True)
    # representative year
    yrs = range(YEARS[0], YEARS[1] + 1)
    yld = np.array([raw["s35"][raw["s35"].index.year == y].sum() for y in yrs])
    hdh = np.array([np.clip(15 - temps[temps.index.year == y], 0, None).sum() for y in yrs])
    score = 2 * ((yld - yld.mean()) / yld.std()) ** 2 + ((hdh - hdh.mean()) / hdh.std()) ** 2
    print({y: (round(a), round(b)) for y, a, b in zip(yrs, yld, hdh)})
    year = list(yrs)[int(score.argmin())]
    print("representative year", year, "yield s35", yld[year - YEARS[0]], "mean", yld.mean(),
          "HDH", hdh[year - YEARS[0]], "mean", hdh.mean())
    arrays = {}
    for k, v in raw.items():
        sel = v[(v.index >= pd.Timestamp(f"{year-1}-12-31", tz="UTC")) & (v.index < pd.Timestamp(f"{year+1}-01-01", tz="UTC"))]
        arrays[f"pv_{k}"] = to_local_8760(sel, year)
    tsel = temps[(temps.index >= pd.Timestamp(f"{year-1}-12-31", tz="UTC")) & (temps.index < pd.Timestamp(f"{year+1}-01-01", tz="UTC"))]
    arrays["temp"] = to_local_8760(tsel, year)
    h0, dl_ver = build_h0()
    arrays["h0"] = h0
    for k, a in arrays.items():
        print(k, a.shape, round(float(a.sum()), 1))
    np.savez_compressed(OUT / "sim_profiles.npz", **arrays)
    meta = {
        "files": {"sim_profiles.npz": "pv_<orient> kWh per kWp per hour (8760, local clock), temp degC, h0 kWh/h for 1000 kWh/yr"},
        "hours": 8760, "calendar_reference_year_for_weekdays": 2023,
        "pv": {"source": "PVGIS v5_3 seriescalc", "url": API, "radiation_db": inputs0["meteo_data"]["radiation_db"],
               "meteo_db": inputs0["meteo_data"]["meteo_db"], "site": {"lat": LAT, "lon": LON, "name": "Kassel"},
               "years_available": list(YEARS), "representative_year": year,
               "selection": "year closest to 2005-2023 mean in S35 annual yield (double weight) and heating degree hours (15C)",
               "params": {"peakpower_kwp": 1, "loss_pct": 14, "mountingplace": "building", "usehorizon": 1},
               "orientations": {k: {"tilt_deg": a, "azimuth_pvgis_deg": z} for k, (a, z) in ORIENTS.items()},
               "annual_kwh_per_kwp": {k: round(float(arrays[f"pv_{k}"].sum()), 1) for k in ORIENTS},
               "time_note": "PVGIS UTC converted to Europe/Berlin clock, Feb 29 dropped",
               "licence": "PVGIS data: free for use incl. commercial, attribution to European Commission JRC; see https://joint-research-centre.ec.europa.eu/photovoltaic-geographical-information-system-pvgis/pvgis-data-download-and-licence_en (EC reuse policy, CC BY 4.0-equivalent)"},
        "load": {"source": "BDEW standard load profile H0, dynamised (h0_dyn) via demandlib", "demandlib_version": dl_ver,
                 "url": "https://github.com/oemof/demandlib", "base_year": 2023, "holidays": "German national holidays 2023",
                 "licence": "demandlib MIT; BDEW SLP coefficients published by BDEW (VDEW 1999 method)"},
        "date_fetched": dt.date.today().isoformat(),
    }
    (OUT / "sim_profiles_meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print("done")


if __name__ == "__main__":
    main()
