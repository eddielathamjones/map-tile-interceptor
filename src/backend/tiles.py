import io
import logging
import os
from pathlib import Path

import requests
from flask import Blueprint, Response, abort, jsonify, send_file
from PIL import Image

from .style_builder import build_style, list_vibes, vibe_exists
from .transforms import transform

log = logging.getLogger(__name__)

tiles_bp = Blueprint('tiles', __name__, url_prefix='/api/tiles')

_CACHE_DIR = Path(os.environ.get('TILE_CACHE_DIR', '/tmp/tile_cache'))
_UPSTREAM  = 'https://tiles.openfreemap.org/natural_earth/ne2sr/{z}/{x}/{y}.png'


def _make_empty_tile() -> bytes:
    buf = io.BytesIO()
    Image.new('RGBA', (256, 256), (0, 0, 0, 0)).save(buf, format='PNG')
    return buf.getvalue()

_EMPTY_TILE_PNG = _make_empty_tile()
del _make_empty_tile


@tiles_bp.route('/vibes')
def vibes():
    return jsonify(list_vibes())


@tiles_bp.route('/style/<vibe>')
def style(vibe: str):
    if not vibe_exists(vibe):
        abort(404)
    try:
        return jsonify(build_style(vibe))
    except Exception:
        log.exception('style build failed vibe=%s', vibe)
        abort(502)


@tiles_bp.route('/raster/<vibe>/<int:z>/<int:x>/<int:y>.png')
def raster(vibe: str, z: int, x: int, y: int):
    if not vibe_exists(vibe):
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
        log.warning('upstream tile fetch failed z=%d x=%d y=%d', z, x, y)
        return Response(_EMPTY_TILE_PNG, mimetype='image/png')

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
