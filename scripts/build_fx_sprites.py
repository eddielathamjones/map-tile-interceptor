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
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) + (255,)


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
    """A quiet badge: disc, thin ring, glyph. Used by Survey and Nouveau."""
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
    img, d, k = canvas(w, h, _rgba('#16210f'))
    for dy in (-h, 0, h):
        d.line([(0, (h + dy) * k), (w / 2 * k, dy * k), (w * k, (h + dy) * k)],
               fill='#2c3d1c', width=int(1.0 * k))
    return done(img)


def noir_windows() -> Image.Image:
    """Dark wall with a few lit windows; used on 3D buildings."""
    rows = ['................', '.dd.dd.dd.dd.dd.', '.dd.dd.oo.dd.dd.', '................',
            '................', '.dd.dd.dd.dd.dd.', '.dd.dd.dd.dd.dd.', '................',
            '................', '.oo.dd.dd.dd.dd.', '.dd.dd.dd.dd.dd.', '................',
            '................', '.dd.dd.dd.dd.oo.', '.dd.dd.dd.dd.dd.', '................']
    return pixel_art(rows, {'.': '#15181b', 'd': '#22262b', 'o': '#c9a352'}, scale=1)


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


def contours(line: str, ground: str, alpha: int) -> Image.Image:
    """Tileable contour lines (the brand's topo background), 256 CSS px square."""
    import numpy as np
    n = 256 * R * 2
    ax = np.linspace(0, 2 * np.pi, n, endpoint=False)
    x, y = np.meshgrid(ax, ax)
    rng = np.random.default_rng(11)
    field = np.zeros((n, n))
    for fx_, fy_ in ((1, 0), (0, 1), (1, 1), (1, -1), (2, 1), (1, 2), (2, -1)):
        field += rng.uniform(0.4, 1.0) / (fx_ * fx_ + fy_ * fy_) ** 0.5 * np.sin(
            fx_ * x + fy_ * y + rng.uniform(0, 2 * np.pi))
    bands = np.floor((field - field.min()) / (field.max() - field.min()) * 9)
    edge = (bands != np.roll(bands, 1, 0)) | (bands != np.roll(bands, 1, 1))
    mask = Image.fromarray((edge * 255).astype('uint8')).resize((256 * R, 256 * R), Image.LANCZOS)
    mask = mask.point(lambda v: min(255, v * 2) * alpha // 255)
    img = Image.new('RGBA', (256 * R, 256 * R), _rgba(ground))
    img.paste(Image.new('RGBA', img.size, _rgba(line)), (0, 0), mask)
    return img


# ── Art Nouveau ──────────────────────────────────────────────────────────────

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
         'b': '#c84c0c', 'k': '#000000', 'm': '#fcbcb0',
         's': '#fcd8a8', 'S': '#e0a868',
         't': '#00a800', 'T': '#005800'}

MARIO_TILES = {
    'mario-grass': ['........', '.G......', 'gGg.....', '........',
                    '........', '.....G..', '....gGg.', '........'],
    'mario-water': ['wwwwwwww', 'wWWwwwww', 'WwwWwwww', 'wwwwwwww',
                    'wwwwwwww', 'wwwwwWWw', 'wwwwWwwW', 'wwwwwwww'],
    'mario-brick': ['bbbkbbbk', 'bbbkbbbk', 'bbbkbbbk', 'kkkkkkkk',
                    'bkbbbkbb', 'bkbbbkbb', 'bkbbbkbb', 'kkkkkkkk'],
    'mario-sand':  ['ssssssss', 'ssSsssss', 'ssssssss', 'ssssssSs',
                    'ssssssss', 'sSssssss', 'ssssssss', 'ssssSsss'],
    'mario-trees': ['..tt....', '.tttt...', '.tTtt...', '..tT..tt',
                    '.....ttt', 'tt...tTt', 'tTt...T.', '.T......'],
}

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
        sprites[f'sv-{cls}'] = flat_icon(cp, '#F2EDE1', '#2350A0', '#2350A0')
        sprites[f'svn-{cls}'] = flat_icon(cp, '#13213D', '#869FCB', '#F2EDE1')
        sprites[f'nv-{cls}'] = flat_icon(cp, '#f6ecd2', '#3d2a20', '#8a4f3a')
        sprites[f'mk-{cls}'] = shape_icon(cp, 'square', '#cc1a1a', '#111111', '#f0ece0')
        sprites[f'deco-{cls}'] = shape_icon(cp, 'diamond', '#14100a', '#c9a84c', '#e8cf8a')
        sprites[f'bp-{cls}'] = flat_icon(cp, '#1c4a8c', '#ffffff', '#ffffff', ring_w=0.9)
        sprites[f'noir-{cls}'] = flat_icon(cp, '#0b0c0e', '#d8d2c2', '#d8d2c2', ring_w=0.9)
    sprites['fd-pin'] = pin('#D33A2C', INK, '#FFFFFF', shadow=INK)
    sprites['sv-pin'] = pin('#D33A2C', '#D33A2C', '#F2EDE1')
    sprites['sv-dot'] = flat_icon(MDI['information'][1], '#F2EDE1', '#2350A0', '#F2EDE1')
    sprites['svn-dot'] = flat_icon(MDI['information'][1], '#13213D', '#869FCB', '#13213D')
    sprites['mk-stripes'] = stripes('#111111', '#3a3a3a')
    sprites['mk-halftone'] = halftone('#e4dccb', '#b9b09c')
    sprites['bp-grid'] = bp_grid()
    sprites['bp-hatch'] = stripes('#173f7a', '#4f82c6', period=6, width=0.8)
    sprites['deco-fan'] = deco_fan()
    sprites['deco-chevron'] = deco_chevron()
    sprites['noir-windows'] = noir_windows()
    for prefix, disc, ring in (('mk', '#cc1a1a', '#111111'), ('deco', '#14100a', '#c9a84c'),
                               ('bp', '#1c4a8c', '#ffffff'), ('noir', '#0b0c0e', '#d8d2c2')):
        sprites[f'{prefix}-dot'] = flat_icon(MDI['information'][1], disc, ring, disc)
    sprites['sv-contours'] = contours('#2350A0', '#F2EDE1', 42)
    sprites['svn-contours'] = contours('#869FCB', '#0C172D', 38)
    for name, rows in MARIO_TILES.items():
        sprites[name] = pixel_art(rows, MARIO)

    # Simple shelf packing; 2px gutters so linear filtering never bleeds.
    pad, width = 2, 1024
    x = y = shelf = 0
    manifest, placed = {}, []
    for name, img in sorted(sprites.items(), key=lambda kv: -kv[1].height):
        if x + img.width > width:
            x, y, shelf = 0, y + shelf + pad, 0
        placed.append((img, x, y))
        manifest[name] = {'x': x, 'y': y, 'width': img.width, 'height': img.height, 'pixelRatio': R}
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
