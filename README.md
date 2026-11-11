# GridFlender (Blender Addon)
[![Blender 4.0+](https://img.shields.io/badge/Blender-4.0%2B-orange)](https://www.blender.org/)

**A tool to generate strictly compliant Gridfinity bases for your custom 3D modeling projects.**

This addon generates the solid "filled" base mesh (1x1, 1x2, 2x3 etc.) with correct profiles, magnet holes, and stacking lips. It is intended to be used as a **starting point** or a **boolean cutter** for modeling your own bins and holders.

## Key Features

- **Procedural Generation**: Bases of any size on the standard 42mm grid (1x1, 2x3, 10x10…).
- **Spec Compliant**: 0.25mm clearance per side (a 1x1 bin is 41.5mm), 3.75mm corner radius and the standard 0.8 / 1.8 / 2.15mm foot profile.
- **Manifold Output**: The result is a single watertight solid, ready for booleans and 3D printing.
- **Magnet Holes**: Optional ⌀6.5 x 2.4mm holes, 4 per cell, 26mm apart.
- **Stackable Socket**: Optional socket (baseplate profile) cut into the top so another bin can sit on it.
- **Height in U**: 1U = 7mm, from 1U up to 30U.
- **Redo Panel**: Tweak every parameter after generating via the *Adjust Last Operation* panel (F9).

## Installation

1.  **Download:** [Latest Release](https://github.com/blekknajt/GridFlender/releases) (ZIP file).
2.  **Blender 4.2+:** `Edit > Preferences > Get Extensions`, open the ▾ menu in the top-right corner and choose **Install from Disk…**, then select the ZIP.
3.  **Blender 4.0 / 4.1:** `Edit > Preferences > Add-ons > Install…`, select the ZIP and enable **GridFlender**.
4.  **Access:**
    *   **View3D → Sidebar (N-panel) → GridFlender** tab, or
    *   **View3D → Add (Shift+A) → Mesh → Gridfinity Base**

To build the ZIP yourself (Blender 4.2+):

```bash
blender --command extension build
```

## Units

Geometry is created in **millimeters, 1 Blender unit = 1 mm** (a 1x1 base is 41.5 units wide). STL/3MF export with default settings gives correct sizes in your slicer.
To see millimeters in Blender, set `Scene Properties > Units`: **Unit Scale = 0.001**, **Length = Millimeters**.

## Workflow Guide

This addon creates a solid geometry. Here is the recommended workflow:

1.  **Configure Base**:
    *   Set **Columns (X)** and **Rows (Y)**.
    *   Select **Height (U)** (e.g., 6U for a deep item, 3U for shallow).
    *   Enable **Magnet Holes** if you plan to use magnets.
    *   Enable **Stackable** if you want another bin to sit on top of this one (requires 2U or more).
2.  **Generate**: Click "Generate Base" (the base is placed at the 3D cursor).
3.  **Model Your Holder**:
    *   **Method A (Start from Base)**: Enter Edit Mode, select the top face, and extrude/inset downwards to carve out custom compartments.
    *   **Method B (Boolean)**: Model your custom object separately, then position the generated base and use a Boolean Modifier (Difference) to cut the Gridfinity profile into the bottom of your object.

## Standard Dimensions

| Feature | Value | Notes |
| :--- | :--- | :--- |
| **Grid Unit** | 42mm x 42mm | Grid pitch |
| **Bin Footprint** | N x 42mm − 0.5mm | 0.25mm clearance on each side |
| **Corner Radius** | 3.75mm | Baseplate 4mm minus clearance |
| **Foot Height** | 4.75mm | 0.8mm chamfer + 1.8mm wall + 2.15mm chamfer |
| **Height Unit (1U)** | 7mm | Total height measured from the bottom of the feet |
| **Stacking Socket** | 4.65mm deep | 2.15mm chamfer + 1.8mm wall + 0.7mm chamfer |
| **Magnet Hole** | ⌀6.5mm x 2.4mm | Fits standard 6x2mm magnets with tolerance |

## License

MIT License

---

Created with ❤️ by **@blekknajt** + **Antigravity**

☕ [Buy me a coffee](https://buycoffee.to/klafciarz)
