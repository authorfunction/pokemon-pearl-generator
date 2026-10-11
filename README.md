# Pokémon Bead Art Generator (Pärlplatta)

A web-based design and crafting companion for making Pokémon bead art on physical pegboards (standard $29 \times 29$ Hama / Nabbi / Perler MIDI boards).

![Pokémon Bead Art Generator](https://raw.githubusercontent.com/msikma/pokesprite/master/icons/pokemon/regular/pikachu.png)

## Features

- **730+ Compatible Pokémon**: Pre-filtered Gen 8 sprites from [`msikma/pokesprite`](https://github.com/msikma/pokesprite) with transparent margins trimmed via alpha bounding-box detection to fit within $\le 29 \times 29$ pegboards.
- **Kid-Friendly iPad Focus Mode**: Click/tap any card to enter a full-screen, distraction-free view with large beads, touch manipulation support, and zoom controls (`+` / `-`).
- **All Settings Accessible in Zoom Mode**: Change palettes, bead style (beads vs. squares), spacing gap, and grid lines directly while zoomed in without exiting.
- **Interactive Custom Palette Tuning**: Click any color swatch in the Bill of Materials sidebar to open a color picker and remap that bead color on-the-fly to whatever beads you have in your physical stash (with instant live preview and reset button).
- **Light & Dark Background Toggle**: Switch between dark background and light background (`#ececee`) to clearly distinguish black or dark outlines from the pegboard surface.
- **Realistic Bead (Donut) Rendering**: Outer bead ring with center peg hole, or classic square pixel mode.
- **Bill of Materials (BOM) / Bead Counter**: Live count of total beads required per color for each Pokémon.
- **Counting Helpers**:
  - Major grid guide lines accented every **5 pegs** to prevent placement mistakes.
  - Optional numerical peg coordinates ($1 \dots 29$) along the axes.
  - Adjustable bead spacing slider ($0\text{px}$ to $6\text{px}$).
- **Color Quantization (Palettes)**:
  - Original game sprite colors
  - Home Stash (Basic 12 colors)
  - Hama MIDI Classic assortment (30 colors)

---

## Quickstart

### 1. Run the Local Web Server

Start any static web server from the repository root:

```bash
python3 -m http.server 8080
```

Open in your browser (or on an iPad on the same local Wi-Fi):

```text
http://localhost:8080
```

---

## Data Pipeline & Rebuilding Manifest

The project includes `build_manifest.py`, which parses the local PokéSprite assets in `pokesprite/pokemon-gen8/regular/` and regenerates `sprites_29x29.json`:

```bash
python3 build_manifest.py
```

### Requirements
- Python 3.8+
- Pillow (`pip3 install pillow`)

---

## Project Structure

```text
pokemon-pearl-generator/
├── index.html                   # Production web application
├── build_manifest.py            # Offline sprite parser and manifest generator
├── sprites_29x29.json           # Precomputed sprite matrix manifest (732 Pokémon)
├── README.md                    # Documentation & instructions
├── documentation/               # Architectural retrospectives and specifications
│   ├── project_description.md
│   └── project_implementation_details.md
├── pokesprite/                  # Local clone of Gen 8 regular icons
│   └── pokemon-gen8/regular/
└── experiments/                 # Historical prototypes (Iteration 1 ANSI & early tests)
```
