# Style Concepts

Proposed new styles. Each entry covers: inspiration, PIL raster transform, vector color palette, font/sprite requirements, and overlay notes.

Status: design phase — not yet implemented.

---

## Open issues / prerequisites

Before any of these styles can be fully realised, three infrastructure gaps need resolving:

| Issue | Repo issue | Scope |
|---|---|---|
| Custom sprite library | [#1](https://github.com/eddielathamjones/map-tile-interceptor/issues/1) | Per-vibe icon sets using SDF sprites — required for mario, tomclancy, deco, metro, mockva |
| Custom font / glyph hosting | [#2](https://github.com/eddielathamjones/map-tile-interceptor/issues/2) | Per-vibe typefaces via hosted PBF glyphs — required for all styles below |
| Global CSS overlay | [#3](https://github.com/eddielathamjones/map-tile-interceptor/issues/3) | Compass rose, scale bar, decorative border — per-vibe styled HTML/SVG layer on top of the MapLibre canvas |

The PIL transforms and vector color palettes can be implemented now. Fonts, sprites, and the overlay are a second pass.

### Global CSS overlay

A fixed-position HTML/SVG layer rendered over the map, styled per vibe. Minimum components:

- **Compass rose** — north indicator; design language matches vibe (pixel, military reticle, art deco geometric, etc.)
- **Scale bar** — distance reference; typography and color per vibe
- **Decorative border** — optional; strong fit for deco, metro, mockva, mario

Each vibe entry below notes the overlay treatment.

---

### Naming note

The term "vibes" is used throughout the codebase. It is a placeholder — consider renaming to something more neutral before a public release (candidates: `filters`, `looks`, `presets`, `lenses`). Tracked here until a decision is made. <!-- TODO: resolve vibe naming -->

---

## mario

**Inspiration:** NES Super Mario Bros — 8-bit pixel art, hard-edged, primary colors, limited palette

**PIL:**
- `ImageOps.posterize(img, 3)` — 3 bits = 8 values per channel
- `ImageEnhance.Color(img).enhance(2.5)` — push saturation hard
- `ImageEnhance.Contrast(img).enhance(1.8)`

**Vectors:**

| Layer | Color | Notes |
|---|---|---|
| background | `#5c94fc` | NES sky blue |
| land | `#38a800` | NES green |
| water | `#5c94fc` | same as bg |
| roads | `#c8a850` | NES tan |
| buildings | `#d04000` | NES brick |
| labels | `#ffffff` | white, no halo |

**Font:** Press Start 2P — 8-bit pixel bitmap font (Google Fonts). Needs hosting as PBF glyphs via issue #2.

**Sprites:** pixel art 8-bit icons matching NES palette. POI icons, transit markers. Issue #1.

**Overlay:** pixel-art compass rose and scale bar. Chunky border — like a game UI frame. Black/white pixel style.

---

## simcity

**Inspiration:** SimCity (1989, DOS) — original Maxis release. Zoning-map color language on a muted 16-color DOS palette. Functional, not artistic. City planner, not game player.

Distinct from mario: less pixel-art, more planning-map. Muted olive tones, not saturated primary colors.

**PIL:**
- `ImageOps.posterize(img, 4)` — flatter than mario but not extreme
- `ImageEnhance.Color(img).enhance(0.85)` — desaturate slightly toward DOS palette
- `ImageEnhance.Contrast(img).enhance(1.1)`

**Vectors:**

| Layer | Color | Notes |
|---|---|---|
| background | `#8a9a6a` | olive DOS green |
| land | `#7a8a5a` | muted zoning green |
| water | `#4a6a8a` | blue-gray |
| roads | `#a0a090` | light gray asphalt |
| buildings | `#c8a030` | muted commercial yellow |
| labels | `#1a1a10` | near-black warm |

**Font:** Courier New or Share Tech Mono — DOS terminal feel. Existing system font, no hosting required initially.

**Sprites:** pixelated zoning icons (R/C/I markers). Issue #1.

**Overlay:** minimal; monochrome scale bar in Courier. No decorative border — keep it functional.

---

## tomclancy

**Inspiration:** 90s PVS-7 night vision phosphor — green monochrome, high contrast, military HUD. Rainbow Six / Splinter Cell aesthetic.

**PIL:**
- `img.convert('L')` — full desaturation
- Per-channel LUT: remap grayscale to phosphor green range
  - R: `0 → 0`, `255 → 30`
  - G: `0 → 10`, `255 → 200`
  - B: `0 → 0`, `255 → 30`
- `ImageEnhance.Contrast(img).enhance(2.0)`
- `ImageEnhance.Sharpness(img).enhance(1.8)`

**Vectors:**

| Layer | Color | Notes |
|---|---|---|
| background | `#000a00` | near-black green |
| land | `#001500` | |
| water | `#000800` | near-black |
| roads | `#00cc33` | phosphor green |
| buildings | `#003300` | dark green |
| labels | `#00ff41` | bright phosphor |
| label halo | `#001a00` | dark green |

**Font:** OCR A Extended or Share Tech Mono — military monospace. Needs PBF hosting (issue #2).

**Sprites:** tactical icons — crosshairs, military markers, grid references. Issue #1.

**Overlay:** targeting reticle compass rose. Scale bar in OCR font with tick marks. Possible corner brackets (HUD frame). Phosphor green on black.

---

## deco

**Inspiration:** Art deco / mid-century — Bond film title sequence aesthetic. Warm blacks, gold roads, cream labels, deep navy water. Geometric precision.

**PIL:**
- Per-channel LUT: warm tint (boost R/G, cut B)
  - R: scale × 1.05
  - G: scale × 1.0
  - B: scale × 0.78
- `ImageEnhance.Contrast(img).enhance(1.3)`
- `ImageEnhance.Sharpness(img).enhance(1.4)`

**Vectors:**

| Layer | Color | Notes |
|---|---|---|
| background | `#1a1008` | warm near-black |
| land | `#1e1a0e` | |
| water | `#0d1a2e` | deep navy |
| roads | `#c9a84c` | gold |
| buildings | `#2a2018` | dark warm brown |
| labels | `#f5f0e8` | cream |
| label halo | `#1a1008` | match bg |

**Font:** Poiret One or Josefin Sans — geometric art deco sans. Needs PBF hosting (issue #2).

**Sprites:** stylized geometric art deco icons. Issue #1.

**Overlay:** geometric compass rose with radiating lines — classical navigation rose redrawn in deco style. Gold on dark. Decorative border with deco corner motifs.

---

## metro

**Inspiration:** Paris Metro — Hector Guimard's Art Nouveau cast-iron entrances. Warm ivory paper, sage greens, amber roads, organic flowing warmth.

**PIL:**
- Per-channel LUT: warm paper tint
  - R: scale × 1.04
  - G: scale × 1.0
  - B: scale × 0.82
- `ImageEnhance.Color(img).enhance(0.75)` — slightly muted
- `ImageEnhance.Contrast(img).enhance(0.85)` — soft, low contrast

**Vectors:**

| Layer | Color | Notes |
|---|---|---|
| background | `#f0ebe0` | warm ivory |
| land | `#e2d9c2` | warm parchment |
| water | `#8ab4a8` | sage-teal |
| parks | `#8b9e6a` | sage green |
| roads | `#c4a86a` | amber |
| buildings | `#c8b898` | warm stone |
| labels | `#3a2e1a` | dark warm brown |

**Font:** IM Fell English Italic or Libre Baskerville — organic serif with period character. Needs PBF hosting (issue #2).

**Sprites:** Art Nouveau organic icons — stylized floral/botanical forms for POI markers. Issue #1.

**Overlay:** compass rose with organic flowing lines, leaf motifs. Decorative border — thin rule with corner flourishes. Amber/brown on ivory.

---

## mockva

**Inspiration:** Russian Constructivism — Rodchenko, El Lissitzky. Cream paper ground, red roads, black water and buildings. Flat, geometric, no naturalism.

**PIL:**
- `img.convert('L')` — full desaturation
- Per-channel LUT: remap grayscale to warm paper range
  - R: `0 → 42`, `255 → 240`
  - G: `0 → 34`, `255 → 232`
  - B: `0 → 24`, `255 → 216` — slight warmth
- `ImageOps.posterize(img, 3)` — flat, graphic, limited tones

**Vectors:**

| Layer | Color | Notes |
|---|---|---|
| background | `#f0ece0` | cream paper |
| land | `#e4ddd0` | slightly darker paper |
| water | `#1a1a1a` | black — graphic, flat |
| roads | `#cc1a1a` | constructivist red |
| buildings | `#1a1a1a` | black |
| labels | `#1a1a1a` | black |
| label halo | `#f0ece0` | match bg |

**Font:** Bebas Neue or Anton — bold condensed geometric sans. Constructivist posters used heavy block letterforms. Needs PBF hosting (issue #2).

**Sprites:** bold geometric icons — circles, arrows, diagonal bars. Red/black only. Issue #1.

**Overlay:** compass rose as a bold geometric star or directional arrow — no decorative flourish, pure form. Scale bar as a thick red rule with black tick marks. Optional thick red border rule around the map edge.
