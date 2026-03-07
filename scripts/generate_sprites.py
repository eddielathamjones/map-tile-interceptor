#!/usr/bin/env python3
"""
Auto-generate sprite icons using Gemini image generation.

Usage:
    python scripts/generate_sprites.py <vibe> [--icon <name>] [--build] [--delay <seconds>]

Skips icons that already exist in assets/sprites/<vibe>/.
Saves generated PNGs to assets/sprites/<vibe>/<icon_name>.png.
"""

import argparse
import io
import os
import subprocess
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types
from PIL import Image

load_dotenv()

MODEL = 'gemini-2.0-flash-exp-image-generation'
DEFAULT_DELAY = 4  # seconds between requests

# ---------------------------------------------------------------------------
# Icon definitions per vibe
# ---------------------------------------------------------------------------

MARIO_PALETTE = (
    '#5c94fc sky blue · #38a800 green · #d04000 brick red · #c8a850 tan · '
    '#ffffff white · #000000 black · #fcbc3c coin gold · #e40058 red'
)

MARIO_ICONS = {
    # Transportation
    'restaurant':       'crossed fork and knife',
    'cafe':             'coffee cup with steam rising',
    'fast_food':        'hamburger burger',
    'bar':              'beer mug with foam',
    'bakery':           'bread loaf',
    # Nature
    'park':             'deciduous tree',
    'mountain':         'mountain peak with snow cap',
    'campsite':         'camping tent',
    # Amenities
    'hospital':         'medical red cross',
    'pharmacy':         'medical green cross',
    'police':           'sheriff star badge',
    'school':           'building with a flag on the roof and windows, completely no text anywhere, no signs, no labels',
    'bank':             'dollar sign',
    'post':             'envelope letter',
    'information':      'lowercase letter i in a circle',
    # Culture
    'museum':           'classical building with columns',
    'cinema':           'film clapperboard',
    'lodging':          'bed with pillow',
    'place_of_worship': 'small chapel silhouette with cross on top',
    # Markers
    'marker':           'teardrop-shaped map pin',
    'circle':           'filled circle',
    'star':             '5-point star',
    'dot_9':            'single small filled circle, sky blue, centered on transparent background, nothing else',
    'dot_10':           'single medium filled circle, sky blue, centered on transparent background, nothing else',
    'dot_11':           'medium filled dot',
    # Road shields
    'road_1':           'white square badge with black border, completely blank white interior, no text, no numbers, no symbols',
    'road_2':           'white rectangular badge slightly wider than tall, black border, completely blank white interior, no text, no numbers, no symbols',
    'road_3':           'white rectangular badge wider than tall, black border, completely blank white interior, no text, no numbers, no symbols',
    'road_4':           'white rectangular badge much wider than tall, black border, completely blank white interior, no text, no numbers, no symbols',
    'road_5':           'white rectangular badge very wide, solid black border only, completely blank white interior, no text, no numbers, no symbols, no color other than black and white',
    'road_6':           'white rectangular badge widest of all, solid black border only, completely blank white interior, no text, no numbers, no symbols, no color other than black and white',
}

TOMCLANCY_PALETTE = '#00ff41 phosphor green · #000000 black'

TOMCLANCY_ICONS = {
    # Transportation
    'bus':              'bus side view',
    'railway':          'locomotive train side view',
    'airport':          'airplane side view',
    'ferry':            'ferry boat side view',
    'car':              'car top-down view',
    'fuel':             'gas pump',
    'parking':          'letter P',
    'restaurant':       'crossed fork and knife',
    'cafe':             'coffee cup with steam rising',
    'fast_food':        'hamburger burger',
    'bar':              'beer mug with foam',
    'bakery':           'bread loaf',
    # Nature
    'park':             'deciduous tree',
    'mountain':         'mountain peak',
    'campsite':         'camping tent',
    # Amenities
    'hospital':         'medical cross',
    'pharmacy':         'medical cross with circle',
    'police':           'star badge',
    'school':           'building with flag on roof, no text, no letters',
    'bank':             'dollar sign',
    'post':             'envelope',
    'information':      'lowercase letter i in a circle',
    # Culture
    'museum':           'classical building with columns',
    'cinema':           'film clapperboard',
    'lodging':          'bed with pillow',
    'place_of_worship': 'chapel silhouette with cross',
    # Markers
    'marker':           'teardrop-shaped map pin',
    'circle':           'filled circle',
    'star':             '5-point star',
    'dot_9':            'single small filled circle, centered, nothing else',
    'dot_10':           'single medium filled circle, centered, nothing else',
    'dot_11':           'single larger filled circle, centered, nothing else',
    # Road shields
    'road_1':           'square badge with border, completely blank interior, no text, no color other than green and black',
    'road_2':           'rectangular badge slightly wider than tall, border, blank interior, no text',
    'road_3':           'rectangular badge wider than tall, border, blank interior, no text',
    'road_4':           'rectangular badge much wider than tall, border, blank interior, no text',
    'road_5':           'rectangular badge very wide, border, blank interior, no text',
    'road_6':           'rectangular badge widest, border, blank interior, no text',
}

VIBES = {
    'mario': {
        'palette': MARIO_PALETTE,
        'icons':   MARIO_ICONS,
    },
    'tomclancy': {
        'palette': TOMCLANCY_PALETTE,
        'icons':   TOMCLANCY_ICONS,
    },
}

# ---------------------------------------------------------------------------

VIBE_STYLES = {
    'mario': (
        '1985 NES pixel art — chunky, hard pixel edges, '
        'no anti-aliasing, no gradients, no partial transparency, black outline'
    ),
    'tomclancy': (
        'military tactical map icon — clean vector silhouette, '
        'phosphor green lines and fills on pure black background, '
        'sharp geometric edges, minimal detail, no gradients, no anti-aliasing'
    ),
}


def build_prompt(vibe: str, palette: str, icon_name: str, description: str) -> str:
    style = VIBE_STYLES.get(vibe, VIBE_STYLES['mario'])
    return (
        'Generate a single map icon:\n'
        f'- Subject: {icon_name} — {description}\n'
        '- Size: 63×63px\n'
        '- Background: transparent\n'
        f'- Style: {style}\n'
        f'- Palette: {palette}\n'
        '- Output: single PNG, no labels, no borders, no extra whitespace'
    )


def generate_icon(client, vibe: str, palette: str, icon_name: str, description: str, out_path: Path) -> bool:
    prompt = build_prompt(vibe, palette, icon_name, description)
    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_modalities=['IMAGE', 'TEXT']
            ),
        )
        for part in response.candidates[0].content.parts:
            if part.inline_data is not None:
                img_data = part.inline_data.data
                if isinstance(img_data, str):
                    import base64
                    img_data = base64.b64decode(img_data)
                img = Image.open(io.BytesIO(img_data))
                img.save(out_path)
                print(f'  OK   {icon_name}  ({img.size[0]}x{img.size[1]}px)')
                return True
        print(f'  SKIP {icon_name}  (no image in response)')
        return False
    except Exception as e:
        print(f'  ERR  {icon_name}: {e}')
        return False


def main():
    parser = argparse.ArgumentParser(description='Generate sprite icons via Gemini.')
    parser.add_argument('vibe', help='Vibe name (e.g. mario)')
    parser.add_argument('--icon', help='Generate a single icon by name and exit')
    parser.add_argument('--build', action='store_true', help='Run build_sprites.py after generation')
    parser.add_argument('--delay', type=float, default=DEFAULT_DELAY,
                        help=f'Seconds between requests (default: {DEFAULT_DELAY})')
    args = parser.parse_args()

    if args.vibe not in VIBES:
        print(f'Unknown vibe "{args.vibe}". Available: {", ".join(VIBES)}')
        sys.exit(1)

    vibe_cfg = VIBES[args.vibe]
    palette  = vibe_cfg['palette']
    all_icons = vibe_cfg['icons']

    repo_root = Path(__file__).parent.parent
    out_dir   = repo_root / 'assets' / 'sprites' / args.vibe
    out_dir.mkdir(parents=True, exist_ok=True)

    if args.icon:
        if args.icon not in all_icons:
            print(f'Unknown icon "{args.icon}". Available: {", ".join(all_icons)}')
            sys.exit(1)
        to_generate = {args.icon: all_icons[args.icon]}
    else:
        to_generate = {k: v for k, v in all_icons.items()
                       if not (out_dir / f'{k}.png').exists()}

    if not to_generate:
        print('All icons already generated.')
    else:
        api_key = os.environ.get('GOOGLE_API_KEY')
        if not api_key:
            print('GOOGLE_API_KEY not set in environment.')
            sys.exit(1)

        client = genai.Client(api_key=api_key)
        print(f'Generating {len(to_generate)} icon(s) for {args.vibe}...')

        for i, (name, desc) in enumerate(to_generate.items()):
            out_path = out_dir / f'{name}.png'
            generate_icon(client, args.vibe, palette, name, desc, out_path)
            if i < len(to_generate) - 1:
                time.sleep(args.delay)

    if args.build:
        build_script = repo_root / 'scripts' / 'build_sprites.py'
        subprocess.run([sys.executable, str(build_script), args.vibe], check=True)


if __name__ == '__main__':
    main()
