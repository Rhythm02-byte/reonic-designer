"""Builds the 3D house for the web frontend and exports web/public/models/house.glb.

    blender --background --python web/blender/house.py

Node names are the contract with the web app (web/components/house/):
  PV_Panel_01..30  roof slots in fill order (show the first N), 450 Wp each like the Reonic modules
  HeatPump, HeatPump_Fan (spin around its local Y in three.js), Battery_1..5 (one per ~5 kWh), Wallbox, Car
Units are metres. South is -Y here, which becomes +Z (towards the default camera) after glTF's Y-up conversion.
"""
import math
from pathlib import Path

import bmesh
import bpy
import mathutils

OUT = Path(__file__).resolve().parents[1] / "public" / "models" / "house.glb"

W, D, WALL = 12.0, 9.0, 6.0  # house width (x), depth (y), eave height
PITCH = math.radians(30)
OVERHANG = 0.6
ROOF_T = 0.18
RIDGE = WALL + D / 2 * math.tan(PITCH)
PANEL = (1.134, 1.762, 0.04)  # portrait module, x along the ridge, y up the slope
COLS, ROWS, GAP = 10, 3, 0.02
BATTERIES = 5

PALETTE = {  # Reonic-ish: warm off-whites, anthracite, emerald accent
    "wall": ("#F4F1EA", 0.85), "plinth": ("#ECE8DE", 0.9), "lawn": ("#CBD6BF", 1.0), "paving": ("#D6D3CB", 0.95),
    "roof": ("#3B3E44", 0.7), "ridge": ("#2E3136", 0.6), "frame": ("#FFFFFF", 0.5), "glass": ("#26303C", 0.15),
    "pv_frame": ("#C9CED4", 0.35), "pv_cell": ("#17233A", 0.2), "device": ("#F7F7F5", 0.45), "dark": ("#24272B", 0.6),
    "led": ("#10B981", 0.4), "car": ("#4A5562", 0.3), "tyre": ("#1E1F22", 0.9), "trunk": ("#8A6C4D", 0.9),
    "leaf": ("#9DB69A", 0.9),
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
    bpy.context.scene.collection.children["House"].objects.link(o)
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
def clear():
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    for coll in (bpy.data.meshes, bpy.data.materials, bpy.data.cameras, bpy.data.lights):
        for item in list(coll):
            coll.remove(item)
    if "House" not in bpy.data.collections:
        bpy.context.scene.collection.children.link(bpy.data.collections.new("House"))


def ground():
    # plinth with a lawn top, slightly rounded like an architectural model
    bevel(box("Plinth", (23, 17, 0.4), (-1, -0.5, -0.2), "plinth"), 0.15, 3)
    box("Lawn", (22.6, 16.6, 0.02), (-1, -0.5, 0.01), "lawn")
    box("Driveway", (4.2, 12.5, 0.03), (-8.4, -2.2, 0.025), "paving")
    box("Path", (1.6, 3.6, 0.03), (0, -6.3, 0.025), "paving")


def house():
    # walls + gables as one pentagonal prism along x
    h, y = W / 2, D / 2
    prof = [(-y, 0), (y, 0), (y, WALL), (0, RIDGE), (-y, WALL)]
    verts = [(-h, a, b) for a, b in prof] + [(h, a, b) for a, b in prof]
    faces = [(4, 3, 2, 1, 0), (5, 6, 7, 8, 9)] + [(i, (i + 1) % 5, (i + 1) % 5 + 5, i + 5) for i in range(5)]
    bevel(obj("Walls", mesh("Walls", verts, faces, ["wall"])), 0.05, 2)

    # roof slabs: underside sits on the plane through wall top and ridge, overhang on all sides
    run = y + OVERHANG
    eave_z = WALL - OVERHANG * math.tan(PITCH)
    n_s, n_c = math.sin(PITCH), math.cos(PITCH)
    for side, sgn in (("South", -1), ("North", 1)):
        lo, hi = (sgn * run, eave_z), (0.0, RIDGE)
        off = (sgn * n_s * ROOF_T, n_c * ROOF_T)  # outward normal * thickness
        pts = [lo, hi, (hi[0] + off[0], hi[1] + off[1]), (lo[0] + off[0], lo[1] + off[1])]
        xr = h + OVERHANG * 0.7
        v = [(-xr, a, b) for a, b in pts] + [(xr, a, b) for a, b in pts]
        f = [(0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]
        obj(f"Roof_{side}", mesh(f"Roof_{side}", v, f, ["roof"]))
    box("Ridge", (W + OVERHANG * 1.4, 0.36, 0.2), (0, 0, RIDGE + ROOF_T * 0.9), "ridge")

    # south facade: door, windows; west facade gets two windows so the orbit view isn't blank
    def window(name, x, z, w=1.2, ht=1.4, face_y=-y, normal=-1, axis="y"):
        if axis == "y":
            box(f"{name}_Frame", (w + 0.16, 0.08, ht + 0.16), (x, face_y + normal * 0.03, z), "frame")
            box(f"{name}_Glass", (w, 0.08, ht), (x, face_y + normal * 0.06, z), "glass")
        else:
            box(f"{name}_Frame", (0.08, w + 0.16, ht + 0.16), (face_y + normal * 0.03, x, z), "frame")
            box(f"{name}_Glass", (0.08, w, ht), (face_y + normal * 0.06, x, z), "glass")

    box("Door_Frame", (1.3, 0.08, 2.35), (0, -y - 0.03, 1.17), "frame")
    box("Door", (1.1, 0.1, 2.2), (0, -y - 0.05, 1.1), "dark")
    for i, x in enumerate((-2.4, 2.4, 4.4)):
        window(f"Window_G{i}", x, 1.55)
    for i, x in enumerate((-4.4, -1.6, 1.6, 4.4)):
        window(f"Window_U{i}", x, 4.4)
    for i, (yy, z) in enumerate(((1.8, 1.55), (1.8, 4.4), (-1.6, 4.4))):
        window(f"Window_W{i}", yy, z, face_y=-h, normal=-1, axis="x")
    for i, (yy, z) in enumerate(((-1.8, 4.4), (1.8, 4.4), (1.8, 1.55))):
        window(f"Window_E{i}", yy, z, face_y=h, normal=1, axis="x")


def pv_panels():
    """30 slots on Roof_South; ordered bottom row first, centred, so any N reads as a tidy block."""
    pm = box_mesh("PV_Panel", PANEL, ("pv_frame", "pv_cell"), top_mat=1)
    eave_y, eave_z = -(D / 2 + OVERHANG), WALL - OVERHANG * math.tan(PITCH)
    up = (math.cos(PITCH), math.sin(PITCH))  # along the slope (y, z)
    nrm = (-math.sin(PITCH), math.cos(PITCH))
    slope_len = (D / 2 + OVERHANG) / math.cos(PITCH)
    block_h = ROWS * PANEL[1] + (ROWS - 1) * GAP
    s0 = (slope_len - block_h) / 2 - 0.08  # small bias towards the eave, the ridge cap eats the top
    slots = [(r, c) for r in range(ROWS) for c in range(COLS)]
    slots.sort(key=lambda rc: (rc[0], abs(rc[1] - (COLS - 1) / 2), rc[1]))
    for i, (r, c) in enumerate(slots, 1):
        x = (c - (COLS - 1) / 2) * (PANEL[0] + GAP)
        s = s0 + r * (PANEL[1] + GAP) + PANEL[1] / 2
        lift = ROOF_T + 0.07  # mounting rails
        loc = (x, eave_y + up[0] * s + nrm[0] * lift, eave_z + up[1] * s + nrm[1] * lift)
        obj(f"PV_Panel_{i:02d}", pm, loc, (PITCH, 0, 0))


def heat_pump():
    hp = bevel(box("HeatPump", (1.1, 0.48, 0.86), (W / 2 - 0.9, -D / 2 - 0.75, 0.53), "device"), 0.03, 2)
    box("HeatPump_Feet", (0.9, 0.4, 0.1), (0, 0, -0.48), "dark", parent=hp)
    cylinder("HeatPump_Grille", 0.33, 0.03, (-0.17, -0.25, 0.02), "dark", rot=(math.pi / 2, 0, 0), parent=hp)
    fan = bpy.data.objects.new("HeatPump_Fan", None)  # empty pivot; blades are its children
    fan.empty_display_size = 0.3
    fan.location, fan.rotation_euler, fan.parent = (-0.17, -0.27, 0.02), (math.pi / 2, 0, 0), hp
    bpy.data.collections["House"].objects.link(fan)
    for k in range(3):
        box(f"HeatPump_Blade{k}", (0.07, 0.29, 0.012), (0, 0, 0), "pv_frame", rot=(0, 0, k * 2 * math.pi / 3),
            parent=fan).data.transform(mathutils.Matrix.Translation((0, 0.15, 0)))
    box("HeatPump_Panel", (0.28, 0.02, 0.6), (0.36, -0.25, 0.02), "pv_frame", parent=hp)


def batteries_and_wallbox():
    # outdoor-rated storage on the south facade next to the driveway, modules stacked bottom up
    y = -D / 2 - 0.12
    for i in range(BATTERIES):
        b = bevel(box(f"Battery_{i + 1}", (0.62, 0.2, 0.36), (-5.3, y, 0.45 + i * 0.4), "device"), 0.02, 2)
        box(f"Battery_{i + 1}_LED", (0.36, 0.01, 0.025), (0, -0.105, 0.1), "led", parent=b)
    wb = bevel(box("Wallbox", (0.32, 0.12, 0.44), (-4.35, -D / 2 - 0.08, 1.3), "dark"), 0.02, 2)
    box("Wallbox_LED", (0.16, 0.01, 0.025), (0, -0.065, 0.12), "led", parent=wb)
    cylinder("Wallbox_Plug", 0.05, 0.06, (0, -0.07, -0.08), "pv_frame", rot=(math.pi / 2, 0, 0), segs=12, parent=wb)


def car():
    c = bevel(box("Car", (1.82, 4.3, 0.62), (-8.4, -2.6, 0.62), "car"), 0.12, 3)
    prof = [(-1.05, 0), (1.35, 0), (1.05, 0.55), (-0.3, 0.55)]  # raked windscreen at the front (-y)
    v = [(-0.78, a, b) for a, b in prof] + [(0.78, a, b) for a, b in prof]
    f = [(3, 2, 1, 0), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    bevel(obj("Car_Cabin", mesh("Car_Cabin", v, f, ["glass"]), (0, 0, 0.3), parent=c), 0.06, 2)
    for i, (x, y) in enumerate(((-0.86, -1.35), (0.86, -1.35), (-0.86, 1.35), (0.86, 1.35))):
        cylinder(f"Car_Wheel{i}", 0.33, 0.24, (x, y, -0.29), "tyre", rot=(0, math.pi / 2, 0), parent=c)
    box("Car_Lights", (1.4, 0.02, 0.08), (0, -2.16, 0.12), "frame", parent=c)


def trees():
    for i, (x, y, s) in enumerate(((8.6, 5.2, 1.0), (-11.0, 5.6, 1.2), (8.9, -6.6, 0.75))):
        cylinder(f"Tree{i}_Trunk", 0.14 * s, 1.6 * s, (x, y, 0.8 * s), "trunk", segs=8)
        me = bm_mesh(f"Tree{i}_Crown", lambda bm: bmesh.ops.create_icosphere(bm, subdivisions=1, radius=1.3 * s),
                     "leaf")
        obj(f"Tree{i}_Crown", me, (x, y, 2.2 * s))


def build():
    clear()
    ground()
    house()
    pv_panels()
    heat_pump()
    batteries_and_wallbox()
    car()
    trees()


# -- preview render and export -----------------------------------------------------------------
def preview(path: str, res=(1400, 900)):
    """Render a quick look from the default web camera angle (not exported)."""
    sc = bpy.context.scene
    cam = bpy.data.objects.new("PreviewCam", bpy.data.cameras.new("PreviewCam"))
    sc.collection.objects.link(cam)
    cam.data.lens = 40
    cam.location = (-12.0, -27.0, 14.0)
    target = mathutils.Vector((-1.2, 0.0, 2.6))
    cam.rotation_euler = (target - cam.location).to_track_quat("-Z", "Y").to_euler()
    sun = bpy.data.objects.new("PreviewSun", bpy.data.lights.new("PreviewSun", "SUN"))
    sc.collection.objects.link(sun)
    sun.data.energy, sun.data.angle = 3.5, math.radians(8)
    sun.rotation_euler = (math.radians(50), math.radians(-20), math.radians(-35))
    world = sc.world or bpy.data.worlds.new("World")
    sc.world = world
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
                              export_yup=True, export_cameras=False, export_lights=False)
    return {"exported": str(path), "bytes": path.stat().st_size}


if __name__ == "__main__":
    build()
    print(export())
