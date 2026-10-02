# Sprite Sheet Generation Prompts

Icons are generated one at a time via nano banana, then assembled into a sprite sheet by the packer script. When asking Claude for a prompt, it will be copied to clipboard automatically.

**Per-icon prompt template:**
```
Generate a single pixel art icon:
- Subject: [icon name and description]
- Size: 63×63px
- Background: transparent
- Style: 1985 NES pixel art — chunky, hard pixel edges, no anti-aliasing, no gradients, no partial transparency, black outline
- Palette: #5c94fc sky blue · #38a800 green · #d04000 brick red · #c8a850 tan · #ffffff white · #000000 black · #fcbc3c coin gold · #e40058 red
- Output: single PNG named [icon_name].png, no labels, no borders
```

**After generating all icons for a vibe:**
1. Drop all PNGs into `assets/sprites/<vibe>/`
2. Run: `python scripts/build_sprites.py <vibe>`
3. Outputs `src/static/sprites/<vibe>.png` + `<vibe>.json` automatically

Assembled sprite sheets go in `src/static/sprites/`.

---

## mario

**Status:** complete ✓

**Palette:** `#5c94fc` sky blue · `#38a800` green · `#d04000` brick red · `#c8a850` tan · `#ffffff` white · `#000000` black · `#fcbc3c` coin gold · `#e40058` red

**Icons** (38/38 complete):

Transportation:
- [x] `bus` — side view
- [x] `railway` — modern streetcar (side view, low-floor tram with flat front)
- [x] `airport` — plane
- [x] `ferry` — boat
- [x] `car` — top-down
- [x] `fuel` — gas pump
- [x] `parking` — P on block

Food & drink:
- [x] `restaurant` — crossed fork & knife
- [x] `cafe` — cup with steam
- [x] `fast_food` — burger
- [x] `bar` — beer mug
- [x] `bakery` — bread loaf

Nature:
- [x] `park` — tree
- [x] `mountain` — mountain
- [x] `campsite` — tent

Amenities:
- [x] `hospital` — red cross
- [x] `pharmacy` — green cross
- [x] `police` — star badge
- [x] `school` — building with flag
- [x] `bank` — dollar sign
- [x] `post` — envelope
- [x] `information` — letter i

Culture:
- [x] `museum` — columns
- [x] `cinema` — clapperboard
- [x] `lodging` — bed
- [x] `place_of_worship` — chapel silhouette

Markers:
- [x] `marker` — map pin
- [x] `circle` — filled circle
- [x] `star` — 5-point star
- [x] `dot_9` — filled dot, 9px
- [x] `dot_10` — filled dot, 10px
- [x] `dot_11` — filled dot, 11px

Road shields (draw as 63×63 square — packer resizes to final dims):
- [x] `road_1` — white badge, black border (final: 14×14)
- [x] `road_2` — white badge, black border (final: 20×14)
- [x] `road_3` — white badge, black border (final: 25×14)
- [x] `road_4` — white badge, black border (final: 31×14)
- [x] `road_5` — white badge, black border (final: 36×14)
- [x] `road_6` — white badge, black border (final: 40×14)

---

## tomclancy

**Status:** complete ✓

---

## metro

**Status:** complete ✓

**Style:** Victorian engraving — fine cross-hatched illustration, dark brown #3a2e1a ink on warm ivory #f0ebe0, amber gold #c4a86a accents. Antique cartographic feel.

**Road shields:** ornate gilded cartouches with cream interior, gold frames with scrollwork corners.

---

## mockva

**Status:** complete ✓

**Style:** Russian Constructivist (Rodchenko, El Lissitzky) — bold flat geometric forms, two colors only: #1a1a1a black and #cc1a1a red on #f0ece0 cream paper. No gradients, no shading. Sharp poster silhouettes.

**Road shields:** solid red rectangles with thin black borders, blank cream interior for road number overlay.

---

## deco

**Status:** complete ✓

**Style:** Art Deco (Chrysler Building, Erté, Bond title sequence) — symmetric geometric forms, gold #c9a84c fine linework on warm near-black #1a1008. Stepped ziggurat corners, radiating sunburst details, streamlined elegance.

**Road shields:** stepped-corner cartouches with thick gold frames and empty cream interior for text overlay.
