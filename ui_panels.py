"""
UI Panels for the GridFlender addon.
"""

import bpy
from bpy.types import Panel

from .geometry import GRID_SIZE, BIN_CLEARANCE, HEIGHT_UNIT, MIN_STACKABLE_HEIGHT


class VIEW3D_PT_gridfinity_panel(Panel):
    """Main panel for GridFlender"""
    bl_label = "GridFlender"
    bl_idname = "VIEW3D_PT_gridfinity_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'GridFlender'

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        settings = context.scene.gridflender

        # Grid dimensions
        box = layout.box()
        box.label(text="Grid Size", icon='MESH_GRID')
        col = box.column(align=True)
        col.prop(settings, "columns")
        col.prop(settings, "rows")

        # Height settings
        height = settings.height_units * HEIGHT_UNIT
        box = layout.box()
        box.label(text="Height", icon='EMPTY_SINGLE_ARROW')
        box.prop(settings, "height_units")
        box.prop(settings, "stackable")
        if settings.stackable and height < MIN_STACKABLE_HEIGHT:
            box.label(text="Stacking socket needs 2U or more", icon='ERROR')

        # Magnet settings
        box = layout.box()
        box.label(text="Magnets", icon='SNAP_ON')
        box.prop(settings, "use_magnets")
        col = box.column(align=True)
        col.active = settings.use_magnets
        col.prop(settings, "magnet_diameter")
        col.prop(settings, "magnet_depth")

        # Resulting size
        w = settings.columns * GRID_SIZE - 2 * BIN_CLEARANCE
        d = settings.rows * GRID_SIZE - 2 * BIN_CLEARANCE
        layout.label(text=f"Size: {w:g} x {d:g} x {height:g} mm")

        # Generate button
        op = layout.operator("mesh.add_gridfinity_base", text="Generate Base", icon='ADD')
        for name, value in settings.param_dict().items():
            setattr(op, name, value)


def register():
    bpy.utils.register_class(VIEW3D_PT_gridfinity_panel)


def unregister():
    bpy.utils.unregister_class(VIEW3D_PT_gridfinity_panel)
