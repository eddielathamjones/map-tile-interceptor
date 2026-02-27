# map-tile-interceptor

A Flask proxy that sits between a MapLibre map and its tile sources, applying visual style transforms ("vibes") at request time.

Vector layer colours are overridden per-vibe via modified Liberty style JSON. Raster underlay tiles are fetched from upstream, transformed with PIL, cached to disk, and served as PNG.

---

## How it works

```
Browser
  |
  ├─ GET /api/tiles/style/<vibe>     modified Liberty style JSON
  |      vector source: unchanged (MapLibre fetches direct)
  |      raster source: rewritten → /api/tiles/raster/<vibe>/{z}/{x}/{y}.png
  |
  └─ GET /api/tiles/raster/<vibe>/<z>/<x>/<y>.png
         check TILE_CACHE_DIR/raster/<vibe>/<z>/<x>/<y>.png
           HIT  → serve file
           MISS → fetch upstream PNG → PIL transform → cache → serve
```

---

## Vibes

| Vibe | Status | Description |
|---|---|---|
| default | active | Unmodified Liberty style, direct from OpenFreeMap |
| noir | active | Near-black teal-cast background, desaturated amber roads, warm cream labels |
| vintage | hidden | Sepia tones, warm paper background |
| toner | hidden | High-contrast black and white |
| blueprint | hidden | Dark navy, technical blue palette |
| dark | hidden | GitHub-style dark UI |
| watercolor | hidden | Soft, painterly pastels |
| highcontrast | hidden | Maximum contrast, accessibility-focused |

Hidden vibes are fully supported by the backend. To enable one, remove `hidden: true` from its entry in `src/frontend/js/app.js`.

---

## Running locally

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python -m src.backend.app
```

Open [http://localhost:5003](http://localhost:5003).

---

## Environment variables

| Variable | Default | Description |
|---|---|---|
| `TILE_CACHE_DIR` | `/tmp/tile_cache` | Disk cache root for transformed raster tiles |
| `PORT` | `5003` | Server port |
| `AI_SERVICE_URL` | — | Optional: POST endpoint for AI-based tile transforms |
| `AI_SERVICE_KEY` | — | Bearer token for AI service |
| `AI_VIBES` | — | Comma-separated list of vibes to route through AI (e.g. `watercolor`) |

Copy `.env.example` to `.env` to configure locally. The AI hook falls back to PIL on any failure.

---

## Pre-warming the cache

At zoom 0–4 there are 341 tiles per vibe. Pre-warm against a running instance:

```bash
python scripts/prewarm_tiles.py --base-url http://localhost:5003 --max-zoom 4
```

---

## Project structure

```
src/
  backend/
    app.py            Flask app + blueprint registration
    tiles.py          /api/tiles/style and /api/tiles/raster routes
    style_builder.py  Fetch Liberty JSON once; apply per-vibe colour overrides
    transforms.py     PIL transforms + optional AI hook
  frontend/
    index.html
    css/app.css
    js/app.js         VIBES dict, vibe picker, localStorage persistence
scripts/
  prewarm_tiles.py
docs/
  vibe-parameters.md  Full reference: what can and cannot be changed per vibe
```

---

## Open issues

- [#1 Custom sprite library](https://github.com/eddielathamjones/map-tile-interceptor/issues/1) — per-vibe icon sets using SDF sprites
- [#2 Custom font / glyph hosting](https://github.com/eddielathamjones/map-tile-interceptor/issues/2) — per-vibe typefaces via hosted PBF glyphs
