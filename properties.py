"""
Properties for the GridFlender addon.
"""

import bpy
from bpy.props import BoolProperty, IntProperty, FloatProperty, PointerProperty
from bpy.types import PropertyGroup

from .geometry import HEIGHT_UNIT


class GridfinityBaseParams:
    """Shared parameter definitions for the scene settings and the operator."""

    columns: IntProperty(
        name="Columns",
        description="Number of grid cells along X",
        default=1,
        min=1,
        max=50,
        soft_max=10,
    )

    rows: IntProperty(
        name="Rows",
        description="Number of grid cells along Y",
        default=1,
        min=1,
        max=50,
        soft_max=10,
    )

    height_units: IntProperty(
        name="Height (U)",
        description=f"Total bin height in Gridfinity units (1U = {HEIGHT_UNIT:g} mm)",
        default=4,
        min=1,
        max=30,
        soft_max=12,
    )

    stackable: BoolProperty(
        name="Stackable (Socket)",
        description="Cut a stacking socket into the top so another bin can sit on this one (needs 2U or more)",
        default=False,
    )

    use_magnets: BoolProperty(
        name="Magnet Holes",
        description="Add 4 magnet holes in the bottom of each cell",
        default=False,
    )

    magnet_diameter: FloatProperty(
        name="Diameter",
        description="Diameter of magnet holes in mm (spec: 6.5 mm for 6 mm magnets)",
        default=6.5,
        min=1.0,
        max=12.0,
        precision=2,
        step=10,
    )

    magnet_depth: FloatProperty(
        name="Depth",
        description="Depth of magnet holes in mm (spec: 2.4 mm for 2 mm magnets)",
        default=2.4,
        min=0.5,
        max=10.0,
        precision=2,
        step=10,
    )

    def param_dict(self):
        return {name: getattr(self, name) for name in GridfinityBaseParams.__annotations__}


class GridFlenderSettings(GridfinityBaseParams, PropertyGroup):
    pass


classes = (GridFlenderSettings,)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.gridflender = PointerProperty(type=GridFlenderSettings)


def unregister():
    del bpy.types.Scene.gridflender
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
