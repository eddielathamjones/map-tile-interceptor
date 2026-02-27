import base64
import io
import logging
import os

from PIL import Image, ImageEnhance, ImageFilter, ImageOps

log = logging.getLogger(__name__)

_AI_URL = os.environ.get('AI_SERVICE_URL', '')
_AI_KEY = os.environ.get('AI_SERVICE_KEY', '')
_AI_VIBES = set(v.strip() for v in os.environ.get('AI_VIBES', '').split(',') if v.strip())


def transform(vibe: str, img_bytes: bytes, z: int, x: int, y: int) -> bytes:
    """Return transformed PNG bytes for the given vibe."""
    if vibe == 'liberty':
        return img_bytes

    if _AI_URL and vibe in _AI_VIBES:
        result = _try_ai(vibe, img_bytes, z, x, y)
        if result:
            return result

    return _pil_transform(vibe, img_bytes)


def _pil_transform(vibe: str, img_bytes: bytes) -> bytes:
    img = Image.open(io.BytesIO(img_bytes)).convert('RGB')

    if vibe == 'vintage':
        img = _sepia(img)
        img = ImageEnhance.Brightness(img).enhance(0.88)
        img = ImageEnhance.Contrast(img).enhance(0.82)
    elif vibe == 'toner':
        img = img.convert('L').convert('RGB')
        img = ImageEnhance.Contrast(img).enhance(1.8)
        img = ImageEnhance.Brightness(img).enhance(1.1)
    elif vibe == 'blueprint':
        img = _blueprint(img)
    elif vibe == 'dark':
        img = ImageOps.invert(img)
        img = _cool_tint(img)
        img = ImageEnhance.Brightness(img).enhance(0.75)
    elif vibe == 'watercolor':
        img = ImageEnhance.Color(img).enhance(1.35)
        img = ImageEnhance.Contrast(img).enhance(0.75)
        img = img.filter(ImageFilter.GaussianBlur(radius=1.2))
        img = ImageEnhance.Color(img).enhance(1.4)
    elif vibe == 'highcontrast':
        img = ImageEnhance.Contrast(img).enhance(2.2)
        img = ImageEnhance.Color(img).enhance(1.6)

    buf = io.BytesIO()
    img.save(buf, format='PNG')
    return buf.getvalue()


def _sepia(img: Image.Image) -> Image.Image:
    """Full 3×3 sepia matrix via getdata/putdata — no numpy needed."""
    r_data, g_data, b_data = [list(ch.getdata()) for ch in img.split()]
    nr = [min(255, int(0.393 * r + 0.769 * g + 0.189 * b))
          for r, g, b in zip(r_data, g_data, b_data)]
    ng = [min(255, int(0.349 * r + 0.686 * g + 0.168 * b))
          for r, g, b in zip(r_data, g_data, b_data)]
    nb = [min(255, int(0.272 * r + 0.534 * g + 0.131 * b))
          for r, g, b in zip(r_data, g_data, b_data)]
    out = Image.new('RGB', img.size)
    out.putdata(list(zip(nr, ng, nb)))
    return out


def _blueprint(img: Image.Image) -> Image.Image:
    """Grayscale → remap into blue range #0a1f5c..#dce8ff via per-channel LUT."""
    gray = img.convert('L')
    r, g, b = gray.convert('RGB').split()
    r_lut = [int(10  + (220 - 10)  * v / 255) for v in range(256)]
    g_lut = [int(31  + (232 - 31)  * v / 255) for v in range(256)]
    b_lut = [int(92  + (255 - 92)  * v / 255) for v in range(256)]
    return Image.merge('RGB', (r.point(r_lut), g.point(g_lut), b.point(b_lut)))


def _cool_tint(img: Image.Image) -> Image.Image:
    """Apply cool (blue-shifted) tint: R×0.55, G×0.60, B×0.72."""
    r, g, b = img.split()
    r_lut = [int(v * 0.55) for v in range(256)]
    g_lut = [int(v * 0.60) for v in range(256)]
    b_lut = [int(v * 0.72) for v in range(256)]
    return Image.merge('RGB', (r.point(r_lut), g.point(g_lut), b.point(b_lut)))


def _try_ai(vibe: str, img_bytes: bytes, z: int, x: int, y: int) -> bytes | None:
    """POST to AI_SERVICE_URL; return transformed PNG bytes, or None on failure."""
    try:
        import requests
        payload = {
            'style': vibe,
            'image_b64': base64.b64encode(img_bytes).decode(),
            'tile_z': z,
            'tile_x': x,
            'tile_y': y,
        }
        headers = {'Content-Type': 'application/json'}
        if _AI_KEY:
            headers['Authorization'] = f'Bearer {_AI_KEY}'
        resp = requests.post(_AI_URL, json=payload, headers=headers, timeout=30)
        resp.raise_for_status()
        if 'image' in resp.headers.get('Content-Type', ''):
            return resp.content
        return base64.b64decode(resp.json()['image_b64'])
    except Exception:
        log.warning('AI tile transform failed vibe=%s z=%d x=%d y=%d', vibe, z, x, y, exc_info=True)
        return None
