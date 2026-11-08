"""Fetches two real photos of an address for lod2_vision to analyse: a street-level
facade shot (Street View Static API) and a satellite roof crop (Maps Static API).

ponytail: the Solar API also has a roof `rgb` data layer, but it comes back as a
GeoTIFF URL needing a second authenticated fetch plus raster decoding. Maps Static's
satellite view is one authenticated request and a normal JPEG -- plenty for a vision
model to read tile/membrane patterns off, so that's what this uses instead.
"""
from __future__ import annotations

import os
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

CACHE_DIR = Path(os.environ.get("IMAGERY_CACHE_DIR", Path(__file__).resolve().parents[2] / "data" / "imagery-cache"))
STREETVIEW_URL = "https://maps.googleapis.com/maps/api/streetview"
STATICMAP_URL = "https://maps.googleapis.com/maps/api/staticmap"


class ImageryError(Exception):
    """Imagery could not be fetched (missing key, no coverage, network failure)."""


def _get(url: str, params: dict, timeout: float = 20.0) -> bytes:
    try:
        with urllib.request.urlopen(f"{url}?{urllib.parse.urlencode(params)}", timeout=timeout) as resp:
            return resp.read()
    except (urllib.error.URLError, urllib.error.HTTPError) as e:
        raise ImageryError(f"fetching {url} failed: {e}") from e


def fetch_images(lat: float, lng: float) -> dict[str, bytes]:
    """Returns {"facade": jpeg bytes, "aerial": jpeg bytes}, cached per rounded coordinate."""
    key = os.environ.get("GOOGLE_MAPS_API_KEY")
    if not key:
        raise ImageryError("GOOGLE_MAPS_API_KEY is not set")

    tag = f"{lat:.6f},{lng:.6f}"
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    out = {}
    for name, url, params in (
        ("facade", STREETVIEW_URL, {"size": "640x640", "location": tag, "fov": 80, "source": "outdoor"}),
        ("aerial", STATICMAP_URL, {"size": "640x640", "center": tag, "zoom": 20, "maptype": "satellite"}),
    ):
        cached = CACHE_DIR / f"{tag}-{name}.jpg"
        if cached.is_file() and cached.stat().st_size > 0:
            out[name] = cached.read_bytes()
            continue
        data = _get(url, {**params, "key": key})
        cached.write_bytes(data)
        out[name] = data
    return out


if __name__ == "__main__":
    import sys

    lat, lng = float(sys.argv[1]), float(sys.argv[2])
    images = fetch_images(lat, lng)
    for name, data in images.items():
        print(f"{name}: {len(data)} bytes")
