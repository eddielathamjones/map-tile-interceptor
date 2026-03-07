"""Serve pre-generated SDF glyph PBF files for per-vibe custom fonts."""

import logging
from functools import lru_cache
from pathlib import Path

from flask import Blueprint, Response, abort, send_from_directory

log = logging.getLogger(__name__)

glyphs_bp = Blueprint('glyphs', __name__, url_prefix='/api/glyphs')

_GLYPHS_DIR = Path(__file__).parent.parent / 'static' / 'glyphs'


@lru_cache(maxsize=None)
def _empty_glyph_pbf(fontstack_name: str, range_str: str) -> bytes:
    """Return a valid empty glyph range PBF (fontstack with no glyphs).

    MapLibre stalls/retries on 404 glyph responses; an empty-but-valid PBF
    tells it 'no glyphs in this range' so it can continue rendering.
    """
    def _varint(n: int) -> bytes:
        out = []
        while n > 0x7F:
            out.append((n & 0x7F) | 0x80)
            n >>= 7
        out.append(n)
        return bytes(out)

    def _field_bytes(num: int, data: bytes) -> bytes:
        return _varint((num << 3) | 2) + _varint(len(data)) + data

    fontstack_msg = _field_bytes(1, fontstack_name.encode()) + _field_bytes(2, range_str.encode())
    return _field_bytes(1, fontstack_msg)


@glyphs_bp.route('/<fontstack>/<range_str>.pbf')
def glyphs(fontstack: str, range_str: str) -> object:
    font_dir = _GLYPHS_DIR / fontstack
    if not font_dir.is_dir():
        abort(404)
    pbf_path = font_dir / f'{range_str}.pbf'
    if not pbf_path.exists():
        log.debug('glyph range missing, returning empty PBF: %s/%s', fontstack, range_str)
        return Response(_empty_glyph_pbf(fontstack, range_str), mimetype='application/x-protobuf')
    return send_from_directory(font_dir, f'{range_str}.pbf', mimetype='application/x-protobuf')
