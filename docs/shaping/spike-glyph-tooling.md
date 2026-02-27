---
shaping: true
---

# A1 Spike: Glyph PBF Generation Tooling

### Context

Shape A requires generating SDF glyph PBF files from TTF/OTF sources offline, committing them to the repo, and serving them from Flask. R5 requires Latin + basic punctuation only (~4–6 files per font). A1 is flagged because we don't yet know whether the available tooling supports range-limited generation, what the CLI looks like, or whether the output is valid for MapLibre.

### Goal

Identify the right tool, confirm it can produce Latin-range-only PBFs, and establish the exact steps needed to generate and validate a single font — so A1 can be unflagged and `scripts/generate_glyphs.sh` can be written with confidence.

---

### Questions

| # | Question |
|---|----------|
| **Q1** | Is `font-maker` (Node, `@elastic/font-maker`) actively maintained and what Node version does it require? |
| **Q2** | Is `pbf-font-builder` (Node, `@mapbox/pbf-font-builder`) a viable alternative — maintenance status, last release? |
| **Q3** | Does `font-maker` support range-limited generation (Latin + punctuation only), and if so, what is the CLI flag or config? |
| **Q4** | Does `pbf-font-builder` support range-limited generation, and if so, how? |
| **Q5** | What input formats do each tool accept — TTF only, or also OTF/WOFF2? |
| **Q6** | What does the output file structure look like — filenames, directory layout, naming conventions for the fontstack? |
| **Q7** | How large are the output PBF files for a typical sans-serif font at Latin range only? |
| **Q8** | How do we verify the output is valid for MapLibre without standing up a full Flask instance — is there a static file test or a known validator? |
| **Q9** | Does Google Fonts provide TTF downloads for all candidate fonts (Press Start 2P, Bebas Neue, Poiret One, OCR A Extended, IM Fell English, Share Tech Mono)? |

---

### Acceptance

Spike is complete when all questions are answered and we can describe:
- Which tool to use and the exact CLI invocation to generate Latin-range PBFs from a TTF
- The output file structure and naming convention for the fontstack path
- The approximate file size per font at Latin range
- How to confirm the output works in MapLibre before committing to the repo
- Any fonts from the candidate list not available as TTF from Google Fonts and what the fallback source is

---

## Findings

### Tool recommendation

**Use `build_pbf_glyphs` (Rust, Stadia Maps).** `cargo install build_pbf_glyphs`. No Node, no C++ build toolchain, no Node version constraints, actively maintained (latest `cli-v1.4.3`, July 2025), BSD-3-Clause license. Outputs clean uncompressed PBF.

`@elastic/font-maker` does not exist on npm — that was a package name confusion. `maplibre/font-maker` is a compiled WASM binary requiring Emscripten + CMake to build. `fontnik` (node-fontnik) is Node ≤16 only, effectively deprecated for new work.

**For quick one-off testing:** use the `maplibre/font-maker` web app at `maplibre.org/font-maker/` — drag-drop a TTF, download the ZIP, no CLI setup needed.

### Q1 — `@elastic/font-maker`
Does not exist. `@elastic/fontnik` (v0.1.0, ~2020) does exist but is abandoned. Not viable.

### Q2 — `@mapbox/pbf-font-builder`
Does not exist. `fontnik` (npm, `mapbox/node-fontnik`) is the correct Mapbox package — v0.7.4, July 2025, but Node ≤16 only. Not recommended for new work.

### Q3 — `font-maker` range-limited generation
No range flag. `maplibre/font-maker` CLI always generates full 256 files. Workaround: generate all, then prune with `find ... -delete`.

### Q4 — `fontnik` range-limited generation
Yes — via the Node API (`fontnik.range({ font, start, end })`). The CLI binary generates all ranges; the library allows selective generation. Not relevant given we're using `build_pbf_glyphs`.

### Q5 — Input formats
All tools: **TTF and OTF** via FreeType. No WOFF2 (decompress to TTF first with `fonttools` if needed). Google Fonts provides both TTF and variable TTF downloads.

### Q6 — Output file structure
```
src/static/glyphs/
└── {Font Name}/           # must match text-font in MapLibre style
    ├── 0-255.pbf
    ├── 256-511.pbf
    └── ...                # 256 files total (prune to Latin after generation)
```
Directory name = fontstack name. Range filenames always `{start}-{end}.pbf`.

### Q7 — File sizes at Latin range
- `0-255.pbf` (Basic Latin): ~80–130 KB for a typical sans-serif
- `256-511.pbf` (Latin Extended-A/B): ~40–90 KB
- **Total for Latin + punctuation (~3–5 files): ~200–350 KB per font weight**
- Press Start 2P (pixel font, sparse coverage): ~20–40 KB for `0-255.pbf`
- Full 256-file set: ~25–30 MB per font (pruning is worth it)

Latin-range pruning: keep `0-255.pbf`, `256-511.pbf`, `512-767.pbf`, and `8192-8447.pbf` (General Punctuation). Delete the rest.

### Q8 — Validation without Flask
```bash
cd src/static/glyphs && python3 -m http.server 8000
```
Then a minimal MapLibre HTML test page with `glyphs: 'http://localhost:8000/{fontstack}/{range}.pbf'` and a symbol layer using the font. No Flask needed.

**Caveat:** `fontnik` outputs gzip-compressed PBF. `build_pbf_glyphs` outputs uncompressed — no `Content-Encoding` issue with Python's server.

**Dynamic alternative:** `martin` tile server (`cargo install martin`) can serve fonts directly from TTF files on-the-fly — good for development iteration before committing PBFs.

### Q9 — Google Fonts TTF availability

| Font | Google Fonts | License | Notes |
|---|---|---|---|
| Press Start 2P | Yes | OFL 1.1 | Single weight |
| Bebas Neue | Yes | OFL 1.1 | Single weight, display only, no lowercase |
| Poiret One | Yes | OFL 1.1 | Single weight |
| IM Fell English | Yes | OFL 1.1 | Regular + Italic |
| Share Tech Mono | Yes | OFL 1.1 | Single weight |
| **OCR A Extended** | **No** | Public Domain | Not on Google Fonts — see below |

**OCR A Extended fallback:** SourceForge `ocr-a-font` project — ANSI X3.17 conformant TTF, Public Domain, last updated October 2020. Alternatively substitute `Share Tech Mono` (already in use for simcity/blueprint) — similar tech/terminal aesthetic without the OCR-A specificity.

### Additional tool found: `versatiles-glyphs-rs`
`cargo install versatiles_glyphs` — v0.8.0, February 2026, most recently updated tool in this space. Outputs metadata (`index.json`, `font_families.json`) alongside PBFs. Less battle-tested than `build_pbf_glyphs`.

---

## Decision

**Use `build_pbf_glyphs`.** Generate all ranges, prune to Latin. A1 flag is resolved.
