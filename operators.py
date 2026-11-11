"""
Operators for the GridFlender addon.
"""

import bpy
from bpy.types import Operator
from bpy_extras.object_utils import AddObjectHelper, object_data_add

from .geometry import (
    HEIGHT_UNIT,
    MIN_STACKABLE_HEIGHT,
    GeometryError,
    create_gridfinity_base_mesh,
)
from .properties import GridfinityBaseParams


class MESH_OT_add_gridfinity_base(GridfinityBaseParams, AddObjectHelper, Operator):
    """Add a Gridfinity base mesh"""
    bl_idname = "mesh.add_gridfinity_base"
    bl_label = "Gridfinity Base"
    bl_options = {'REGISTER', 'UNDO'}

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        col = layout.column(align=True)
        col.prop(self, "columns")
        col.prop(self, "rows")
        layout.prop(self, "height_units")
        layout.prop(self, "stackable")
        layout.prop(self, "use_magnets")
        col = layout.column(align=True)
        col.active = self.use_magnets
        col.prop(self, "magnet_diameter")
        col.prop(self, "magnet_depth")

        layout.separator()
        layout.prop(self, "align")
        layout.prop(self, "location")
        layout.prop(self, "rotation")

    def execute(self, context):
        height = self.height_units * HEIGHT_UNIT

        if self.stackable and height < MIN_STACKABLE_HEIGHT:
            self.report({'ERROR'}, f"Stackable socket needs at least {MIN_STACKABLE_HEIGHT:.1f} mm (2U)")
            return {'CANCELLED'}

        try:
            mesh = create_gridfinity_base_mesh(
                columns=self.columns,
                rows=self.rows,
                use_magnets=self.use_magnets,
                magnet_diameter=self.magnet_diameter,
                magnet_depth=self.magnet_depth,
                tile_height=height,
                stackable=self.stackable,
            )
        except GeometryError as e:
            self.report({'ERROR'}, str(e))
            return {'CANCELLED'}

        object_data_add(context, mesh, operator=self, name="GridfinityBase")

        self.report({'INFO'}, f"Created {self.columns}x{self.rows}x{self.height_units}U base")
        return {'FINISHED'}


def menu_func(self, context):
    self.layout.operator(MESH_OT_add_gridfinity_base.bl_idname, icon='MESH_GRID')


def register():
    bpy.utils.register_class(MESH_OT_add_gridfinity_base)
    bpy.types.VIEW3D_MT_mesh_add.append(menu_func)


def unregister():
    bpy.types.VIEW3D_MT_mesh_add.remove(menu_func)
    bpy.utils.unregister_class(MESH_OT_add_gridfinity_base)
