# Mobius Dyson Ring Renderer
<img width="1200" height="928" alt="2025-12-08_11-29-05" src="https://github.com/user-attachments/assets/fc6b2bcd-4d4c-4f71-8551-052146ebd5ed" />

Render a stylized Dyson ring as a rotating wireframe with flickering starfield
backdrop. The camera uses an orthographic projection so the ring keeps its
scale while you yaw, pitch, and let it spin. The project now ships with both
the original Python/Pygame renderer and a dependency-free WebGPU single-page
version.

## Requirements

- Python 3.10+ (tested with 3.14)
- `pygame` (2.6.x) with SDL runtime
- `numpy`

Install the Python deps with pip:

```bash
python -m pip install pygame numpy
```

If you use a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\\Scripts\\activate
python -m pip install pygame numpy
```

## Running (Python build)

From the repo root:

```bash
python main.py
```

This opens a window, animates the ring, and displays HUD text with the current
Euler angles for pitch, yaw, and spin.

## What it does

- Tesselates a ring into beveled curved box segments, seeds each face with
  randomized red city lights, and rotates everything in 3D.
- Projects with an orthographic camera, painter-sorts faces, draws edges in
  neon green, and overlays a glowing central star.
- Generates a saturated, twinkling background starfield for atmosphere.

## Controls

- Drag left mouse button: yaw and pitch the view.
- `ESC`: quit.

## Notes

- The HUD uses `pygame.font.SysFont`. If the requested typeface is missing,
  Pygame falls back to an available system font automatically.
- On macOS you may need to allow the SDL window to receive input if prompted.

## WebGPU build (no dependencies)

The WebGPU version lives in `index.html` and runs entirely client-side with no
external libraries.

1. Use a browser with WebGPU enabled (Chrome 113+, Edge 113+, Safari TP, or
   Firefox Nightly with `dom.webgpu.enabled`).
2. Serve the repo as a static site (WebGPU requires HTTPS/localhost):
   ```bash
   python -m http.server 8000
   ```
3. Visit `http://localhost:8000/index.html`.
4. Drag with the mouse to yaw/pitch. Rotation speed and HUD readouts match the
   Python build.

Notes:

- The background stars and city lights run as instanced quads with additive
  blending, so performance scales well even on integrated GPUs.
- If the canvas is blank, make sure the browser reports `navigator.gpu` and
  that the page is served from `https://` or `http://localhost`.
- The WebGPU renderer painter-sorts every panel each frame so translucent
  faces stay in order. Close heavy tabs if you notice stutter.
