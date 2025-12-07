# Mobius Dyson Ring Renderer

Render a stylized Dyson ring as a rotating wireframe with flickering starfield
backdrop. The camera uses an orthographic projection so the ring keeps its
scale while you yaw, pitch, and let it spin.

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

## Running

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
