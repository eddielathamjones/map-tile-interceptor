# map-tile-interceptor — Next Steps

## What this repo is

A proof-of-concept experiment exploring server-side raster tile transformation.
It proved out the concept of applying visual "vibes" to map tiles at request time.
The learnings feed directly into the pedestrian-safety-mapper flagship project.

## Portfolio reframing (Phase 2)

- [ ] Relabel as "Experiment: Tile Vibe Engine" in README and GitHub description
- [ ] Rewrite README to lead with the "experiment" narrative:
      - What question was being explored?
      - What was learned?
      - What did it become in the safety mapper?
- [ ] Add Ko-fi tip button
- [ ] Add GitHub Sponsors link
- [ ] Deploy self-hosted at `vibes.eddielathamjones.com` (always-on, no cold starts)
- [ ] Write Ghost portfolio post telling the experiment → flagship story

## What gets absorbed into safety mapper

The **concept** (map vibes) gets absorbed, not the code directly.

The safety mapper uses vector tiles — so vibes are implemented client-side as
MapLibre style JSON swaps. Much simpler than this repo's server-side PIL approach.

This repo remains the canonical demonstration of the more powerful server-side
raster approach — relevant for satellite/raster tile sources, AI-driven transforms,
and the `AI_SERVICE_URL` hook which has future potential.

## Future potential in this repo

- The AI hook (`AI_SERVICE_URL`) for routing vibes through an AI image transform
  is the most interesting unexplored feature — worth a dedicated experiment post
