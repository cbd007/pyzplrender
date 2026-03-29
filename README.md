# PyZPLRender

A pure Python, offline ZPL (Zebra Programming Language) rendering engine.

## Overview

PyZPLRender parses ZPL strings and renders them into high-quality, high-resolution PNG images using the `Pillow` library. It is designed as a standalone, offline alternative to web-based APIs like Labelary, providing pixel-perfect rendering for industrial thermal printers.

## Key Features

- **Pixel-Perfect Accuracy**: Verified 100% match on physical Zebra hardware (GX420d).
- **Fully Offline**: No internet connection required; all rendering happens locally.
- **Universal & Lightweight**: Written in pure Python with minimal dependencies.
- **Advanced Layout**: Supports multi-line blocks, justification, and complex rotations.
- **Templating Engine**: Full support for Download Format (`^DF`) and Recall Format (`^XF`) with variable substitution (`^FN`).

---

## Supported ZPL Commands

| Command | Name | Description |
| :--- | :--- | :--- |
| **`^XA`** | Start Format | Marks the beginning of a label format. |
| **`^XZ`** | End Format | Marks the end of a label format and triggers the render. |
| **`^FO`** | Field Origin | Sets the (X, Y) coordinates for the next field, relative to Label Home. |
| **`^FS`** | Field Separator | Marks the end of a field definition. |
| **`^LH`** | Label Home | Sets a global (X, Y) offset for all subsequent `^FO` commands. |
| **`^PW`** | Print Width | Defines the width of the label in dots (prevents horizontal clipping). |
| **`^LL`** | Label Length | Defines the length of the label in dots (prevents vertical wrapping). |
| **`^LS`** | Label Shift | Shifts the entire label for physical hardware calibration. |
| **`^FD`** | Field Data | The primary command for providing text or data to be rendered. |
| **`^A`** | Font Scaling | Selects a font and sets its height, width, and rotation (N, R, I, B). |
| **`^CF`** | Default Font | Sets the default font, height, and width for all fields. |
| **`^FB`** | Field Block | Multi-line text with automatic wrapping and alignment (L, R, C). |
| **`^FR`** | Field Reverse | Reverses the color of the field (e.g., white text on black). |
| **`^GB`** | Graphic Box | Draws a rectangle with configurable thickness and **rounded corners**. |
| **`^GC`** | Graphic Circle | Draws a circle with a specified diameter and border thickness. |
| **`^GF`** | Graphic Field | Renders embedded hexadecimal bitmap images. |
| **`^BC`** | Code 128 | Renders a Code 128 barcode with support for data prefixes. |
| **`^BQ`** | QR Code | Renders a high-density QR Code (Model 2). |
| **`^DF`** | Download Format | Stores a sequence of commands as a template in memory. |
| **`^XF`** | Recall Format | Executes a previously stored template. |
| **`^FN`** | Field Number | Variable data substitution placeholder for templates. |

---

## Pending Features (Roadmap)

The following commands are planned for future releases to increase engine versatility:

| Command | Name | Description |
| :--- | :--- | :--- |
| **`^FT`** | Field Typeset | Positioning relative to the bottom-left of the field. |
| **`^BY`** | Barcode Yield | Global defaults for barcode module width, height, and ratio. |
| **`^B3`** | Code 39 | Support for Code 39 (3 of 9) barcode type. |
| **`^CI`** | Character Set | Support for UTF-8 and international character encodings. |
| **`^GE`** | Graphic Ellipse | Drawing ellipses with independent X/Y radii. |
| **`^SN`** | Serialization | Automatic incrementing of serial numbers. |
| **`^PO`** | Orientation | Global 180-degree label inversion. |
| **`~DG`** | Download Graphic | Support for the legacy `~DG` bitmap storage format. |

---

## Installation

```bash
pip install Pillow python-barcode qrcode
```

## Usage

### Simple Label
```python
from pyzplrender.renderer import ZPLRenderer

# 1.5 x 0.5 inches @ 8 dots per mm (203 DPI)
renderer = ZPLRenderer(width_mm=38.1, height_mm=12.7, dpmm=8)

zpl = "^XA^FO50,20^A0N,30,30^FDHello World^FS^XZ"
renderer.render(zpl)
renderer.save_png("label.png")
```

### Hardware Calibration

If your physical print is shifted, use the `^LS` command to calibrate your specific printer:

```zpl
^XA
^LS-30  (Shifts the entire label 30 dots to the left)
...
^XZ
```

## Development & Testing

**Run Tests:**
```bash
pytest --cov=pyzplrender test/
```

**Build Package:**
```bash
python3 -m build
```

## License
MIT
