"""Run with: python -m pytest tests/  (or python tests/test_mapcss.py)"""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.backend import mapcss, style_builder  # noqa: E402

BASE = {'layers': [
    {'id': 'background', 'type': 'background', 'paint': {'background-color': '#fff'}},
    {'id': 'water', 'type': 'fill', 'source': 's', 'source-layer': 'water', 'paint': {'fill-color': '#00f'}},
    {'id': 'road_motorway_casing', 'type': 'line', 'source': 's', 'source-layer': 'transportation', 'paint': {}},
    {'id': 'road_motorway', 'type': 'line', 'source': 's', 'source-layer': 'transportation', 'paint': {}},
    {'id': 'road_major_rail', 'type': 'line', 'source': 's', 'source-layer': 'transportation', 'paint': {}},
    {'id': 'label_city', 'type': 'symbol', 'source': 's', 'source-layer': 'place',
     'layout': {'text-font': ['Noto Sans Regular']}, 'paint': {'text-halo-color': '#fff'}},
]}


def build(css: str) -> dict:
    with tempfile.TemporaryDirectory() as d:
        path = Path(d) / 'v.mcss'
        path.write_text(css)
        return {l['id']: l for l in mapcss.apply_sheet(BASE, mapcss.parse(path))['layers']}


def test_cascade_and_aliases():
    out = build('''
        @vibe { font: "Fredoka SemiBold"; }
        :root { --ink: #111; }
        road { color: red; }
        road.casing { color: var(--ink); width: zoom(exp 1.4, 8 1, 18 20); }
        road.motorway:not(.casing) { color: gold; dash: 3 2; cap: round; }
        rail { color: blue; }
        background { color: var(--paper, #eee); }
        label { color: var(--ink); halo: rgba(0, 0, 0, 0.5) 2; }
        label.city { halo: unset; transform: uppercase; }
    ''')
    assert out['road_motorway_casing']['paint']['line-color'] == '#111'
    assert out['road_motorway_casing']['paint']['line-width'] == \
        ['interpolate', ['exponential', 1.4], ['zoom'], 8, 1, 18, 20]
    assert out['road_motorway']['paint'] == {'line-color': 'gold', 'line-dasharray': [3, 2]}
    assert out['road_motorway']['layout'] == {'line-cap': 'round'}
    assert out['road_major_rail']['paint']['line-color'] == 'blue'   # rail is its own element
    assert out['background']['paint']['background-color'] == '#eee'
    city = out['label_city']
    assert city['layout'] == {'text-font': ['Fredoka SemiBold'], 'text-transform': 'uppercase'}
    assert city['paint'] == {'text-color': '#111'}                   # halo removed by `unset`


def test_generated_layers():
    out = build('''
        water::before { color: black; translate: 3 3; }
        water::after  { type: line; color: black; width: 2; }
    ''')
    assert list(out) [1:4] == ['water::before', 'water', 'water::after']
    assert out['water::before']['paint'] == {'fill-color': 'black', 'fill-translate': [3, 3]}
    assert out['water::after']['type'] == 'line'
    assert out['water::after']['source-layer'] == 'water'


def test_zoom_array_stops_are_literals():
    # MapLibre reads a bare list inside an expression as another expression
    expr = mapcss.parse_value('zoom(14 1 1, 18 3 3)')
    assert expr == ['interpolate', ['linear'], ['zoom'], 14, ['literal', [1, 1]], 18, ['literal', [3, 3]]]


def test_every_vibe_compiles():
    for vibe in style_builder.list_vibes():
        assert style_builder.build_style(vibe['id'])['layers']


if __name__ == '__main__':
    test_cascade_and_aliases(); test_generated_layers(); test_zoom_array_stops_are_literals(); test_every_vibe_compiles()
    print('ok')
