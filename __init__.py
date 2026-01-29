bl_info = {
    "name": "GridfLender",
    "author": "blekknajt + Antigravity",
    "version": (3, 4),
    "blender": (4, 0, 0),
    "location": "View3D > Sidebar > Gridfinity",
    "description": "Adds a Gridfinity base mesh with optional magnet holes",
    "category": "Add Mesh",
}

import bpy

from . import properties
from . import operators
from . import ui_panels

modules = [properties, operators, ui_panels]


def register():
    for module in modules:
        module.register()


def unregister():
    for module in reversed(modules):
        module.unregister()


if __name__ == "__main__":
    register()