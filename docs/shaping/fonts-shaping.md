---
shaping: true
---

# Custom Fonts — Shaping

---

## Shape A: Offline PBF generation + Flask static serve

Generate glyph PBF files offline from TTF/OTF sources, serve them from Flask, override the `glyphs` URL and `text-font` per vibe in `style_builder.py`.

| Part | Mechanism | Flag |
|------|-----------|:----:|
| **A1** | **Offline PBF generation** | ⚠️ |
| A1 | Run `font-maker` (Node) or `pbf-font-builder` against TTF/OTF source files → produces `.pbf` files per 256-glyph range. Output committed to repo or generated at build time. | ⚠️ |
| **A2** | **Flask static serve** | |
| A2 | Route at `/api/glyphs/{fontstack}/{range}.pbf` — reads pre-generated `.pbf` files from a static directory and serves them. No processing at request time. | |
| **A3** | **style_builder.py override** | |
| A3 | Per-vibe: override `glyphs` URL in style JSON to point to `/api/glyphs/...`. Override `text-font` in symbol layer `layout` properties for vibes with custom fonts. Vibes without custom fonts continue to point at OpenFreeMap's glyph server. | |
| **A4** | **Font selection** | |
| A4 | Choose one typeface per vibe from open-source candidates. Generate PBFs for Latin + basic punctuation ranges only (~4–6 files per font). | |
| **A5** | **Generation script** | |
| A5 | `scripts/generate_glyphs.sh` — downloads TTF from Google Fonts, runs `font-maker`, outputs PBFs to `src/static/glyphs/<fontstack>/`. Committed to repo. PBF output also committed so runtime has no Node dependency. | |

### Font candidates (from style-concepts.md + issue #2)

| Vibe | Candidate | Source |
|---|---|---|
| mario | Press Start 2P | Google Fonts |
| simcity | Share Tech Mono | Google Fonts |
| tomclancy | OCR A Extended or Share Tech Mono | Google Fonts |
| deco | Poiret One or Josefin Sans | Google Fonts |
| metro | IM Fell English Italic or Libre Baskerville | Google Fonts |
| mockva | Bebas Neue or Anton | Google Fonts |
| vintage | IM Fell English, Playfair Display | Google Fonts |
| blueprint | Share Tech Mono, Roboto Mono | Google Fonts |
| watercolor | Caveat, Patrick Hand | Google Fonts |
| toner | Inter, Source Sans | Google Fonts |
| dark | Space Grotesk, IBM Plex Sans | Google Fonts |
| highcontrast | Atkinson Hyperlegible | Google Fonts |

---

## Requirements (R)

| ID | Requirement | Status |
|----|-------------|--------|
| R0 | Each vibe can display map labels in a typeface matching its aesthetic | Core goal |
| R1 | Font rendering works in MapLibre GL JS (SDF PBF format required) | Must-have |
| R2 | Fonts served from this Flask app with no external CDN dependency at runtime — PBF files committed to repo | Must-have |
| R3 | Only open-source fonts (OFL or Apache 2.0) | Must-have |
| R4 | Vibes without custom fonts continue using the default OpenFreeMap glyph server unchanged | Must-have |
| R5 | PBF files cover Latin + basic punctuation only (~4–6 files per font, ~50–200KB total per font) | Must-have |
| R6 | PBF generation is reproducible via a committed script so fonts can be added or regenerated without archaeology | Must-have |
| R7 | At least one vibe ships as a working proof of concept before full rollout | Must-have |

---

## Fit Check: R × A

| Req | Requirement | Status | A |
|-----|-------------|--------|---|
| R0 | Each vibe can display map labels in a typeface matching its aesthetic | Core goal | ✅ |
| R1 | Font rendering works in MapLibre GL JS (SDF PBF format required) | Must-have | ✅ |
| R2 | Fonts served from this Flask app with no external CDN dependency at runtime — PBF files committed to repo | Must-have | ✅ |
| R3 | Only open-source fonts (OFL or Apache 2.0) | Must-have | ✅ |
| R4 | Vibes without custom fonts continue using the default OpenFreeMap glyph server unchanged | Must-have | ✅ |
| R5 | PBF files cover Latin + basic punctuation only (~4–6 files per font, ~50–200KB total per font) | Must-have | ❌ |
| R6 | PBF generation is reproducible via a committed script so fonts can be added or regenerated without archaeology | Must-have | ✅ |
| R7 | At least one vibe ships as a working proof of concept before full rollout | Must-have | ✅ |

**Notes:**
- A fails R5: A1 is flagged — we haven't confirmed whether `font-maker` / `pbf-font-builder` supports range-limited generation or always generates full Unicode. Needs a spike.
