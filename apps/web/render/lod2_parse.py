"""Extracts one building's wall/roof geometry from a Bavaria LoD2 CityGML tile.

Only exterior rings are read (no window/door holes in wall faces) — that's
enough for massing + roof shape; ponytail: add interior-ring handling if a
facade opening ever needs to show through.
"""
from dataclasses import dataclass
from pathlib import Path
from xml.etree import ElementTree as ET

Point = tuple[float, float, float]
Ring = list[Point]


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _rings_in(elem: ET.Element) -> list[Ring]:
    """Every gml:posList under elem, as exterior rings (closing point dropped)."""
    rings = []
    for pos_list in elem.iter():
        if _local(pos_list.tag) != "posList":
            continue
        dim = int(pos_list.get("srsDimension", "3"))
        nums = [float(v) for v in pos_list.text.split()]
        pts = [tuple(nums[i:i + dim][:3]) for i in range(0, len(nums), dim)]
        if len(pts) > 1 and pts[0] == pts[-1]:
            pts = pts[:-1]
        rings.append(pts)
    return rings


def _rings_of(building: ET.Element, surface_tag: str) -> list[Ring]:
    rings = []
    for surface in building.iter():
        if _local(surface.tag) == surface_tag:
            rings.extend(_rings_in(surface))
    return rings


def _contains(ring: Ring, x: float, y: float) -> bool:
    """Standard even-odd ray casting, ignoring z (the footprint is flat)."""
    inside = False
    n = len(ring)
    for i in range(n):
        x1, y1 = ring[i][0], ring[i][1]
        x2, y2 = ring[(i + 1) % n][0], ring[(i + 1) % n][1]
        if (y1 > y) != (y2 > y):
            x_at_y = x1 + (y - y1) * (x2 - x1) / (y2 - y1)
            if x < x_at_y:
                inside = not inside
    return inside


@dataclass
class BuildingGeometry:
    footprint: Ring  # local metres: origin at the footprint centroid, x = east, y = north, z = up from ground
    walls: list[Ring]
    roofs: list[Ring]


def find_building_at(gml_path: Path, easting: float, northing: float) -> BuildingGeometry | None:
    """Streams the tile and returns the Building whose GroundSurface contains (easting, northing), or None."""
    for _, elem in ET.iterparse(gml_path, events=("end",)):
        if _local(elem.tag) != "Building":
            continue
        ground_rings = _rings_of(elem, "GroundSurface")
        match = next((r for r in ground_rings if _contains(r, easting, northing)), None)
        if match is None:
            elem.clear()
            continue

        walls, roofs = _rings_of(elem, "WallSurface"), _rings_of(elem, "RoofSurface")
        cx = sum(p[0] for p in match) / len(match)
        cy = sum(p[1] for p in match) / len(match)
        gz = min(p[2] for p in match)

        def to_local(ring: Ring) -> Ring:
            return [(p[0] - cx, p[1] - cy, p[2] - gz) for p in ring]

        geometry = BuildingGeometry(to_local(match), [to_local(r) for r in walls], [to_local(r) for r in roofs])
        elem.clear()
        return geometry
    return None


if __name__ == "__main__":
    import sys

    from render.lod2_geo import wgs84_to_utm32

    path, lat, lon = Path(sys.argv[1]), float(sys.argv[2]), float(sys.argv[3])
    e, n = wgs84_to_utm32(lat, lon)
    found = find_building_at(path, e, n)
    print(f"footprint: {len(found.footprint)} pts, {len(found.walls)} walls, {len(found.roofs)} roofs" if found else "no building at that point")
