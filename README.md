# GridFlender (Blender Addon)
[![Blender 4.0+](https://img.shields.io/badge/Blender-4.0%2B-orange)](https://www.blender.org/)

**A tool to generate strictly compliant Gridfinity bases for your custom 3D modeling projects.**

This addon generates the solid "filled" base mesh (1x1, 1x2, 2x3 etc.) with correct profiles, magnet holes, and stacking lips. It is intended to be used as a **starting point** or a **boolean cutter** for modeling your own bins and holders.

## Key Features

- **Procedural Generation**: Create standard 42mm grid bases of any size.
- **Spec Compliant**: Dimensions and profiles match Zach Freedman's Gridfinity specifications.
- **Magnet Holes**: Optional standard 6mm holes with correct spacing (from corners) and depth.
- **Stackable Socket**: Optional top "socket" lip for creating stackable bins.
- **Height Presets**: Choose standard heights in "U" units (1U = 7mm) or customize.

## Installation

1.  **Download:** [Latest Release](https://github.com/blekknajt/GridFlender/releases)
2.  **Open Blender:** Go to `Edit > Preferences > Add-ons`.
3.  **Install:** Click top-right "Install..." button (or "Install from Disk") and select the downloaded ZIP file.
4.  **Enable:** Search for "Gridfinity" in the list and check the box to enable it.
5.  **Access:** Find the panel in **View3D → Sidebar (N-panel) → Gridfinity**

## Workflow Guide

This addon creates a solid geometry. Here is the recommended workflow:

1.  **Configure Base**:
    *   Set **Columns (X)** and **Rows (Y)**.
    *   Select **Height** (e.g., 6U for a deep item, 3U for shallow).
    *   Enable **Magnet Holes** if you plan to use magnets.
    *   Enable **Stackable** if you want another bin to sit on top of this one.
2.  **Generate**: Click "Generate Base".
3.  **Model Your Holder**:
    *   **Method A (Start from Base)**: Enter Edit Mode, select the top face, and extrude/inset downwards to carve out custom compartments.
    *   **Method B (Boolean)**: Model your custom object separately, then position the generated base and use a Boolean Modifier (Difference) to cut the Gridfinity profile into the bottom of your object.

## Standard Dimensions

| Feature | Value | Notes |
| :--- | :--- | :--- |
| **Grid Unit** | 42mm x 42mm | Standard module size |
| **Height Unit (1U)** | 7mm | Multiples of this define bin height |
| **Magnet Hole** | ⌀6.5mm x 2.4mm | Fits standard 6x2mm magnets with tolerance |

## License

MIT License

---

Created with ❤️ by **@blekknajt** + **Antigravity**

☕ [Buy me a coffee](https://buycoffee.to/klafciarz)
