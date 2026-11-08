"""Create and serve a LoD2-based GLB for a selected Bavarian address.

The expensive work is deliberately behind a small, deterministic cache.  A
browser only receives the resulting GLB; CityGML tiles and temporary geometry
never leave the local API process.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import re
import subprocess
import tempfile
from dataclasses import asdict
from pathlib import Path

from . import imagery
from .lod2_fetch import NotInBavaria, NotInCoverage, TileNotFound, fetch_tile
from .lod2_geo import wgs84_to_utm32
from .lod2_parse import find_building_at
from .lod2_vision import analyze

ROOT = Path(__file__).resolve().parents[3]
BLENDER_SCRIPT = ROOT / "apps" / "web" / "blender" / "house_lod2.py"
CACHE_DIR = Path(os.environ.get("HOUSE_CACHE_DIR", ROOT / ".cache" / "lod2-house"))
# Homebrew's Blender cask is an app bundle and deliberately does not add a
# `blender` binary to PATH.  Docker uses its installed command; local macOS
# development works out of the box with the standard app location.
_MACOS_BLENDER = Path("/Applications/Blender.app/Contents/MacOS/Blender")
# ours: Windows installs Blender under Program Files without adding it to PATH; take the newest one found.
_WIN_BLENDER = sorted(Path(os.environ.get("ProgramFiles", r"C:\Program Files"), "Blender Foundation").glob("Blender */blender.exe"), key=lambda p: [int(x) if x.isdigit() else 0 for x in p.parent.name.split()[-1].split(".")]) if os.name == "nt" else []
BLENDER = os.environ.get("BLENDER_BIN") or (str(_MACOS_BLENDER) if _MACOS_BLENDER.is_file() else str(_WIN_BLENDER[-1]) if _WIN_BLENDER else "blender")
_PANELS = re.compile(r"['\"]panels['\"]\s*:\s*(\d+)")
# Include a renderer revision in the cache key: a corrected panel-layout
# algorithm must not keep serving an older GLB for the same address.
RENDER_REVISION = "4"


class HouseRenderError(ValueError):
    """A location cannot currently produce a house model suitable for display."""


def _number(name: str, value, minimum: float, maximum: float) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not minimum <= value <= maximum:
        raise HouseRenderError(f"{name} must be a number between {minimum:g} and {maximum:g}")
    return float(value)


def coordinates(body: dict) -> tuple[float, float]:
    if not isinstance(body, dict):
        raise HouseRenderError("body must be a JSON object")
    return _number("lat", body.get("lat"), -90, 90), _number("lng", body.get("lng"), -180, 180)


def cache_key(lat: float, lng: float) -> str:
    # Six decimal places are about 11 cm.  This means a dragged pin gets a new
    # house, while repeated requests for exactly the same building are instant.
    return hashlib.sha256(f"{RENDER_REVISION}:{lat:.6f},{lng:.6f}".encode()).hexdigest()[:20]


def _meta_path(key: str) -> Path:
    return CACHE_DIR / f"{key}.json"


def cached(key: str) -> dict | None:
    glb, meta = CACHE_DIR / f"{key}.glb", _meta_path(key)
    if not glb.is_file() or not meta.is_file():
        return None
    try:
        return json.loads(meta.read_text())
    except (OSError, json.JSONDecodeError):
        return None


def render(lat: float, lng: float) -> dict:
    """Return cache metadata, creating the model on the first request."""
    key = cache_key(lat, lng)
    if result := cached(key):
        return result

    tile = fetch_tile(lat, lng)
    easting, northing = wgs84_to_utm32(lat, lng)
    geometry = find_building_at(tile, easting, northing)
    if geometry is None or not geometry.walls or not geometry.roofs:
        raise HouseRenderError("No complete LoD2 building geometry was found at this pin. Move it onto the building.")
    if not BLENDER_SCRIPT.is_file():
        raise HouseRenderError("The LoD2 Blender script is not installed on this server.")

    try:
        images = imagery.fetch_images(lat, lng)
        style = asdict(analyze(images["facade"], images["aerial"]))
    except imagery.ImageryError:  # no API key, no Street View coverage, network failure: a plain house, not a failed one
        style = {}

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    output = CACHE_DIR / f"{key}.glb"
    # Geometry belongs in a private temporary file, not the static/cache tree.
    with tempfile.TemporaryDirectory(prefix="reonic-lod2-") as temp:
        source = Path(temp) / "geometry.json"
        source.write_text(json.dumps({**asdict(geometry), "style": style}))
        try:
            proc = subprocess.run(
                [BLENDER, "-b", "--python", str(BLENDER_SCRIPT), "--", str(source), str(output)],
                check=True,
                capture_output=True,
                text=True,
                timeout=120,
            )
        except FileNotFoundError as exc:
            raise HouseRenderError("Blender is not installed on this server.") from exc
        except subprocess.TimeoutExpired as exc:
            output.unlink(missing_ok=True)
            raise HouseRenderError("Building the 3D house took too long; please try again.") from exc
        except subprocess.CalledProcessError as exc:
            output.unlink(missing_ok=True)
            detail = (exc.stderr or exc.stdout).strip().splitlines()[-1:] or ["unknown Blender error"]
            raise HouseRenderError(f"Blender could not create this house: {detail[0]}") from exc

    if not output.is_file() or output.stat().st_size == 0:
        raise HouseRenderError("Blender did not produce a house model.")
    panels = _PANELS.search(proc.stdout)
    region = "Bavaria" if tile.parent.name == "bavaria" else "Schleswig-Holstein"
    result = {
        "id": key,
        "url": f"/api/house/{key}.glb",
        "panels": int(panels.group(1)) if panels else None,
        "source": f"{region} LoD2",
    }
    _meta_path(key).write_text(json.dumps(result))
    return result


def model_path(key: str) -> Path | None:
    # Route parameters are untrusted: accept only our cache-key format.
    if not re.fullmatch(r"[0-9a-f]{20}", key):
        return None
    path = CACHE_DIR / f"{key}.glb"
    return path if path.is_file() else None
