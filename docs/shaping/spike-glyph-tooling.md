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
