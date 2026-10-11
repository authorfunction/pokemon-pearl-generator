# Pokémon Bead Art Generator (Pärlplatta) — Project Blueprint & Documentation

## 1. Project Background & Architectural Retrospective

The goal of this project is to generate physical bead pegboard patterns (Hama/Nabbi MIDI beads, typically $29 \times 29$ grids) using Pokémon pixel art.

### Path A: The Terminal Colorscripts Route (Evaluated & Deprecated)
We initially evaluated parsing plain-text assets from `phoneybadger/pokemon-colorscripts`.
* **Mechanism:** Plain-text files containing ECMA-48 ANSI escape sequences (`\x1b[38;2;R;G;Bm` for foreground and `\x1b[48;2;R;G;Bm` for background) paired with Unicode half-block characters (`▀` / `U+2580`).
* **Hidden Dimension Trap:** A single text line containing `▀` encodes **two vertical pixels** (top pixel = foreground, bottom pixel = background). Standard CLI line counting (`wc -l`) undercounts vertical bead height by 50%.
* **Architectural Redundancy:** `pokemon-colorscripts` originally derived its assets by converting PNG files from `msikma/pokesprite` *into* ANSI escape strings. Parsing ANSI in a browser/Canvas app was essentially doing `PNG -> ANSI -> Canvas Pixels`.

### Path B: Direct PokeSprite Ingestion (Adopted Standard)
We transitioned directly to the upstream source: **`msikma/pokesprite`**.
* **Source:** Box/menu sprites from Gen 8 (`pokemon-gen8/regular/*.png`).
* **Format:** Transparent PNGs natively padded inside a $68 \times 56$ canvas.
* **Extraction Pipeline:** Images are ingested, transparent borders are trimmed via alpha channel bounding box detection (`A > 40`), and resulting matrices are filtered by exact bead limits ($\le 29 \times 29$).
* **Reliability:** Direct browser querying of GitHub/GitLab trees causes CORS issues (`file:///` origin bugs) and HTTP 403/404 rate-limiting. The production pipeline uses a local Python pre-processor to generate an offline JSON manifest.

---

## 2. Directory Structure

The initial prototype in `experiments/` has been deprecated. All production application files must reside in the repository root:

```text
pokemon-pearl-generator/
├── pokesprite/                       # Sparse git checkout (Gen 8 regular icons)
│   └── pokemon-gen8/
│       └── regular/
│           ├── bulbasaur.png
│           ├── pikachu.png
│           └── ...
├── build_manifest.py                 # Offline parser: trims PNGs & emits manifest
├── sprites_29x29.json                # Pre-filtered, bounding-box-trimmed sprite data
├── index.html                        # Production web application (vanilla HTML5/CSS/JS)
├── README.md
└── experiments/                      # (Deprecated scratchpad)
```

---

## 3. Data Ingestion & Manifest Generation Script

Run this script locally to check out the exact sprite assets and generate the trimmed bead matrix:

```bash
# 1. Sparse clone only the Gen 8 regular icons
git clone --depth 1 --filter=blob:none --sparse [https://github.com/msikma/pokesprite.git](https://github.com/msikma/pokesprite.git)
cd pokesprite
git sparse-checkout set pokemon-gen8/regular
cd ..

# 2. Install Pillow if not already installed
pip3 install pillow
```

Save as `build_manifest.py` in the repo root and execute (`python3 build_manifest.py`):

```python
#!/usr/bin/env python3
"""
build_manifest.py
Scans msikma/pokesprite Gen 8 assets, trims transparent padding,
filters for <= 29x29 physical pegboards, and outputs sprites_29x29.json.
"""

import os
import json
from PIL import Image

SRC_DIR = "./pokesprite/pokemon-gen8/regular"
OUT_FILE = "./sprites_29x29.json"
MAX_WIDTH = 29
MAX_HEIGHT = 29

if not os.path.exists(SRC_DIR):
    raise SystemExit(f"Error: Source directory {SRC_DIR} not found. Run sparse clone first.")

results = []

for fname in sorted(os.listdir(SRC_DIR)):
    if not fname.endswith(".png"):
        continue

    fpath = os.path.join(SRC_DIR, fname)
    img = Image.open(fpath).convert("RGBA")

    # Detect bounding box of non-transparent content
    # Pillow getbbox() uses alpha threshold > 0; filter slightly higher to avoid artifacts
    alpha = img.split()[-1]
    threshold_mask = alpha.point(lambda p: 255 if p > 40 else 0)
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
                row.append([r, g, b] if a > 40 else None)
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
```

---

## 4. Production Web Application (`index.html`)

This production application includes:
1. **Catalog View with Search:** Live filter by name and dimensions.
2. **Kid-Friendly iPad Fullscreen Mode:** Tap any card to open a full-screen, distraction-free crafting view with zoom controls and a clean exit button.
3. **Bead-Pixel (Donut) Rendering Toggle:** Switch between classic square pixels and realistic circular beads with hollow center pegs.
4. **Counting Grid & Configurable Spacing:** Adjustable bead separation slider ($0\text{px}$ to $8\text{px}$) with accented grid lines every 5 beads for easy counting.
5. **Custom Inventory Quantization:** Adapts sprite colors to whatever bead colors are available at home via Euclidean RGB delta matching.

Save as `index.html` in the repository root:

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
  <title>Pokémon Bead Art Generator</title>
  <style>
    :root {
      --bg: #121212;
      --card-bg: #1e1e1e;
      --border: #333;
      --text: #eee;
      --accent: #ffcb05;
    }
    * { box-sizing: border-box; touch-action: manipulation; }
    body {
      font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      background: var(--bg);
      color: var(--text);
      margin: 0;
      padding: 16px;
    }
    header {
      background: var(--card-bg);
      padding: 16px;
      border-radius: 8px;
      border: 1px solid var(--border);
      margin-bottom: 20px;
    }
    h1 { margin: 0 0 12px 0; color: var(--accent); font-size: 1.5rem; }
    .control-row { display: flex; flex-wrap: wrap; gap: 12px; align-items: center; }
    input, select, button {
      background: #2a2a2a;
      border: 1px solid #444;
      color: #fff;
      padding: 8px 12px;
      border-radius: 6px;
      font-size: 0.95rem;
    }
    button { background: #2563eb; border: none; cursor: pointer; font-weight: bold; }
    #grid { display: flex; flex-wrap: wrap; gap: 12px; justify-content: center; }
    .card {
      background: var(--card-bg);
      border: 1px solid var(--border);
      padding: 10px;
      border-radius: 8px;
      text-align: center;
      width: 160px;
      cursor: pointer;
      transition: transform 0.1s, border-color 0.2s;
    }
    .card:hover { border-color: #666; transform: translateY(-2px); }
    .card-title { font-weight: bold; text-transform: capitalize; font-size: 0.9rem; margin-bottom: 4px; }
    .card-dim { font-size: 0.75rem; color: #888; margin-bottom: 8px; }
    .card canvas { display: block; margin: 0 auto; background: #000; border-radius: 4px; }

    /* Fullscreen iPad Mode */
    #fullscreen-modal {
      display: none;
      position: fixed;
      inset: 0;
      background: #000;
      z-index: 1000;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: 20px;
    }
    #fullscreen-modal.active { display: flex; }
    #modal-header {
      position: absolute;
      top: 16px;
      left: 16px;
      right: 16px;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    #modal-title { font-size: 1.4rem; font-weight: bold; text-transform: capitalize; }
    .modal-tools { display: flex; gap: 10px; align-items: center; }
    .exit-btn { background: #dc2626; padding: 10px 18px; font-size: 1rem; }
    #canvas-holder {
      flex: 1;
      display: flex;
      align-items: center;
      justify-content: center;
      width: 100%;
      height: 100%;
      overflow: auto;
    }
    #fsCanvas {
      max-width: 95vw;
      max-height: 80vh;
      object-fit: contain;
      image-rendering: pixelated;
    }
  </style>
</head>
<body>

  <header>
    <h1>Pokémon Pärlplatta Studio (≤ 29×29)</h1>
    <div class="control-row">
      <input type="text" id="search" placeholder="Search Pokémon..." oninput="filterCatalog()">
      <label>
        Style:
        <select id="beadShape" onchange="refreshCurrentView()">
          <option value="donut">Beads (Circles)</option>
          <option value="square">Pixels (Squares)</option>
        </select>
      </label>
      <label>
        Spacing:
        <input type="range" id="gapSize" min="0" max="6" value="2" onchange="refreshCurrentView()">
      </label>
      <label>
        Palette:
        <select id="paletteMode" onchange="refreshCurrentView()">
          <option value="original">Original Game Colors</option>
          <option value="basic12">Home Stash (Basic 12 Colors)</option>
        </select>
      </label>
      <span id="status" style="color: #aaa; font-size: 0.85rem;"></span>
    </div>
  </header>

  <div id="grid"></div>

  <!-- iPad Crafting Fullscreen Modal -->
  <div id="fullscreen-modal">
    <div id="modal-header">
      <div id="modal-title"></div>
      <div class="modal-tools">
        <button onclick="toggleGridLines()">Toggle 5-Peg Lines</button>
        <button class="exit-btn" onclick="closeFullscreen()">✕ Exit</button>
      </div>
    </div>
    <div id="canvas-holder">
      <canvas id="fsCanvas"></canvas>
    </div>
  </div>

  <script>
    let catalog = [];
    let activePokemon = null;
    let showPegLines = true;

    // Common standard home bead stash (arbitrary palette)
    const HOME_PALETTE_12 = [
      { name: "White", rgb: [255, 255, 255] },
      { name: "Black", rgb: [0, 0, 0] },
      { name: "Yellow", rgb: [245, 218, 55] },
      { name: "Red", rgb: [210, 35, 42] },
      { name: "Dark Blue", rgb: [30, 60, 150] },
      { name: "Light Blue", rgb: [100, 180, 240] },
      { name: "Green", rgb: [40, 140, 50] },
      { name: "Light Green", rgb: [120, 200, 80] },
      { name: "Orange", rgb: [240, 120, 30] },
      { name: "Pink", rgb: [240, 130, 170] },
      { name: "Purple", rgb: [120, 50, 140] },
      { name: "Brown", rgb: [110, 60, 35] },
      { name: "Grey", rgb: [130, 130, 130] }
    ];

    async function init() {
      const status = document.getElementById('status');
      try {
        const res = await fetch('sprites_29x29.json');
        if (!res.ok) throw new Error("Manifest sprites_29x29.json not found. Run build_manifest.py first.");
        catalog = await res.json();
        status.innerText = `${catalog.length} sprites ready. Tap any to open iPad mode.`;
        renderCatalog(catalog);
      } catch (err) {
        status.innerText = "Error: " + err.message;
        console.error(err);
      }
    }

    function quantize(rgb, palette) {
      let minDistance = Infinity;
      let matched = rgb;
      for (const p of palette) {
        // Weighted Euclidean distance for human perception
        const d = 0.3 * (rgb[0] - p.rgb[0]) ** 2 +
                  0.59 * (rgb[1] - p.rgb[1]) ** 2 +
                  0.11 * (rgb[2] - p.rgb[2]) ** 2;
        if (d < minDistance) {
          minDistance = d;
          matched = p.rgb;
        }
      }
      return matched;
    }

    function renderSpriteToCanvas(canvas, item, pitch, shape, gap, usePalette) {
      const w = item.w;
      const h = item.h;
      canvas.width = w * pitch;
      canvas.height = h * pitch;
      const ctx = canvas.getContext('2d');

      ctx.fillStyle = "#181818";
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      item.pixels.forEach((row, y) => {
        row.forEach((pixel, x) => {
          if (!pixel) return;

          let color = pixel;
          if (usePalette === "basic12") {
            color = quantize(pixel, HOME_PALETTE_12);
          }

          const px = x * pitch;
          const py = y * pitch;
          const size = pitch - gap;

          ctx.fillStyle = `rgb(${color[0]}, ${color[1]}, ${color[2]})`;

          if (shape === "donut") {
            const radius = size / 2;
            const centerX = px + radius;
            const centerY = py + radius;

            // Outer bead circle
            ctx.beginPath();
            ctx.arc(centerX, centerY, Math.max(1, radius), 0, Math.PI * 2);
            ctx.fill();

            // Inner hollow hole
            ctx.fillStyle = "#181818";
            ctx.beginPath();
            ctx.arc(centerX, centerY, Math.max(0.5, radius * 0.35), 0, Math.PI * 2);
            ctx.fill();
          } else {
            // Square pixel mode
            ctx.fillRect(px, py, size, size);
          }
        });
      });

      // Accent lines every 5 pegs for easy counting
      if (showPegLines && pitch >= 16) {
        ctx.strokeStyle = "rgba(255, 255, 255, 0.25)";
        ctx.lineWidth = 1;
        for (let x = 0; x <= w; x += 5) {
          ctx.beginPath();
          ctx.moveTo(x * pitch, 0);
          ctx.lineTo(x * pitch, canvas.height);
          ctx.stroke();
        }
        for (let y = 0; y <= h; y += 5) {
          ctx.beginPath();
          ctx.moveTo(0, y * pitch);
          ctx.lineTo(canvas.width, y * pitch);
          ctx.stroke();
        }
      }
    }

    function renderCatalog(list) {
      const grid = document.getElementById('grid');
      grid.innerHTML = '';

      const shape = document.getElementById('beadShape').value;
      const gap = parseInt(document.getElementById('gapSize').value, 10);
      const palette = document.getElementById('paletteMode').value;

      list.forEach(item => {
        const card = document.createElement('div');
        card.className = 'card';
        card.onclick = () => openFullscreen(item);

        card.innerHTML = `
          <div class="card-title">${item.name}</div>
          <div class="card-dim">${item.w}×${item.h} beads</div>
        `;

        const canvas = document.createElement('canvas');
        renderSpriteToCanvas(canvas, item, 5, shape, Math.min(gap, 1), palette);
        card.appendChild(canvas);
        grid.appendChild(card);
      });
    }

    function filterCatalog() {
      const q = document.getElementById('search').value.toLowerCase();
      const filtered = catalog.filter(s => s.name.toLowerCase().includes(q));
      renderCatalog(filtered);
    }

    function openFullscreen(item) {
      activePokemon = item;
      document.getElementById('modal-title').innerText = `${item.name} (${item.w}×${item.h} beads)`;
      document.getElementById('fullscreen-modal').classList.add('active');
      drawFullscreen();
    }

    function closeFullscreen() {
      document.getElementById('fullscreen-modal').classList.remove('active');
      activePokemon = null;
    }

    function drawFullscreen() {
      if (!activePokemon) return;
      const fsCanvas = document.getElementById('fsCanvas');
      const shape = document.getElementById('beadShape').value;
      const gap = parseInt(document.getElementById('gapSize').value, 10);
      const palette = document.getElementById('paletteMode').value;

      // Pitch large enough for counting on an iPad screen
      renderSpriteToCanvas(fsCanvas, activePokemon, 24, shape, gap, palette);
    }

    function toggleGridLines() {
      showPegLines = !showPegLines;
      drawFullscreen();
    }

    function refreshCurrentView() {
      filterCatalog();
      if (activePokemon) drawFullscreen();
    }

    init();
  </script>
</body>
</html>
```

---

## 5. Execution Instructions

1. **Build Manifest:**
   ```bash
   cd /Users/mattslindstrom/code/pokemon-pearl-generator
   python3 build_manifest.py
   ```
2. **Serve Root:**
   ```bash
   python3 -m http.server 8080
   ```
3. **Open:** Navigate to `http://localhost:8080` or `http://<YOUR-MAC-IP>:8080` on the iPad.