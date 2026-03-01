"""Serve pre-generated SDF glyph PBF files for per-vibe custom fonts."""

import logging
from pathlib import Path

from flask import Blueprint, abort, send_from_directory

log = logging.getLogger(__name__)

glyphs_bp = Blueprint('glyphs', __name__, url_prefix='/api/glyphs')

_GLYPHS_DIR = Path(__file__).parent.parent / 'static' / 'glyphs'


@glyphs_bp.route('/<fontstack>/<range_str>.pbf')
def glyphs(fontstack: str, range_str: str) -> object:
    font_dir = _GLYPHS_DIR / fontstack
    if not font_dir.is_dir():
        abort(404)
    filename = f'{range_str}.pbf'
    return send_from_directory(font_dir, filename, mimetype='application/x-protobuf')
