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

MODEL = 'gemini-2.5-flash-image'
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

TOMCLANCY_PALETTE = 'EXACTLY TWO COLORS ONLY: #00ff41 bright phosphor green · #000000 pure black. No other colors permitted.'

TOMCLANCY_ICONS = {
    # Transportation
    'bus':              'bus side view silhouette filled solid bright #00ff41 green',
    'railway':          'locomotive train side view silhouette filled solid bright #00ff41 green',
    'airport':          'airplane side view silhouette filled solid bright #00ff41 green, wings spread',
    'ferry':            'ferry boat side view silhouette filled solid bright #00ff41 green',
    'car':              'car top-down view silhouette filled solid bright #00ff41 green',
    'fuel':             'gas pump silhouette filled solid bright #00ff41 green',
    'parking':          'capital letter P in bright #00ff41 green on black background',
    'restaurant':       'crossed fork and knife silhouette in bright #00ff41 green on black background',
    'cafe':             'coffee cup silhouette filled solid bright #00ff41 green',
    'fast_food':        'hamburger burger silhouette filled solid bright #00ff41 green',
    'bar':              'beer mug silhouette filled solid bright #00ff41 green',
    'bakery':           'bread loaf silhouette filled solid bright #00ff41 green',
    # Nature
    'park':             'simple tree silhouette triangle shape filled solid bright #00ff41 green on black',
    'mountain':         'mountain peak triangle silhouette filled solid bright #00ff41 green on black',
    'campsite':         'camping tent silhouette filled solid bright #00ff41 green',
    # Amenities
    'hospital':         'medical plus cross shape filled solid bright #00ff41 green on black background, thick arms',
    'pharmacy':         'medical plus cross inside a circle outline, all in bright #00ff41 green on black',
    'police':           '5-pointed star badge silhouette filled solid bright #00ff41 green on black',
    'school':           'building silhouette with small flag on top, filled solid bright #00ff41 green on black, no text',
    'bank':             'dollar sign symbol in bright #00ff41 green on black background',
    'post':             'envelope silhouette filled solid bright #00ff41 green on black',
    'information':      'lowercase letter i inside a circle outline, all in bright #00ff41 green on black, simple',
    # Culture
    'museum':           'classical building with 3 columns silhouette filled solid bright #00ff41 green on black',
    'cinema':           'film clapperboard silhouette filled solid bright #00ff41 green on black',
    'lodging':          'bed silhouette filled solid bright #00ff41 green on black',
    'place_of_worship': 'simple chapel silhouette with cross on top, filled solid bright #00ff41 green on black',
    # Markers
    'marker':           'teardrop map pin silhouette filled solid bright #00ff41 green on black, hollow circle at center',
    'circle':           'filled circle bright #00ff41 green on black',
    'star':             '5-point star filled solid bright #00ff41 green on black',
    'dot_9':            'small filled circle bright #00ff41 green centered on black background, nothing else',
    'dot_10':           'medium filled circle bright #00ff41 green centered on black background, nothing else',
    'dot_11':           'larger filled circle bright #00ff41 green centered on black background, nothing else',
    # Road shields — blank badge shapes for map road labels (text is rendered on top by MapLibre)
    'road_1':           'square badge: pure black fill, bright #00ff41 green border outline only, completely empty interior, no text, no symbols, no patterns',
    'road_2':           'rectangular badge slightly wider than tall: pure black fill, bright #00ff41 green border outline only, completely empty interior, no text',
    'road_3':           'rectangular badge wider than tall: pure black fill, bright #00ff41 green border outline only, completely empty interior, no text',
    'road_4':           'rectangular badge much wider than tall: pure black fill, bright #00ff41 green border outline only, completely empty interior, no text',
    'road_5':           'rectangular badge very wide: pure black fill, bright #00ff41 green border outline only, completely empty interior, no text',
    'road_6':           'rectangular badge widest of all: pure black fill, bright #00ff41 green border outline only, completely empty interior, no text',
}

METRO_PALETTE = (
    '#3a2e1a dark brown (primary) · #c4a86a amber gold (accent) · '
    '#f0ebe0 warm ivory (light fill) · #8ab4a8 muted teal (water) · '
    '#ffffff white · #000000 black'
)

METRO_ICONS = {
    # Transportation
    'bus':              'bus side view',
    'railway':          'locomotive train side view',
    'airport':          'airplane top-down view',
    'ferry':            'ferry boat side view',
    'car':              'car side view',
    'fuel':             'gas pump',
    'parking':          'capital letter P',
    'restaurant':       'crossed fork and knife',
    'cafe':             'coffee cup with saucer',
    'fast_food':        'hamburger burger',
    'bar':              'wine glass',
    'bakery':           'bread loaf',
    # Nature
    'park':             'deciduous tree',
    'mountain':         'mountain peak',
    'campsite':         'camping tent',
    # Amenities
    'hospital':         'medical cross',
    'pharmacy':         'mortar and pestle',
    'police':           'shield badge',
    'school':           'open book',
    'bank':             'classical building with columns and pediment',
    'post':             'envelope with wax seal',
    'information':      'lowercase letter i in a circle',
    # Culture
    'museum':           'classical building with columns',
    'cinema':           'film reel',
    'lodging':          'old-fashioned key',
    'place_of_worship': 'church with steeple and cross',
    # Markers
    'marker':           'teardrop map pin',
    'circle':           'filled circle',
    'star':             '5-point star',
    'dot_9':            'small filled circle centered on transparent background',
    'dot_10':           'medium filled circle centered on transparent background',
    'dot_11':           'larger filled circle centered on transparent background',
    # Road shields — blank badge shapes
    'road_1':           'square cartouche with ornate border, blank ivory interior, no text, no numbers',
    'road_2':           'rectangular cartouche slightly wider than tall, ornate border, blank ivory interior, no text',
    'road_3':           'rectangular cartouche wider than tall, ornate border, blank ivory interior, no text',
    'road_4':           'rectangular cartouche much wider than tall, ornate border, blank ivory interior, no text',
    'road_5':           'rectangular cartouche very wide, ornate border, blank ivory interior, no text',
    'road_6':           'rectangular cartouche widest, ornate border, blank ivory interior, no text',
}

MOCKVA_PALETTE = (
    '#f0ece0 cream paper background · #1a1a1a pure black · '
    '#cc1a1a constructivist red · NO other colors'
)

MOCKVA_ICONS = {
    # Transportation
    'bus':              'bold flat geometric bus silhouette in solid black, side view, no detail',
    'railway':          'bold flat geometric locomotive silhouette in solid black, side view',
    'airport':          'bold flat geometric airplane silhouette in solid black, top-down view, sharp triangular wings',
    'ferry':            'bold flat geometric boat silhouette in solid black, side view',
    'car':              'bold flat geometric car silhouette in solid black, side view',
    'fuel':             'bold flat geometric gas pump silhouette in solid black',
    'parking':          'bold capital letter P in solid black inside a solid red square, constructivist poster style',
    'restaurant':       'crossed fork and knife as bold flat solid black silhouettes, no detail, no shading',
    'cafe':             'bold flat geometric coffee cup silhouette in solid black with a small red dot of steam',
    'fast_food':        'bold flat geometric hamburger silhouette in solid black',
    'bar':              'bold flat geometric beer mug silhouette in solid black',
    'bakery':           'bold flat geometric bread loaf silhouette in solid black',
    # Nature
    'park':             'bold flat geometric tree silhouette in solid black: triangle on a rectangle trunk, no detail',
    'mountain':         'bold solid red triangle on cream background, constructivist poster style, flat geometric mountain',
    'campsite':         'bold flat geometric tent silhouette in solid black: simple triangle',
    # Amenities
    'hospital':         'bold solid red plus cross shape on cream background, thick equal arms, flat geometric',
    'pharmacy':         'bold solid red plus cross inside a thin black circle outline, flat geometric',
    'police':           'bold flat solid black 5-pointed star silhouette, geometric, no detail',
    'school':           'bold flat geometric building silhouette in solid black with a small red flag on top, no text, no windows',
    'bank':             'bold solid black dollar sign symbol, geometric, sans-serif',
    'post':             'bold flat geometric envelope silhouette in solid black',
    'information':      'bold lowercase letter i in solid black inside a solid red circle, constructivist style',
    # Culture
    'museum':           'bold flat geometric classical building silhouette with three columns and a triangular pediment, solid black, no detail',
    'cinema':           'bold flat geometric film clapperboard silhouette in solid black, sharp angles',
    'lodging':          'bold flat geometric bed silhouette in solid black, side view',
    'place_of_worship': 'bold flat geometric chapel silhouette in solid black with a small cross on top, no detail',
    # Markers
    'marker':           'bold flat geometric teardrop map pin in solid red with a black circle hole at the center, constructivist style',
    'circle':           'solid red filled circle on cream background, no outline, perfectly round',
    'star':             'bold flat solid red 5-pointed star, geometric, no outline',
    'dot_9':            'small solid red filled circle centered on cream background, nothing else',
    'dot_10':           'medium solid red filled circle centered on cream background, nothing else',
    'dot_11':           'larger solid red filled circle centered on cream background, nothing else',
    # Road shields — solid constructivist red badges with thin black borders, empty interior for text overlay
    'road_1':           'solid #cc1a1a red square badge with a thin black border, completely empty cream-colored interior space for text, no text, no numbers, no symbols',
    'road_2':           'solid #cc1a1a red rectangular badge slightly wider than tall, thin black border, completely empty cream interior for text, no text',
    'road_3':           'solid #cc1a1a red rectangular badge wider than tall, thin black border, completely empty cream interior for text, no text',
    'road_4':           'solid #cc1a1a red rectangular badge much wider than tall, thin black border, completely empty cream interior for text, no text',
    'road_5':           'solid #cc1a1a red rectangular badge very wide, thin black border, completely empty cream interior for text, no text',
    'road_6':           'solid #cc1a1a red rectangular badge widest of all, thin black border, completely empty cream interior for text, no text',
}

DECO_PALETTE = (
    '#1a1008 warm near-black background · #c9a84c gold (primary accent) · '
    '#f5f0e8 cream (highlights) · #0d1a2e deep navy · NO other colors'
)

DECO_ICONS = {
    # Transportation
    'bus':              'art deco geometric bus icon, gold #c9a84c lines on pure black background, symmetric streamlined silhouette, fine gold linework, no detail clutter',
    'railway':          'art deco geometric locomotive icon, gold #c9a84c lines on pure black background, streamlined classic train side view, fine gold linework',
    'airport':          'art deco geometric airplane icon, gold #c9a84c silhouette on pure black background, symmetric top-down, swept wings, fine deco linework',
    'ferry':            'art deco geometric boat icon, gold #c9a84c lines on pure black background, streamlined ocean liner silhouette',
    'car':              'art deco geometric car icon, gold #c9a84c lines on pure black background, streamlined 1930s coupe side view',
    'fuel':             'art deco geometric gas pump icon, gold #c9a84c lines on pure black background, symmetric streamlined',
    'parking':          'capital letter P in elegant geometric art deco font, gold #c9a84c on pure black background background, inside a thin gold circle',
    'restaurant':       'art deco crossed fork and knife, gold #c9a84c on pure black background, symmetric, fine geometric linework, elegant',
    'cafe':             'art deco geometric coffee cup with saucer, gold #c9a84c on pure black background, symmetric, fine deco linework, optional radiating steam lines',
    'fast_food':        'art deco geometric hamburger icon, gold #c9a84c on pure black background, symmetric, stacked geometric forms',
    'bar':              'art deco geometric coupe cocktail glass, gold #c9a84c on pure black background, symmetric triangular bowl on tall stem',
    'bakery':           'art deco geometric bread loaf, gold #c9a84c on pure black background, symmetric oval form with fine scoring lines',
    # Nature
    'park':             'art deco stylized tree, geometric symmetric foliage in gold #c9a84c on pure black background, fan-shaped leaves on a simple trunk',
    'mountain':         'art deco stepped geometric mountain, ziggurat-like layered triangles in gold #c9a84c on pure black background, fine linework',
    'campsite':         'art deco geometric triangular tent, gold #c9a84c lines on pure black background, symmetric, decorative pole tips',
    # Amenities
    'hospital':         'art deco geometric plus cross, gold #c9a84c on pure black background, thick equal arms with stepped corners and fine linework details',
    'pharmacy':         'art deco geometric plus cross inside a thin gold #c9a84c circle, on pure black background background, symmetric and elegant',
    'police':           'art deco geometric 5-pointed star badge, gold #c9a84c on pure black background, faceted with radiating fine linework',
    'school':           'art deco geometric building with three columns and ziggurat roof, gold #c9a84c on pure black background, no text',
    'bank':             'art deco classical building with stepped pediment and columns, gold #c9a84c on pure black background, symmetric, fine deco detail',
    'post':             'art deco geometric envelope, gold #c9a84c on pure black background, symmetric with decorative wax-seal star in the center',
    'information':      'elegant lowercase letter i in deco geometric font, gold #c9a84c on pure black background, inside a thin gold circle',
    # Culture
    'museum':           'art deco classical building with three columns and triangular pediment, gold #c9a84c on pure black background, symmetric, fine geometric linework',
    'cinema':           'art deco geometric film reel, gold #c9a84c on pure black background, concentric circles with sunburst spokes radiating out',
    'lodging':          'art deco geometric stylized key, gold #c9a84c on pure black background, ornate symmetric bow at top, fine deco linework',
    'place_of_worship': 'art deco geometric chapel with stepped facade and cross on top, gold #c9a84c on pure black background, symmetric, fine linework',
    # Markers
    'marker':           'art deco geometric teardrop map pin, gold #c9a84c on pure black background, symmetric, with a decorative geometric sunburst at the center',
    'circle':           'solid gold #c9a84c filled circle on pure black background background, perfectly round, no outline',
    'star':             'art deco 5-pointed star, gold #c9a84c on pure black background, faceted with fine radiating linework, no outline',
    'dot_9':            'small solid gold #c9a84c filled circle centered on pure black background background, nothing else',
    'dot_10':           'medium solid gold #c9a84c filled circle centered on pure black background background, nothing else',
    'dot_11':           'larger solid gold #c9a84c filled circle centered on pure black background background, nothing else',
    # Road shields — gold-framed cream cartouches with stepped deco corners, empty interior for text overlay
    'road_1':           'art deco square badge with stepped corners: thick gold #c9a84c frame, completely empty cream #f5f0e8 interior for text, no text, no numbers, no symbols',
    'road_2':           'art deco rectangular badge slightly wider than tall with stepped deco corners: thick gold #c9a84c frame, empty cream #f5f0e8 interior, no text',
    'road_3':           'art deco rectangular badge wider than tall with stepped deco corners: thick gold #c9a84c frame, empty cream #f5f0e8 interior, no text',
    'road_4':           'art deco rectangular badge much wider than tall with stepped deco corners: thick gold #c9a84c frame, empty cream #f5f0e8 interior, no text',
    'road_5':           'art deco rectangular badge very wide with stepped deco corners: thick gold #c9a84c frame, empty cream #f5f0e8 interior, no text',
    'road_6':           'art deco rectangular badge widest of all with stepped deco corners: thick gold #c9a84c frame, empty cream #f5f0e8 interior, no text',
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
    'metro': {
        'palette': METRO_PALETTE,
        'icons':   METRO_ICONS,
    },
    'mockva': {
        'palette': MOCKVA_PALETTE,
        'icons':   MOCKVA_ICONS,
    },
    'deco': {
        'palette': DECO_PALETTE,
        'icons':   DECO_ICONS,
    },
}

# ---------------------------------------------------------------------------

VIBE_STYLES = {
    'mario': (
        '1985 NES pixel art — chunky, hard pixel edges, '
        'no anti-aliasing, no gradients, no partial transparency, black outline'
    ),
    'tomclancy': (
        'military tactical map icon — solid filled silhouette, '
        'BRIGHT #00ff41 phosphor green fills on pure black background, '
        'sharp geometric edges, minimal detail, no gradients, no anti-aliasing, '
        'no dark green, no forest green, only bright neon #00ff41 green and pure black'
    ),
    'metro': (
        'Victorian engraving style map icon — fine cross-hatched illustration, '
        'dark brown #3a2e1a ink on warm ivory #f0ebe0 background, '
        'amber gold #c4a86a accent details, elegant and detailed linework, '
        'antique cartographic feel, no flat colors, no gradients'
    ),
    'mockva': (
        'Russian Constructivist poster icon (Rodchenko, El Lissitzky) — '
        'bold flat geometric forms, pure solid colors, no gradients, no shading, '
        'no anti-aliasing fuzz, no cross-hatching, no realism. '
        'STRICTLY only #1a1a1a black and #cc1a1a red on a #f0ece0 cream paper background. '
        'Sharp geometric silhouettes, poster-like, graphic and flat'
    ),
    'deco': (
        'Art Deco map icon (Chrysler Building, Erté, Bond film title sequence) — '
        'symmetric geometric forms, fine gold #c9a84c linework and gold silhouettes '
        'on PURE BLACK #000000 background (background must be solid black, not gold), '
        'stepped ziggurat corners, radiating sunburst details, streamlined elegance, '
        'no realism, no shading, no naturalism — pure geometric stylization. '
        'STRICTLY only gold #c9a84c and pure black — black is the background, gold is the subject'
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
