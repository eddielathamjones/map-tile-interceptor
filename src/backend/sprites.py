"""Serve per-vibe sprite sheets (PNG + JSON manifest)."""
from pathlib import Path

from flask import Blueprint, send_from_directory

sprites_bp = Blueprint('sprites', __name__, url_prefix='/api/sprites')
_SPRITES_DIR = Path(__file__).parent.parent / 'static' / 'sprites'


@sprites_bp.route('/<vibe>.png')
def sprite_png(vibe: str) -> object:
    return send_from_directory(_SPRITES_DIR, f'{vibe}.png', mimetype='image/png')


@sprites_bp.route('/<vibe>.json')
def sprite_json(vibe: str) -> object:
    return send_from_directory(_SPRITES_DIR, f'{vibe}.json', mimetype='application/json')
