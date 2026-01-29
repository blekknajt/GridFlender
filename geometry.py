"""
Gridfinity base geometry - Version 3.1
Units: MILLIMETERS
Features: Magnet holes, Stackable socket
Fix: Separate Boolean operations for stability
"""

import bpy
import bmesh
import math
from mathutils import Matrix


GRID_SIZE = 42.0  # mm

# Bottom profile (inset, height)
BOTTOM_PROFILE = [
    (2.55, 0.0),
    (0.8, 1.8),
    (0.8, 2.15),
    (0.0, 4.75),
    (0.0, 5.0),
]

# Socket profile (inset, depth_from_top)
SOCKET_PROFILE = [
    (0.0, 0.0),       # Top outer edge
    (0.0, 0.25),      # Rim
    (0.8, 2.35),      # Wall
    (0.8, 3.2),       # Wall
    (2.55, 4.15),     # Chamfer
    (2.55, 5.0),      # Bottom of socket
]

MAGNET_OFFSET_FROM_EDGE = 7.75


def create_gridfinity_base_mesh(
    columns: int = 1,
    rows: int = 1,
    use_magnets: bool = False,
    magnet_diameter: float = 6.0,
    magnet_depth: float = 2.0,
    tile_height: float = 28.0,
    stackable: bool = False,
) -> bpy.types.Mesh:
    """Create Gridfinity base using sequential boolean operations."""
    
    # 1. Create solid base body
    base_mesh = _create_base_body(columns, rows, tile_height)
    
    # 2. Apply Magnet Holes (if enabled)
    if use_magnets:
        cutter_mesh = _create_magnet_cutter(columns, rows, magnet_diameter, magnet_depth)
        base_mesh = _apply_boolean(base_mesh, cutter_mesh)
        
    # 3. Apply Stackable Socket (if enabled)
    if stackable:
        cutter_mesh = _create_socket_cutter(columns, rows, tile_height)
        base_mesh = _apply_boolean(base_mesh, cutter_mesh)
    
    return base_mesh


def _create_base_body(columns, rows, tile_height):
    """Create solid base body."""
    bm = bmesh.new()
    
    width = columns * GRID_SIZE
    depth = rows * GRID_SIZE
    segments = 32
    
    layers = []
    
    for inset, z in BOTTOM_PROFILE:
        verts = _create_rect_layer(bm, width, depth, z, inset, segments)
        layers.append(verts)
    
    if tile_height > 5.0:
        verts = _create_rect_layer(bm, width, depth, tile_height, 0.0, segments)
        layers.append(verts)
        
    for i in range(len(layers) - 1):
        _connect_layers(bm, layers[i], layers[i + 1])
        
    if layers:
        _fill_face(bm, layers[0], flip=False)
        _fill_face(bm, layers[-1], flip=True)
        
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    mesh = bpy.data.meshes.new("GridfinityBase_Temp")
    bm.to_mesh(mesh)
    bm.free()
    return mesh


def _create_magnet_cutter(columns, rows, diameter, depth):
    """Create cutter for magnet holes."""
    bm = bmesh.new()
    width = columns * GRID_SIZE
    depth_y = rows * GRID_SIZE
    radius = diameter / 2
    offset = MAGNET_OFFSET_FROM_EDGE
    
    corners = [
        (-width/2 + offset, -depth_y/2 + offset),
        (width/2 - offset, -depth_y/2 + offset),
        (-width/2 + offset, depth_y/2 - offset),
        (width/2 - offset, depth_y/2 - offset),
    ]
    
    for cx, cy in corners:
        # Cut from slightly below 0 up to depth
        bmesh.ops.create_cone(
            bm,
            cap_ends=True,
            cap_tris=False,
            segments=24,
            radius1=radius,
            radius2=radius,
            depth=depth + 0.5,
            matrix=Matrix.Translation((cx, cy, (depth + 0.5)/2 - 0.25))
        )
        
    mesh = bpy.data.meshes.new("MagnetCutter")
    bm.to_mesh(mesh)
    bm.free()
    return mesh


def _create_socket_cutter(columns, rows, tile_height):
    """Create cutter for stackable socket."""
    bm = bmesh.new()
    width = columns * GRID_SIZE
    depth = rows * GRID_SIZE
    segments = 32
    
    # Start slightly above top surface
    top_z_start = tile_height + 0.1
    
    layers = []
    # Start high
    layers.append(_create_rect_layer(bm, width, depth, top_z_start, 0.0, segments))
    
    # Follow profile downwards
    for inset, depth_from_top in SOCKET_PROFILE:
        z = tile_height - depth_from_top
        layers.append(_create_rect_layer(bm, width, depth, z, inset, segments))
        
    for i in range(len(layers) - 1):
        _connect_layers(bm, layers[i], layers[i + 1])
        
    # Close top and bottom (solid cutter)
    _fill_face(bm, layers[0], flip=False)
    _fill_face(bm, layers[-1], flip=True)
    
    mesh = bpy.data.meshes.new("SocketCutter")
    bm.to_mesh(mesh)
    bm.free()
    return mesh


def _apply_boolean(base_mesh, cutter_mesh):
    """Apply boolean difference."""
    base_obj = bpy.data.objects.new("Base_Temp", base_mesh)
    cutter_obj = bpy.data.objects.new("Cutter_Temp", cutter_mesh)
    
    col = bpy.context.collection
    col.objects.link(base_obj)
    col.objects.link(cutter_obj)
    cutter_obj.hide_set(True)
    
    mod = base_obj.modifiers.new("Boolean", 'BOOLEAN')
    mod.operation = 'DIFFERENCE'
    mod.object = cutter_obj
    mod.solver = 'EXACT'
    
    bpy.context.view_layer.objects.active = base_obj
    base_obj.select_set(True)
    
    try:
        bpy.ops.object.modifier_apply(modifier="Boolean")
    except Exception as e:
        print(f"Boolean failed: {e}")
        
    result = base_obj.data.copy()
    result.name = "GridfinityBase"
    
    # Cleanup
    bpy.data.objects.remove(base_obj, do_unlink=True)
    bpy.data.objects.remove(cutter_obj, do_unlink=True)
    # Note: base_mesh input is cleared because base_obj used it
    # cutter_mesh input is explicitly removed
    bpy.data.meshes.remove(cutter_mesh, do_unlink=True)
    # base_obj.data (which is modified base_mesh) is NOT removed, but result is a copy?
    # Actually modifier_apply modifies the mesh in-place on the object.
    # So base_obj.data IS the result.
    # The original passed 'base_mesh' is what base_obj uses.
    # So we don't need to return a copy if we just return base_obj.data
    # BUT we are removing base_obj. If we remove object, data remains if it has users?
    # Let's ensure we return a safe mesh.
    
    return result


def _create_rect_layer(bm, width, depth, z, inset, segments):
    w = max(width - 2 * inset, 1.0)
    d = max(depth - 2 * inset, 1.0)
    r = max(4.0 - inset, 0.5)
    r = min(r, w/2, d/2)
    
    verts = []
    corners = [
        (w/2 - r, d/2 - r), (-w/2 + r, d/2 - r),
        (-w/2 + r, -d/2 + r), (w/2 - r, -d/2 + r)
    ]
    angles = [0, math.pi/2, math.pi, 3*math.pi/2]
    
    for idx, (cx, cy) in enumerate(corners):
        for s in range(segments):
            angle = angles[idx] + (math.pi/2) * s / segments
            x = cx + r * math.cos(angle)
            y = cy + r * math.sin(angle)
            verts.append(bm.verts.new((x, y, z)))
    return verts


def _connect_layers(bm, lower, upper):
    n = len(lower)
    if len(upper) != n: return
    for i in range(n):
        i_next = (i+1)%n
        try:
            bm.faces.new([lower[i], lower[i_next], upper[i_next], upper[i]])
        except ValueError: pass


def _fill_face(bm, verts, flip=False):
    try:
        if flip: bm.faces.new(list(reversed(verts)))
        else: bm.faces.new(verts)
    except ValueError: pass
