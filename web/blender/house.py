"""Turns the bought house model into web/public/models/house.glb.

    blender -b /path/to/3D_house10.blend --python web/blender/house.py

The model is "House 10" by TomaszCGB (TurboSquid licence). Only the GLB built from it is in the repo, never the .blend.
Its image textures aren't shipped with it, so every material becomes a flat colour from PALETTE.

Node names are the contract with web/components/HouseScene.tsx:
  PV_Panel_01..NN  slots on the east roof face in fill order (show the first N), 450 Wp each like the Reonic modules;
                   NN is printed on export and must match MAX_PANELS
  HeatPump, HeatPump_Fan (spin around its local Y in three.js), Battery_1..5 (one per ~5 kWh), Wallbox, Car
Units are metres. The street side (garage, balcony) faces -Y, which becomes +Z in three.js after glTF's Y-up conversion.
"""
import math
from pathlib import Path

import bmesh
import bpy
from mathutils import Matrix, Vector

OUT = Path(__file__).resolve().parents[1] / "public" / "models" / "house.glb"

PANEL = (1.134, 1.762, 0.04)  # portrait module: width along the ridge, height down the slope
GAP = 0.02
BATTERIES = 5
PAVING, LAWN = -0.19, -0.55  # top of the model's paving and of its (removed) grass platform
DRIVEWAY_END = -8.5  # the model's driveway runs 15 m to the street; cut it so the scene stays compact
DROP = ("floor", "ceiling", "door_wing", "door_frame", "grass", "camera_")  # interior, grass blades, camera rig
KEEP = {"door_wing.011", "door_frame.011", "door_wing.013", "door_frame.013"}  # the front and back door

PALETTE = {  # Reonic-ish: warm off-whites, anthracite, emerald accent
    "wall": ("#F4F1EA", 0.85), "plinth": ("#ECE8DE", 0.9), "lawn": ("#CBD6BF", 1.0), "paving": ("#D6D3CB", 0.95),
    "roof": ("#9A6150", 0.8), "ridge": ("#3A3D42", 0.6), "frame": ("#FFFFFF", 0.5), "glass": ("#26303C", 0.15),
    "pv_frame": ("#C9CED4", 0.35), "pv_cell": ("#142033", 0.2), "pv_grid": ("#5E6B7E", 0.4), "device": ("#F7F7F5", 0.45), "dark": ("#24272B", 0.6),
    "led": ("#34D399", 0.4), "car": ("#55657A", 0.3), "tyre": ("#1E1F22", 0.9), "trunk": ("#8A6C4D", 0.9),
    "leaf": ("#9DB69A", 0.9), "wood": ("#8F6E52", 0.8), "metal": ("#9AA0A6", 0.45), "base": ("#BDB8AE", 0.9),
    "curb": ("#C8C4BB", 0.9), "soil": ("#6B5A48", 1.0), "terrace": ("#CFCBC2", 0.85),
    "hedge": ("#7F9C78", 0.95), "conifer": ("#6E8A6A", 0.95), "stone": ("#E2DED5", 0.9), "tail": ("#B4483F", 0.4),
    "bloom": ("#E8C9A0", 0.9), "rail": ("#AEB4BA", 0.4),
}
MODEL_MATS = {  # the model's material names -> PALETTE
    "plaster_white": "wall", "roof_01": "roof", "metal_blue": "ridge", "wood_brown": "wood", "wood_balls_brown": "wood",
    "window_glass": "glass", "window_glass_old": "glass", "glass_door": "glass", "metal_grey": "metal",
    "plate_grey": "terrace", "foundation_grey_brick": "base", "brick_hexagonal": "paving", "curb": "curb",
    "parapet": "frame", "ground": "soil",
}


# -- helpers -------------------------------------------------------------------------------------
def srgb(hex_: str) -> tuple[float, float, float, float]:
    c = [int(hex_[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    return (*[x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c], 1.0)


def material(name: str) -> bpy.types.Material:
    if name in bpy.data.materials:
        return bpy.data.materials[name]
    hex_, rough = PALETTE[name]
    m = bpy.data.materials.new(name)
    bsdf = m.node_tree.nodes["Principled BSDF"] if m.node_tree else None
    if bsdf is None:  # Blender < 5 needs use_nodes; 5.x materials always have a node tree
        m.use_nodes = True
        bsdf = m.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = srgb(hex_)
    bsdf.inputs["Roughness"].default_value = rough
    if name == "led":
        bsdf.inputs["Emission Color"].default_value = srgb(hex_)
        bsdf.inputs["Emission Strength"].default_value = 3.0
    m.diffuse_color = srgb(hex_)
    return m


def obj(name: str, mesh: bpy.types.Mesh, loc=(0, 0, 0), rot=(0, 0, 0), parent=None) -> bpy.types.Object:
    o = bpy.data.objects.new(name, mesh)
    o.location, o.rotation_euler, o.parent = loc, rot, parent
    bpy.data.collections["House"].objects.link(o)
    return o


def mesh(name: str, verts, faces, mats: list[str], face_mats=None) -> bpy.types.Mesh:
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    for m in mats:
        me.materials.append(material(m))
    if face_mats:
        for poly, i in zip(me.polygons, face_mats):
            poly.material_index = i
    me.validate()
    return me


def box_mesh(name: str, size, mats=("wall",), top_mat: int = 0) -> bpy.types.Mesh:
    x, y, z = (s / 2 for s in size)
    v = [(-x, -y, -z), (x, -y, -z), (x, y, -z), (-x, y, -z), (-x, -y, z), (x, -y, z), (x, y, z), (-x, y, z)]
    f = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    return mesh(name, v, f, list(mats), [0, top_mat, 0, 0, 0, 0])


def box(name, size, loc, mat="wall", rot=(0, 0, 0), parent=None):
    return obj(name, box_mesh(name, size, (mat,)), loc, rot, parent)


def bm_mesh(name: str, build, mat: str) -> bpy.types.Mesh:
    bm = bmesh.new()
    build(bm)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    me.materials.append(material(mat))
    return me


def cylinder(name, r, depth, loc, mat, rot=(0, 0, 0), segs=24, parent=None):
    me = bm_mesh(name, lambda bm: bmesh.ops.create_cone(bm, cap_ends=True, segments=segs, radius1=r, radius2=r,
                                                        depth=depth), mat)
    return obj(name, me, loc, rot, parent)


def bevel(o, width=0.04, segments=2):
    m = o.modifiers.new("Bevel", "BEVEL")
    m.width, m.segments, m.limit_method = width, segments, "ANGLE"
    return o


# -- model ---------------------------------------------------------------------------------------
def strip():
    """Keep the outside of the house, move it into the House collection, swap every material for a flat colour."""
    house = bpy.data.collections.new("House")
    bpy.context.scene.collection.children.link(house)
    for m in list(bpy.data.materials):  # out of PALETTE's way: the model has its own "curb"
        m.name = "model_" + m.name
    for o in list(bpy.data.objects):
        if o.type != "MESH" or (o.name.startswith(DROP) and o.name not in KEEP):
            bpy.data.objects.remove(o, do_unlink=True)
            continue
        for c in list(o.users_collection):
            c.objects.unlink(o)
        house.objects.link(o)
        for slot in o.material_slots:
            if slot.material:
                slot.material = material(MODEL_MATS[slot.material.name.removeprefix("model_")])  # KeyError = unmapped

    g = bpy.data.objects["ground_around_house"]
    bm = bmesh.new()
    bm.from_mesh(g.data)
    bm.transform(g.matrix_world)
    cut = bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=(0, DRIVEWAY_END, 0),
                                 plane_no=(0, 1, 0), clear_inner=True)["geom_cut"]
    bmesh.ops.holes_fill(bm, edges=[e for e in cut if isinstance(e, bmesh.types.BMEdge) and e.is_boundary])
    bm.transform(g.matrix_world.inverted())
    bm.to_mesh(g.data)
    bm.free()


def ground():
    # plinth with a lawn top, slightly rounded like an architectural model, in place of the 60 m grass platform
    bevel(box("Plinth", (22, 19.5, 0.4), (0.6, 0.5, LAWN - 0.21), "plinth"), 0.15, 3)
    box("Lawn", (21.6, 19.1, 0.02), (0.6, 0.5, LAWN - 0.005), "lawn")


def wall(origin, direction) -> Vector:
    """Where a ray first hits the model, so devices sit flush on the real facade."""
    hit, loc, *_ = bpy.context.scene.ray_cast(bpy.context.evaluated_depsgraph_get(), Vector(origin), Vector(direction))
    if not hit:
        raise RuntimeError(f"nothing hit from {origin} towards {direction}")
    return loc


def panel_mesh() -> bpy.types.Mesh:
    """Silver frame, a grey backsheet showing through as the grid, 6 x 10 dark cells just above it."""
    me = box_mesh("PV_Panel", (PANEL[1], PANEL[0], PANEL[2]), ("pv_frame", "pv_grid", "pv_cell"), top_mat=1)
    bm = bmesh.new()
    bm.from_mesh(me)
    rows, cols, rim, gap = 10, 6, 0.035, 0.012
    cw, ch = (PANEL[0] - 2 * rim) / cols, (PANEL[1] - 2 * rim) / rows
    z = PANEL[2] / 2 + 0.002
    for r in range(rows):
        for c in range(cols):
            x0, y0 = -PANEL[1] / 2 + rim + r * ch + gap / 2, -PANEL[0] / 2 + rim + c * cw + gap / 2
            x1, y1 = x0 + ch - gap, y0 + cw - gap
            f = bm.faces.new([bm.verts.new(v) for v in ((x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z))])
            f.material_index = 2
    bm.to_mesh(me)
    bm.free()
    return me


def pv_panels() -> int:
    """Slots on the east face of the main roof, around its two skylights and the chimney.

    Fill order: the fullest rows first, each centred, so any N reads as a tidy block."""
    roof = bpy.data.objects["roof"]
    rot = roof.matrix_world.to_3x3()
    east = Vector((0.67, 0, 0.74)).normalized()
    faces = [p for p in roof.data.polygons if (rot @ p.normal).normalized().dot(east) > 0.99]
    pts = [roof.matrix_world @ roof.data.vertices[i].co for p in faces for i in p.vertices]
    n = sum(((rot @ p.normal).normalized() for p in faces), Vector()).normalized()
    d = max(n.dot(p) for p in pts)  # the outer surface, not the rafters underneath
    top = max(pts, key=lambda p: p.z)
    top += (d - n.dot(top)) * n
    down = Vector((n.z, 0, -n.x)).normalized()  # down the slope, towards the eave
    slope = max((p - top).dot(down) for p in pts)
    y0, y1 = min(p.y for p in pts), max(p.y for p in pts)

    obstacles = []
    for name in ("window_roof", "chimney.002"):
        o = bpy.data.objects[name]
        for v in o.data.vertices:
            p = o.matrix_world @ v.co
            if -0.5 < n.dot(p) - d < 2.0 and (p - top).dot(down) > -0.5:
                obstacles.append(((p - top).dot(down), p.y))

    step_s, step_y = PANEL[1] + GAP, PANEL[0] + GAP
    rows = int((slope - 0.45 - 0.25 + GAP) // step_s)  # 45 cm below the ridge cap, 25 cm above the gutter
    cols = int((y1 - y0 - 0.6 + GAP) // step_y)
    slots = []
    for r in range(rows):
        s = 0.45 + r * step_s + PANEL[1] / 2
        for c in range(cols):
            y = (y0 + y1) / 2 + (c - (cols - 1) / 2) * step_y
            if not any(abs(os - s) < PANEL[1] / 2 + 0.12 and abs(oy - y) < PANEL[0] / 2 + 0.12 for os, oy in obstacles):
                slots.append((r, c, s, y))
    per_row = {r: sum(1 for x in slots if x[0] == r) for r in range(rows)}
    slots.sort(key=lambda x: (-per_row[x[0]], -x[0], abs(x[1] - (cols - 1) / 2), x[1]))

    pm = panel_mesh()
    orient = Matrix((down, n.cross(down), n)).transposed().to_euler()
    for i, (_, _, s, y) in enumerate(slots, 1):
        loc = Vector((top.x, y, top.z)) + down * s + n * (PANEL[2] / 2 + 0.1)  # 10 cm of mounting rails
        obj(f"PV_Panel_{i:02d}", pm, loc, orient)
    return len(slots)


def heat_pump():
    # outdoor unit on the windowless stretch of the east facade, blowing away from the house
    y = 2.75
    x = wall((12, y, 1.2), (-1, 0, 0)).x + 0.3
    hp = bevel(box("HeatPump", (1.3, 0.55, 1.0), (x + 0.05, y, PAVING + 0.6), "device", rot=(0, 0, math.pi / 2)), 0.04, 2)
    box("HeatPump_Feet", (1.1, 0.45, 0.1), (0, 0, -0.55), "dark", parent=hp)
    box("HeatPump_Pad", (1.6, 0.9, 0.1), (0, 0.05, -0.62), "terrace", parent=hp)
    cylinder("HeatPump_Grille", 0.38, 0.03, (-0.2, -0.285, 0.02), "dark", rot=(math.pi / 2, 0, 0), parent=hp)
    fan = bpy.data.objects.new("HeatPump_Fan", None)  # empty pivot; blades are its children
    fan.empty_display_size = 0.3
    fan.location, fan.rotation_euler, fan.parent = (-0.2, -0.305, 0.02), (math.pi / 2, 0, 0), hp
    bpy.data.collections["House"].objects.link(fan)
    for k in range(3):
        box(f"HeatPump_Blade{k}", (0.08, 0.33, 0.012), (0, 0, 0), "pv_frame", rot=(0, 0, k * 2 * math.pi / 3),
            parent=fan).data.transform(Matrix.Translation((0, 0.17, 0)))
    box("HeatPump_Panel", (0.3, 0.02, 0.7), (0.42, -0.28, 0.02), "pv_frame", parent=hp)
    box("HeatPump_Cover", (1.36, 0.6, 0.04), (0, 0, 0.52), "metal", parent=hp)
    for k in range(5):  # side louvres on the service panel
        box(f"HeatPump_Louvre{k}", (0.24, 0.015, 0.025), (0.42, -0.295, -0.22 + k * 0.1), "dark", parent=hp)
    for k, dx in enumerate((0.3, 0.42)):  # refrigerant lines into the wall, in white trunking
        box(f"HeatPump_Pipe{k}", (0.06, 0.5, 0.06), (dx, 0.5, -0.2 + k * 0.08), "frame", parent=hp)


def batteries_and_wallbox():
    # battery modules stacked on the main block's front wall under the balcony
    bx = 5.75
    by = wall((bx, -12, 1.2), (0, 1, 0)).y - 0.12
    for i in range(BATTERIES):
        b = bevel(box(f"Battery_{i + 1}", (0.62, 0.2, 0.36), (bx, by, PAVING + 0.45 + i * 0.4), "device"), 0.02, 2)
        box(f"Battery_{i + 1}_LED", (0.36, 0.01, 0.025), (0, -0.105, 0.1), "led", parent=b)
        box(f"Battery_{i + 1}_Seam", (0.64, 0.205, 0.02), (0, 0, -0.19), "metal", parent=b)
        if i == 0:  # the base unit carries the plinth
            box("Battery_1_Plinth", (0.66, 0.24, 0.24), (0, 0, -0.3), "dark", parent=b)
    # the wallbox on a charging post beside the car's nose, out of the garage's shadow
    wb = bevel(box("Wallbox", (0.4, 0.16, 0.56), (-3.6, -4.9, PAVING + 1.3), "device"), 0.03, 2)
    box("Wallbox_Post", (0.14, 0.14, 1.3), (0, 0.12, -0.65), "dark", parent=wb)
    box("Wallbox_Face", (0.3, 0.01, 0.4), (0, -0.085, 0), "dark", parent=wb)
    box("Wallbox_LED", (0.18, 0.01, 0.03), (0, -0.092, 0.13), "led", parent=wb)
    cylinder("Wallbox_Plug", 0.06, 0.07, (0, -0.1, -0.08), "pv_frame", rot=(math.pi / 2, 0, 0), segs=12, parent=wb)
    box("Wallbox_Base", (0.34, 0.34, 0.04), (0, 0.12, -1.29), "metal", parent=wb)
    box("Wallbox_Cap", (0.46, 0.22, 0.03), (0, 0.02, 0.295), "dark", parent=wb)
    for k in range(9):  # the charging cable hanging in a loop beside the box, as short segments
        a = math.radians(200 + k * 20)
        box(f"Wallbox_Cable{k}", (0.07, 0.03, 0.03), (0.26 + 0.12 * math.cos(a), -0.02, -0.3 + 0.2 * math.sin(a)), "dark",
            rot=(0, -(a + math.pi / 2), 0), parent=wb)


def extrude(name: str, profile, half_width: float, mat: str) -> bpy.types.Mesh:
    """A convex side profile [(y, z), ...] extruded from x = -half_width to +half_width."""
    n = len(profile)
    v = [(-half_width, y, z) for y, z in profile] + [(half_width, y, z) for y, z in profile]
    f = [tuple(range(n - 1, -1, -1)), tuple(range(n, 2 * n))] + [(i, (i + 1) % n, n + (i + 1) % n, n + i) for i in range(n)]
    me = mesh(name, v, f, [mat])
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])  # outward, whichever way the profile winds
    bm.to_mesh(me)
    bm.free()
    return me


def car():
    # on the driveway in front of the garage door
    # body: a side profile (y forward is -y, z up) extruded across the width, nose sloping into the bonnet
    c = obj("Car", extrude("Car", [(-2.15, -0.3), (2.15, -0.3), (2.18, 0.12), (2.05, 0.3), (-1.55, 0.3),
                                    (-2.12, 0.12)], 0.91, "car"), (-5.14, -3.6, PAVING + 0.66))
    bevel(c, 0.1, 3)
    cabin = extrude("Car_Cabin", [(-1.15, 0.28), (1.6, 0.28), (1.35, 0.82), (-0.25, 0.82)], 0.78, "glass")
    bevel(obj("Car_Cabin", cabin, parent=c), 0.06, 2)
    roof = extrude("Car_Roof", [(-0.2, 0.8), (1.33, 0.8), (1.3, 0.86), (-0.17, 0.86)], 0.8, "car")
    obj("Car_Roof", roof, parent=c)
    for i, (x, y) in enumerate(((-0.86, -1.35), (0.86, -1.35), (-0.86, 1.35), (0.86, 1.35))):
        cylinder(f"Car_Wheel{i}", 0.33, 0.24, (x, y, -0.33), "tyre", rot=(0, math.pi / 2, 0), parent=c)
        cylinder(f"Car_Rim{i}", 0.2, 0.02, (x * 1.15, y, -0.33), "rail", rot=(0, math.pi / 2, 0), segs=16, parent=c)
    box("Car_Lights", (1.4, 0.02, 0.07), (0, -2.19, 0.14), "frame", parent=c)
    box("Car_Tail", (1.5, 0.02, 0.08), (0, 2.19, 0.16), "tail", parent=c)
    for side in (-1, 1):
        box(f"Car_Mirror{side}", (0.14, 0.08, 0.07), (side * 0.98, -0.95, 0.42), "car", parent=c)
        box(f"Car_Pillar{side}", (0.02, 0.1, 0.52), (side * 0.785, 0.45, 0.55), "car", parent=c)


def trees():
    for i, (x, y, s) in enumerate(((-9.0, 8.2, 1.2), (10.0, 7.6, 1.0))):
        cylinder(f"Tree{i}_Trunk", 0.14 * s, 1.6 * s, (x, y, LAWN + 0.8 * s), "trunk", segs=8)
        me = bm_mesh(f"Tree{i}_Crown", lambda bm: bmesh.ops.create_icosphere(bm, subdivisions=1, radius=1.3 * s),
                     "leaf")
        obj(f"Tree{i}_Crown", me, (x, y, LAWN + 2.2 * s))


def garden():
    """Hedges round the back and sides, two conifers and a few shrubs, so the house sits in a garden, not on a tray."""
    for name, size, loc in (("Hedge_Back", (19.0, 0.7, 0.9), (0.6, 9.75, LAWN + 0.45)),
                            ("Hedge_West", (0.7, 11.0, 0.9), (-9.9, 4.0, LAWN + 0.45)),
                            ("Hedge_East", (0.7, 11.0, 0.9), (11.1, 4.0, LAWN + 0.45))):
        bevel(box(name, size, loc, "hedge"), 0.2, 2)
    for i, (x, y, s) in enumerate(((-8.6, 2.0, 1.0), (9.8, 2.6, 1.15))):
        cylinder(f"Conifer{i}_Trunk", 0.1 * s, 0.6 * s, (x, y, LAWN + 0.3 * s), "trunk", segs=8)
        me = bm_mesh(f"Conifer{i}", lambda bm: bmesh.ops.create_cone(bm, cap_ends=True, segments=10, radius1=0.9 * s,
                                                                     radius2=0, depth=3.2 * s), "conifer")
        obj(f"Conifer{i}", me, (x, y, LAWN + 0.6 * s + 1.6 * s))
    for i, (x, y, r, mat) in enumerate(((-8.8, -6.8, 0.55, "hedge"), (-8.0, -7.6, 0.4, "bloom"), (9.6, -6.0, 0.6, "hedge"),
                                        (10.4, -7.0, 0.42, "leaf"), (8.6, 8.2, 0.5, "bloom"))):
        me = bm_mesh(f"Shrub{i}", lambda bm: bmesh.ops.create_icosphere(bm, subdivisions=1, radius=r), mat)
        obj(f"Shrub{i}", me, (x, y, LAWN + r * 0.7))


def roof_tiles(course=0.3, lip=0.03):
    """Tile courses on every upward roof face: wedges rising from the surface to a lip at each course's lower edge.

    Courses sit on a world grid along the slope, so neighbouring faces of one roof plane line up."""
    bm = bmesh.new()
    for name in ("roof", "roof.001"):
        o = bpy.data.objects[name]
        rot = o.matrix_world.to_3x3()
        tile = [i for i, slot in enumerate(o.material_slots) if slot.material and slot.material.name == "roof"]
        for poly in o.data.polygons:
            n = (rot @ poly.normal).normalized()
            if poly.material_index not in tile or n.z < 0.3 or poly.area < 0.05:
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
    me.materials.append(material("roof"))
    obj("Roof_Tiles", me)


def build() -> int:
    strip()
    ground()
    panels = pv_panels()
    heat_pump()
    batteries_and_wallbox()
    car()
    trees()
    garden()
    roof_tiles()  # last, so the facade ray casts never hit a tile
    return panels


# -- preview render and export -----------------------------------------------------------------
def preview(path: str, res=(1400, 900)):
    """Render a quick look from the default web camera angle (not exported)."""
    sc = bpy.context.scene
    cam = bpy.data.objects.new("PreviewCam", bpy.data.cameras.new("PreviewCam"))
    sc.collection.objects.link(cam)
    cam.data.lens = 40
    cam.location = (17.0, -27.0, 14.0)
    target = Vector((0.5, 0.5, 2.6))
    cam.rotation_euler = (target - cam.location).to_track_quat("-Z", "Y").to_euler()
    sun = bpy.data.objects.new("PreviewSun", bpy.data.lights.new("PreviewSun", "SUN"))
    sc.collection.objects.link(sun)
    sun.data.energy, sun.data.angle = 3.5, math.radians(8)
    sun.rotation_euler = (math.radians(50), math.radians(-20), math.radians(-35))
    world = sc.world = bpy.data.worlds.new("Preview")  # the model's own world wants an HDR that isn't shipped
    if world.node_tree is None:
        world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Color"].default_value = srgb("#FDFDFB")
    world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.9
    sc.camera = cam
    sc.render.engine = "BLENDER_EEVEE"
    sc.eevee.taa_render_samples = 32
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.film_transparent = False
    sc.view_settings.view_transform = "Standard"
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    return {"rendered": path}


def export(path: Path = OUT):
    path.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.object.select_all(action="DESELECT")
    for o in bpy.data.collections["House"].all_objects:
        o.select_set(True)
    bpy.ops.export_scene.gltf(filepath=str(path), export_format="GLB", use_selection=True, export_apply=True,
                              export_yup=True, export_cameras=False, export_lights=False,
                              export_texcoords=False)  # flat colours only: UVs would just add bytes
    return {"exported": str(path), "bytes": path.stat().st_size}


if __name__ == "__main__":
    panels = build()
    print({**export(), "panels": panels})
