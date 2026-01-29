"""
Properties for the Gridfinity Tile Generator addon.
"""

import bpy
from bpy.props import BoolProperty, IntProperty, FloatProperty, EnumProperty


# Gridfinity height unit = 7mm
# Common heights: 1U, 2U, 3U, 4U, 5U, 6U
HEIGHT_OPTIONS = [
    ('7', '1U (7mm)', 'Quarter height'),
    ('14', '2U (14mm)', 'Half height'),
    ('21', '3U (21mm)', 'Three-quarter height'),
    ('28', '4U (28mm)', 'Standard full height'),
    ('35', '5U (35mm)', 'Tall'),
    ('42', '6U (42mm)', 'Extra tall'),
    ('49', '7U (49mm)', 'Very tall'),
    ('56', '8U (56mm)', 'Maximum'),
]


def register():
    bpy.types.Scene.gridfinity_columns = IntProperty(
        name="Columns",
        description="Number of columns (X)",
        default=1,
        min=1,
        max=50,
    )

    bpy.types.Scene.gridfinity_rows = IntProperty(
        name="Rows",
        description="Number of rows (Y)",
        default=1,
        min=1,
        max=50,
    )

    bpy.types.Scene.gridfinity_use_magnets = BoolProperty(
        name="Include Magnet Holes",
        description="Add magnet holes at base corners",
        default=False,
    )

    bpy.types.Scene.gridfinity_magnet_diameter = FloatProperty(
        name="Magnet Diameter",
        description="Diameter of magnet holes (mm)",
        default=6.0,
        min=1.0,
        max=20.0,
        precision=1,
    )

    bpy.types.Scene.gridfinity_magnet_depth = FloatProperty(
        name="Magnet Depth",
        description="Depth of magnet holes (mm)",
        default=2.0,
        min=0.5,
        max=10.0,
        precision=1,
    )

    bpy.types.Scene.gridfinity_height_preset = EnumProperty(
        name="Height",
        description="Bin height in Gridfinity units (1U = 7mm)",
        items=HEIGHT_OPTIONS,
        default='28',  # 4U = standard
    )
    
    bpy.types.Scene.gridfinity_stackable = BoolProperty(
        name="Stackable (Top Lip)",
        description="Add stacking lip on top for bin-on-bin stacking",
        default=False,
    )


def unregister():
    del bpy.types.Scene.gridfinity_columns
    del bpy.types.Scene.gridfinity_rows
    del bpy.types.Scene.gridfinity_use_magnets
    del bpy.types.Scene.gridfinity_magnet_diameter
    del bpy.types.Scene.gridfinity_magnet_depth
    del bpy.types.Scene.gridfinity_height_preset
    del bpy.types.Scene.gridfinity_stackable
