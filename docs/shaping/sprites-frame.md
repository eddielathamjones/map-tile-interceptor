---
shaping: true
---

# Sprite Generator — Frame

## Source

> a simple nano banana prompt is not working. might need to be separate prompts for each sprite that get stitched together with software, or something different. I need help and we kind of need to look at this with fresh eyes

> I want it generated with an ai tool. not sure which vibes will get sprites — want to do them one at a time. probably will end up with about 5 total, we will kind of test the colors and fonts and the really good ones that I like will get this functionality. once it is done and finalized I want it done, maybe a little tweaking during the formation process but I want to be able to finalize and be done

---

## Problem

AI image generation (nano banana) produces visually appealing pixel-art previews but not technically correct sprite sheets. The output is a large labeled preview image (~1408×768) rather than a compact packed PNG with icons at exact pixel coordinates. MapLibre requires precise coordinates — the PNG and JSON manifest must match exactly. A single prompt cannot reliably produce both good art and pixel-exact layout simultaneously.

---

## Outcome

A repeatable pipeline for generating a MapLibre-compatible sprite sheet for any given vibe. The pipeline uses AI for art generation and produces a finalized `<vibe>.png` + `<vibe>.json` that renders correctly in the browser. Once finalized, a vibe's sprites are done — no ongoing maintenance needed.
