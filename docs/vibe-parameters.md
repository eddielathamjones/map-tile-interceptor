# Vibe Parameter Reference

Parameters available when defining a vibe. Grouped by system.

---

## 1. Vector layers — `paint` properties

Set in `style_builder.py` per vibe. Override any MapLibre paint property by matching layer type and ID pattern.

### Background

| Property | Type | Effect |
|---|---|---|
| `background-color` | color | Base canvas color behind all layers |
| `background-opacity` | 0–1 | Fade the background (rarely needed) |

### Fill layers (land, water, parks, buildings)

| Property | Type | Effect |
|---|---|---|
| `fill-color` | color | Primary fill color |
| `fill-opacity` | 0–1 | Transparency of the fill |
| `fill-outline-color` | color | 1px border around fill polygons |
| `fill-antialias` | bool | Smooth polygon edges (default true) |

> **Layer groups:** land · water · park/green · building · landuse

### Line layers (roads, borders, rivers)

| Property | Type | Effect |
|---|---|---|
| `line-color` | color | Stroke color |
| `line-width` | px | Stroke width (can use expressions for zoom-dependent scaling) |
| `line-opacity` | 0–1 | Transparency |
| `line-blur` | px | Soften edges (glow effect at higher values) |
| `line-dasharray` | [px, px, …] | Dashed lines — good for vintage/blueprint |
| `line-gap-width` | px | Casing width (renders a second stroke outside the main line) |

> **Layer groups:** road · highway · path · border · waterway · rail

### Symbol layers (labels, POI icons)

| Property | Type | Effect |
|---|---|---|
| `text-color` | color | Label text color |
| `text-halo-color` | color | Halo/glow around text — critical for readability |
| `text-halo-width` | px | Halo radius (0 = off, 1–2 = standard, 3+ = heavy glow) |
| `text-halo-blur` | px | Blur the halo edge |
| `text-opacity` | 0–1 | Fade all labels (0 = labels-off vibe) |
| `icon-color` | color | Recolor SDF icons (only works with SDF sprites) |
| `icon-opacity` | 0–1 | Fade icons |

---

## 2. Vector layers — `layout` properties

Also set in `style_builder.py`. Less commonly changed.

| Property | Layer type | Effect | Constraint |
|---|---|---|---|
| `visibility` | any | `'visible'` or `'none'` — hide entire layer categories | None |
| `text-font` | symbol | Font family for labels | Must exist in the glyphs source |
| `text-size` | symbol | Label size in px | Can use zoom expressions |
| `text-transform` | symbol | `'uppercase'`, `'lowercase'`, `'none'` | None |

### Fonts

Font names come from the `glyphs` PBF endpoint defined in the style. The Liberty style uses **OpenFreeMap's glyph server**, which provides:

- Noto Sans Regular / Bold / Italic
- Standard OpenMapTiles stack variants

**To use custom fonts:** generate `.pbf` glyph tiles from a TTF (e.g. with `font-maker`), serve from Flask at `/api/glyphs/{fontstack}/{range}.pbf`, and override the `glyphs` URL in the style JSON. This is a separate project (medium effort).

---

## 3. Raster tiles — PIL transforms

Applied in `transforms.py` to the **ne2_shaded** Natural Earth underlay (256×256 PNG tiles). Any PIL operation is valid.

| Operation | API | Notes |
|---|---|---|
| Brightness | `ImageEnhance.Brightness(img).enhance(f)` | f < 1 = darker, f > 1 = brighter |
| Contrast | `ImageEnhance.Contrast(img).enhance(f)` | f = 0 → grey, f > 1 → punchy |
| Saturation / color | `ImageEnhance.Color(img).enhance(f)` | f = 0 → greyscale, f > 1 → vivid |
| Sharpness | `ImageEnhance.Sharpness(img).enhance(f)` | f = 0 → blurred, f = 2 → sharpened |
| Greyscale | `img.convert('L').convert('RGB')` | Full desaturation |
| Invert | `ImageOps.invert(img)` | Flip pixel values |
| Sepia matrix | `getdata()` / `putdata()` | Full 3×3 cross-channel mix |
| Per-channel LUT | `channel.point(lut_list)` | Remap 0–255 → any range per R/G/B channel |
| Gaussian blur | `img.filter(ImageFilter.GaussianBlur(r))` | Soft/painterly effect |
| Unsharp mask | `img.filter(ImageFilter.UnsharpMask(...))` | Crisp detail enhancement |
| Posterize | `ImageOps.posterize(img, bits)` | Reduce color depth (2–8 bits) |
| Solarize | `ImageOps.solarize(img, threshold)` | Invert pixels above threshold |
| Hue rotation | HSV round-trip via `colorsys` | Shift terrain colors to any hue |
| Paper grain overlay | `Image.blend()` with noise texture | Tactile texture for vintage/watercolor |
| Color temperature | Per-channel LUT (warm = boost R, reduce B) | Sunrise / cool / warm presets |

---

## 4. Style-level properties

Set at the top of the style JSON. Override in `style_builder.py`.

| Property | Effect | Constraint |
|---|---|---|
| `sprite` | URL to sprite sheet PNG + JSON manifest | Requires hosting sprites; see issue #1 |
| `glyphs` | URL template for font PBF tiles | Requires hosting glyph PBFs for custom fonts |
| `light` | Ambient + directional light for 3D layers | Only affects 3D extrusion layers |
| `fog` | Atmospheric depth haze | MapLibre 3.x+ only |

---

## 5. Fixed — cannot change

| Thing | Why |
|---|---|
| Vector geometry | Road paths, coastlines, building footprints are baked into the tiles from OpenFreeMap |
| Tile projection | Spherical Mercator, determined by the tile scheme |
| ne2_shaded content | Natural Earth shaded relief — pixel colors transform, but terrain shape is fixed |
| Icon shapes (default sprites) | Sprite sheet from OpenFreeMap; need custom sprites (issue #1) to change |
| Zoom levels / tile grid | Fixed by the XYZ tile standard |

---

## Current vibe definitions (quick ref)

| Vibe | bg | land | water | roads | labels |
|---|---|---|---|---|---|
| default | — | — | — | — | — |
| vintage | `#f0e8d0` | `#e8ddc0` | `#c8d8d0` | `#9b7b52` | `#3a2a18` |
| toner | `#ffffff` | `#f5f5f5` | `#c8c8c8` | `#404040` | `#000000` |
| blueprint | `#1a3a6c` | `#1e4080` | `#0a1f5c` | `#5588cc` | `#dce8ff` |
| dark | `#0d1117` | `#161b22` | `#0d1b2a` | `#30363d` | `#8b949e` |
| watercolor | `#f5ede0` | `#e8dbc8` | `#b8ccd8` | `#c09060` | `#4a3020` |
| highcontrast | `#000000` | `#111111` | `#0033cc` | `#ffee00` | `#ffffff` |

**Not yet set per-vibe:** `text-halo-color`, `text-halo-width`, `fill-opacity`, `line-width`, `line-dasharray`
