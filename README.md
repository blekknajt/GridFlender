# GridfLender (Blender Addon)
[![Blender 5.0+](https://img.shields.io/badge/Blender-5.0%2B-orange)](https://www.blender.org/)

**A tool to generate strictly compliant Gridfinity bases for your custom 3D modeling projects.** 

This addon generates the solid "filled" base mesh (1x1, 1x2, 2x3 etc.) with correct profiles, magnet holes, and stacking lips. It is intended to be used as a starting point or a boolean cutter for modeling your own bins and holders.

## Features

- **Procedural Generation**: Create standard 42mm grid bases.
- **Spec Compliant**: Dimensions and profiles match Gridfinity specifications.
- **Magnet Holes**: Optional 6mm holes with correct spacing (7.75mm from corners) and depth.
- **Stackable Socket**: Optional top "socket" for creating stackable bins.
- **Height Presets**: Choose standard heights in "U" units (1U = 7mm).

## Installation

1.  **Download the Addon:** [Download Gridfinity-Blender-Addon-v3.2.zip](../Gridfinity-Blender-Addon-v3.2.zip)
2.  **Open Blender:** Go to `Edit > Preferences > Add-ons`.
3.  **Install:** Click "Install..." and select the downloaded ZIP file.
4.  **Enable:** Search for "Gridfinity" and check the box to enable the addon.
5. Access via: **View3D → Sidebar (N) → Gridfinity**

## Usage Guide

1. **Set Grid Size**: Choose columns (X) and rows (Y).
2. **Select Height**: Pick a standard unit height (e.g., 4U = 28mm).
3. **Features**:
   - Check **Include Magnet Holes** to add 6mm holes at the bottom corners.
   - Check **Stackable** to cut the standard "socket" profile into the top.
4. **Generate**: Click "Generate Base".

### Workflow Tip
This object is solid. To make a useful bin:
1. Generate the base (e.g., 1x1, 6U).
2. Enter Edit Mode.
3. Select top faces and inset/extrude downwards to create the compartment hollows.
4. Or use boolean operations to cut specfic shapes for your tools.

## Standard Dimensions

| Unit | Value |
|------|-------|
| **Grid Unit** | 42mm x 42mm |
| **Height Unit (1U)** | 7mm |
| **Magnet Hole** | ⌀6mm x 2mm deep |

## License

MIT License

---
Created with ❤️ by **@blekknajt** + **Antigravity**

☕ [Buy me a coffee](https://buycoffee.to/klafciarz)
