"""
UI Panels for the Gridfinity Tile Generator addon.
"""

import bpy
from bpy.types import Panel


class VIEW3D_PT_gridfinity_panel(Panel):
    """Main panel for GridfLender"""
    bl_label = "GridfLender"
    bl_idname = "VIEW3D_PT_gridfinity_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Gridfinity'

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        # Grid dimensions
        box = layout.box()
        box.label(text="Grid Size")
        row = box.row(align=True)
        row.prop(scene, "gridfinity_columns")
        row.prop(scene, "gridfinity_rows")

        # Height settings
        box = layout.box()
        box.label(text="Dimensions")
        box.prop(scene, "gridfinity_height_preset")
        box.prop(scene, "gridfinity_stackable")

        # Magnet settings
        box = layout.box()
        box.label(text="Magnets")
        box.prop(scene, "gridfinity_use_magnets")
        
        if hasattr(scene, "gridfinity_magnet_diameter"):
            col = box.column()
            col.enabled = scene.gridfinity_use_magnets
            col.prop(scene, "gridfinity_magnet_diameter")
            col.prop(scene, "gridfinity_magnet_depth")

        # Generate button
        layout.separator()
        layout.operator("mesh.add_gridfinity_base", text="Generate Base")


def register():
    bpy.utils.register_class(VIEW3D_PT_gridfinity_panel)


def unregister():
    bpy.utils.unregister_class(VIEW3D_PT_gridfinity_panel)