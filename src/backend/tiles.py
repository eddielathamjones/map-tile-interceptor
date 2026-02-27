import logging
import os
from pathlib import Path

import requests
from flask import Blueprint, Response, abort, jsonify, send_file

from .style_builder import build_style
from .transforms import transform

log = logging.getLogger(__name__)

tiles_bp = Blueprint('tiles', __name__, url_prefix='/api/tiles')

_CACHE_DIR = Path(os.environ.get('TILE_CACHE_DIR', '/tmp/tile_cache'))
_UPSTREAM  = 'https://tiles.openfreemap.org/natural_earth/ne2sr/{z}/{x}/{y}.png'
_VIBES     = frozenset({
    'default', 'vintage', 'toner', 'blueprint', 'dark', 'watercolor', 'highcontrast',
})


@tiles_bp.route('/style/<vibe>')
def style(vibe: str):
    if vibe not in _VIBES:
        abort(404)
    try:
        return jsonify(build_style(vibe))
    except Exception:
        log.exception('style build failed vibe=%s', vibe)
        abort(502)


@tiles_bp.route('/raster/<vibe>/<int:z>/<int:x>/<int:y>.png')
def raster(vibe: str, z: int, x: int, y: int):
    if vibe not in _VIBES:
        abort(404)

    cache_path = _CACHE_DIR / 'raster' / vibe / str(z) / str(x) / f'{y}.png'

    if cache_path.exists():
        return send_file(cache_path, mimetype='image/png')

    url = _UPSTREAM.format(z=z, x=x, y=y)
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        upstream = resp.content
    except Exception:
        log.exception('upstream tile fetch failed z=%d x=%d y=%d', z, x, y)
        abort(502)

    try:
        png = transform(vibe, upstream, z, x, y)
    except Exception:
        log.exception('transform failed vibe=%s z=%d x=%d y=%d', vibe, z, x, y)
        png = upstream

    try:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_bytes(png)
    except Exception:
        log.warning('cache write failed %s', cache_path)

    return Response(png, mimetype='image/png')
