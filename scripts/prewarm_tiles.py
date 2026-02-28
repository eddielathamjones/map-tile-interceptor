#!/usr/bin/env python3
"""Pre-warm the raster tile cache for all vibes at zoom levels 0-N.

Usage:
    python scripts/prewarm_tiles.py --base-url http://localhost:5002 --max-zoom 2
"""

import argparse
import concurrent.futures
import sys

import requests

VIBES = [
    'noir', 'mockva', 'vintage', 'toner', 'blueprint', 'dark', 'watercolor',
    'highcontrast', 'mario', 'simcity', 'tomclancy', 'deco', 'metro',
]


def tile_coords(max_zoom: int):
    for z in range(max_zoom + 1):
        size = 2 ** z
        for x in range(size):
            for y in range(size):
                yield z, x, y


def fetch_tile(session: requests.Session, base_url: str, vibe: str,
               z: int, x: int, y: int) -> bool:
    url = f'{base_url}/api/tiles/raster/{vibe}/{z}/{x}/{y}.png'
    try:
        r = session.get(url, timeout=30)
        r.raise_for_status()
        return True
    except Exception as exc:
        print(f'FAIL {vibe}/{z}/{x}/{y}: {exc}', flush=True)
        return False


def main() -> None:
    parser = argparse.ArgumentParser(description='Pre-warm geochron tile cache')
    parser.add_argument('--base-url', default='http://localhost:5003',
                        help='Base URL of the running app (default: http://localhost:5002)')
    parser.add_argument('--max-zoom', type=int, default=4,
                        help='Maximum zoom level to warm (default: 4)')
    parser.add_argument('--workers', type=int, default=8,
                        help='Parallel workers (default: 8)')
    args = parser.parse_args()

    tiles = list(tile_coords(args.max_zoom))
    total = len(VIBES) * len(tiles)
    print(f'Warming {len(VIBES)} vibes × {len(tiles)} tiles = {total} requests '
          f'(z0–{args.max_zoom}) against {args.base_url}')

    done = ok = 0
    with requests.Session() as session:
        futures: dict[concurrent.futures.Future, tuple] = {}
        with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
            for vibe in VIBES:
                for z, x, y in tiles:
                    fut = pool.submit(fetch_tile, session, args.base_url, vibe, z, x, y)
                    futures[fut] = (vibe, z, x, y)

            for fut in concurrent.futures.as_completed(futures):
                done += 1
                vibe, z, x, y = futures[fut]
                if fut.result():
                    ok += 1
                    print(f'[{done}/{total}] ok  {vibe}/{z}/{x}/{y}', flush=True)

    print(f'\nDone: {ok}/{total} tiles cached.')
    if ok < total:
        sys.exit(1)


if __name__ == '__main__':
    main()
