#!/usr/bin/env python3
"""
Build a MapLibre sprite sheet from individual source icon PNGs.

Usage:
    python scripts/build_sprites.py <vibe>

Reads from:  assets/sprites/<vibe>/<icon_name>.png  (63×63px each)
Outputs:     src/static/sprites/<vibe>.png
             src/static/sprites/<vibe>.json

Icons are resized to their target sizes using nearest-neighbor interpolation
(preserves hard pixel-art edges) and packed into a sprite sheet.
"""

import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw

# Layout — order determines position in the sprite sheet.
# Each sublist is a row of regular 21×21 icons.
ICON_ROWS = [
    ['bus', 'railway', 'airport', 'ferry', 'car', 'fuel', 'parking'],
    ['restaurant', 'cafe', 'fast_food', 'bar', 'bakery'],
    ['park', 'mountain', 'campsite'],
    ['hospital', 'pharmacy', 'police', 'school', 'bank', 'post', 'information'],
    ['museum', 'cinema', 'lodging', 'place_of_worship'],
    ['marker', 'circle', 'star', 'dot_9', 'dot_10', 'dot_11'],
]

# Road shields: (name, final_width, final_height)
ROAD_SHIELDS = [
    ('road_1', 14, 14),
    ('road_2', 20, 14),
    ('road_3', 25, 14),
    ('road_4', 31, 14),
    ('road_5', 36, 14),
    ('road_6', 40, 14),
]

ICON_SIZE = 21  # final size for regular icons
BG_TOLERANCE = 30  # max channel delta to consider a pixel "background"


def strip_background(img: Image.Image) -> Image.Image:
    """Flood-fill from all four corners to remove solid backgrounds.

    Handles white, grey, or any uniform color that nano banana bakes in
    instead of producing true transparency.
    """
    img = img.convert('RGBA')
    w, h = img.size
    pixels = img.load()

    def similar(a, b):
        return all(abs(int(a[i]) - int(b[i])) <= BG_TOLERANCE for i in range(3))

    visited = [[False] * h for _ in range(w)]
    queue = []
    for corner in [(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)]:
        cx, cy = corner
        if pixels[cx, cy][3] > 0:  # only flood opaque corners
            queue.append(corner)

    bg_color = pixels[0, 0]

    while queue:
        x, y = queue.pop()
        if x < 0 or x >= w or y < 0 or y >= h:
            continue
        if visited[x][y]:
            continue
        if pixels[x, y][3] == 0:
            continue
        if not similar(pixels[x, y], bg_color):
            continue
        visited[x][y] = True
        pixels[x, y] = (0, 0, 0, 0)
        queue.extend([(x+1, y), (x-1, y), (x, y+1), (x, y-1)])

    return img


def load_icon(path: Path) -> Image.Image:
    img = Image.open(path).convert('RGBA')
    # If any corner is opaque, assume a baked background and strip it
    w, h = img.size
    corners = [img.getpixel((0, 0)), img.getpixel((w-1, 0)),
               img.getpixel((0, h-1)), img.getpixel((w-1, h-1))]
    if any(c[3] > 0 for c in corners):
        img = strip_background(img)
    return img


def build_sprites(vibe: str) -> None:
    repo_root = Path(__file__).parent.parent
    src_dir   = repo_root / 'assets' / 'sprites' / vibe
    out_dir   = repo_root / 'src' / 'static' / 'sprites'
    out_dir.mkdir(parents=True, exist_ok=True)

    max_icon_width  = max(len(row) for row in ICON_ROWS) * ICON_SIZE
    road_total_width = sum(w for _, w, _ in ROAD_SHIELDS)
    canvas_w = max(max_icon_width, road_total_width)
    canvas_h = len(ICON_ROWS) * ICON_SIZE + ROAD_SHIELDS[0][2]

    canvas   = Image.new('RGBA', (canvas_w, canvas_h), (0, 0, 0, 0))
    manifest = {}
    missing  = []

    # Regular icons
    for row_idx, row in enumerate(ICON_ROWS):
        y = row_idx * ICON_SIZE
        for col_idx, name in enumerate(row):
            x = col_idx * ICON_SIZE
            path = src_dir / f'{name}.png'
            if not path.exists():
                missing.append(name)
                continue
            img = load_icon(path).resize((ICON_SIZE, ICON_SIZE), Image.NEAREST)
            canvas.paste(img, (x, y), img)
            manifest[name] = {
                'x': x, 'y': y,
                'width': ICON_SIZE, 'height': ICON_SIZE,
                'pixelRatio': 1,
            }

    # Road shields
    road_y = len(ICON_ROWS) * ICON_SIZE
    road_x = 0
    for name, w, h in ROAD_SHIELDS:
        path = src_dir / f'{name}.png'
        if not path.exists():
            missing.append(name)
            road_x += w
            continue
        img = load_icon(path).resize((w, h), Image.NEAREST)
        canvas.paste(img, (road_x, road_y), img)
        manifest[name] = {
            'x': road_x, 'y': road_y,
            'width': w, 'height': h,
            'pixelRatio': 1,
        }
        road_x += w

    canvas.save(out_dir / f'{vibe}.png')
    (out_dir / f'{vibe}.json').write_text(json.dumps(manifest, indent=2))

    print(f'OK  {out_dir}/{vibe}.png  ({canvas_w}×{canvas_h}px, {len(manifest)} icons)')
    print(f'OK  {out_dir}/{vibe}.json')
    if missing:
        print(f'MISSING ({len(missing)}): {", ".join(missing)}')


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Usage: python scripts/build_sprites.py <vibe>')
        sys.exit(1)
    build_sprites(sys.argv[1])
