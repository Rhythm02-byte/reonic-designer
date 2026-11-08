"""Builds a per-customer house.glb directly from Bavaria LoD2 CityGML geometry.

    blender -b --python web/blender/house_lod2.py -- <geometry.json> <out.glb>

house.py reskins one bought, fixed-shape model; this instead builds walls and
roof as the real surveyed polygons from reonic.lod2_parse.BuildingGeometry, so
the roof pitch, shape and orientation match the actual building. Reuses
house.py's materials, primitives, PV panel mesh and export pipeline, placed
generically off the footprint instead of hardcoded coordinates for one known
model.

<geometry.json>: {"footprint": [[x,y,z],...], "walls": [[[x,y,z],...],...], "roofs": [[[x,y,z],...],...],
                  "style": {...reonic.lod2_vision.HouseStyle fields, optional...}}
  (same local frame as lod2_parse.BuildingGeometry: origin at the footprint
  centroid, x = east, y = north, z = up from the ground)

Style-driven detail (from a vision read of real photos, see reonic.lod2_vision):
roof tiles only on "tile" roofs, a window grid sized/spaced per the facade read, and
the real roof/wall colours instead of the fixed PALETTE ones.

Heat pump, battery stack, wallbox, car and garden reuse house.py's device/plant
meshes (see accessories(), parked_car(), garden() below), anchored off the wall
polygons and footprint bounding box instead of house.py's ray-cast against one
known model.

ponytail: no eave/gutter/ridge-cap trim -- detecting ridge/eave edges generically from
an arbitrary LoD2 polygon is a separate, fiddlier geometry problem than tiling or
windowing a known face, and the brief's two examples (tiles, windows) don't need it.
"""
import json
import math
import sys
from pathlib import Path

import bmesh
import bpy
from mathutils import Matrix, Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
# noqa: E402  (reuse)
from house import (GAP, PALETTE, PANEL, batteries_and_wallbox, bevel, bm_mesh, box, car, cylinder, export,
                    heat_pump, material, mesh, obj, panel_mesh)

GROUND_MARGIN = 6.0  # metres of plinth/lawn beyond the footprint's bounding box
LOCAL_PAVING, LOCAL_LAWN = -0.05, -0.12  # ground z is 0 here (the footprint's own base), unlike house.py's bought-model floor
MIN_PITCH, MAX_PITCH = 0.25, 0.97  # normal.z range counted as a sloped (not vertical, not flat) roof face
DEFAULT_STYLE = {  # reonic.lod2_vision.FALLBACK, duplicated so this script has no import on reonic.*
    "roof_material": "tile", "roof_color_hex": "#9A6150", "wall_color_hex": "#F4F1EA",
    "window_width_m": 1.1, "window_height_m": 1.3, "window_spacing_m": 2.4,
    "sill_height_m": 0.9, "floor_height_m": 2.7,
}


def load_geometry(path: Path) -> dict:
    return json.loads(path.read_text())


def dyn_material(base: str, hex_: str | None) -> str:
    """A PALETTE entry sized to the vision-read colour, reusing house.material()'s lookup/caching."""
    if not hex_:
        return base
    name = f"{base}_{hex_.lstrip('#')}"
    if name not in PALETTE:
        PALETTE[name] = (hex_, PALETTE[base][1])
    return name


def _vecs(ring) -> list[Vector]:
    return [Vector(p) for p in ring]


def _normal(ring: list[Vector]) -> Vector:
    """Newell's method: robust against a non-planar or non-convex n-gon."""
    n = Vector()
    for i in range(len(ring)):
        a, b = ring[i], ring[(i + 1) % len(ring)]
        n += a.cross(b)
    return n.normalized()


def _area(ring: list[Vector]) -> float:
    n = Vector()
    for i in range(len(ring)):
        a, b = ring[i], ring[(i + 1) % len(ring)]
        n += a.cross(b)
    return n.length / 2


def _oriented(ring: list[Vector], outward: Vector) -> list[Vector]:
    """CityGML exterior rings are CCW as seen from outside, so this is usually a no-op; flips if the source data disagrees."""
    return ring if _normal(ring).dot(outward) >= 0 else list(reversed(ring))


def setup_collection() -> bpy.types.Collection:
    house = bpy.data.collections.new("House")
    bpy.context.scene.collection.children.link(house)
    return house


def polygon_obj(name: str, ring: list[Vector], mat: str) -> bpy.types.Object:
    me = mesh(name, ring, [tuple(range(len(ring)))], [mat])
    return obj(name, me)


def build_walls(walls: list[list[Vector]], style: dict):
    wall_mat = dyn_material("wall", style.get("wall_color_hex"))
    for i, ring in enumerate(walls):
        cx = sum(p.x for p in ring) / len(ring)
        cy = sum(p.y for p in ring) / len(ring)
        polygon_obj(f"Wall_{i}", _oriented(ring, Vector((cx, cy, 0))), wall_mat)  # outward = away from the footprint centre (origin)


def build_roofs(roofs: list[list[Vector]], style: dict):
    roof_mat = dyn_material("roof", style.get("roof_color_hex"))
    for i, ring in enumerate(roofs):
        polygon_obj(f"Roof_{i}", _oriented(ring, Vector((0, 0, 1))), roof_mat)
    return roof_mat


def roof_tiles(roofs: list[list[Vector]], roof_mat: str, course: float = 0.3, lip: float = 0.03):
    """house.py's roof_tiles(), generalized from its two hardcoded object names to this file's
    arbitrary-count Roof_i objects, and from a mixed-material mesh's per-face filter to "every
    sufficiently sloped face" (each Roof_i here is already a single real roof plane)."""
    bm = bmesh.new()
    for i in range(len(roofs)):
        o = bpy.data.objects[f"Roof_{i}"]
        rot = o.matrix_world.to_3x3()
        for poly in o.data.polygons:
            n = (rot @ poly.normal).normalized()
            if n.z < MIN_PITCH or n.z > MAX_PITCH or poly.area < 0.05:
                continue
            down = (Vector((0, 0, -1)) - n * -n.z).normalized()
            pts = [o.matrix_world @ o.data.vertices[i].co for i in poly.vertices]
            ts = [p.dot(down) for p in pts]
            tmin, tmax = min(ts), max(ts)
            for k in range(math.ceil(tmin / course + 1e-6), math.floor(tmax / course - 1e-6) + 1):
                t = k * course
                cut = [a.lerp(b, (t - ta) / (tb - ta)) for (a, ta), (b, tb) in zip(zip(pts, ts), zip(pts[1:] + pts[:1], ts[1:] + ts[:1]))
                       if (ta - t) * (tb - t) < 0]
                if len(cut) < 2:
                    continue
                along = n.cross(down)
                p0, p1 = min(cut, key=along.dot), max(cut, key=along.dot)  # ponytail: assumes convex faces
                back = -down * (t - max(t - course, tmin))
                v = [bm.verts.new(x) for x in (p0 + back + n * 0.004, p1 + back + n * 0.004, p1 + n * lip, p0 + n * lip,
                                              p0 + n * 0.004, p1 + n * 0.004)]
                bm.faces.new((v[0], v[1], v[2], v[3]))
                bm.faces.new((v[3], v[2], v[5], v[4]))
    me = bpy.data.meshes.new("Roof_Tiles")
    bm.normal_update()
    bm.to_mesh(me)
    bm.free()
    me.materials.append(material(roof_mat))
    obj("Roof_Tiles", me)


def _wall_point(base: Vector, along: Vector, s: float, z: float, normal: Vector, offset: float) -> Vector:
    """A point on a vertical wall's plane at horizontal offset s (along `along`) and height z,
    pushed out along the wall's outward normal -- used to place window geometry on the facade."""
    return base + (s - base.dot(along)) * along + (z - base.z) * Vector((0, 0, 1)) + normal * offset


def build_windows(walls: list[list[Vector]], style: dict) -> int:
    """A repeating window grid per wall, sized/spaced from the vision-read style: one row per
    floor from `sill_height_m` up in `floor_height_m` steps, columns at `window_spacing_m`,
    reusing `_point_in_ring_2d` (built for roof-panel placement) to keep each window inside its
    real wall polygon."""
    width, height = style["window_width_m"], style["window_height_m"]
    sill, floor_h, spacing = style["sill_height_m"], style["floor_height_m"], style["window_spacing_m"]
    margin, frame_w = 0.4, 0.06
    bm = bmesh.new()
    count = 0
    for ring in walls:
        normal = _normal(ring)
        if abs(normal.z) > 0.3:  # ponytail: skip near-horizontal "walls" (dormer cheeks etc.) -- no reliable window placement
            continue
        along = normal.cross(Vector((0, 0, 1)))
        if along.length < 1e-6:
            continue
        along = along.normalized()
        ring2d = [(p.dot(along), p.z) for p in ring]
        s_vals, z_vals = [p[0] for p in ring2d], [p[1] for p in ring2d]
        s0, s1, z1 = min(s_vals), max(s_vals), max(z_vals)
        if s1 - s0 < 2 * margin + width:
            continue
        cols = int((s1 - s0 - 2 * margin - width) // spacing) + 1
        floors = []
        z = sill
        while z + height + margin <= z1:
            floors.append(z)
            z += floor_h
        for fz in floors:
            for c in range(cols):
                s = s0 + margin + width / 2 + c * spacing
                cs, cz = (s - width / 2, s + width / 2), (fz, fz + height)
                if not all(_point_in_ring_2d(ring2d, x, y) for x in cs for y in cz):
                    continue
                count += 1
                frame = [bm.verts.new(_wall_point(ring[0], along, x, y, normal, 0.004))
                         for x, y in ((cs[0], cz[0]), (cs[1], cz[0]), (cs[1], cz[1]), (cs[0], cz[1]))]
                bm.faces.new(frame).material_index = 0
                glass = [bm.verts.new(_wall_point(ring[0], along, x, y, normal, 0.012))
                         for x, y in ((cs[0] + frame_w, cz[0] + frame_w), (cs[1] - frame_w, cz[0] + frame_w),
                                      (cs[1] - frame_w, cz[1] - frame_w), (cs[0] + frame_w, cz[1] - frame_w))]
                bm.faces.new(glass).material_index = 1
    me = bpy.data.meshes.new("Windows")
    bm.normal_update()
    bm.to_mesh(me)
    bm.free()
    me.materials.append(material("frame"))
    me.materials.append(material("glass"))
    obj("Windows", me)
    return count


def _longest_wall(walls: list[list[Vector]]) -> list[Vector]:
    return max(walls, key=lambda w: (max(p.x for p in w) - min(p.x for p in w)) ** 2
                                     + (max(p.y for p in w) - min(p.y for p in w)) ** 2)


def _wall_basis(ring: list[Vector]) -> tuple[Vector, Vector] | None:
    """Outward normal and the wall's horizontal direction, or None for a near-horizontal "wall" (dormer cheek etc.)."""
    normal = _normal(ring)
    if abs(normal.z) > 0.3:
        return None
    along = normal.cross(Vector((0, 0, 1)))
    return (normal, along.normalized()) if along.length > 1e-6 else None


def _wall_ground_point(ring: list[Vector], normal: Vector, along: Vector, s_frac: float, offset: float) -> Vector:
    """A point `offset` m out from the wall at ground level, s_frac along its horizontal extent."""
    s_vals = [p.dot(along) for p in ring]
    s = min(s_vals) + s_frac * (max(s_vals) - min(s_vals))
    return _wall_point(ring[0], along, s, 0.0, normal, offset)


def accessories(walls: list[list[Vector]], front: list[Vector]):
    """Heat pump, battery stack and wallbox flush against a real side wall -- house.py finds its
    anchors by ray-casting against one known model; here the wall polygon's own normal/along
    stand in for that, so the same device meshes land on an arbitrary footprint."""
    candidates = [w for w in walls if w is not front and _wall_basis(w)]
    if not candidates:
        return
    service = _longest_wall(candidates)
    normal, along = _wall_basis(service)
    rot = Matrix((along, normal, Vector((0, 0, 1)))).transposed().to_euler()

    hp = _wall_ground_point(service, normal, along, 0.3, 0.33)
    heat_pump(Vector((hp.x, hp.y, LOCAL_PAVING + 0.6)), rot)

    batt = _wall_ground_point(service, normal, along, 0.75, 0.31)
    wb = batt + along * 1.3 + normal * 0.5
    batteries_and_wallbox((batt.x, batt.y, LOCAL_PAVING + 0.45), (wb.x, wb.y, LOCAL_PAVING + 1.3), rot)


def parked_car(front: list[Vector]):
    """A car on the driveway in front of the door wall, nose towards the house."""
    basis = _wall_basis(front)
    if basis is None:
        return
    normal, along = basis
    p = _wall_ground_point(front, normal, along, 0.5, 4.0)  # 4 m of driveway clearance
    rot = Matrix((along, normal, Vector((0, 0, 1)))).transposed().to_euler()
    car(Vector((p.x, p.y, LOCAL_LAWN + 0.66)), rot)


def garden(footprint: list[Vector]):
    """Hedges, two conifers, a couple of shrubs and trees around the footprint -- house.py's
    garden()/trees() use absolute coordinates tied to one bought model; here every position is
    relative to the footprint's own bounding box instead."""
    xs, ys = [p.x for p in footprint], [p.y for p in footprint]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    pad = 1.5  # metres outside the footprint, inside ground()'s GROUND_MARGIN of 6 m

    bevel(box("Hedge_Back", (x1 - x0 + 2 * pad, 0.7, 0.9), (cx, y1 + pad, LOCAL_LAWN + 0.45), "hedge"), 0.2, 2)
    bevel(box("Hedge_West", (0.7, y1 - y0 + 2 * pad, 0.9), (x0 - pad, cy, LOCAL_LAWN + 0.45), "hedge"), 0.2, 2)
    bevel(box("Hedge_East", (0.7, y1 - y0 + 2 * pad, 0.9), (x1 + pad, cy, LOCAL_LAWN + 0.45), "hedge"), 0.2, 2)

    for i, (x, y, s) in enumerate(((x0 - pad * 0.6, y0 - pad * 0.6, 1.0), (x1 + pad * 0.6, y0 - pad * 0.4, 1.15))):
        cylinder(f"Conifer{i}_Trunk", 0.1 * s, 0.6 * s, (x, y, LOCAL_LAWN + 0.3 * s), "trunk", segs=8)
        me = bm_mesh(f"Conifer{i}", lambda bm: bmesh.ops.create_cone(bm, cap_ends=True, segments=10, radius1=0.9 * s,
                                                                     radius2=0, depth=3.2 * s), "conifer")
        obj(f"Conifer{i}", me, (x, y, LOCAL_LAWN + 0.6 * s + 1.6 * s))

    for i, (x, y, r, mat) in enumerate(((x0 - pad * 0.3, y1 + pad * 0.3, 0.5, "bloom"),
                                        (x1 + pad * 0.3, y1 + pad * 0.3, 0.42, "leaf"))):
        me = bm_mesh(f"Shrub{i}", lambda bm: bmesh.ops.create_icosphere(bm, subdivisions=1, radius=r), mat)
        obj(f"Shrub{i}", me, (x, y, LOCAL_LAWN + r * 0.7))

    for i, (x, y, s) in enumerate(((x0 - pad * 0.8, y1 + pad * 0.8, 1.1), (x1 + pad * 0.8, y1 + pad * 0.6, 0.95))):
        cylinder(f"Tree{i}_Trunk", 0.14 * s, 1.6 * s, (x, y, LOCAL_LAWN + 0.8 * s), "trunk", segs=8)
        me = bm_mesh(f"Tree{i}_Crown", lambda bm: bmesh.ops.create_icosphere(bm, subdivisions=1, radius=1.3 * s),
                     "leaf")
        obj(f"Tree{i}_Crown", me, (x, y, LOCAL_LAWN + 2.2 * s))


def ground(footprint: list[Vector]):
    xs, ys = [p.x for p in footprint], [p.y for p in footprint]
    w, d = (max(xs) - min(xs)) + 2 * GROUND_MARGIN, (max(ys) - min(ys)) + 2 * GROUND_MARGIN
    cx, cy = (max(xs) + min(xs)) / 2, (max(ys) + min(ys)) / 2
    bevel(box("Plinth", (w, d, 0.4), (cx, cy, LOCAL_PAVING - 0.21), "plinth"), 0.15, 3)
    box("Lawn", (w - 0.4, d - 0.4, 0.02), (cx, cy, LOCAL_LAWN - 0.005), "lawn")


def _face_basis(normal: Vector) -> tuple[Vector, Vector]:
    """down = steepest in-plane descent (ridge -> eave), along = ridge-parallel, matching house.py's panel orientation."""
    world_down = Vector((0, 0, -1))
    down = world_down - normal * normal.dot(world_down)
    if down.length < 1e-6:  # perfectly flat roof: no slope direction, pick an arbitrary in-plane one
        down = Vector((1, 0, 0)) - normal * normal.dot(Vector((1, 0, 0)))
    down = down.normalized()
    return down, normal.cross(down).normalized()


def _to_2d(ring: list[Vector], ref: Vector, down: Vector, along: Vector) -> list[tuple[float, float]]:
    return [((p - ref).dot(down), (p - ref).dot(along)) for p in ring]


def _point_in_ring_2d(ring2d: list[tuple[float, float]], s: float, u: float) -> bool:
    inside = False
    n = len(ring2d)
    for i in range(n):
        s1, u1 = ring2d[i]
        s2, u2 = ring2d[(i + 1) % n]
        if (u1 > u) != (u2 > u):
            s_at_u = s1 + (u - u1) * (s2 - s1) / (u2 - u1)
            if s < s_at_u:
                inside = not inside
    return inside


def _panel_slots(ring: list[Vector], normal: Vector):
    """Yield panel transforms wholly inside one real roof polygon."""
    down, along = _face_basis(normal)
    ref = ring[0]
    ring2d = _to_2d(ring, ref, down, along)
    s_vals, u_vals = [p[0] for p in ring2d], [p[1] for p in ring2d]
    s0, s1, u0, u1 = min(s_vals), max(s_vals), min(u_vals), max(u_vals)

    step_s, step_u, margin = PANEL[1] + GAP, PANEL[0] + GAP, 0.3
    rows = max(0, int((s1 - s0 - 2 * margin + GAP) // step_s))
    cols = max(0, int((u1 - u0 - 2 * margin + GAP) // step_u))
    orient = Matrix((down, along, normal)).transposed().to_euler()
    for r in range(rows):
        s = s0 + margin + PANEL[1] / 2 + r * step_s
        for c in range(cols):
            u = u0 + margin + PANEL[0] / 2 + c * step_u
            corners = [(s + ds * PANEL[1] / 2, u + du * PANEL[0] / 2) for ds in (-1, 1) for du in (-1, 1)]
            if all(_point_in_ring_2d(ring2d, cs, cu) for cs, cu in corners):
                yield ref + down * s + along * u + normal * (PANEL[2] / 2 + 0.03), orient


def pv_panels(roofs: list[list[Vector]]) -> int:
    """Tiles the whole usable real roof, starting with the most south-facing plane.

    Earlier versions used only one best face. That made the GLB contain fewer
    slots than a planner could select (for example 15 visible panels for a
    30-panel design). Each panel is still accepted only when all four corners
    lie inside its actual CityGML roof polygon.

    ponytail: no skylight/chimney avoidance -- LoD2 doesn't carry that detail, unlike the hand-placed bought model."""
    candidates = []
    for ring in roofs:
        oriented = _oriented(ring, Vector((0, 0, 1)))
        normal = _normal(oriented)
        if normal.z <= 0:
            continue
        candidates.append((oriented, normal, _area(oriented), -normal.y))  # local y = north, so south-facing = -y
    if not candidates:
        return 0
    sloped = [c for c in candidates if MIN_PITCH <= c[1].z <= MAX_PITCH]
    # All usable sloped planes get slots, in yield-priority order.  A flat roof
    # is a fallback only when the data contains no pitched face at all.
    chosen = sloped or candidates
    chosen.sort(key=lambda c: (c[3], c[2]), reverse=True)
    pm = panel_mesh()
    placed = 0
    for ring, normal, _area_, _south in chosen:
        for loc, orient in _panel_slots(ring, normal):
            placed += 1
            obj(f"PV_Panel_{placed:02d}", pm, loc, orient)
    return placed


def front_door(ring: list[Vector], style: dict):
    """A door on the longest ground-level wall -- every real house has one and LoD2 doesn't say
    which wall faces the street, so the longest facade is the reasonable generic pick."""
    width, height = 1.0, 2.05
    normal = _normal(ring)
    if abs(normal.z) > 0.3:
        return
    along = normal.cross(Vector((0, 0, 1)))
    if along.length < 1e-6:
        return
    along = along.normalized()
    ring2d = [(p.dot(along), p.z) for p in ring]
    s_vals = [p[0] for p in ring2d]
    s_mid = (min(s_vals) + max(s_vals)) / 2
    cs, cz = (s_mid - width / 2, s_mid + width / 2), (0.0, height)
    if not all(_point_in_ring_2d(ring2d, x, y) for x in cs for y in cz):
        return
    door_mat = dyn_material("frame", style.get("wall_color_hex"))
    verts = [_wall_point(ring[0], along, x, y, normal, 0.01) for x, y in
             ((cs[0], cz[0]), (cs[1], cz[0]), (cs[1], cz[1]), (cs[0], cz[1]))]
    me = mesh("Front_Door", verts, [(0, 1, 2, 3)], [door_mat])
    obj("Front_Door", me)


def build(geometry: dict) -> dict:
    style = {**DEFAULT_STYLE, **geometry.get("style", {})}
    footprint = _vecs(geometry["footprint"])
    walls = [_vecs(w) for w in geometry["walls"]]
    roofs = [_vecs(r) for r in geometry["roofs"]]
    setup_collection()
    ground(footprint)
    build_walls(walls, style)
    roof_mat = build_roofs(roofs, style)
    windows = build_windows(walls, style)
    front = _longest_wall(walls)
    front_door(front, style)
    accessories(walls, front)
    parked_car(front)
    garden(footprint)
    if style["roof_material"] == "tile":
        roof_tiles(roofs, roof_mat)  # last, so the facade/window ray casts never hit a tile
    return {"panels": pv_panels(roofs), "windows": windows}


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    geometry_path, out_path = Path(argv[0]), Path(argv[1])
    result = build(load_geometry(geometry_path))
    print({**export(out_path), **result})
