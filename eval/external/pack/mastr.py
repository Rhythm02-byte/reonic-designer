"""MaStR snapshot extraction. Public data only; row caches stay ignored.

No nearest-postcode matching. Solar storage-installation references are absent in this snapshot;
use one-to-one shared nonempty registry location AND operator IDs, labelled co-location.
"""
from __future__ import annotations

import json
import sys
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import DATA, RAW, quantiles, write_json

BASE = ["EinheitMastrNummer", "EinheitBetriebsstatus", "EinheitSystemstatus", "Land",
        "Inbetriebnahmedatum", "Bundesland", "LokationMastrNummer", "AnlagenbetreiberMastrNummer",
        "SpeMastrNummer"]


def storage_capacity_map(installations):
    """One installation's capacity maps only to its single explicit linked unit."""
    f = installations.loc[installations.VerknuepfteEinheit.str.fullmatch(r"SEE\d{12}")
                          & installations.AnlageBetriebsstatus.eq("In Betrieb")].copy()
    f = f.loc[~f.duplicated("MastrNummer", keep=False)]
    f = f.loc[~f.duplicated("VerknuepfteEinheit", keep=False)]
    return f.rename(columns={"NutzbareSpeicherkapazitaet": "installation_capacity"})


def attach_storage_capacity(units, installations):
    f = units.merge(installations, left_on="SpeMastrNummer", right_on="MastrNummer", how="left", validate="many_to_one")
    match = f.VerknuepfteEinheit.eq(f.EinheitMastrNummer)
    f["NutzbareSpeicherkapazitaet"] = f.installation_capacity.where(match, "")
    return f


def eligible(frame: pd.DataFrame, kind: str) -> pd.Series:
    year = pd.to_numeric(frame.Inbetriebnahmedatum.str[:4], errors="coerce")
    ok = (frame.EinheitBetriebsstatus.eq("In Betrieb") & frame.EinheitSystemstatus.eq("Aktiviert")
          & frame.Land.eq("Deutschland") & year.between(2018, 2026))
    if kind == "solar":
        power = pd.to_numeric(frame.Bruttoleistung, errors="coerce")
        ok &= power.between(1, 30) & frame.Lage.eq("Bauliche Anlagen (Hausdach, Gebäude und Fassade)")
        ok &= frame.Nutzungsbereich.eq("Haushalt")
    else:
        cap = pd.to_numeric(frame.NutzbareSpeicherkapazitaet, errors="coerce")
        ok &= cap.between(0, np.inf, inclusive="neither") & frame.Batterietechnologie.eq("Lithium-Batterie")
    return ok.fillna(False)


def extract(kind: str):
    cols = BASE + (["Bruttoleistung", "Lage", "Nutzungsbereich"] if kind == "solar" else
                   ["NutzbareSpeicherkapazitaet", "Batterietechnologie"])
    path = RAW / f"mastr_bnetza_mastr_{kind}_raw.csv.zip"
    frames, scanned = [], 0
    installations = None
    if kind == "storage":
        with zipfile.ZipFile(RAW / "mastr_bnetza_mastr_storage_units_raw.csv.zip") as archive, archive.open(archive.namelist()[0]) as source:
            installations = pd.read_csv(source, dtype=str, keep_default_na=False,
                                        usecols=["MastrNummer", "NutzbareSpeicherkapazitaet", "VerknuepfteEinheit", "AnlageBetriebsstatus"])
        # Capacity belongs to a storage installation (SSE). Only map its single explicitly
        # linked SEE unit; never duplicate an installation's capacity over units.
        installations = storage_capacity_map(installations)
    # Stream ZipExtFile: pandas' direct ZIP adapter materializes the multi-GB CSV.
    with zipfile.ZipFile(path) as archive, archive.open(archive.namelist()[0]) as source:
        for chunk in pd.read_csv(source, usecols=cols, dtype=str, keep_default_na=False, chunksize=100_000):
            scanned += len(chunk)
            if installations is not None:
                # Require both directions to agree, not just membership in a shared storage installation.
                chunk = attach_storage_capacity(chunk, installations)
            selected = chunk.loc[eligible(chunk, kind)].copy()
            selected["year"] = pd.to_numeric(selected.Inbetriebnahmedatum.str[:4]).astype(int)
            selected["value"] = pd.to_numeric(selected["Bruttoleistung" if kind == "solar" else "NutzbareSpeicherkapazitaet"])
            frames.append(selected)
    frame = pd.concat(frames, ignore_index=True)
    # Drop duplicate unit IDs only if all used fields are identical; exclude conflicting duplicates.
    duplicates = frame.duplicated("EinheitMastrNummer", keep=False)
    conflicted = frame.loc[duplicates].groupby("EinheitMastrNummer").nunique().max(axis=1).gt(1)
    bad_ids = conflicted[conflicted].index
    frame = frame.loc[~frame.EinheitMastrNummer.isin(bad_ids)]
    before = len(frame)
    frame = frame.drop_duplicates("EinheitMastrNummer").reset_index(drop=True)
    return frame, {"rows_scanned": scanned, "retained_units": len(frame),
                   "identical_duplicate_rows_removed": before - len(frame),
                   "conflicting_unit_ids_excluded": len(bad_ids)}


def link_colocated(solar, storage):
    """Conservative registered co-location, never a claim of electrical coupling.

    Count uniqueness before joining; an empty reference never matches an empty one.
    Exact location/operator join is allowed by handoff; no address/coordinate inference.
    """
    keys = ["LokationMastrNummer", "AnlagenbetreiberMastrNummer"]
    def unique(frame):
        f = frame.loc[frame[keys].ne("").all(axis=1)].copy()
        return f.loc[~f.duplicated(keys, keep=False)]
    left, right = unique(solar), unique(storage)
    return left.merge(right, on=keys, suffixes=("_pv", "_battery"), validate="one_to_one")


def by_year(frame):
    return {str(year): quantiles(g.value) for year, g in frame.groupby("year", sort=True)}


def main():
    cache = RAW / "mastr_filtered_v3.pkl"
    if cache.exists():
        solar, battery, diagnostics = pd.read_pickle(cache)  # locally generated public cache only
    else:
        old_cache = RAW / "mastr_filtered_v2.pkl"
        if old_cache.exists():
            solar, _, old_diagnostics = pd.read_pickle(old_cache)
            a = old_diagnostics["solar"]
        else:
            solar, a = extract("solar")
        battery, b = extract("storage")
        diagnostics = {"solar": a, "battery": b}
        pd.to_pickle((solar, battery, diagnostics), cache)
    linked = link_colocated(solar, battery)
    ratio = linked.value_battery / linked.value_pv
    years = {}
    for year, g in solar.groupby("year", sort=True):
        subset = linked.loc[linked.year_pv.eq(year)]
        years[str(year)] = {"pv": quantiles(g.value), "linked_colocated_n": len(subset),
                            "observed_colocation_share": len(subset) / len(g),
                            "linked_colocated_pv_kwp": quantiles(subset.value_pv),
                            "linked_colocated_demo_9kwp_ecdf_percent": 100 * float(subset.value_pv.le(9).mean()) if len(subset) else None,
                            "usable_kwh_per_kwp": quantiles(subset.value_battery / subset.value_pv),
                            "usable_ratio_quantile_sketch_1001": np.quantile(subset.value_battery / subset.value_pv, (np.arange(1001) + .5) / 1001).tolist() if len(subset) else []}
    out = {
        "schema_version": 1, "snapshot": "2025-02-09-unboxed", "accessed_at": "2026-11-08",
        "source": "https://zenodo.org/records/14843222", "license": "dl-de/by-2-0",
        "coverage": "2018-2024 complete calendar cohorts as recorded by snapshot; 2025 partial through 2025-02-09; 2026 unavailable",
        "scope": "Operating activated Germany household-use building/roof/facade PV units, 1-30 gross kWp. Residential proxy, not verified single-family dwellings.",
        "diagnostics": diagnostics, "pv_by_year": by_year(solar),
        "battery_lithium_all_sizes_kwh_by_year": by_year(battery),
        "pv_by_state": {state: quantiles(g.value) for state, g in solar.groupby("Bundesland", sort=True)},
        "linkage": {"method": "one_to_one_nonempty_LokationMastrNummer_AND_AnlagenbetreiberMastrNummer",
                    "ratio_sketch_positions": "midpoints q=(i+0.5)/1001, i=0..1000; avoids overweighting extrema",
                    "interpretation": "Registered co-location under same operator, not proof of electrical pairing. Observed colocation share is NOT the market battery attach rate.",
                    "n": len(linked), "ratio_usable_kwh_per_kwp": quantiles(ratio),
                    "by_pv_commissioning_year": years,
                    "explicit_spe_reference_solar_n": int(solar.SpeMastrNummer.ne("").sum()),
                    "excluded_ambiguous_or_unlinked_pv_n": len(solar) - len(linked)},
        "unavailable": {"2026": "snapshot predates year", "market_attach_rate": "co-location coverage/registry missing links prevent unbiased rate", "nominal_battery_ratio": "registry usable kWh differs from engine nominal capacity"},
    }
    write_json(DATA / "mastr_summary.json", out)
    print(json.dumps({"pv_units": len(solar), "storage_units": len(battery), "linked": len(linked)}))


if __name__ == "__main__":
    main()
