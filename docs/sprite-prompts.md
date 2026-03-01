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

**Status:** in progress

**Palette:** `#5c94fc` sky blue · `#38a800` green · `#d04000` brick red · `#c8a850` tan · `#ffffff` white · `#000000` black · `#fcbc3c` coin gold · `#e40058` red

**Icons** (38 total — check off as generated):

Transportation:
- [x] `bus` — side view
- [x] `railway` — locomotive
- [x] `airport` — plane
- [x] `ferry` — boat
- [x] `car` — top-down
- [x] `fuel` — gas pump
- [x] `parking` — P on block

Food & drink:
- [ ] `restaurant` — crossed fork & knife
- [ ] `cafe` — cup with steam
- [ ] `fast_food` — burger
- [ ] `bar` — beer mug
- [ ] `bakery` — bread loaf

Nature:
- [ ] `park` — tree
- [ ] `mountain` — mountain
- [ ] `campsite` — tent

Amenities:
- [ ] `hospital` — red cross
- [ ] `pharmacy` — green cross
- [ ] `police` — star badge
- [ ] `school` — building with flag
- [ ] `bank` — dollar sign
- [ ] `post` — envelope
- [ ] `information` — letter i

Culture:
- [ ] `museum` — columns
- [ ] `cinema` — clapperboard
- [ ] `lodging` — bed
- [ ] `place_of_worship` — chapel silhouette

Markers:
- [ ] `marker` — map pin
- [ ] `circle` — filled circle
- [ ] `star` — 5-point star
- [ ] `dot_9` — filled dot, 9px
- [ ] `dot_10` — filled dot, 10px
- [ ] `dot_11` — filled dot, 11px

Road shields (draw as 63×63 square — packer resizes to final dims):
- [ ] `road_1` — white badge, black border (final: 14×14)
- [ ] `road_2` — white badge, black border (final: 20×14)
- [ ] `road_3` — white badge, black border (final: 25×14)
- [ ] `road_4` — white badge, black border (final: 31×14)
- [ ] `road_5` — white badge, black border (final: 36×14)
- [ ] `road_6` — white badge, black border (final: 40×14)

---

## tomclancy

**Status:** not started

---

## mockva

**Status:** not started

---

## deco

**Status:** not started

---

## metro

**Status:** not started
