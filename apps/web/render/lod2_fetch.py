"""Download and cache official LoD2 CityGML tiles for Bavaria and Schleswig-Holstein."""
import hashlib
import os
import ssl
import urllib.error
import urllib.request
from functools import lru_cache
from pathlib import Path
from urllib.parse import urlencode

import certifi

from render.lod2_geo import in_bavaria_bbox, tile_filename, tile_id, wgs84_to_utm32

BAVARIA_TILE_URL = "https://download1.bayernwolke.de/a/lod2/citygml/{name}"
SH_DOWNLOAD_URL = "https://geodaten.schleswig-holstein.de/gaialight-sh/_apps/dladownload/massen.php"
CACHE_DIR = Path(os.environ.get("LOD2_CACHE_DIR", Path(__file__).resolve().parents[2] / "data" / "lod2-cache"))
SH_BBOX_WGS84 = (53.35, 8.9, 55.1, 11.45)
# The SH download host omits this intermediate from its TLS response. Fetch it
# from D-TRUST's public AIA endpoint and pin its SHA-256 before trusting it.
SH_TLS_INTERMEDIATE_URL = "http://www.d-trust.net/cgi-bin/D-TRUST_BR_CA_1-20-1_2020.crt"
SH_TLS_INTERMEDIATE_SHA256 = "199ab2aaafff40401e0a3b7b87ee9964659effa94a1fecbe918ae136e4b4e0a8"


class NotInBavaria(Exception):
    pass


class NotInCoverage(Exception):
    pass


class TileNotFound(Exception):
    pass


def in_schleswig_holstein_bbox(lat: float, lon: float) -> bool:
    south, west, north, east = SH_BBOX_WGS84
    return south <= lat <= north and west <= lon <= east


def sh_tile_filename(easting: float, northing: float) -> str:
    return f"LoD2_32_{int(easting // 1000):03d}_{int(northing // 1000):04d}_1_SH.xml"


def sh_tile_url(easting: float, northing: float) -> str:
    name = sh_tile_filename(easting, northing)
    km = f"32{int(easting // 10_000) * 10:03d}_{int(northing // 10_000) * 10:04d}"
    return f"{SH_DOWNLOAD_URL}?{urlencode({'file': name, 'id': 4, 'live': 2024, 'km': km})}"


@lru_cache(maxsize=1)
def _tls_context() -> ssl.SSLContext:
    """Keep TLS verification intact when the SH host serves an incomplete chain."""
    intermediate = urllib.request.urlopen(SH_TLS_INTERMEDIATE_URL, timeout=15).read()
    if hashlib.sha256(intermediate).hexdigest() != SH_TLS_INTERMEDIATE_SHA256:
        raise ssl.SSLError("D-TRUST intermediate certificate fingerprint did not match")
    context = ssl.create_default_context(cafile=certifi.where())
    context.load_verify_locations(cadata=ssl.DER_cert_to_PEM_cert(intermediate))
    return context


def _download(url: str, dest: Path, timeout: float) -> Path:
    if dest.exists():
        return dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".part")
    try:
        with urllib.request.urlopen(url, timeout=timeout, context=_tls_context()) as response, open(tmp, "wb") as out:
            while chunk := response.read(1 << 20):
                out.write(chunk)
        with open(tmp, "rb") as result:
            if not result.read(32).lstrip().startswith(b"<?xml"):
                raise TileNotFound(f"no LoD2 tile at {url}")
    except urllib.error.HTTPError as exc:
        tmp.unlink(missing_ok=True)
        if exc.code == 404:
            raise TileNotFound(f"no LoD2 tile at {url}") from exc
        raise
    except Exception:
        tmp.unlink(missing_ok=True)
        raise
    tmp.rename(dest)
    return dest


def fetch_tile(lat: float, lon: float, cache_dir: Path = CACHE_DIR, timeout: float = 60.0) -> Path:
    """Return the official CityGML tile for Bavaria or Schleswig-Holstein."""
    easting, northing = wgs84_to_utm32(lat, lon)
    if in_bavaria_bbox(lat, lon):
        name = tile_filename(*tile_id(easting, northing))
        return _download(BAVARIA_TILE_URL.format(name=name), cache_dir / "bavaria" / name, timeout)
    if in_schleswig_holstein_bbox(lat, lon):
        name = sh_tile_filename(easting, northing)
        return _download(sh_tile_url(easting, northing), cache_dir / "schleswig-holstein" / name, timeout)
    raise NotInCoverage(f"({lat}, {lon}) is outside supported LoD2 coverage (Bavaria and Schleswig-Holstein)")
