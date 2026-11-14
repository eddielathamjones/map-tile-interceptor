"""Map stylesheets: a small CSS dialect that restyles a MapLibre style.

A vibe is one `.mcss` file. Rules select layers of the base style and set
paint/layout properties; the usual cascade applies (specificity, then source
order).

    @vibe { label: "Field Day"; font: "Fredoka SemiBold"; }
    :root { --ink: #1D1F23; }

    water                { color: #617FB4; }
    road.casing          { color: var(--ink); width: zoom(exp 1.4, 8 3, 18 34); }
    road.motorway:not(.casing) { color: #E8B13A; }
    building::before     { color: var(--ink); translate: 3 3; }   /* hard shadow */
    #landcover_wood      { color: #6F9A5E; }

Selectors
    element   background raster water waterway park landuse landcover building
              road rail aeroway boundary label, or `*`
    .class    every `_`/`-` separated token of the layer id (motorway, casing,
              tunnel, bridge, wood, city ...), the layer type (fill, line,
              symbol, extrusion), and for labels the kind (place, poi, road,
              shield, water, airport, arrow)
    #id       exact layer id
    :not(.class)
    ::before  ::after   a generated layer under / over the matched one, sharing
              its source, filter and zoom range (`type:` picks fill or line)

Properties
    Short names resolve per layer type: color, opacity, width, outline,
    pattern, dash, gap, blur, cap, join, translate, halo, font, size,
    transform, spacing, icon, icon-scale, text, display, minzoom, maxzoom,
    filter. Any real MapLibre property name works too. `unset` removes a
    property from the base style.

Values
    var(--name[, fallback])       custom properties from :root
    zoom(8 1, 13 4, 18 16)        linear interpolation over zoom
    zoom(exp 1.4, 8 1, 18 16)     exponential interpolation
    json([...])                   a raw MapLibre expression
    3 2                           a number list (dash, translate, offset)
"""

from __future__ import annotations

import copy
import json
import re
from dataclasses import dataclass, field
from pathlib import Path

# ── Layer classification ─────────────────────────────────────────────────────

_SOURCE_LAYER_ELEMENT = {
    'water': 'water', 'waterway': 'waterway', 'park': 'park',
    'landuse': 'landuse', 'landcover': 'landcover', 'building': 'building',
    'boundary': 'boundary', 'aeroway': 'aeroway', 'transportation': 'road',
}
_LABEL_KIND = {
    'place': 'place', 'poi': 'poi', 'transportation_name': 'road',
    'water_name': 'water', 'waterway': 'water', 'aerodrome_label': 'airport',
    'transportation': 'arrow',
}


def classify(layer: dict) -> tuple[str, set[str]]:
    """Return (element, classes) for a base-style layer."""
    ltype = layer.get('type', '')
    lid = layer.get('id', '')
    sl = layer.get('source-layer', '')
    classes = {t for t in re.split(r'[_\-]', lid.lower()) if t}
    classes.add('extrusion' if ltype == 'fill-extrusion' else ltype)
    if 'street' in classes:          # Liberty calls minor roads "street" on bridges/tunnels
        classes.add('minor')

    if ltype in ('background', 'raster'):
        return ltype, classes
    if ltype == 'symbol':
        classes.add(_LABEL_KIND.get(sl, 'other'))
        return 'label', classes
    element = _SOURCE_LAYER_ELEMENT.get(sl, sl or ltype)
    if element == 'road' and 'rail' in classes:
        element = 'rail'
    return element, classes


# ── Parsing ──────────────────────────────────────────────────────────────────

@dataclass
class Selector:
    element: str = '*'
    classes: tuple[str, ...] = ()
    ids: tuple[str, ...] = ()
    nots: tuple[str, ...] = ()
    pseudo: str = ''

    @property
    def specificity(self) -> int:
        return 100 * len(self.ids) + 10 * (len(self.classes) + len(self.nots)) + (self.element != '*')

    def matches(self, element: str, classes: set[str], lid: str) -> bool:
        return ((self.element == '*' or self.element == element)
                and all(c in classes for c in self.classes)
                and all(i == lid for i in self.ids)
                and not any(c in classes for c in self.nots))


@dataclass
class Sheet:
    meta: dict[str, str] = field(default_factory=dict)
    vars: dict[str, str] = field(default_factory=dict)
    rules: list[tuple[Selector, dict[str, str]]] = field(default_factory=list)
    files: list[Path] = field(default_factory=list)


class MapCSSError(ValueError):
    pass


_SELECTOR_RE = re.compile(r'::?[a-z]+(?:\([^)]*\))?|[.#][\w\-]+|[\w\-]+|\*')


def _parse_selector(text: str) -> Selector:
    sel = Selector()
    classes, ids, nots = [], [], []
    pos = 0
    for m in _SELECTOR_RE.finditer(text):
        if m.start() != pos:
            raise MapCSSError(f'bad selector: {text!r}')
        pos = m.end()
        tok = m.group()
        if tok.startswith('::'):
            if tok not in ('::before', '::after'):
                raise MapCSSError(f'unknown pseudo-element {tok} in {text!r}')
            sel.pseudo = tok[2:]
        elif tok.startswith(':not('):
            nots.append(tok[5:-1].strip().lstrip('.'))
        elif tok.startswith(':'):
            raise MapCSSError(f'unknown pseudo-class {tok} in {text!r}')
        elif tok.startswith('.'):
            classes.append(tok[1:])
        elif tok.startswith('#'):
            ids.append(tok[1:])
        else:
            sel.element = tok
    if pos != len(text):
        raise MapCSSError(f'bad selector: {text!r}')
    sel.classes, sel.ids, sel.nots = tuple(classes), tuple(ids), tuple(nots)
    return sel


def _split_top(text: str, sep: str) -> list[str]:
    """Split on `sep` outside parentheses, brackets and quotes."""
    out, depth, start, quote = [], 0, 0, ''
    for i, ch in enumerate(text):
        if quote:
            if ch == quote:
                quote = ''
        elif ch in '"\'':
            quote = ch
        elif ch in '([':
            depth += 1
        elif ch in ')]':
            depth -= 1
        elif ch == sep and depth == 0:
            out.append(text[start:i])
            start = i + 1
    out.append(text[start:])
    return out


def _parse_decls(body: str) -> dict[str, str]:
    decls = {}
    for part in _split_top(body, ';'):
        part = part.strip()
        if not part:
            continue
        name, colon, value = part.partition(':')
        if not colon:
            raise MapCSSError(f'bad declaration: {part!r}')
        decls[name.strip()] = value.strip()
    return decls


def parse(path: Path, _sheet: Sheet | None = None) -> Sheet:
    """Parse a stylesheet file, following @import relative to it."""
    sheet = _sheet or Sheet()
    sheet.files.append(path)
    text = re.sub(r'/\*.*?\*/', '', path.read_text(encoding='utf-8'), flags=re.S)
    pos = 0
    while True:
        m = re.compile(r'\s*(@import\s+"([^"]+)"\s*;|([^{};]+)\{([^}]*)\})').match(text, pos)
        if not m:
            break
        pos = m.end()
        if m.group(2):
            parse(path.parent / m.group(2), sheet)
            continue
        head, decls = m.group(3).strip(), _parse_decls(m.group(4))
        if head == '@vibe':
            sheet.meta.update({k: v.strip('"\'') for k, v in decls.items()})
        elif head == ':root':
            sheet.vars.update(decls)
        else:
            for sel in _split_top(head, ','):
                sheet.rules.append((_parse_selector(sel.strip()), decls))
    if text[pos:].strip():
        raise MapCSSError(f'{path.name}: cannot parse near {text[pos:].strip()[:60]!r}')
    return sheet


# ── Values ───────────────────────────────────────────────────────────────────

_VAR_RE = re.compile(r'var\(\s*(--[\w\-]+)\s*(?:,\s*([^()]*(?:\([^()]*\))?[^()]*))?\)')
_NUM_RE = re.compile(r'^-?(\d+\.?\d*|\.\d+)$')


def _subst(value: str, variables: dict[str, str]) -> str:
    for _ in range(16):
        def repl(m: re.Match) -> str:
            name, fallback = m.group(1), m.group(2)
            if name in variables:
                return variables[name]
            if fallback is not None:
                return fallback.strip()
            raise MapCSSError(f'undefined variable {name}')
        new = _VAR_RE.sub(repl, value)
        if new == value:
            return value
        value = new
    raise MapCSSError(f'variable cycle in {value!r}')


def _num(tok: str) -> float | int:
    f = float(tok)
    return int(f) if f.is_integer() else f


def _scalar(tok: str):
    tok = tok.strip()
    if _NUM_RE.match(tok):
        return _num(tok)
    if tok in ('true', 'false'):
        return tok == 'true'
    if len(tok) >= 2 and tok[0] == tok[-1] and tok[0] in '"\'':
        return tok[1:-1]
    return tok


def parse_value(value: str):
    value = value.strip()
    if value.startswith('json(') and value.endswith(')'):
        return json.loads(value[5:-1])
    if value.startswith('zoom(') and value.endswith(')'):
        stops = [s.strip() for s in _split_top(value[5:-1], ',')]
        curve: list = ['linear']
        if stops and stops[0].startswith('exp '):
            curve = ['exponential', _num(stops.pop(0)[4:].strip())]
        expr: list = ['interpolate', curve, ['zoom']]
        for stop in stops:
            z, _, v = stop.partition(' ')
            expr += [_num(z), parse_value(v)]
        return expr
    toks = value.split()
    if len(toks) > 1 and all(_NUM_RE.match(t) for t in toks):
        return [_num(t) for t in toks]
    return _scalar(value)


# ── Property resolution ──────────────────────────────────────────────────────

_PAINT_PREFIX = {'fill': 'fill', 'line': 'line', 'background': 'background',
                 'raster': 'raster', 'fill-extrusion': 'fill-extrusion', 'symbol': 'text'}
_SYMBOL_PAINT = {
    'text-color', 'text-opacity', 'text-halo-color', 'text-halo-width', 'text-halo-blur',
    'text-translate', 'text-translate-anchor',
    'icon-color', 'icon-opacity', 'icon-halo-color', 'icon-halo-width', 'icon-halo-blur',
    'icon-translate', 'icon-translate-anchor',
}
_LINE_LAYOUT = {'line-cap', 'line-join', 'line-miter-limit', 'line-round-limit', 'line-sort-key'}
_TYPE_PREFIXES = {
    'fill': ('fill-',), 'line': ('line-',), 'background': ('background-',),
    'raster': ('raster-',), 'fill-extrusion': ('fill-extrusion-',),
    'symbol': ('text-', 'icon-', 'symbol-'),
}
_LINE_ALIASES = {'width': 'line-width', 'gap': 'line-gap-width', 'blur': 'line-blur',
                 'dash': 'line-dasharray', 'cap': 'line-cap', 'join': 'line-join'}
_SYMBOL_ALIASES = {'font': 'text-font', 'size': 'text-size', 'transform': 'text-transform',
                   'spacing': 'text-letter-spacing', 'icon': 'icon-image',
                   'icon-scale': 'icon-size', 'text': 'text-field'}
_LAYER_KEYS = ('minzoom', 'maxzoom', 'filter')


def _canonical(ltype: str, name: str, value: str) -> list[tuple[str, str]]:
    """Expand a short property name to real property names for this layer type."""
    prefix = _PAINT_PREFIX.get(ltype, ltype)
    if name == 'display':
        return [('visibility', 'none' if value == 'none' else 'visible')]
    if name == 'color':
        return [(f'{prefix}-color', value)] if ltype != 'raster' else []
    if name == 'opacity':
        if ltype == 'symbol':
            return [('text-opacity', value), ('icon-opacity', value)]
        return [(f'{prefix}-opacity', value)]
    if name == 'outline':
        return [('fill-outline-color', value)] if ltype == 'fill' else []
    if name == 'pattern':
        return [(f'{ltype}-pattern', value)] if ltype in ('fill', 'line', 'background', 'fill-extrusion') else []
    if name == 'translate':
        return [(f'{ltype}-translate', value)] if ltype in ('fill', 'line', 'fill-extrusion') else []
    if name == 'halo':
        if ltype != 'symbol':
            return []
        if value == 'unset':
            return [('text-halo-color', value), ('text-halo-width', value)]
        # "color [width [blur]]" — the colour may itself contain spaces (rgba(...))
        m = re.match(r'^(.*?)(?:\s+(-?[\d.]+))?(?:\s+(-?[\d.]+))?$', value)
        out = [('text-halo-color', m.group(1).strip())]
        if m.group(2):
            out.append(('text-halo-width', m.group(2)))
        if m.group(3):
            out.append(('text-halo-blur', m.group(3)))
        return out
    if name in _LINE_ALIASES:
        return [(_LINE_ALIASES[name], value)] if ltype == 'line' else []
    if name in _SYMBOL_ALIASES:
        return [(_SYMBOL_ALIASES[name], value)] if ltype == 'symbol' else []
    if name in _LAYER_KEYS:
        return [(name, value)]
    if name == 'visibility' or name.startswith(_TYPE_PREFIXES.get(ltype, ())):
        return [(name, value)]
    return []   # a real property for some other layer type: not applicable here


def _is_layout(ltype: str, prop: str) -> bool:
    if prop == 'visibility':
        return True
    if ltype == 'symbol':
        return prop not in _SYMBOL_PAINT
    if ltype == 'line':
        return prop in _LINE_LAYOUT
    return prop.endswith('-sort-key')


def _apply(layer: dict, decls: dict[str, str], variables: dict[str, str]) -> None:
    ltype = layer['type']
    for name, raw in decls.items():
        if name == 'type':
            continue
        for prop, text in _canonical(ltype, name, _subst(raw, variables)):
            if prop in _LAYER_KEYS:
                if text == 'unset':
                    layer.pop(prop, None)
                else:
                    layer[prop] = parse_value(text)
                continue
            bucket = layer.setdefault('layout' if _is_layout(ltype, prop) else 'paint', {})
            if text == 'unset':
                bucket.pop(prop, None)
                continue
            value = parse_value(text)
            if prop == 'text-font' and isinstance(value, str):
                value = [value]
            bucket[prop] = value


def _cascade(matches: list[tuple[int, int, dict[str, str]]]) -> dict[str, str]:
    merged: dict[str, str] = {}
    for _, _, decls in sorted(matches, key=lambda m: (m[0], m[1])):
        for k, v in decls.items():
            merged.pop(k, None)     # re-insert so later declarations apply last
            merged[k] = v
    return merged


def apply_sheet(style: dict, sheet: Sheet) -> dict:
    """Return a copy of `style` with the stylesheet's rules applied."""
    style = copy.deepcopy(style)
    variables = {k: _subst(v, sheet.vars) for k, v in sheet.vars.items()}
    default_font = sheet.meta.get('font')
    out_layers = []

    for layer in style.get('layers', []):
        element, classes = classify(layer)
        lid = layer.get('id', '')
        own, before, after = [], [], []
        if default_font and layer['type'] == 'symbol' and 'text-font' in layer.get('layout', {}):
            own.append((-1, -1, {'font': f'"{default_font}"'}))
        for order, (sel, decls) in enumerate(sheet.rules):
            if sel.matches(element, classes, lid):
                bucket = {'': own, 'before': before, 'after': after}[sel.pseudo]
                bucket.append((sel.specificity, order, decls))

        _apply(layer, _cascade(own), variables)

        generated = {}
        for where, matches in (('before', before), ('after', after)):
            if not matches or 'source' not in layer:
                continue
            decls = _cascade(matches)
            gtype = decls.get('type', layer['type'])
            if gtype not in ('fill', 'line'):
                raise MapCSSError(f'{lid}::{where}: type must be fill or line')
            gen = {'id': f'{lid}::{where}', 'type': gtype,
                   **{k: copy.deepcopy(layer[k]) for k in ('source', 'source-layer', 'filter', 'minzoom', 'maxzoom')
                      if k in layer}}
            if gtype == 'line':
                gen['layout'] = {'line-join': 'round', 'line-cap': 'round'}
            if layer.get('layout', {}).get('visibility') == 'none':
                gen.setdefault('layout', {})['visibility'] = 'none'
            _apply(gen, decls, variables)
            generated[where] = gen

        if 'before' in generated:
            out_layers.append(generated['before'])
        out_layers.append(layer)
        if 'after' in generated:
            out_layers.append(generated['after'])

    style['layers'] = out_layers
    return style
