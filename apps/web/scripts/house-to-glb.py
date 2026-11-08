"""Blender's only role is importing local OBJ materials and packaging a Y-up, metre-scale GLB."""
import bpy, json, pathlib, sys
from mathutils import Vector
source, target = map(pathlib.Path, sys.argv[sys.argv.index('--')+1:])
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
bpy.ops.wm.obj_import(filepath=str(source), forward_axis='Y', up_axis='Z')
meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
if not meshes: raise RuntimeError('The exported area has no mesh.')
triangles = sum(sum(max(0, len(p.vertices)-2) for p in o.data.polygons) for o in meshes)
if not triangles: raise RuntimeError('The exported mesh has no faces.')
for obj in meshes:
    for slot in obj.material_slots:
        if slot.material and slot.material.use_nodes:
            for tex in slot.material.node_tree.nodes:
                if tex.type == 'TEX_IMAGE': tex.extension = 'EXTEND'
bpy.ops.export_scene.gltf(filepath=str(target), export_format='GLB', export_yup=True, export_cameras=False, export_lights=False)
target.with_name('geometry.json').write_text(json.dumps({'triangles':triangles}))
