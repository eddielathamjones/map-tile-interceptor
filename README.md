# map-tile-interceptor

An exercise in cartography as a stylesheet. A Flask proxy sits between a MapLibre map and its tile sources and restyles the map per "vibe". Each vibe is one CSS-like file.

---

## How it works

```
Browser
  |
  ├─ GET /api/tiles/vibes            list of vibes (one per stylesheet)
  ├─ GET /api/tiles/style/<vibe>     Liberty style JSON + src/vibes/<vibe>.mcss
  ├─ GET /api/glyphs/...             per-vibe label fonts (SDF PBFs)
  ├─ GET /api/sprites/...            per-vibe icon sheets + shared `fx` patterns
  └─ GET /api/tiles/raster/<vibe>/<z>/<x>/<y>.png
         Natural Earth relief, PIL-transformed per vibe, cached to disk
```

The Liberty base style is fetched from OpenFreeMap at startup; if that fails, the bundled snapshot in `src/static/liberty.json` is used.

---

## Vibes are stylesheets

`src/vibes/<name>.mcss` is compiled onto the Liberty style by `src/backend/mapcss.py`. Edit a file and reload the page; styles rebuild when the file changes.

```css
@vibe { label: "Field Day"; order: 1; font: "Fredoka SemiBold"; }
:root { --ink: #1D1F23; }

water                { color: #617FB4; }
water::after         { type: line; color: var(--ink); width: zoom(4 1, 16 4); }
road.casing          { color: var(--ink); width: zoom(exp 1.4, 8 3, 18 34); }
road.motorway:not(.casing) { color: #E8B13A; }
#building::before    { color: var(--ink); translate: 3 3; }   /* hard drop shadow */
label.place          { transform: uppercase; spacing: 0.12; }
```

**Selectors**

| Part | Matches |
|---|---|
| element | `background` `raster` `water` `waterway` `park` `landuse` `landcover` `building` `road` `rail` `aeroway` `boundary` `label`, or `*` |
| `.class` | any `_`/`-` token of the Liberty layer id (`motorway`, `casing`, `tunnel`, `wood`, `city` ...), the layer type (`fill` `line` `symbol` `extrusion`), and for labels the kind (`place` `poi` `road` `shield` `water` `airport`) |
| `#id` | exact Liberty layer id |
| `:not(.class)` | exclusion |
| `::before` `::after` | a generated layer under / over the match, sharing its source and filter. `type: line` on a fill draws its outline as a real stroke |

Specificity and source order work as in CSS.

**Properties.** Short names resolve per layer type: `color` `opacity` `width` `outline` `pattern` `dash` `gap` `blur` `cap` `join` `translate` `halo` `font` `size` `transform` `spacing` `icon` `icon-scale` `text` `display` `minzoom` `maxzoom` `filter`. Any real MapLibre paint or layout property name also works. `unset` removes a property inherited from Liberty.

**Values.** `var(--x, fallback)`, `zoom(8 1, 18 16)` (linear) or `zoom(exp 1.4, 8 1, 18 16)`, `json([...])` for a raw MapLibre expression, and space-separated number lists.

**`@vibe` block.** `label` and `order` drive the picker; `font` moves every label to a hosted glyph set; `sprite` swaps the whole icon sheet. Images named `fx:<name>` come from the shared pattern sheet drawn by `scripts/build_fx_sprites.py`.

Files starting with `_` are partials for `@import`. Every vibe imports `_shared.mcss` first: fixes to Liberty defaults that apply everywhere (transit-label density, small-water label size, park edge colour, boundaries and tunnel rail over water). A vibe's own rules still win when they set the same property.

---

## Vibes

| Vibe | Description |
|---|---|
| Field Day | The kids' register of the ELJ brand: paper ground, a sheet of pastel sticker buildings, pop-up-book 3D, red race-track motorways, place names on sticker plates, chalked pitches and prize ribbons |
| Nouveau | Mucha-poster Paris: pale stained-glass blocks with ink leading, mosaic 3D, peacock water and stem-like rivers, gilded halos behind cities, Glass Antiqua lettering, a whiplash frame; Effects: poster mode |
| Mario | 8-bit overworld: tiled grass, animated water, pixel roads with brick highways, coin trails, pipes for subway stops, place names on title cards; Effects: four building treatments, sound |
| Mario Underground | The same rules after dark: black ground, blue-grey blocks, cyan water |
| Tom Clancy | Phosphor tactical display: road brightness by importance, glow, scanlines, contact-marker POIs with amber for health, grid-reference ticks, banner strips with a live Zulu time, radar sweep, target lock on click; Effects: Sentinel-2 satellite pass |
| Mockva | Constructivist poster in three inks: black mass, red streets on grained paper, misregistered second pass, Cyrillic slab labels tilted off true, towers that are black or red, a red wedge |
| Blueprint | Drafting sheet: ruled grid, hollow double-line roads with centre lines, line-only footprints, hatched water, crosshatched parks, dimension-line labels, one redline colour, an aged folded print, roads that plot themselves in |
| Deco | Gold on black lacquer: fish-scale water with a double gold shoreline, bronze chevron parks, inlaid gold motorways, towers with gilded crowns, sunburst landmarks, a passing gold sheen |
| Noir | The city at 2 a.m.: sodium-lit roads with glow and a wet sheen, lit windows in 3D, Venetian-blind light, a case-file menu, crime-scene pins on click; Effects: rain |

The chrome around the map (menu, compass, scale bar, frame) is themed per vibe in `src/frontend/css/app.css`. The menu (top left) holds the vibe picker, POI toggles, per-vibe effects, export and issue reporting. Effects that a stylesheet can't express (overlays, animation, click behaviours, extra sources) live in `src/frontend/js/fx.js`, one function per vibe. 3D buildings fade in as the map tilts; top-down, every vibe shows its flat footprints.

**Export.** *Save image* and *Print* compose a finished sheet in the vibe's own colours and type: the map at 2x resolution inside a neat line, and a title band with the place name (taken from the nearest prominent place label, or typed in), coordinates, vibe and date, compass, scale bar and attribution.

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

## Adding a font or pattern

- **Font:** `npx -p fontnik build-glyphs <font.ttf> <outdir>`, copy the `0-255`, `256-511`, `512-767` and `8192-8447` ranges to `src/static/glyphs/<Font Name>/`, then set `font: "<Font Name>"` in the vibe. (`scripts/generate_glyphs.sh` does the same with `build_pbf_glyphs`.)
- **POI icon:** add a `class: [mdi-name, codepoint]` entry to `assets/fonts/mdi-icons.json`, re-subset `mdi-subset.ttf` from `@mdi/font` to include it, and rerun `scripts/build_fx_sprites.py`. Every vibe's badge set (`fx:fd-*`, `fx:sv-*`, `fx:svn-*`, `fx:nv-*`) is redrawn.
- **Pattern or other image:** add a drawing function to `scripts/build_fx_sprites.py`, run it, and reference the result as `fx:<name>`.

---

## Project structure

```
src/
  vibes/              one .mcss stylesheet per vibe (+ _shared.mcss partial)
  backend/
    app.py            Flask app + blueprint registration
    mapcss.py         stylesheet parser and compiler
    style_builder.py  Liberty base + stylesheet -> style JSON, cached per file mtime
    tiles.py          /api/tiles/vibes, /style and /raster routes
    transforms.py     PIL transforms for the raster underlay + optional AI hook
    glyphs.py, sprites.py
  frontend/           index.html, css/app.css (per-vibe chrome), js/app.js, js/fx.js (per-vibe effects)
  static/             glyph PBFs, sprite sheets, liberty.json snapshot
scripts/
  build_fx_sprites.py draws the shared pattern/icon sheet
  build_sprites.py    packs a full icon sheet from assets/sprites/<vibe>/
  prewarm_tiles.py
assets/fonts/         OFL TTFs used for glyphs and drawn sprites
tests/test_mapcss.py
```

---

## Open issues

- [#1 Custom sprite library](https://github.com/eddielathamjones/map-tile-interceptor/issues/1) — per-vibe icon sets using SDF sprites
- [#2 Custom font / glyph hosting](https://github.com/eddielathamjones/map-tile-interceptor/issues/2) — per-vibe typefaces via hosted PBF glyphs
