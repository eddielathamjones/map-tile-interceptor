# Nightly Claude Routine — Multi-Repo Issue Triage

This repo participates in a combined nightly routine that processes `claude`-labeled issues across all four GIS/web projects. The schedule entry is registered once on the equity mapper; see that repo's `.github/claude-routine.md` for the full prompt.

## This repo's context (for the routine)

- **Repo:** `eddielathamjones/map-tile-interceptor`
- **Working directory:** `/home/edwardlatham/repos/map-tile-interceptor`
- **Site:** `https://vibes.eddielathamjones.com/` (planned; may not be live)
- **Key files:**
  - `src/backend/app.py` — Flask routes, tile cache, PIL pipeline
  - `src/backend/transforms.py` — per-vibe image transforms
  - `src/backend/style_builder.py` — Liberty style JSON mutations
  - `src/frontend/index.html` — main page
  - `src/frontend/js/` — vibe config; vibes with `hidden: true` are not shown in UI
  - `src/frontend/css/` — styles
- **Deploy:** push to main triggers self-hosted GitHub Actions runner
- **Tests:** none yet

## Public reports

The site's Report button files issues labelled `report`, not `claude`. Anyone on the internet can write them, so the routine never reads them directly: a human reviews each one and re-labels it `claude` only if it should be worked on.

## How to file an issue for the routine

Label the issue `claude`. Paste the current URL + any relevant state (active vibe, console errors, screenshot) into the body. The routine reads this context to reproduce the problem.
