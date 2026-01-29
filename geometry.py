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
    """Create solid base body with individual 1x1 feet.
    
    Strategy: Build everything in one bmesh to preserve individual foot geometry.
    - Each foot goes from Z=0 to Z=5 with the Gridfinity profile
    - A shared slab covers the top from Z=5 to tile_height
    - Feet share edges at their boundaries but maintain separate bottom profiles
    """
    bm = bmesh.new()
    
    width = columns * GRID_SIZE
    depth = rows * GRID_SIZE
    segments = 32
    
    # Calculate cell center offsets
    start_x = -(width / 2) + (GRID_SIZE / 2)
    start_y = -(depth / 2) + (GRID_SIZE / 2)
    
    # 1. Create individual feet for each cell
    for c in range(columns):
        for r in range(rows):
            cx = start_x + (c * GRID_SIZE)
            cy = start_y + (r * GRID_SIZE)
            
            foot_layers = []
            
            # Create foot profile layers
            for inset, z in BOTTOM_PROFILE:
                layer_verts = _create_rect_layer(bm, GRID_SIZE, GRID_SIZE, z, inset, segments)
                
                # Translate to cell position
                matrix = Matrix.Translation((cx, cy, 0))
                bmesh.ops.transform(bm, matrix=matrix, verts=layer_verts)
                
                foot_layers.append(layer_verts)
            
            # Connect layers
            for i in range(len(foot_layers) - 1):
                _connect_layers(bm, foot_layers[i], foot_layers[i + 1])
            
            # Close only the bottom (top stays open to merge with slab)
            if foot_layers:
                _fill_face(bm, foot_layers[0], flip=False)
                # Top face of foot will be created by the slab
    
    # 2. Create top slab from Z=5 to tile_height
    slab_z_bottom = 5.0
    if tile_height > slab_z_bottom:
        # Create slab layers
        slab_bottom = _create_rect_layer(bm, width, depth, slab_z_bottom, 0.0, segments)
        slab_top = _create_rect_layer(bm, width, depth, tile_height, 0.0, segments)
        
        # Connect slab walls
        _connect_layers(bm, slab_bottom, slab_top)
        
        # Close top (bottom of slab is open - feet tops are open too, they share Z=5)
        _fill_face(bm, slab_top, flip=True)
    
    # Recalculate normals
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
    
    # Per-cell calculation
    start_x = -(width / 2) + (GRID_SIZE / 2)
    start_y = -(depth_y / 2) + (GRID_SIZE / 2)
    offset = MAGNET_OFFSET_FROM_EDGE
    
    # Ideally magnets are per-cell corners. 
    # Standard spec: 4 magnets per unit.
    # We should iterate cells and place 4 magnets relative to cell center.
    # Center of unit is (0,0). Corners are +/- 21.
    # Magnet centers are at specific distance from outside?
    # Spec: "Holes are 26mm apart" (centered). 42-26 = 16. 16/2 = 8mm from edge?
    # Code had 7.75mm. 
    # Let's stick to the previous iterative approach but PER CELL if we want true multi-cell support.
    # Previous code: calculated 4 corners for the WHOLE shape. 
    # WAIT. Gridfinity spec implies magnets on every unit?
    # "Gridfinity base... magnets at corners of each 42mm squares".
    # Yes, we need magnets for EACH cell.
    
    magnet_positions = []
    
    # Relative positions in a 42x42 cell
    # 26mm spacing means +/- 13mm from center
    cell_offsets = [
        (-13, -13), (13, -13), 
        (-13, 13), (13, 13)
    ]
    
    for c in range(columns):
        for r in range(rows):
            cx = start_x + (c * GRID_SIZE)
            cy = start_y + (r * GRID_SIZE)
            
            for ox, oy in cell_offsets:
                magnet_positions.append((cx + ox, cy + oy))
    
    for mx, my in magnet_positions:
        # Cut from slightly below 0 up to depth
        bmesh.ops.create_cone(
            bm,
            cap_ends=True,
            cap_tris=False,
            segments=24,
            radius1=radius,
            radius2=radius,
            depth=depth + 0.5,
            matrix=Matrix.Translation((mx, my, (depth + 0.5)/2 - 0.25))
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


def _apply_boolean(base_mesh, cutter_mesh, operation='DIFFERENCE'):
    """Apply boolean operation."""
    base_obj = bpy.data.objects.new("Base_Temp", base_mesh)
    cutter_obj = bpy.data.objects.new("Cutter_Temp", cutter_mesh)
    
    col = bpy.context.collection
    col.objects.link(base_obj)
    col.objects.link(cutter_obj)
    cutter_obj.hide_set(True)
    
    mod = base_obj.modifiers.new("Boolean", 'BOOLEAN')
    mod.operation = operation
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
    # The cutter mesh input is explicitly removed
    bpy.data.meshes.remove(cutter_mesh, do_unlink=True)
    # If operation was Union, base_mesh is now "old", result is new.
    # If logic assumes base_mesh is consumed, we might want to remove it if it's not the result
    # In _create_base_body we pass slab_mesh as base_mesh.
    # bpy.data.meshes.remove(base_mesh, do_unlink=True) # Let caller handle or Python GC?
    # Better to be explicit if we created temp meshes.
    
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
