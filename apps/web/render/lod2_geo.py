"""WGS84 -> UTM32 (EPSG:25832) projection and Bavaria LoD2 tile math.

Bavaria's LoD2 CityGML is distributed as a 2 km x 2 km grid in EPSG:25832; tile
"690_5332.gml" covers easting [690000, 692000), northing [5332000, 5334000).
Hand-rolled transverse Mercator instead of pyproj: the zone is fixed (32N,
ETRS89/GRS80), so a ~40-line formula replaces a dependency most of whose
features (arbitrary CRS pairs, PROJ data files) we'd never use.
"""
import math

# GRS80 ellipsoid (ETRS89)
_A = 6378137.0
_F = 1 / 298.257222101
_E2 = _F * (2 - _F)
_EP2 = _E2 / (1 - _E2)
_K0 = 0.9996
_LON0 = math.radians(9.0)  # UTM zone 32 central meridian
_FALSE_E = 500000.0

TILE_SIZE_M = 2000

# Generous rectangle around Bavaria (true border is a polygon; this only gates
# "don't bother fetching" before we try the real tile download).
BAVARIA_BBOX_WGS84 = (47.2, 8.9, 50.6, 13.9)  # (min_lat, min_lon, max_lat, max_lon)


def in_bavaria_bbox(lat: float, lon: float) -> bool:
    min_lat, min_lon, max_lat, max_lon = BAVARIA_BBOX_WGS84
    return min_lat <= lat <= max_lat and min_lon <= lon <= max_lon


def wgs84_to_utm32(lat: float, lon: float) -> tuple[float, float]:
    """Forward transverse Mercator, UTM zone 32N, ETRS89/GRS80. Returns (easting, northing) in metres."""
    phi, lam = math.radians(lat), math.radians(lon)
    sin_phi, cos_phi, tan_phi = math.sin(phi), math.cos(phi), math.tan(phi)

    n = _A / math.sqrt(1 - _E2 * sin_phi ** 2)
    t = tan_phi ** 2
    c = _EP2 * cos_phi ** 2
    a = (lam - _LON0) * cos_phi
    e2, e4, e6 = _E2, _E2 ** 2, _E2 ** 3
    m = _A * (
        (1 - e2 / 4 - 3 * e4 / 64 - 5 * e6 / 256) * phi
        - (3 * e2 / 8 + 3 * e4 / 32 + 45 * e6 / 1024) * math.sin(2 * phi)
        + (15 * e4 / 256 + 45 * e6 / 1024) * math.sin(4 * phi)
        - (35 * e6 / 3072) * math.sin(6 * phi)
    )

    easting = _K0 * n * (
        a + (1 - t + c) * a ** 3 / 6
        + (5 - 18 * t + t ** 2 + 72 * c - 58 * _EP2) * a ** 5 / 120
    ) + _FALSE_E
    northing = _K0 * (
        m + n * tan_phi * (
            a ** 2 / 2 + (5 - t + 9 * c + 4 * c ** 2) * a ** 4 / 24
            + (61 - 58 * t + t ** 2 + 600 * c - 330 * _EP2) * a ** 6 / 720
        )
    )
    return easting, northing


def tile_id(easting: float, northing: float) -> tuple[int, int]:
    """2 km grid cell, as (tx, ty) km of its lower-left corner, matching the "{tx}_{ty}.gml" filenames."""
    tx = math.floor(easting / TILE_SIZE_M) * (TILE_SIZE_M // 1000)
    ty = math.floor(northing / TILE_SIZE_M) * (TILE_SIZE_M // 1000)
    return tx, ty


def tile_filename(tx: int, ty: int) -> str:
    return f"{tx}_{ty}.gml"
