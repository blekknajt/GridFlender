"""
Gridfinity base geometry - Version 4.0
Units: MILLIMETERS
Features: Magnet holes, Stackable socket
Fixes:
  - Manifold geometry: each foot is a closed solid, unioned with slab
  - N-gon caps replaced with triangle fan fill
  - Magnet hole defaults match spec (6.5mm dia x 2.4mm depth)
  - Socket cutter no longer creates degenerate thin layer
  - Robust boolean pipeline with full cleanup
"""

import bpy
import bmesh
import math
from mathutils import Matrix


GRID_SIZE = 42.0  # mm

# Bottom profile (inset_from_cell_edge, z_height)
# Defines the stepped/chamfered base of each 42x42 cell
BOTTOM_PROFILE = [
    (2.55, 0.0),   # Bottom outer lip
    (0.8,  1.8),   # First chamfer
    (0.8,  2.15),  # Vertical wall
    (0.0,  4.75),  # Second chamfer to full width
    (0.0,  5.0),   # Top of foot = base of slab
]

# Socket profile (inset_from_outer_edge, depth_from_top)
# Cut from the top of the bin to create a stacking socket
SOCKET_PROFILE = [
    (0.0,  0.0),   # Top outer edge
    (0.0,  0.25),  # Rim
    (0.8,  2.35),  # Angled wall
    (0.8,  3.2),   # Vertical wall
    (2.55, 4.15),  # Chamfer
    (2.55, 5.0),   # Bottom of socket
]

# Magnet placement: 26mm apart center-to-center within each cell
# => +/- 13mm from cell center
MAGNET_CELL_OFFSETS = [
    (-13.0, -13.0),
    ( 13.0, -13.0),
    (-13.0,  13.0),
    ( 13.0,  13.0),
]

# Corner rounding on the outer edge of a full-size cell
BASE_CORNER_RADIUS = 4.0

# Segments per 90-degree arc (4 corners = 4x this many verts per layer)
ARC_SEGMENTS = 16


def create_gridfinity_base_mesh(
    columns: int = 1,
    rows: int = 1,
    use_magnets: bool = False,
    magnet_diameter: float = 6.5,
    magnet_depth: float = 2.4,
    tile_height: float = 28.0,
    stackable: bool = False,
) -> bpy.types.Mesh:
    """Create Gridfinity base mesh using sequential boolean operations.

    The base is built as a single manifold solid, then magnet holes
    and stacking socket are subtracted via boolean difference.
    """

    # 1. Create solid base body (manifold, closed mesh)
    base_mesh = _create_base_body(columns, rows, tile_height)

    # 2. Subtract magnet holes
    if use_magnets:
        cutter_mesh = _create_magnet_cutter(columns, rows, magnet_diameter, magnet_depth)
        base_mesh = _apply_boolean(base_mesh, cutter_mesh, 'DIFFERENCE')

    # 3. Subtract stackable socket
    if stackable:
        cutter_mesh = _create_socket_cutter(columns, rows, tile_height)
        base_mesh = _apply_boolean(base_mesh, cutter_mesh, 'DIFFERENCE')

    return base_mesh


# ---------------------------------------------------------------------------
#  Base body
# ---------------------------------------------------------------------------

def _create_base_body(columns, rows, tile_height):
    """Create a manifold solid base.

    Strategy:
      - For each cell, create a closed profiled foot from Z=0 to Z=5.
      - Create one outer slab (closed rounded-rect box) from Z=5 to tile_height.
      - Union all feet with the slab so shared faces merge cleanly.

    This guarantees a manifold result even for multi-cell grids.
    """
    width = columns * GRID_SIZE
    depth = rows * GRID_SIZE

    start_x = -(width / 2) + (GRID_SIZE / 2)
    start_y = -(depth / 2) + (GRID_SIZE / 2)

    foot_top_z = BOTTOM_PROFILE[-1][1]  # 5.0

    # Build each foot as a separate closed solid
    foot_meshes = []
    for c in range(columns):
        for r in range(rows):
            cx = start_x + c * GRID_SIZE
            cy = start_y + r * GRID_SIZE
            foot_meshes.append(_create_single_foot(cx, cy, foot_top_z))

    # Build the top slab as a closed box
    slab_mesh = _create_box_mesh(width, depth, z_bottom=foot_top_z, z_top=tile_height)

    # Combine: start with slab, union each foot
    result = slab_mesh
    for fm in foot_meshes:
        result = _apply_boolean(result, fm, 'UNION')

    return result


def _create_single_foot(cx, cy, top_z):
    """Create one closed 42x42 foot centered at (cx, cy), from Z=0 to top_z."""
    bm = bmesh.new()

    layers = []
    for inset, z in BOTTOM_PROFILE:
        layer_verts = _create_rounded_rect(bm, GRID_SIZE, GRID_SIZE, z, inset)
        # Translate to cell position
        mat = Matrix.Translation((cx, cy, 0))
        bmesh.ops.transform(bm, matrix=mat, verts=layer_verts)
        layers.append(layer_verts)

    # Connect profile layers with quad strips
    for i in range(len(layers) - 1):
        _bridge_loops(bm, layers[i], layers[i + 1])

    # Close bottom (Z=0) and top (Z=top_z) with triangle fans
    _fill_cap(bm, layers[0], flip=True)
    _fill_cap(bm, layers[-1], flip=False)

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])

    mesh = bpy.data.meshes.new("Foot_Temp")
    bm.to_mesh(mesh)
    bm.free()
    return mesh


def _create_box_mesh(width, depth, z_bottom, z_top):
    """Create a closed rounded-rect box from z_bottom to z_top."""
    bm = bmesh.new()

    bottom = _create_rounded_rect(bm, width, depth, z_bottom, inset=0.0)
    top = _create_rounded_rect(bm, width, depth, z_top, inset=0.0)

    _bridge_loops(bm, bottom, top)
    _fill_cap(bm, bottom, flip=True)
    _fill_cap(bm, top, flip=False)

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])

    mesh = bpy.data.meshes.new("Slab_Temp")
    bm.to_mesh(mesh)
    bm.free()
    return mesh


# ---------------------------------------------------------------------------
#  Magnet cutter
# ---------------------------------------------------------------------------

def _create_magnet_cutter(columns, rows, diameter, hole_depth):
    """Create a combined cutter mesh for all magnet holes.

    Each cell gets 4 magnet holes at +/-13mm from cell center.
    Holes extend from Z = -0.1 to Z = hole_depth (cutting through the bottom).
    """
    bm = bmesh.new()

    width = columns * GRID_SIZE
    depth_y = rows * GRID_SIZE
    radius = diameter / 2.0

    start_x = -(width / 2) + (GRID_SIZE / 2)
    start_y = -(depth_y / 2) + (GRID_SIZE / 2)

    # Total cylinder height with margin for clean boolean cut
    cyl_height = hole_depth + 0.2
    # Position so bottom of cylinder is at Z = -0.1
    cyl_center_z = -0.1 + cyl_height / 2.0

    for c in range(columns):
        for r in range(rows):
            cx = start_x + c * GRID_SIZE
            cy = start_y + r * GRID_SIZE

            for ox, oy in MAGNET_CELL_OFFSETS:
                mx = cx + ox
                my = cy + oy

                bmesh.ops.create_cone(
                    bm,
                    cap_ends=True,
                    cap_tris=True,
                    segments=24,
                    radius1=radius,
                    radius2=radius,
                    depth=cyl_height,
                    matrix=Matrix.Translation((mx, my, cyl_center_z)),
                )

    mesh = bpy.data.meshes.new("MagnetCutter_Temp")
    bm.to_mesh(mesh)
    bm.free()
    return mesh


# ---------------------------------------------------------------------------
#  Socket cutter
# ---------------------------------------------------------------------------

def _create_socket_cutter(columns, rows, tile_height):
    """Create cutter for the stackable socket at the top of the bin.

    The cutter follows the socket profile and extends above the top face
    to guarantee a clean boolean subtraction.
    """
    bm = bmesh.new()

    width = columns * GRID_SIZE
    depth = rows * GRID_SIZE

    layers = []

    # Build profile layers from top down
    for inset, depth_from_top in SOCKET_PROFILE:
        z = tile_height - depth_from_top
        layer = _create_rounded_rect(bm, width, depth, z, inset)
        layers.append(layer)

    # Extension above the top for clean boolean cut (1mm above top surface)
    top_extension = _create_rounded_rect(bm, width, depth, tile_height + 1.0, inset=0.0)

    # Full layer list: extension on top, then profile layers (top-to-bottom)
    all_layers = [top_extension] + layers

    # Bridge consecutive layers
    for i in range(len(all_layers) - 1):
        _bridge_loops(bm, all_layers[i], all_layers[i + 1])

    # Close top and bottom caps
    _fill_cap(bm, all_layers[0], flip=False)
    _fill_cap(bm, all_layers[-1], flip=True)

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])

    mesh = bpy.data.meshes.new("SocketCutter_Temp")
    bm.to_mesh(mesh)
    bm.free()
    return mesh


# ---------------------------------------------------------------------------
#  Boolean helper
# ---------------------------------------------------------------------------

def _apply_boolean(base_mesh, cutter_mesh, operation='DIFFERENCE'):
    """Apply a boolean modifier and return the resulting mesh.

    Both input meshes are consumed (removed from bpy.data after operation).
    """
    base_obj = bpy.data.objects.new("Bool_Base", base_mesh)
    cutter_obj = bpy.data.objects.new("Bool_Cutter", cutter_mesh)

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
        print(f"[GridFlender] Boolean ({operation}) failed: {e}")

    # Copy result mesh before cleanup
    result = base_obj.data.copy()
    result.name = "GridfinityBase"

    # Cleanup temporary objects and consumed meshes
    bpy.data.objects.remove(base_obj, do_unlink=True)
    bpy.data.objects.remove(cutter_obj, do_unlink=True)
    bpy.data.meshes.remove(cutter_mesh, do_unlink=True)
    bpy.data.meshes.remove(base_mesh, do_unlink=True)

    return result


# ---------------------------------------------------------------------------
#  Geometry primitives
# ---------------------------------------------------------------------------

def _create_rounded_rect(bm, width, height, z, inset):
    """Create a rounded-rectangle vertex loop at the given Z height.

    Returns a list of BMVerts forming a closed loop (last connects to first).
    Corner radius decreases with inset, clamped to valid range.
    """
    w = max(width - 2.0 * inset, 0.01)
    h = max(height - 2.0 * inset, 0.01)

    # Corner radius shrinks with inset, minimum 0.5mm
    r = max(BASE_CORNER_RADIUS - inset, 0.5)
    r = min(r, w / 2.0, h / 2.0)

    # Corner centers (inside the rounded rect)
    corners = [
        ( w / 2 - r,  h / 2 - r),   # top-right
        (-w / 2 + r,  h / 2 - r),   # top-left
        (-w / 2 + r, -h / 2 + r),   # bottom-left
        ( w / 2 - r, -h / 2 + r),   # bottom-right
    ]
    start_angles = [0, math.pi / 2, math.pi, 3 * math.pi / 2]

    verts = []
    for idx, (cx, cy) in enumerate(corners):
        for s in range(ARC_SEGMENTS):
            angle = start_angles[idx] + (math.pi / 2) * s / ARC_SEGMENTS
            x = cx + r * math.cos(angle)
            y = cy + r * math.sin(angle)
            verts.append(bm.verts.new((x, y, z)))

    return verts


def _bridge_loops(bm, lower, upper):
    """Connect two equal-length vertex loops with quad faces."""
    n = len(lower)
    if len(upper) != n:
        print(f"[GridFlender] Bridge error: loop sizes differ ({n} vs {len(upper)})")
        return
    for i in range(n):
        j = (i + 1) % n
        try:
            bm.faces.new([lower[i], lower[j], upper[j], upper[i]])
        except ValueError:
            pass


def _fill_cap(bm, verts, flip=False):
    """Fill a vertex loop with a triangle fan from the centroid.

    This avoids creating a single n-gon with 64+ vertices, which causes
    issues with booleans and rendering.
    """
    if len(verts) < 3:
        return

    # Compute centroid
    cx = sum(v.co.x for v in verts) / len(verts)
    cy = sum(v.co.y for v in verts) / len(verts)
    cz = sum(v.co.z for v in verts) / len(verts)
    center = bm.verts.new((cx, cy, cz))

    n = len(verts)
    for i in range(n):
        j = (i + 1) % n
        try:
            if flip:
                bm.faces.new([verts[j], verts[i], center])
            else:
                bm.faces.new([verts[i], verts[j], center])
        except ValueError:
            pass