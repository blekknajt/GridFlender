"""
Operators for the Gridfinity Tile Generator addon.
"""

import bpy
from bpy.types import Operator

from .geometry import create_gridfinity_base_mesh


class MESH_OT_add_gridfinity_base(Operator):
    """Add a Gridfinity base tile mesh"""
    bl_idname = "mesh.add_gridfinity_base"
    bl_label = "Add Gridfinity Base"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene
        
        # Get height from preset (string -> float)
        height = float(scene.gridfinity_height_preset)

        mesh = create_gridfinity_base_mesh(
            columns=scene.gridfinity_columns,
            rows=scene.gridfinity_rows,
            use_magnets=scene.gridfinity_use_magnets,
            magnet_diameter=scene.gridfinity_magnet_diameter,
            magnet_depth=scene.gridfinity_magnet_depth,
            tile_height=height,
            stackable=scene.gridfinity_stackable,
        )

        obj = bpy.data.objects.new("GridfinityBase", mesh)
        context.collection.objects.link(obj)
        context.view_layer.objects.active = obj
        obj.select_set(True)

        cols = scene.gridfinity_columns
        rows = scene.gridfinity_rows
        units = int(height / 7)
        self.report({'INFO'}, f"Created {cols}x{rows}x{units}U base")
        return {'FINISHED'}


def register():
    bpy.utils.register_class(MESH_OT_add_gridfinity_base)


def unregister():
    bpy.utils.unregister_class(MESH_OT_add_gridfinity_base)
