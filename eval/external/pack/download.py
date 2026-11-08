"""Explicit online acquisition only. Benchmark never calls this module.

Usage: node scripts/py.mjs eval/external/pack/download.py
"""
from __future__ import annotations

import concurrent.futures
import hashlib
import json
import urllib.request
from pathlib import Path

RAW = Path(__file__).resolve().parents[3] / "data/external/raw"
ZENODO = {
    "14843222": ("mastr_", ["bnetza_open_mastr_datapackage.json", "LICENSE",
                            "bnetza_mastr_solar_raw.csv.zip", "bnetza_mastr_storage_raw.csv.zip",
                            "bnetza_mastr_storage_units_raw.csv.zip"]),
    "5642902": ("wpuq_", ["datapackage.json", "2019_data_60min.hdf5", "2019_weather.hdf5"]),
}


def fetch(url, dest, size=None, checksum=None):
    def valid():
        if not dest.exists() or (size is not None and dest.stat().st_size != size):
            return False
        if checksum is None:
            return True
        h = hashlib.md5()
        with dest.open("rb") as source:
            for block in iter(lambda: source.read(2**20), b""):
                h.update(block)
        return h.hexdigest() == checksum.removeprefix("md5:")
    if valid():
        return dest.name, "cached, verified"
    temp = dest.with_suffix(dest.suffix + ".part")
    with urllib.request.urlopen(url, timeout=120) as source, temp.open("wb") as out:
        while block := source.read(2**20):
            out.write(block)
    temp.replace(dest)
    if not valid():
        raise ValueError(f"Download size/checksum mismatch: {dest.name}")
    return dest.name, dest.stat().st_size


def main():
    RAW.mkdir(parents=True, exist_ok=True)
    jobs = []
    for record, (prefix, names) in ZENODO.items():
        url = f"https://zenodo.org/api/records/{record}"
        with urllib.request.urlopen(url, timeout=60) as response:
            metadata = response.read()
        (RAW / f"{record}.json").write_bytes(metadata)
        for f in json.loads(metadata)["files"]:
            if f["key"] in names:
                jobs.append((f["links"]["self"], RAW / (prefix + f["key"]), f["size"], f.get("checksum")))
    for name in ("datapackage.json", "README.md", "household_data_60min_singleindex.csv"):
        jobs.append(("https://data.open-power-system-data.org/household_data/2020-04-15/" + name,
                     RAW / ("opsd_" + name)))
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        futures = [pool.submit(fetch, *args) for args in jobs]
        for future in concurrent.futures.as_completed(futures):
            print(*future.result(), flush=True)


if __name__ == "__main__":
    main()
