#!/usr/bin/env python3
"""Draw the shared `fx` sprite sheet: fill patterns and small icons that the
map stylesheets reference as `fx:<name>`.

Everything is drawn in code (no source art), at 2x for retina. POI glyphs
come from a subset of Material Design Icons (assets/fonts/mdi-subset.ttf,
Apache 2.0; class -> icon map in assets/fonts/mdi-icons.json).

    python scripts/build_fx_sprites.py
    -> src/static/sprites/fx.png, fx.json
"""

import json
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).parent.parent
OUT = ROOT / 'src' / 'static' / 'sprites'
FONTS = ROOT / 'assets' / 'fonts'
R = 2          # pixel ratio of the sheet
SS = 4         # supersampling for smooth shapes


def canvas(w: int, h: int, bg=(0, 0, 0, 0)):
    """A supersampled canvas for a w×h (CSS px) sprite."""
    img = Image.new('RGBA', (w * R * SS, h * R * SS), bg)
    return img, ImageDraw.Draw(img), R * SS


def done(img: Image.Image) -> Image.Image:
    return img.resize((img.width // SS, img.height // SS), Image.LANCZOS)


def pixel_art(rows: list[str], palette: dict[str, str], scale: int = 2) -> Image.Image:
    """Rows of palette keys -> crisp sprite; each cell is `scale` CSS px."""
    img = Image.new('RGBA', (len(rows[0]), len(rows)))
    for y, row in enumerate(rows):
        for x, key in enumerate(row):
            img.putpixel((x, y), _rgba(palette[key]))
    return img.resize((img.width * scale * R, img.height * scale * R), Image.NEAREST)


def _rgba(hex_color: str):
    h = hex_color.lstrip('#')
    alpha = int(h[6:8], 16) if len(h) == 8 else 255
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) + (alpha,)


# ── Field Day: sticker dots ──────────────────────────────────────────────────

INK = '#1D1F23'


def fd_dot(fill: str) -> Image.Image:
    img, d, k = canvas(18, 18)
    d.ellipse([4 * k, 4 * k, 17 * k, 17 * k], fill=INK)                      # hard shadow
    d.ellipse([1 * k, 1 * k, 15 * k, 15 * k], fill=fill, outline=INK, width=2 * k)
    return done(img)


# ── POI icon sets: Material Design Icons glyphs on a per-vibe badge ──────────

MDI = json.loads((FONTS / 'mdi-icons.json').read_text())      # poi class -> [icon name, codepoint]

FOOD = {'restaurant', 'cafe', 'fast_food', 'bar', 'beer', 'bakery', 'ice_cream', 'grocery', 'alcohol_shop'}
NATURE = {'park', 'garden', 'playground', 'pitch', 'stadium', 'swimming', 'swimming_pool', 'sports_centre',
          'golf', 'zoo', 'aquarium', 'dog_park', 'campsite', 'picnic_site'}
CULTURE = {'school', 'college', 'library', 'museum', 'art_gallery', 'cinema', 'theatre', 'music',
           'attraction', 'castle', 'monument', 'place_of_worship', 'town_hall'}
HEALTH = {'hospital', 'doctors', 'dentist', 'pharmacy', 'police', 'fire_station'}
TRANSPORT = {'bus', 'railway', 'airport', 'ferry_terminal', 'harbor', 'bicycle', 'bicycle_rental',
             'bicycle_parking', 'fuel', 'parking'}


def _glyph(d, k, cx, cy, codepoint: str, size: float, fill: str) -> None:
    font = ImageFont.truetype(str(FONTS / 'mdi-subset.ttf'), int(size * k))
    d.text((cx * k, cy * k), chr(int(codepoint, 16)), font=font, fill=fill, anchor='mm')


def fd_icon(cls: str, codepoint: str) -> Image.Image:
    """Field Day: sticker disc coloured by kind, ink outline, hard ink shadow."""
    fill, fg = ('#FFFFFF', INK)
    if cls in FOOD: fill = '#E8B13A'
    elif cls in NATURE: fill = '#A9BF84'
    elif cls in CULTURE: fill, fg = '#2350A0', '#FFFFFF'
    elif cls in HEALTH: fill, fg = '#D33A2C', '#FFFFFF'
    elif cls in TRANSPORT: fill = '#869FCB'
    img, d, k = canvas(26, 26)
    d.ellipse([4 * k, 4 * k, 26 * k, 26 * k], fill=INK)
    d.ellipse([1 * k, 1 * k, 23 * k, 23 * k], fill=fill, outline=INK, width=2 * k)
    _glyph(d, k, 12, 12, codepoint, 14, fg)
    return done(img)


def flat_icon(codepoint: str, disc: str, ring: str, fg: str, ring_w: float = 1.2) -> Image.Image:
    """A quiet badge: disc, thin ring, glyph. Used by Nouveau, Blueprint and Noir."""
    img, d, k = canvas(20, 20)
    d.ellipse([1 * k, 1 * k, 19 * k, 19 * k], fill=disc, outline=ring, width=int(ring_w * k))
    _glyph(d, k, 10, 10, codepoint, 12, fg)
    return done(img)


def shape_icon(codepoint: str, shape: str, fill: str, edge: str, fg: str) -> Image.Image:
    """Square (Mockva) or diamond (Deco) badge with a glyph."""
    img, d, k = canvas(22, 22)
    if shape == 'square':
        d.rectangle([2 * k, 2 * k, 20 * k, 20 * k], fill=fill, outline=edge, width=int(1.5 * k))
    else:
        d.polygon([(11 * k, 0.5 * k), (21.5 * k, 11 * k), (11 * k, 21.5 * k), (0.5 * k, 11 * k)], fill=edge)
        d.polygon([(11 * k, 2.3 * k), (19.7 * k, 11 * k), (11 * k, 19.7 * k), (2.3 * k, 11 * k)], fill=fill)
    _glyph(d, k, 11, 11, codepoint, 11 if shape == 'diamond' else 13, fg)
    return done(img)


# ── Road shields: one per vibe, one width per route-number length ────────────

def shield(n: int, fill: str, edge: str, shape: str = 'round', edge_w: float = 1.5,
           char_w: float = 7, inner: str | None = None, shadow: str | None = None) -> Image.Image:
    """A route shield wide enough for `n` characters. Shapes: round, square,
    octagon (chamfered corners), brackets (open corners, tactical)."""
    w, h = 10 + char_w * n, 18
    off = 2 if shadow else 0
    img, d, k = canvas(int(w + off + 1), h + off + 1)
    box = [0.5 * k, 0.5 * k, (w + 0.5) * k, (h + 0.5) * k]
    ew = max(1, int(edge_w * k))
    if shadow:
        d.rounded_rectangle([b + off * k for b in box], radius=4 * k, fill=shadow)
    if shape == 'round':
        d.rounded_rectangle(box, radius=4 * k, fill=fill, outline=edge, width=ew)
    elif shape == 'square':
        d.rectangle(box, fill=fill, outline=edge, width=ew)
    elif shape == 'octagon':
        x0, y0, x1, y1 = box
        c = 4 * k
        pts = [(x0 + c, y0), (x1 - c, y0), (x1, y0 + c), (x1, y1 - c),
               (x1 - c, y1), (x0 + c, y1), (x0, y1 - c), (x0, y0 + c)]
        d.polygon(pts, fill=edge)
        i = ew
        inset = [(x0 + c, y0 + i), (x1 - c, y0 + i), (x1 - i, y0 + c), (x1 - i, y1 - c),
                 (x1 - c, y1 - i), (x0 + c, y1 - i), (x0 + i, y1 - c), (x0 + i, y0 + c)]
        d.polygon(inset, fill=fill)
    elif shape == 'brackets':
        d.rectangle(box, fill=fill)
        x0, y0, x1, y1 = box
        arm = 4 * k
        for cx, cy, sx, sy in ((x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1)):
            d.line([(cx, cy), (cx + sx * arm, cy)], fill=edge, width=ew)
            d.line([(cx, cy), (cx, cy + sy * arm)], fill=edge, width=ew)
    if inner:
        g = 2.5 * k
        d.rounded_rectangle([box[0] + g, box[1] + g, box[2] - g, box[3] - g],
                            radius=2 * k, outline=inner, width=max(1, int(0.6 * k)))
    return done(img)


SHIELDS = {   # prefix -> shield() keyword arguments
    'fd':    dict(fill='#FFFFFF', edge=INK, edge_w=2, shadow=INK),
    'nv':    dict(fill='#fbf3dc', edge='#3d2a20', inner='#e0ac3e'),
    'mk':    dict(fill='#cc1a1a', edge='#cc1a1a', shape='square'),
    'bp':    dict(fill='#1c4a8c', edge='#ffffff', shape='square', edge_w=1),
    'deco':  dict(fill='#14100a', edge='#c9a84c', shape='octagon', edge_w=1.2),
    'noir':  dict(fill='#0b0c0e', edge='#d8d2c2', edge_w=0.9, char_w=7.5),
    'mario': dict(fill='#fcd800', edge='#000000', shape='square', edge_w=2, char_w=9),
    'tc':    dict(fill='#010a03', edge='#00ff41', shape='brackets', edge_w=1.2, char_w=7.5),
}


# ── Patterns for Mockva, Blueprint, Deco, Noir ───────────────────────────────

def stripes(ground: str, line: str, period: int = 8, width: float = 1.2) -> Image.Image:
    """Tileable 45° stripes."""
    img, d, k = canvas(period, period, _rgba(ground))
    n = period * k
    for off in (-n, 0, n):
        d.line([(off, n), (off + n, 0)], fill=line, width=int(width * k))
    return done(img)


def halftone(ground: str, dot: str, period: int = 6, r: float = 1.1) -> Image.Image:
    img, d, k = canvas(period, period, _rgba(ground))
    for cx, cy in ((period / 4, period / 4), (3 * period / 4, 3 * period / 4)):
        d.ellipse([(cx - r) * k, (cy - r) * k, (cx + r) * k, (cy + r) * k], fill=dot)
    return done(img)


def bp_grid() -> Image.Image:
    """Drafting grid: fine lines every 8px, a stronger one every 40."""
    n = 40
    img, d, k = canvas(n, n, _rgba('#1c4a8c'))
    for i in range(0, n, 8):
        color, w = ('#3f72b8', 1.0) if i == 0 else ('#2a5a9e', 0.6)
        d.line([(i * k, 0), (i * k, n * k)], fill=color, width=max(1, int(w * k)))
        d.line([(0, i * k), (n * k, i * k)], fill=color, width=max(1, int(w * k)))
    return done(img)


def deco_fan() -> Image.Image:
    """Tileable scallop (fish-scale) pattern: gold arcs on deep navy."""
    w, h = 24, 12
    img, d, k = canvas(w, h, _rgba('#0b1626'))
    for cx, cy in ((0, h), (w, h), (w / 2, h / 2), (w / 2, h * 1.5), (0, 0), (w, 0)):
        for r, color in ((12, '#7a6530'), (8, '#3d3a34'), (4, '#3d3a34')):
            d.arc([(cx - r) * k, (cy - r) * k, (cx + r) * k, (cy + r) * k], 180, 360,
                  fill=color, width=max(1, int(0.8 * k)))
    return done(img)


def deco_chevron() -> Image.Image:
    w, h = 16, 8
    # Bronze zigzag inlaid in the lacquer: parks stay in the metals, not green.
    img, d, k = canvas(w, h, _rgba('#1a150c'))
    for dy in (-h, 0, h):
        d.line([(0, (h + dy) * k), (w / 2 * k, dy * k), (w * k, (h + dy) * k)],
               fill='#5a4a24', width=int(1.0 * k))
    return done(img)


def noir_windows(wall: str, pane: str) -> Image.Image:
    """Wall with a few lit windows; used on 3D buildings, lighter for taller ones."""
    rows = ['................', '.dd.dd.dd.dd.dd.', '.dd.dd.oo.dd.dd.', '................',
            '................', '.dd.dd.dd.dd.dd.', '.dd.dd.dd.dd.dd.', '................',
            '................', '.oo.dd.dd.dd.dd.', '.dd.dd.dd.dd.dd.', '................',
            '................', '.dd.dd.dd.dd.oo.', '.dd.dd.dd.dd.dd.', '................']
    return pixel_art(rows, {'.': wall, 'd': pane, 'o': '#e8c26a'}, scale=1)


def pin(fill: str, edge: str, eye: str, shadow: str | None = None) -> Image.Image:
    """The ELJ teardrop pin, tip at bottom centre."""
    w, h = 18, 26
    img, d, k = canvas(w + (3 if shadow else 0), h + (3 if shadow else 0))

    def tear(dx: float, dy: float, color: str, inset: float = 0) -> None:
        r = 8 - inset
        cx, cy = (9 + dx) * k, (9 + dy) * k
        d.polygon([(cx - r * 0.86 * k, cy + r * 0.5 * k), (cx + r * 0.86 * k, cy + r * 0.5 * k),
                   (cx, (25 - inset * 1.8 + dy) * k)], fill=color)
        d.ellipse([cx - r * k, cy - r * k, cx + r * k, cy + r * k], fill=color)

    if shadow:
        tear(2.5, 2.5, shadow)
    tear(0, 0, edge)
    tear(0, 0, fill, inset=1.6)
    d.ellipse([6 * k, 6 * k, 12 * k, 12 * k], fill=eye)
    return done(img)


def nouveau_waves() -> Image.Image:
    """Tileable whiplash wave lines on peacock teal."""
    w, h = 36, 14
    img, d, k = canvas(w, h, _rgba('#4f8f88'))
    for phase, color, width in ((0, '#6fa89f', 1.3), (math.pi, '#3d7a74', 1.0)):
        y0 = h * (0.3 if phase == 0 else 0.8)
        pts = [(x, (y0 + 2.4 * math.sin(2 * math.pi * x / (w * k) + phase)) * k)
               for x in range(-k, w * k + k)]
        d.line(pts, fill=color, width=int(width * k))
    return done(img)


def nouveau_leaves() -> Image.Image:
    """Tileable scatter of small leaf strokes on absinthe green."""
    w = h = 28
    img, d, k = canvas(w, h, _rgba('#a9b56a'))
    for cx, cy, rot in ((7, 7, 30), (21, 21, 30), (21, 7, 120), (7, 21, 120)):
        leaf = Image.new('RGBA', (10 * k, 10 * k))
        ld = ImageDraw.Draw(leaf)
        ld.ellipse([3.2 * k, 1 * k, 6.8 * k, 9 * k], fill=_rgba('#93a257'))
        ld.line([5 * k, 1.5 * k, 5 * k, 8.5 * k], fill=_rgba('#7d8d48'), width=max(1, k // 3))
        leaf = leaf.rotate(rot, resample=Image.BICUBIC)
        img.alpha_composite(leaf, (int((cx - 5) * k), int((cy - 5) * k)))
    return done(img)


def nouveau_metro() -> Image.Image:
    """Métro roundel: cream M on Guimard green, gold ring."""
    img, d, k = canvas(22, 22)
    d.ellipse([1 * k, 1 * k, 21 * k, 21 * k], fill='#2f5d3a', outline='#3d2a20', width=int(1.2 * k))
    d.ellipse([2.6 * k, 2.6 * k, 19.4 * k, 19.4 * k], outline='#e0ac3e', width=int(1.1 * k))
    font = ImageFont.truetype(str(FONTS / 'Federo-Regular.ttf'), 13 * k)
    d.text((11 * k, 11.3 * k), 'M', font=font, fill='#f6ecd2', anchor='mm')
    return done(img)


def nouveau_dot() -> Image.Image:
    """Small rosette for POIs: ink ring, gold petal ring, ink eye."""
    img, d, k = canvas(14, 14)
    d.ellipse([1 * k, 1 * k, 13 * k, 13 * k], fill='#f6ecd2', outline='#3d2a20', width=int(1.2 * k))
    for i in range(6):
        a = i * math.pi / 3
        cx, cy = 7 * k + 3 * k * math.cos(a), 7 * k + 3 * k * math.sin(a)
        d.ellipse([cx - 1.5 * k, cy - 1.5 * k, cx + 1.5 * k, cy + 1.5 * k], fill='#c9785c')
    d.ellipse([5.4 * k, 5.4 * k, 8.6 * k, 8.6 * k], fill='#3d2a20')
    return done(img)


# ── Mario: 8×8 tiles, 2 CSS px per art pixel ─────────────────────────────────

MARIO = {'.': '#38a800', 'g': '#2c8400', 'G': '#80d010',
         'w': '#5c94fc', 'W': '#a4c8fc', 'd': '#3c6cd0',
         'b': '#c84c0c', 'k': '#000000', 'm': '#8c3408',
         's': '#fcd8a8', 'S': '#e0a868',
         't': '#00a800', 'T': '#005800'}

MARIO_TILES = {
    'mario-grass': ['........', '.G......', 'gGg.....', '........',
                    '........', '.....G..', '....gGg.', '........'],
    'mario-water': ['wwwwwwww', 'wWWwwwww', 'WwwWwwww', 'wwwwwwww',
                    'wwwwwwww', 'wwwwwWWw', 'wwwwWwwW', 'wwwwwwww'],
    # Mortar in a darker brick, not black, and courses twice as long: the
    # black-mortar version read as noise across a whole skyline.
    'mario-brick': ['bbbbbbbm', 'bbbbbbbm', 'bbbbbbbm', 'mmmmmmmm',
                    'bbbmbbbb', 'bbbmbbbb', 'bbbmbbbb', 'mmmmmmmm'],
    'mario-sand':  ['ssssssss', 'ssSsssss', 'ssssssss', 'ssssssSs',
                    'ssssssss', 'sSssssss', 'ssssssss', 'ssssSsss'],
    'mario-trees': ['..tt....', '.tttt...', '.tTtt...', '..tT..tt',
                    '.....ttt', 'tt...tTt', 'tTt...T.', '.T......'],
}

MARIO_TILES.update({
    # second water frame: the highlights shift a column, for a 2-frame cycle
    'mario-water-2': ['wwwwwwww', 'wwWWwwww', 'wWwwWwww', 'wwwwwwww',
                      'wwwwwwww', 'Wwwwwwww', 'wWwwwwwW', 'wwwwwwww'],
    # building options (the brick read as too busy across a whole city):
    # a bevelled "hard block", grey castle stone, and plain plaster with a roof edge
    'mario-block': ['hhhhhhhq', 'hoooooaq', 'hoooooaq', 'hoooooaq',
                    'hoooooaq', 'hoooooaq', 'haaaaaaq', 'qqqqqqqq'],
    'mario-stone': ['ggggggGg', 'gGgggggg', 'gggggggg', 'KKKKKKKK',
                    'gggGgggg', 'gggggggG', 'Gggggggg', 'KKKKKKKK'],
    'mario-plaster': ['pppppppp', 'pppppppp', 'ppppPppp', 'pppppppp',
                      'pppppppp', 'pPpppppp', 'pppppppp', 'pppppppp'],
    # courtyard for built-up land, so towns stand out from the overworld grass
    'mario-court': ['cccccccc', 'cCcccccc', 'cccccccc', 'ccccCccc',
                    'cccccccc', 'cccccCcc', 'cccccccc', 'cCcccccc'],
})
MARIO.update({'h': '#fce0a8', 'o': '#e09038', 'a': '#c87020', 'q': '#883800',
              'K': '#3c3c3c', 'p': '#f8d0a0', 'P': '#e8b880',
              'c': '#d8a060', 'C': '#c08040'})
MARIO_STONE = {**MARIO, 'g': '#9c9c9c', 'G': '#bcbcbc'}    # stone reuses the grass keys

MARIO_ICONS = {
    'mario-coin': (['..yyyy..', '.yYYYYy.', 'yYyyyyYy', 'yYyYYyYy',
                    'yYyYYyYy', 'yYyyyyYy', '.yYYYYy.', '..yyyy..'],
                   {'.': '#00000000', 'y': '#fcd800', 'Y': '#ac7c00'}),
    'mario-pipe': (['kkkkkkkk', 'kGgGgggk', 'kGgGgggk', 'kkkkkkkk',
                    '.kGgggk.', '.kGgggk.', '.kGgggk.', '.kGgggk.'],
                   {'.': '#00000000', 'k': '#000000', 'G': '#b8f818', 'g': '#00a800'}),
}


def mario_card():
    """Title card behind place names: black, with a 1px white inner rule; stretches."""
    rows = ['kkkkkkkkkkkk', 'kWWWWWWWWWWk', 'kWkkkkkkkkWk', 'kWkkkkkkkkWk', 'kWkkkkkkkkWk',
            'kWkkkkkkkkWk', 'kWkkkkkkkkWk', 'kWkkkkkkkkWk', 'kWWWWWWWWWWk', 'kkkkkkkkkkkk']
    img = pixel_art(rows, {'k': '#000000', 'W': '#ffffff'}, scale=2)
    u = 2 * R      # one art pixel in sheet pixels
    meta = {'stretchX': [[3 * u, 9 * u]], 'stretchY': [[3 * u, 7 * u]], 'content': [3 * u, 3 * u, 9 * u, 7 * u]}
    return img, meta


# Underground palette: black ground, blue-grey brick, cyan water
MARIO_UG = {**MARIO, 'w': '#008888', 'W': '#3cbcfc', 'h': '#7c9cbc', 'o': '#3c5c7c', 'a': '#2c4060', 'q': '#101830',
            'c': '#202838', 'C': '#303c50'}
MARIO_UG_TILES = {
    'mario-ug-water': MARIO_TILES['mario-water'],
    'mario-ug-water-2': MARIO_TILES['mario-water-2'],
    'mario-ug-block': MARIO_TILES['mario-block'],
    'mario-ug-court': MARIO_TILES['mario-court'],
}


def mario_road() -> Image.Image:
    """Line pattern for roads: tan with a darker pixel kerb on both edges."""
    rows = ['kkkkkkkk', 'SSSSSSSS', 'ssssssss', 'ssssssss', 'ssssSsss', 'ssssssss', 'SSSSSSSS', 'kkkkkkkk']
    return pixel_art(rows, {**MARIO, 'k': '#000000'}, scale=1)


# ── Field Day extras ─────────────────────────────────────────────────────────

def fd_plate():
    """A white sticker plate behind city names; stretches to fit the text."""
    w, h = 24, 20
    img, d, k = canvas(w, h)
    d.rounded_rectangle([3 * k, 3 * k, (w - 0.5) * k, (h - 0.5) * k], radius=7 * k, fill=INK)
    d.rounded_rectangle([0.5 * k, 0.5 * k, (w - 3) * k, (h - 3) * k], radius=7 * k,
                        fill='#FFFFFF', outline=INK, width=2 * k)
    img = done(img)
    meta = {'stretchX': [[8 * R, 16 * R]], 'stretchY': [[8 * R, 12 * R]],
            'content': [6 * R, 4 * R, 18 * R, 14 * R]}
    return img, meta


def fd_ribbon() -> Image.Image:
    """A prize rosette: mustard disc, red tails, ink outline."""
    img, d, k = canvas(20, 26)
    d.polygon([(6 * k, 12 * k), (3 * k, 25 * k), (7 * k, 22 * k), (9 * k, 25 * k), (10 * k, 13 * k)],
              fill='#D33A2C', outline=INK)
    d.polygon([(14 * k, 12 * k), (17 * k, 25 * k), (13 * k, 22 * k), (11 * k, 25 * k), (10 * k, 13 * k)],
              fill='#2350A0', outline=INK)
    d.ellipse([2 * k, 1 * k, 18 * k, 17 * k], fill='#E8B13A', outline=INK, width=2 * k)
    d.ellipse([6 * k, 5 * k, 14 * k, 13 * k], fill='#FFFFFF', outline=INK, width=k)
    return done(img)


# ── Nouveau extras ───────────────────────────────────────────────────────────

def nv_nimbus() -> Image.Image:
    """Mucha's halo: a gold ring with a thin concentric ornament, cream inside."""
    n = 64
    img, d, k = canvas(n, n)
    c = n / 2
    for r, fill, outline, wd in ((31, '#f6ecd2', '#e0ac3e', 3), (25, None, '#3d2a20', 0.8), (21, None, '#e0ac3e', 0.8)):
        d.ellipse([(c - r) * k, (c - r) * k, (c + r) * k, (c + r) * k], fill=fill, outline=outline, width=max(1, int(wd * k)))
    for i in range(24):
        a = 2 * math.pi * i / 24
        d.ellipse([(c + 28 * math.cos(a) - 0.9) * k, (c + 28 * math.sin(a) - 0.9) * k,
                   (c + 28 * math.cos(a) + 0.9) * k, (c + 28 * math.sin(a) + 0.9) * k], fill='#3d2a20')
    return done(img)


def nv_stem() -> Image.Image:
    """Line pattern for rivers: a sinuous whiplash stroke on peacock."""
    w, h = 48, 8
    img, d, k = canvas(w, h, _rgba('#4f8f88'))
    pts = [(x, (h / 2 + 2.6 * math.sin(2 * math.pi * x / (w * k) * 1)) * k) for x in range(0, w * k + 1, 2)]
    pts = [(x, y) for x, y in pts]
    d.line(pts, fill='#2f6660', width=int(1.6 * k))
    pts2 = [(x, (h / 2 + 2.6 * math.sin(2 * math.pi * x / (w * k) + math.pi)) * k) for x in range(0, w * k + 1, 2)]
    d.line(pts2, fill='#f3ead0', width=max(1, int(0.7 * k)))
    return done(img)


# ── Deco extras ──────────────────────────────────────────────────────────────

def deco_sun(codepoint: str) -> Image.Image:
    """Landmark badge: a radiating gold sunburst behind the diamond glyph."""
    n = 40
    img, d, k = canvas(n, n)
    c = n / 2
    for i in range(16):
        a = 2 * math.pi * i / 16
        r1 = 19 if i % 2 == 0 else 15
        d.polygon([(c * k, c * k),
                   ((c + r1 * math.cos(a - 0.08)) * k, (c + r1 * math.sin(a - 0.08)) * k),
                   ((c + r1 * math.cos(a + 0.08)) * k, (c + r1 * math.sin(a + 0.08)) * k)], fill='#c9a84c')
    d.polygon([(c * k, (c - 11) * k), ((c + 11) * k, c * k), (c * k, (c + 11) * k), ((c - 11) * k, c * k)], fill='#e8cf8a')
    d.polygon([(c * k, (c - 9.3) * k), ((c + 9.3) * k, c * k), (c * k, (c + 9.3) * k), ((c - 9.3) * k, c * k)], fill='#14100a')
    _glyph(d, k, c, c, codepoint, 10, '#e8cf8a')
    return done(img)


# ── Mockva / Blueprint extras ────────────────────────────────────────────────

def paper_grain(ground: str, fleck: str, n: int = 64, count: int = 90, seed: int = 7) -> Image.Image:
    import random
    rnd = random.Random(seed)
    img, d, k = canvas(n, n, _rgba(ground))
    for _ in range(count):
        x, y, r = rnd.uniform(0, n), rnd.uniform(0, n), rnd.uniform(0.3, 0.8)
        d.ellipse([(x - r) * k, (y - r) * k, (x + r) * k, (y + r) * k], fill=fleck)
    return done(img)


def crosshatch(ground: str, line: str, period: int = 10, width: float = 0.9) -> Image.Image:
    img, d, k = canvas(period, period, _rgba(ground))
    n = period * k
    for off in (-n, 0, n):
        d.line([(off, n), (off + n, 0)], fill=line, width=int(width * k))
        d.line([(off, 0), (off + n, n)], fill=line, width=int(width * k))
    return done(img)


# ── Tom Clancy ───────────────────────────────────────────────────────────────

def tc_marker(shape: str, color: str) -> Image.Image:
    """Track symbology, original: open square, diamond, chevron, cross, circle."""
    img, d, k = canvas(14, 14)
    w = int(1.3 * k)
    if shape == 'square':
        d.rectangle([2 * k, 2 * k, 12 * k, 12 * k], outline=color, width=w)
    elif shape == 'diamond':
        d.polygon([(7 * k, 1 * k), (13 * k, 7 * k), (7 * k, 13 * k), (1 * k, 7 * k)], outline=color, width=w)
    elif shape == 'chevron':
        d.line([(2 * k, 10 * k), (7 * k, 4 * k), (12 * k, 10 * k)], fill=color, width=w, joint='curve')
    elif shape == 'cross':
        d.rectangle([2 * k, 2 * k, 12 * k, 12 * k], outline=color, width=w)
        d.line([(7 * k, 4 * k), (7 * k, 10 * k)], fill=color, width=w)
        d.line([(4 * k, 7 * k), (10 * k, 7 * k)], fill=color, width=w)
    else:
        d.ellipse([2 * k, 2 * k, 12 * k, 12 * k], outline=color, width=w)
    d.rectangle([6.3 * k, 6.3 * k, 7.7 * k, 7.7 * k], fill=color)
    return done(img)


# ── Tom Clancy ───────────────────────────────────────────────────────────────

def tc_scan() -> Image.Image:
    """Diagonal hatch for water: dim phosphor lines on near-black."""
    n = 8 * R
    img = Image.new('RGBA', (n, n), _rgba('#010a03'))
    for i in range(n):
        img.putpixel((i, (n - 1 - i)), _rgba('#0a3d17'))
    return img


def tc_dot() -> Image.Image:
    """Contact marker: open square with a centre pip."""
    img, d, k = canvas(12, 12)
    d.rectangle([1 * k, 1 * k, 11 * k, 11 * k], fill='#021405', outline='#00ff41', width=k)
    d.rectangle([5 * k, 5 * k, 7 * k, 7 * k], fill='#00ff41')
    return done(img)


def build() -> None:
    sprites: dict[str, Image.Image] = {
        'fd-dot-mustard': fd_dot('#E8B13A'), 'fd-dot-green': fd_dot('#6F9A5E'),
        'fd-dot-cobalt': fd_dot('#2350A0'), 'fd-dot-red': fd_dot('#D33A2C'),
        'fd-dot-white': fd_dot('#FFFFFF'), 'fd-dot-ink': fd_dot('#869FCB'),
        'nouveau-waves': nouveau_waves(), 'nouveau-leaves': nouveau_leaves(),
        'nouveau-metro': nouveau_metro(), 'nouveau-dot': nouveau_dot(),
        'tc-scan': tc_scan(), 'tc-dot': tc_dot(),
    }
    for cls, (_, cp) in MDI.items():
        sprites[f'fd-{cls}'] = fd_icon(cls, cp)
        sprites[f'nv-{cls}'] = flat_icon(cp, '#f6ecd2', '#3d2a20', '#8a4f3a')
        sprites[f'mk-{cls}'] = shape_icon(cp, 'square', '#cc1a1a', '#111111', '#f0ece0')
        sprites[f'deco-{cls}'] = shape_icon(cp, 'diamond', '#14100a', '#c9a84c', '#e8cf8a')
        sprites[f'bp-{cls}'] = flat_icon(cp, '#1c4a8c', '#ffffff', '#ffffff', ring_w=0.9)
        sprites[f'noir-{cls}'] = flat_icon(cp, '#0b0c0e', '#d8d2c2', '#d8d2c2', ring_w=0.9)
    sprites['fd-pin'] = pin('#D33A2C', INK, '#FFFFFF', shadow=INK)
    # Coarse enough not to alias into moiré rings when the map is pitched.
    sprites['mk-stripes'] = stripes('#111111', '#3a3a3a', period=12, width=2)
    sprites['mk-halftone'] = halftone('#e4dccb', '#b9b09c')
    sprites['bp-grid'] = bp_grid()
    sprites['bp-hatch'] = stripes('#173f7a', '#4f82c6', period=10, width=1.2)
    sprites['deco-fan'] = deco_fan()
    sprites['deco-chevron'] = deco_chevron()
    sprites['noir-windows-low'] = noir_windows('#1d2024', '#14161a')
    sprites['noir-windows-mid'] = noir_windows('#2d3137', '#1c1f23')
    sprites['noir-windows-high'] = noir_windows('#40454d', '#272b30')
    for prefix, disc, ring in (('mk', '#cc1a1a', '#111111'), ('deco', '#14100a', '#c9a84c'),
                               ('bp', '#1c4a8c', '#ffffff'), ('noir', '#0b0c0e', '#d8d2c2')):
        sprites[f'{prefix}-dot'] = flat_icon(MDI['information'][1], disc, ring, disc)
    for name, rows in MARIO_TILES.items():
        sprites[name] = pixel_art(rows, MARIO_STONE if name == 'mario-stone' else MARIO)
    for name, (rows, pal) in MARIO_ICONS.items():
        sprites[name] = pixel_art(rows, pal)
    sprites['mario-road'] = mario_road()
    sprites['mario-card'] = mario_card()
    for name, rows in MARIO_UG_TILES.items():
        sprites[name] = pixel_art(rows, MARIO_UG)
    sprites['fd-plate'] = fd_plate()
    sprites['fd-ribbon'] = fd_ribbon()
    sprites['nv-nimbus'] = nv_nimbus()
    sprites['nv-stem'] = nv_stem()
    sprites['mk-grain'] = paper_grain('#f0ece0', '#d9d1bd')
    sprites['bp-crosshatch'] = crosshatch('#1c4a8c', '#2f62a8')
    groups = ((TRANSPORT, 'chevron'), (FOOD, 'diamond'), (HEALTH, 'cross'), (CULTURE, 'square'), (NATURE, 'circle'))
    for cls, (_, cp) in MDI.items():
        shape = next((sh for members, sh in groups if cls in members), 'square')
        color = '#ffb000' if cls in HEALTH else '#00ff41'      # one amber alert class: health
        sprites[f'tc-{cls}'] = tc_marker(shape, color)
        sprites[f'deco-sun-{cls}'] = deco_sun(cp)
    sprites['tc-mark'] = tc_marker('square', '#00ff41')
    for prefix, kw in SHIELDS.items():
        for n in range(1, 7):
            sprites[f'{prefix}-shield-{n}'] = shield(n, **kw)

    # Simple shelf packing; 2px gutters so linear filtering never bleeds.
    pad, width = 2, 1024
    x = y = shelf = 0
    manifest, placed = {}, []
    # A sprite is an image, or (image, extra manifest keys) for stretchable ones.
    entries = {name: v if isinstance(v, tuple) else (v, {}) for name, v in sprites.items()}
    for name, (img, meta) in sorted(entries.items(), key=lambda kv: -kv[1][0].height):
        if x + img.width > width:
            x, y, shelf = 0, y + shelf + pad, 0
        placed.append((img, x, y))
        manifest[name] = {'x': x, 'y': y, 'width': img.width, 'height': img.height, 'pixelRatio': R, **meta}
        x += img.width + pad
        shelf = max(shelf, img.height)
    sheet = Image.new('RGBA', (width, y + shelf), (0, 0, 0, 0))
    for img, px, py in placed:
        sheet.paste(img, (px, py))

    OUT.mkdir(parents=True, exist_ok=True)
    sheet.save(OUT / 'fx.png')
    (OUT / 'fx.json').write_text(json.dumps(manifest, indent=2))
    print(f'OK  fx.png {sheet.width}×{sheet.height}  {len(manifest)} sprites')


if __name__ == '__main__':
    build()
