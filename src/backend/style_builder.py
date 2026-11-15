"""Build per-vibe MapLibre styles: Liberty base + one map stylesheet per vibe.

Each vibe is `src/vibes/<name>.mcss` (see mapcss.py for the dialect). Files
whose name starts with `_` are shared partials for @import, not vibes.
"""

import json
import logging
import threading
from pathlib import Path

import requests

from . import mapcss

log = logging.getLogger(__name__)

_LIBERTY_URL = 'https://tiles.openfreemap.org/styles/liberty'
_VIBES_DIR = Path(__file__).parent.parent / 'vibes'
_SNAPSHOT = Path(__file__).parent.parent / 'static' / 'liberty.json'

_base_style: dict | None = None
_lock = threading.Lock()
# vibe -> (stylesheet mtimes, built style); rebuilt when any source file changes
_style_cache: dict[str, tuple[tuple, dict]] = {}


def _get_base() -> dict:
    global _base_style
    if _base_style is None:
        with _lock:
            if _base_style is None:
                try:
                    resp = requests.get(_LIBERTY_URL, timeout=15)
                    resp.raise_for_status()
                    _base_style = resp.json()
                except Exception:
                    log.warning('Liberty fetch failed; using bundled snapshot', exc_info=True)
                    _base_style = json.loads(_SNAPSHOT.read_text(encoding='utf-8'))
                log.info('Liberty style loaded (%d layers)', len(_base_style.get('layers', [])))
    return _base_style


def _sheet_path(vibe: str) -> Path:
    return _VIBES_DIR / f'{vibe}.mcss'


def list_vibes() -> list[dict]:
    """All vibes, in picker order: [{id, label}], with 'default' first."""
    vibes = []
    for path in _VIBES_DIR.glob('*.mcss'):
        if path.name.startswith('_'):
            continue
        meta = mapcss.parse(path).meta
        vibes.append((float(meta.get('order', 100)), path.stem, meta.get('label', path.stem.title())))
    vibes.sort()
    return [{'id': 'default', 'label': 'Default'}] + [{'id': v, 'label': label} for _, v, label in vibes]


def vibe_exists(vibe: str) -> bool:
    return vibe == 'default' or (vibe.isidentifier() and _sheet_path(vibe).is_file())


def _uses_fx(node) -> bool:
    if isinstance(node, str):
        return node.startswith('fx:')
    if isinstance(node, dict):
        return any(_uses_fx(v) for v in node.values())
    if isinstance(node, list):
        return any(_uses_fx(v) for v in node)
    return False


def build_style(vibe: str) -> dict:
    """Return the MapLibre style dict for a vibe ('default' is Liberty as-is)."""
    base = _get_base()
    if vibe == 'default':
        return base

    sheet = mapcss.parse(_sheet_path(vibe))
    stamp = tuple(p.stat().st_mtime_ns for p in sheet.files)
    cached = _style_cache.get(vibe)
    if cached and cached[0] == stamp:
        return cached[1]

    style = mapcss.apply_sheet(base, sheet)

    # Raster underlay goes through our proxy so transforms.py can restyle it.
    for src in style.get('sources', {}).values():
        if src.get('type') == 'raster' and 'ne2sr' in (src.get('tiles') or [''])[0]:
            src['tiles'] = [f'/api/tiles/raster/{vibe}/{{z}}/{{x}}/{{y}}.png']

    # Every label was moved to the vibe font, so glyphs must come from us.
    if sheet.meta.get('font'):
        style['glyphs'] = '/api/glyphs/{fontstack}/{range}.pbf'

    # `sprite:` swaps the whole icon sheet for one of ours.
    sprite = sheet.meta.get('sprite')
    if sprite:
        style['sprite'] = f'/api/sprites/{sprite}'
        for layer in style['layers']:
            layout = layer.get('layout', {})
            if layer['id'] == 'airport' and layout.get('icon-image') == 'airport_11':
                layout['icon-image'] = 'airport'
            # Liberty builds 'us-interstate_N' etc; our sheets only have road_N.
            # Leave it alone if the stylesheet already chose its own shield.
            elif (layer['id'] in ('highway-shield-us-interstate', 'road_shield_us')
                  and 'network' in json.dumps(layout.get('icon-image'))):
                layout['icon-image'] = ['concat', 'road_', ['get', 'ref_length']]

    # Patterns and extra icons referenced as `fx:name` live in a second sheet.
    if _uses_fx(style['layers']):
        style['sprite'] = [{'id': 'default', 'url': style['sprite']},
                           {'id': 'fx', 'url': '/api/sprites/fx'}]

    _style_cache[vibe] = (stamp, style)
    return style
