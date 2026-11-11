"""
Gridfinity base geometry.
Units: MILLIMETERS (1 Blender unit = 1 mm)

Pipeline:
  1. Slab (rounded-rect box) UNION all feet (one disjoint mesh)  -> 1 boolean
  2. DIFFERENCE magnet holes + stacking socket (one disjoint mesh) -> 1 boolean

Dimensions follow the Gridfinity spec (Zack Freedman):
  - 42 mm grid, bins are 0.5 mm smaller (0.25 mm clearance per side)
  - outer corner radius 3.75 mm (baseplate 4 mm minus clearance)
  - foot profile: 0.8 mm 45deg chamfer, 1.8 mm vertical, 2.15 mm 45deg chamfer
  - stacking socket uses the baseplate profile: 2.15 / 1.8 / 0.7 mm
  - magnet holes 6.5 x 2.4 mm, 26 mm apart (8 mm from cell edges)
"""

import bpy
import bmesh
import math
from mathutils import Matrix


GRID_SIZE = 42.0       # mm, grid pitch
HEIGHT_UNIT = 7.0      # mm, 1U
BIN_CLEARANCE = 0.25   # mm per side between bin and grid
BIN_CORNER_RADIUS = 3.75
MIN_CORNER_RADIUS = 0.5

# Foot profile (inset_from_foot_top_edge, z), bottom to top.
FOOT_PROFILE = [
    (2.95, 0.0),   # bottom face
    (2.15, 0.8),   # 0.8 mm 45deg chamfer
    (2.15, 2.6),   # 1.8 mm vertical wall
    (0.0,  4.75),  # 2.15 mm 45deg chamfer to full width
]
FOOT_HEIGHT = FOOT_PROFILE[-1][1]

# Stacking socket profile (inset_from_bin_edge, depth_from_top), top to bottom.
# Mirrors the baseplate profile so a bin of the same footprint drops in.
SOCKET_PROFILE = [
    (0.0,  0.0),
    (2.15, 2.15),  # 2.15 mm 45deg chamfer
    (2.15, 3.95),  # 1.8 mm vertical wall
    (2.85, 4.65),  # 0.7 mm 45deg chamfer
]
SOCKET_DEPTH = SOCKET_PROFILE[-1][1]

# Minimum solid material between the top of the feet and the socket floor.
MIN_SOCKET_FLOOR = 1.0
MIN_STACKABLE_HEIGHT = FOOT_HEIGHT + SOCKET_DEPTH + MIN_SOCKET_FLOOR

# Magnet placement: 26 mm apart center-to-center => +/- 13 mm from cell center
MAGNET_CELL_OFFSETS = [
    (-13.0, -13.0),
    ( 13.0, -13.0),
    (-13.0,  13.0),
    ( 13.0,  13.0),
]
MAGNET_SEGMENTS = 32

# Segments per 90-degree arc (4 corners = 4x this many verts per loop)
ARC_SEGMENTS = 16

# Overshoot for cutters so they never share a face with the body
CUT_MARGIN = 0.1


class GeometryError(Exception):
    pass


def create_gridfinity_base_mesh(
    columns: int = 1,
    rows: int = 1,
    use_magnets: bool = False,
    magnet_diameter: float = 6.5,
    magnet_depth: float = 2.4,
    tile_height: float = 28.0,
    stackable: bool = False,
) -> bpy.types.Mesh:
    """Create a manifold Gridfinity base mesh (millimeters, centered on XY, Z=0 at the bottom)."""
    if stackable and tile_height < MIN_STACKABLE_HEIGHT:
        raise GeometryError(
            f"Stackable socket needs a height of at least {MIN_STACKABLE_HEIGHT:.2f} mm"
        )

    base_mesh = _apply_boolean(
        _create_box_mesh(columns, rows, FOOT_HEIGHT, tile_height),
        _create_feet_mesh(columns, rows),
        'UNION',
    )

    if use_magnets or stackable:
        bm = bmesh.new()
        if use_magnets:
            _add_magnet_cutters(bm, columns, rows, magnet_diameter, magnet_depth)
        if stackable:
            _add_socket_cutter(bm, columns, rows, tile_height)
        base_mesh = _apply_boolean(base_mesh, _bmesh_to_mesh(bm, "GF_Cutter_Temp"), 'DIFFERENCE')

    base_mesh.name = "GridfinityBase"
    return base_mesh


# ---------------------------------------------------------------------------
#  Solids
# ---------------------------------------------------------------------------

def _cell_centers(columns, rows):
    start_x = -(columns - 1) * GRID_SIZE / 2.0
    start_y = -(rows - 1) * GRID_SIZE / 2.0
    for c in range(columns):
        for r in range(rows):
            yield start_x + c * GRID_SIZE, start_y + r * GRID_SIZE


def _bin_size(cells):
    return cells * GRID_SIZE - 2.0 * BIN_CLEARANCE


def _create_feet_mesh(columns, rows):
    """All feet as disjoint closed solids, from Z=0 to FOOT_HEIGHT."""
    bm = bmesh.new()
    foot_size = _bin_size(1)
    for cx, cy in _cell_centers(columns, rows):
        loops = [
            _create_rounded_rect(bm, foot_size, foot_size, z, inset, center=(cx, cy))
            for inset, z in FOOT_PROFILE
        ]
        _create_lofted_solid(bm, loops)
    return _bmesh_to_mesh(bm, "GF_Feet_Temp")


def _create_box_mesh(columns, rows, z_bottom, z_top):
    """Closed rounded-rect box covering the whole bin footprint."""
    bm = bmesh.new()
    w, d = _bin_size(columns), _bin_size(rows)
    _create_lofted_solid(bm, [
        _create_rounded_rect(bm, w, d, z_bottom, 0.0),
        _create_rounded_rect(bm, w, d, z_top, 0.0),
    ])
    return _bmesh_to_mesh(bm, "GF_Slab_Temp")


def _add_magnet_cutters(bm, columns, rows, diameter, hole_depth):
    """Cylinders from Z=-CUT_MARGIN up to Z=hole_depth at each cell's magnet spots."""
    height = hole_depth + CUT_MARGIN
    center_z = -CUT_MARGIN + height / 2.0
    for cx, cy in _cell_centers(columns, rows):
        for ox, oy in MAGNET_CELL_OFFSETS:
            bmesh.ops.create_cone(
                bm,
                cap_ends=True,
                cap_tris=True,
                segments=MAGNET_SEGMENTS,
                radius1=diameter / 2.0,
                radius2=diameter / 2.0,
                depth=height,
                matrix=Matrix.Translation((cx + ox, cy + oy, center_z)),
            )


def _add_socket_cutter(bm, columns, rows, tile_height):
    """Socket following SOCKET_PROFILE, flared outward above the top face
    so the cutter only touches the body along the outer top edge."""
    w, d = _bin_size(columns), _bin_size(rows)
    loops = [_create_rounded_rect(bm, w, d, tile_height + 1.0, -1.0)]
    loops += [
        _create_rounded_rect(bm, w, d, tile_height - depth, inset)
        for inset, depth in SOCKET_PROFILE
    ]
    loops.reverse()  # bottom to top
    _create_lofted_solid(bm, loops)


# ---------------------------------------------------------------------------
#  Boolean helper
# ---------------------------------------------------------------------------

def _apply_boolean(base_mesh, cutter_mesh, operation):
    """Evaluate a boolean modifier and return the resulting new mesh.

    Both input meshes are consumed. Uses the evaluated depsgraph instead of
    bpy.ops, so it works regardless of the current mode or selection.
    """
    scene = bpy.context.scene
    base_obj = bpy.data.objects.new("GF_Bool_Base", base_mesh)
    cutter_obj = bpy.data.objects.new("GF_Bool_Cutter", cutter_mesh)
    try:
        scene.collection.objects.link(base_obj)
        scene.collection.objects.link(cutter_obj)

        mod = base_obj.modifiers.new("Boolean", 'BOOLEAN')
        mod.operation = operation
        mod.object = cutter_obj
        mod.solver = 'EXACT'

        depsgraph = bpy.context.evaluated_depsgraph_get()
        result = bpy.data.meshes.new_from_object(
            base_obj.evaluated_get(depsgraph), depsgraph=depsgraph
        )
    finally:
        bpy.data.objects.remove(base_obj, do_unlink=True)
        bpy.data.objects.remove(cutter_obj, do_unlink=True)
        bpy.data.meshes.remove(base_mesh, do_unlink=True)
        bpy.data.meshes.remove(cutter_mesh, do_unlink=True)

    return result


# ---------------------------------------------------------------------------
#  Geometry primitives
# ---------------------------------------------------------------------------

def _bmesh_to_mesh(bm, name):
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    return mesh


def _create_lofted_solid(bm, loops):
    """Bridge consecutive loops (bottom to top) and cap both ends."""
    for lower, upper in zip(loops, loops[1:]):
        _bridge_loops(bm, lower, upper)
    _fill_cap(bm, loops[0])
    _fill_cap(bm, loops[-1])


def _create_rounded_rect(bm, width, height, z, inset, center=(0.0, 0.0)):
    """Create a rounded-rectangle vertex loop at the given Z height.

    Returns a list of BMVerts forming a closed loop (last connects to first).
    Corner radius follows the inset (keeps offset curves concentric),
    clamped to a valid range.
    """
    w = max(width - 2.0 * inset, 0.01)
    h = max(height - 2.0 * inset, 0.01)

    r = max(BIN_CORNER_RADIUS - inset, MIN_CORNER_RADIUS)
    r = min(r, w / 2.0, h / 2.0)

    ox, oy = center
    corners = [
        ( w / 2 - r,  h / 2 - r),   # top-right
        (-w / 2 + r,  h / 2 - r),   # top-left
        (-w / 2 + r, -h / 2 + r),   # bottom-left
        ( w / 2 - r, -h / 2 + r),   # bottom-right
    ]

    verts = []
    for idx, (cx, cy) in enumerate(corners):
        for s in range(ARC_SEGMENTS + 1):
            angle = (math.pi / 2) * (idx + s / ARC_SEGMENTS)
            x = ox + cx + r * math.cos(angle)
            y = oy + cy + r * math.sin(angle)
            verts.append(bm.verts.new((x, y, z)))

    return verts


def _bridge_loops(bm, lower, upper):
    """Connect two equal-length vertex loops with quad faces."""
    n = len(lower)
    assert len(upper) == n, f"loop sizes differ ({n} vs {len(upper)})"
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new([lower[i], lower[j], upper[j], upper[i]])


def _fill_cap(bm, verts):
    """Fill a convex vertex loop with a triangle fan from its centroid.

    Avoids a single n-gon with 60+ vertices, which booleans handle poorly.
    Winding is fixed later by recalc_face_normals.
    """
    n = len(verts)
    cx = sum(v.co.x for v in verts) / n
    cy = sum(v.co.y for v in verts) / n
    cz = sum(v.co.z for v in verts) / n
    center = bm.verts.new((cx, cy, cz))
    for i in range(n):
        bm.faces.new([verts[i], verts[(i + 1) % n], center])
