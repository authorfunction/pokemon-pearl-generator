#!/usr/bin/env python3
"""
build_manifest.py
Scans msikma/pokesprite Gen 8 assets, trims transparent padding using alpha bbox,
filters for <= 29x29 physical pegboards, and outputs sprites_29x29.json.
"""

import os
import json
import sys
from PIL import Image

SRC_DIR = "./pokesprite/pokemon-gen8/regular"
OUT_FILE = "./sprites_29x29.json"
MAX_WIDTH = 29
MAX_HEIGHT = 29
ALPHA_THRESHOLD = 40

def build_manifest():
    if not os.path.exists(SRC_DIR):
        print(f"Error: Source directory {SRC_DIR} not found.", file=sys.stderr)
        sys.exit(1)

    results = []
    file_list = sorted([f for f in os.listdir(SRC_DIR) if f.endswith(".png")])
    print(f"Found {len(file_list)} sprites in {SRC_DIR}. Processing...")

    for fname in file_list:
        fpath = os.path.join(SRC_DIR, fname)
        try:
            img = Image.open(fpath).convert("RGBA")
        except Exception as e:
            print(f"Warning: Failed to open {fname}: {e}", file=sys.stderr)
            continue

        # Alpha thresholding mask for clean bounding box
        alpha = img.split()[-1]
        threshold_mask = alpha.point(lambda p: 255 if p > ALPHA_THRESHOLD else 0)
        bbox = threshold_mask.getbbox()

        if not bbox:
            continue

        cropped = img.crop(bbox)
        w, h = cropped.size

        if 0 < w <= MAX_WIDTH and 0 < h <= MAX_HEIGHT:
            name = fname.replace(".png", "").replace("-", " ")
            pixel_grid = []

            for y in range(h):
                row = []
                for x in range(w):
                    r, g, b, a = cropped.getpixel((x, y))
                    row.append([r, g, b] if a > ALPHA_THRESHOLD else None)
                pixel_grid.append(row)

            results.append({
                "name": name,
                "w": w,
                "h": h,
                "pixels": pixel_grid
            })

    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f)

    print(f"Manifest build complete: {len(results)} sprites saved to {OUT_FILE}")

if __name__ == "__main__":
    build_manifest()
