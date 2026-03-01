"""Fetch the Liberty base style once; build per-vibe derivatives lazily."""

import copy
import logging
import threading

import requests

log = logging.getLogger(__name__)

_LIBERTY_URL = 'https://tiles.openfreemap.org/styles/liberty'

# (background, land, water, roads, labels)
_VIBE_COLORS: dict[str, tuple[str, str, str, str, str]] = {
    'vintage':      ('#f0e8d0', '#e8ddc0', '#c8d8d0', '#9b7b52', '#3a2a18'),
    'toner':        ('#ffffff', '#f5f5f5', '#c8c8c8', '#404040', '#000000'),
    'blueprint':    ('#1a3a6c', '#1e4080', '#0a1f5c', '#5588cc', '#dce8ff'),
    'dark':         ('#0d1117', '#161b22', '#0d1b2a', '#30363d', '#8b949e'),
    'watercolor':   ('#f5ede0', '#e8dbc8', '#b8ccd8', '#c09060', '#4a3020'),
    'highcontrast': ('#000000', '#111111', '#0033cc', '#ffee00', '#ffffff'),
    'noir':         ('#080e0d', '#0e1a18', '#0c1e30', '#8a7844', '#e8dfc8'),
    'mockva':       ('#f0ece0', '#e4ddd0', '#1a1a1a', '#cc1a1a', '#1a1a1a'),
    'mario':        ('#5c94fc', '#38a800', '#5c94fc', '#c8a850', '#ffffff'),
    'simcity':      ('#8a9a6a', '#7a8a5a', '#4a6a8a', '#a0a090', '#1a1a10'),
    'tomclancy':    ('#000a00', '#001500', '#000800', '#00cc33', '#00ff41'),
    'deco':         ('#1a1008', '#1e1a0e', '#0d1a2e', '#c9a84c', '#f5f0e8'),
    'metro':        ('#f0ebe0', '#e2d9c2', '#8ab4a8', '#c4a86a', '#3a2e1a'),
}

# (halo_color, halo_width) — applied to all symbol layers for the vibe
_VIBE_HALOS: dict[str, tuple[str, float]] = {
    'vintage':      ('#f0e8d0', 1.0),
    'toner':        ('#ffffff', 1.5),
    'blueprint':    ('#1a3a6c', 1.5),
    'dark':         ('#0d1117', 1.5),
    'watercolor':   ('#f5ede0', 1.0),
    'highcontrast': ('#000000', 2.0),
    'noir':         ('#080e0d', 1.5),
    'mockva':       ('#f0ece0', 1.5),
    'tomclancy':    ('#001a00', 1.5),
    'deco':         ('#1a1008', 1.5),
    'metro':        ('#f0ebe0', 1.0),
}

_VIBE_FONTS: dict[str, str] = {
    'mockva':       'Bebas Neue Regular',
    'mario':        'Press Start 2P Regular',
    'simcity':      'Share Tech Mono Regular',
    'tomclancy':    'Share Tech Mono Regular',   # OCR A Extended not available as TTF; Share Tech Mono is the fallback
    'deco':         'Poiret One Regular',
    'metro':        'IM Fell English Italic',
    'vintage':      'IM Fell English Regular',
    'blueprint':    'Share Tech Mono Regular',
    'watercolor':   'Caveat Regular',
    'toner':        'Inter Regular',
    'dark':         'Space Grotesk Regular',
    'highcontrast': 'Atkinson Hyperlegible Regular',
}

_LAND_KEYWORDS  = ('land', 'park', 'grass', 'green', 'wood', 'forest',
                   'vegetation', 'farmland', 'scrub', 'rock', 'sand', 'earth')
_WATER_KEYWORDS = ('water', 'lake', 'ocean', 'sea', 'river', 'wetland', 'stream')
_ROAD_KEYWORDS  = ('road', 'highway', 'motorway', 'trunk', 'street', 'path',
                   'bridge', 'tunnel', 'rail', 'transit', 'ferry')

_base_style: dict | None = None
_lock = threading.Lock()
_style_cache: dict[str, dict] = {}


def _fetch_base() -> None:
    global _base_style
    resp = requests.get(_LIBERTY_URL, timeout=15)
    resp.raise_for_status()
    _base_style = resp.json()
    log.info('Liberty style fetched (%d layers)', len(_base_style.get('layers', [])))


def _get_base() -> dict:
    global _base_style
    if _base_style is None:
        with _lock:
            if _base_style is None:
                _fetch_base()
    return _base_style  # type: ignore[return-value]


def build_style(vibe: str) -> dict:
    """Return a MapLibre style dict for the given vibe.

    For 'default' the base style is returned as-is.
    For all other vibes: raster source tiles URL is rewritten to our proxy,
    and vector layer paint colours are overridden per vibe.
    Built styles are cached — the layer walk only runs once per vibe.
    """
    if vibe in _style_cache:
        return _style_cache[vibe]

    base = _get_base()

    if vibe == 'default':
        _style_cache[vibe] = base
        return base

    style = copy.deepcopy(base)
    bg_col, land_col, water_col, road_col, label_col = _VIBE_COLORS[vibe]
    halo = _VIBE_HALOS.get(vibe)
    font = _VIBE_FONTS.get(vibe)

    # Rewrite raster underlay source → our proxy
    for src in style.get('sources', {}).values():
        if src.get('type') == 'raster':
            tiles = src.get('tiles', [])
            if tiles and 'ne2sr' in tiles[0]:
                src['tiles'] = [f'/api/tiles/raster/{vibe}/{{z}}/{{x}}/{{y}}.png']
                break

    # Override glyphs endpoint for vibes with custom fonts
    if font:
        style['glyphs'] = '/api/glyphs/{fontstack}/{range}.pbf'

    # Override vector layer colours and raster layer behaviour
    for layer in style.get('layers', []):
        ltype = layer.get('type', '')
        lid   = layer.get('id', '').lower()
        paint = layer.setdefault('paint', {})

        if ltype == 'raster':
            # Liberty fades the raster out by z6 and kills it at z7 — keep it
            # visible at all zoom levels for custom vibes.
            layer.pop('maxzoom', None)
            paint['raster-opacity'] = 0.85

        elif ltype == 'background':
            paint['background-color'] = bg_col

        elif ltype == 'fill':
            if any(k in lid for k in _WATER_KEYWORDS):
                paint['fill-color'] = water_col
            elif any(k in lid for k in _LAND_KEYWORDS):
                paint['fill-color'] = land_col

        elif ltype == 'line':
            if any(k in lid for k in _ROAD_KEYWORDS):
                paint['line-color'] = road_col

        elif ltype == 'symbol':
            # Shields: skip colour overrides (sprite background provides context)
            # but still override text-font — we've redirected the glyphs URL to
            # our server, so any layer left on Noto Sans will 404 and stall rendering.
            if 'shield' not in lid:
                paint['text-color'] = label_col
                if halo:
                    paint['text-halo-color'] = halo[0]
                    paint['text-halo-width'] = halo[1]
            if font:
                layout = layer.setdefault('layout', {})
                if 'text-font' in layout:
                    layout['text-font'] = [font]

    _style_cache[vibe] = style
    return style
