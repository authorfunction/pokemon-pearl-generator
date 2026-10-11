# Pokémon Bead Art (Pärlplatta) Generator: Architecture & Implementation Brief

## 1. Project Goal

Build an interactive web application that displays Pokémon pixel art formatted as printable / viewable bead patterns (pärlplatta), specifically targeting physical pegboard dimensions such as standard single $29 \times 29$ **Hama/Nabbi Midi pegboards**.

## 2. Iteration 1: Terminal Colorscripts Analysis & Pitfalls

### Overview

Initially explored using [`phoneybadger/pokemon-colorscripts`](https://gitlab.com/phoneybadger/pokemon-colorscripts), an ANSI-encoded sprite repository derived from the original `msikma/pokesprite` database.

### Technical Challenges & Realizations

1. **Dual-Pixel Terminal Geometry:**
   * In terminals, characters have an approximate 1:2 aspect ratio.
   * Sprites achieve square pixels by leveraging Unicode half-blocks:
     * `▀` (`U+2580`): Top half-pixel colored by foreground escape code `\x1b[38;2;R;G;Bm`, bottom half-pixel colored by background escape code `\x1b[48;2;R;G;Bm`.
   * **Crucial Consequence:** Counting lines in text files (`wc -l`) does not yield the true pixel height. One line represents **2 vertical bead rows**. A sprite measuring 20 text lines tall is actually 40 beads tall and cannot fit on a $29 \times 29$ board.

2. **Network & Browser Barriers:**
   * The upstream source is hosted on **GitLab**, not GitHub.
   * Attempting client-side dynamic fetching via GitHub/GitLab REST APIs hit:
     * 404 errors (branch mismatches, repository moves).
     * CORS security blocks when accessing resources from `file:///` and localhost.
     * Rate-limiting when performing sequential network queries for hundreds of individual files.

3. **Architectural Redundancy:**
   * `pokemon-colorscripts` originally converted PNG images into ANSI escape codes for terminals.
   * Decoding ANSI sequences in JavaScript back into canvas pixels was an unnecessary round-trip (**PNG** $\rightarrow$ **ANSI text** $\rightarrow$ **Canvas pixels**).

## 3. Iteration 2: Direct Source Integration via `msikma/pokesprite`

### Overview

Bypassed the terminal encoding layer entirely by connecting directly to the canonical source: [`msikma/pokesprite`](https://github.com/msikma/pokesprite).

### Key Repository Discoveries

* Sprite files are stored under `pokemon-gen8/regular/<slug>.png`.
* Files are indexed by **English slug names** (e.g., `pikachu.png`), not numeric Dex IDs.
* Every icon is natively framed inside a fixed $68 \times 56$ **transparent canvas**.
* Direct dimensions (`naturalWidth` / `naturalHeight`) cannot be used alone for pegboard bounds—sprites must have their transparent padding cropped (`getbbox()`) to assess true physical peg requirements.

## 4. Production Workflow & Architecture

To achieve zero network latency, zero CDN rate limits, and 100% offline reliability, the pipeline uses a two-stage architecture:

```
[msikma/pokesprite Git Repo]
           │
           │ (git sparse-checkout)
           ▼
[Local PNG Assets: pokemon-gen8/regular/]
           │
           │ (Python + Pillow crop & filter)
           ▼
[Precomputed JSON Manifest: pokesprite_29x29.json]
           │
           │ (Local fetch())
           ▼
[HTML5 Canvas Browser App: pokesprite_app.html]
```

## 5. Implementation Code

### Stage A: Sparse Clone & Offline Manifest Builder

Run from the project root (`/Users/mattslindstrom/code/pokemon-pearl-generator`):

```bash
# 1. Sparse clone only the Gen 8 regular icons (fast, minimal disk footprint)
git clone --depth 1 --filter=blob:none --sparse https://github.com/msikma/pokesprite.git
cd pokesprite
git sparse-checkout set pokemon-gen8/regular
cd ..

# 2. Process icons: crop transparent borders, filter <= 29x29, emit matrix
python3 -c "
import os, json
from PIL import Image

src_dir = './pokesprite/pokemon-gen8/regular'
out_path = './experiments/pokesprite_29x29.json'
results = []

if not os.path.exists(src_dir):
    print(f'Error: Directory {src_dir} not found!')
    exit(1)

for fname in sorted(os.listdir(src_dir)):
    if not fname.endswith('.png'):
        continue
    
    fpath = os.path.join(src_dir, fname)
    img = Image.open(fpath).convert('RGBA')
    
    # Calculate non-transparent pixel boundary
    bbox = img.getbbox()
    if not bbox:
        continue
    
    cropped = img.crop(bbox)
    w, h = cropped.size
    
    # Filter for single 29x29 Hama board
    if 0 < w <= 29 and 0 < h <= 29:
        name = fname.replace('.png', '').replace('-', ' ')
        
        # Build 2D pixel grid [ [ [r,g,b] | None ], ... ]
        pixels = []
        for y in range(h):
            row = []
            for x in range(w):
                r, g, b, a = cropped.getpixel((x, y))
                row.append([r, g, b] if a > 40 else None)
            pixels.append(row)
            
        results.append({
            'name': name,
            'w': w,
            'h': h,
            'pixels': pixels
        })

os.makedirs('experiments', exist_ok=True)
with open(out_path, 'w') as f:
    json.dump(results, f)

print(f'Done! Found {len(results)} sprites fitting <= 29x29. Saved to {out_path}')
"
```

### Stage B: Web Viewer (`experiments/pokesprite_app.html`)

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>PokéSprite 29×29 Bead Art Maker</title>
  <style>
    body { font-family: system-ui, -apple-system, sans-serif; background: #121212; color: #eee; padding: 20px; margin: 0; }
    header { background: #1e1e1e; padding: 16px 20px; border-radius: 8px; margin-bottom: 20px; border: 1px solid #333; display: flex; align-items: center; justify-content: space-between; }
    h1 { margin: 0; font-size: 1.5rem; color: #ffcb05; }
    .controls { display: flex; gap: 15px; align-items: center; }
    input { background: #2a2a2a; border: 1px solid #444; color: #fff; padding: 6px 12px; border-radius: 4px; font-size: 0.95rem; }
    #grid { display: flex; flex-wrap: wrap; gap: 12px; justify-content: center; }
    .card { background: #1e1e1e; border: 1px solid #333; padding: 10px; border-radius: 8px; text-align: center; width: 160px; }
    .sprite-name { font-weight: bold; text-transform: capitalize; margin-bottom: 4px; font-size: 0.95rem; }
    .dimensions { font-size: 0.8rem; color: #888; margin-bottom: 8px; }
    canvas { background: #000; image-rendering: pixelated; border-radius: 4px; border: 1px solid #333; display: block; margin: 0 auto; }
  </style>
</head>
<body>

  <header>
    <h1>PokéSprite Bead Art Maker (≤ 29×29)</h1>
    <div class="controls">
      <input type="text" id="search" placeholder="Search Pokémon..." oninput="filterSprites()" />
      <span id="status" style="color: #aaa; font-size: 0.9rem;">Loading...</span>
    </div>
  </header>

  <div id="grid"></div>

  <script>
    let allSprites = [];
    const scale = 5; // Bead pixel scale multiplier

    async function loadData() {
      const status = document.getElementById('status');
      try {
        const res = await fetch('pokesprite_29x29.json');
        if (!res.ok) throw new Error(`HTTP ${res.status}: Run the Python generator script first.`);
        allSprites = await res.json();
        status.innerText = `${allSprites.length} compatible sprites found.`;
        renderGrid(allSprites);
      } catch (err) {
        status.innerText = "Error: " + err.message;
        console.error(err);
      }
    }

    function renderGrid(list) {
      const grid = document.getElementById('grid');
      grid.innerHTML = '';

      list.forEach(item => {
        const card = document.createElement('div');
        card.className = 'card';
        card.innerHTML = `
          <div class="sprite-name">${item.name}</div>
          <div class="dimensions">${item.w}×${item.h} beads</div>
        `;

        const canvas = document.createElement('canvas');
        canvas.width = item.w * scale;
        canvas.height = item.h * scale;
        const ctx = canvas.getContext('2d');

        item.pixels.forEach((row, y) => {
          row.forEach((pixel, x) => {
            if (pixel) {
              ctx.fillStyle = `rgb(${pixel[0]}, ${pixel[1]}, ${pixel[2]})`;
              // "-1" leaves a 1px gap matching physical pegboard pegs
              ctx.fillRect(x * scale, y * scale, scale - 1, scale - 1);
            }
          });
        });

        card.appendChild(canvas);
        grid.appendChild(card);
      });
    }

    function filterSprites() {
      const q = document.getElementById('search').value.toLowerCase();
      const filtered = allSprites.filter(s => s.name.toLowerCase().includes(q));
      renderGrid(filtered);
    }

    loadData();
  </script>
</body>
</html>
```

## 6. How to Run Locally

```bash
cd /Users/mattslindstrom/code/pokemon-pearl-generator
python3 -m http.server 8080
```

Open in browser:
```text
http://localhost:8080/experiments/pokesprite_app.html
```

## 7. Next Recommended Features for Future Agents

### 1. iPad-Friendly Focus / Full-Screen View Mode
* **Goal:** Allow children to place an iPad next to or under their pegboard without UI distractions, accidental zooming, or navigation shifts.
* **Requirements:**
  * Clicking on any card opens a distraction-free, full-screen overlay/modal.
  * Hide search inputs, titles, and card headers.
  * Render the selected Pokémon centered on the screen scaled to large, comfortable touch dimensions.
  * Use touch-friendly controls: tap top corner to close, prevent accidental multi-touch pinch zoom (`touch-action: manipulation;`).
  * Support optional 1:1 screen-to-peg calibration (calibrating physical millimeters per bead so the iPad screen matches physical bead spacing).

### 2. Custom Home Inventory Color Quantization
* **Goal:** Map the original sprite colors to the physical bead buckets available at home (custom palette) or standard manufacturers (Hama, Nabbi, Artkal, Perler).
* **Requirements:**
  * Support a user-configurable JSON palette or color-picker list of "In-Stock Beads" (e.g., Red, Dark Blue, Light Blue, Black, White, Yellow, Orange, Green).
  * Color quantization algorithm: Map each sprite pixel's RGB tuple to the nearest available in-stock bead color using Euclidean distance or weighted RGB distance:
    $$\Delta C = \sqrt{2(R_1 - R_2)^2 + 4(G_1 - G_2)^2 + 3(B_1 - B_2)^2}$$
    *(or optionally convert to CIELAB $\Delta E$ for perceptually accurate color matching).*
  * Provide a toggle to switch between "Original Sprite Colors" and "Quantized In-Stock Beads".

### 3. "Bead-Pixel" Circular Rendering Mode
* **Goal:** Make the digital pattern resemble real beads instead of flat square pixels.
* **Requirements:**
  * Toggle between square pixels and round beads.
  * When rendering each bead at $(x, y)$:
    * Draw an outer filled circle (`ctx.arc(cx, cy, radius, 0, Math.PI * 2)`).
    * Draw a small dark inner circle at the center to emulate the bead's physical hole (`r_{inner} \approx 0.35 \times r_{outer}`).
    * Optional subtle radial gradient or soft rim stroke to simulate physical plastic beads on pegboard pegs.

### 4. Adjustable Grid Lines & Counting Separation
* **Goal:** Simplify counting rows and columns when placing beads onto the pegboard.
* **Requirements:**
  * Adjustable spacing slider (gap size between beads: 1px, 2px, 3px, 4px).
  * Major grid line emphasis: Draw thicker or high-contrast grid lines every **5 beads** (e.g. at peg positions 5, 10, 15, 20, 25) to make counting blocks fast and prevent misplacement mistakes.
  * Optional index coordinates along the top and left axes ($1 \dots 29$).

### 5. Bill of Materials (BOM) / Bead Counter
* Count and summarize required beads per color for the active sprite (e.g., "Black: 84 beads, Yellow: 142 beads, Red: 12 beads") so kids can count out their pieces before starting.