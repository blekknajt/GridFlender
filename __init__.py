bl_info = {
    "name": "GridFlender",
    "author": "blekknajt + Antigravity",
    "version": (4, 1, 0),
    "blender": (4, 0, 0),
    "location": "View3D > Sidebar > GridFlender, View3D > Add > Mesh > Gridfinity Base",
    "description": "Adds a Gridfinity base mesh with optional magnet holes and stacking socket",
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
