# PyZPLRender

A pure Python, offline ZPL (Zebra Programming Language) rendering engine.

## Overview

PyZPLRender parses ZPL strings and renders them into high-quality PNG images using the `Pillow` library. This project aims to provide a lightweight, local alternative to online APIs like Labelary.

## Features

### Supported Commands
- **Framework**: `^XA`, `^XZ`, `^FO`, `^FS`
- **Text**: `^FD` (Field Data)
- **Barcodes (Phase 3)**:
  - `^BC` (Code 128) - Requires `python-barcode`
  - `^BQ` (QR Code) - Requires `qrcode`
- **Graphics (Phase 4)**:
  - `^GF` (Graphic Field) - Support for embedded hexadecimal bitmaps.

## Installation

```bash
pip install Pillow python-barcode qrcode
```

## Usage

```python
from pyzplrender.renderer import ZPLRenderer

# 38.1mm x 12.7mm at 8 dots per mm
renderer = ZPLRenderer(width_mm=38.1, height_mm=12.7, dpmm=8)

# Example with Barcode
zpl = "^XA^FO50,20^BC^FD123456^FS^XZ"
renderer.render(zpl)
renderer.save_png("label.png")
```

## Project Plan

1. **Phase 1: Foundation & Text (Completed)**
2. **Phase 2: Geometry & Shapes (Completed)**
3. **Phase 3: Barcodes & QR Codes (Completed)**
4. **Phase 4: Graphic Fields (^GF) (Completed)**
5. **Phase 5: Advanced Logic & Templates**
