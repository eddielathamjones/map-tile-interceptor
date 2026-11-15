'use strict';

// ── Vibe switcher ─────────────────────────────────────────────────────────────

// Filled from /api/tiles/vibes: one entry per stylesheet in src/vibes/.
const VIBES = {};

async function loadVibes() {
  const list = await fetch('/api/tiles/vibes').then(r => r.json());
  for (const { id, label } of list) {
    VIBES[id] = {
      label,
      styleUrl: id === 'default' ? 'https://tiles.openfreemap.org/styles/liberty' : `/api/tiles/style/${id}`,
    };
  }
}

// Google Fonts used by the UI chrome of each vibe
const UI_FONTS = [
  'Press Start 2P', 'Share Tech Mono', 'Poiret One', 'Limelight', 'Special Elite', 'Bebas Neue', 'Fredoka:wght@500;600', 'Barlow Condensed:wght@600', 'Federo',
];

function loadVibeFonts() {
  const params = UI_FONTS.map(f => `family=${f.replace(/ /g, '+')}`).join('&');
  const link = document.createElement('link');
  link.rel = 'stylesheet';
  link.href = `https://fonts.googleapis.com/css2?${params}&display=swap`;
  document.head.appendChild(link);
}

const STORAGE_KEY  = 'mti-vibe';
const DEFAULT_VIBE = 'default';

function currentVibe() {
  const saved = localStorage.getItem(STORAGE_KEY);
  return (saved && VIBES[saved]) ? saved : DEFAULT_VIBE;
}

function switchVibe(vibe) {
  if (!VIBES[vibe]) return;
  localStorage.setItem(STORAGE_KEY, vibe);
  document.body.dataset.vibe = vibe;
  document.querySelectorAll('#vibe-picker button').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.vibe === vibe);
  });
  document.getElementById('menu-current').textContent = VIBES[vibe].label;
  map.setStyle(VIBES[vibe].styleUrl);
}

function buildVibePicker() {
  const picker = document.getElementById('vibe-picker');
  const active = currentVibe();
  for (const [key, { label }] of Object.entries(VIBES)) {
    const btn = document.createElement('button');
    btn.dataset.vibe = key;
    btn.textContent  = label;
    if (key === active) btn.classList.add('active');
    btn.addEventListener('click', () => switchVibe(key));
    picker.appendChild(btn);
  }
  document.getElementById('menu-current').textContent = VIBES[active].label;
}

// ── Menu ──────────────────────────────────────────────────────────────────────

function setMenuOpen(open) {
  document.getElementById('menu-panel').hidden = !open;
  document.getElementById('menu-btn').setAttribute('aria-expanded', String(open));
}

function initMenu() {
  const menu = document.getElementById('menu');
  document.getElementById('menu-btn').addEventListener('click', () => {
    setMenuOpen(document.getElementById('menu-panel').hidden);
  });
  document.addEventListener('click', e => { if (!menu.contains(e.target)) setMenuOpen(false); });
  document.addEventListener('keydown', e => { if (e.key === 'Escape') setMenuOpen(false); });
}

// ── POI toggles ───────────────────────────────────────────────────────────────

// Class values in the vector tile data for each category.
// poi_r* layers use ['get', 'class']; poi_transit uses the same.
const POI_GROUPS = {
  'Transport':  { transit: true },
  'Food':       { classes: ['restaurant', 'cafe', 'fast_food', 'bar', 'bakery'] },
  'Nature':     { classes: ['park', 'mountain', 'campsite'] },
  'Amenities':  { classes: ['hospital', 'pharmacy', 'police', 'school', 'bank', 'post', 'information'] },
  'Culture':    { classes: ['museum', 'cinema', 'lodging', 'place_of_worship'] },
};

const RANK_LAYERS    = ['poi_r1', 'poi_r7', 'poi_r20'];
const TRANSIT_LAYERS = ['poi_transit', 'airport'];

let activeGroups = new Set(Object.keys(POI_GROUPS));
let origFilters  = {};

function applyPoiFilter() {
  if (!map.isStyleLoaded()) return;

  // Compute enabled classes for rank-based POI layers
  const enabledClasses = [];
  for (const [name, cfg] of Object.entries(POI_GROUPS)) {
    if (activeGroups.has(name) && cfg.classes) enabledClasses.push(...cfg.classes);
  }

  const allNonTransitActive = Object.entries(POI_GROUPS)
    .filter(([, cfg]) => cfg.classes)
    .every(([name]) => activeGroups.has(name));

  RANK_LAYERS.forEach(id => {
    if (!map.getLayer(id)) return;
    if (enabledClasses.length === 0) {
      map.setLayoutProperty(id, 'visibility', 'none');
      return;
    }
    map.setLayoutProperty(id, 'visibility', 'visible');
    if (allNonTransitActive) {
      map.setFilter(id, origFilters[id] || null);
    } else {
      const classFilter = ['in', ['get', 'class'], ['literal', enabledClasses]];
      map.setFilter(id, origFilters[id]
        ? ['all', origFilters[id], classFilter]
        : classFilter);
    }
  });

  // Transit layers: toggle visibility directly
  const showTransport = activeGroups.has('Transport');
  TRANSIT_LAYERS.forEach(id => {
    if (map.getLayer(id)) {
      map.setLayoutProperty(id, 'visibility', showTransport ? 'visible' : 'none');
    }
  });
}

function toggleGroup(name) {
  if (activeGroups.has(name)) {
    activeGroups.delete(name);
  } else {
    activeGroups.add(name);
  }
  document.querySelectorAll('#poi-panel button').forEach(btn => {
    btn.classList.toggle('active', activeGroups.has(btn.dataset.group));
  });
  applyPoiFilter();
}

function buildPoiPanel() {
  const panel = document.getElementById('poi-panel');
  for (const name of Object.keys(POI_GROUPS)) {
    const btn = document.createElement('button');
    btn.dataset.group = name;
    btn.textContent   = name;
    btn.classList.add('active');
    btn.addEventListener('click', () => toggleGroup(name));
    panel.appendChild(btn);
  }
}

// ── Map init ──────────────────────────────────────────────────────────────────

let map;

function initMap() {
  map = new maplibregl.Map({
    container: 'map',
    style: VIBES[currentVibe()].styleUrl,
    center: [-110.9747, 32.2226],
    zoom: 11,
    minZoom: 1,
    maxZoom: 18,
    attributionControl: { compact: true },
    preserveDrawingBuffer: true,   // lets export read the canvas
  });

  map.on('style.load', () => {
    origFilters = {};
    RANK_LAYERS.forEach(id => {
      if (map.getLayer(id)) origFilters[id] = map.getFilter(id);
    });
    applyPoiFilter();
    updateCompassBearing();
    updateScaleBar();
  });
  map.on('rotate', updateCompassBearing);
  map.on('move', updateScaleBar);
}

// ── Compass rose ───────────────────────────────────────────────────────────────

function updateCompassBearing() {
  document.getElementById('compass-svg').style.transform = `rotate(${-map.getBearing()}deg)`;
}

// ── Scale bar ──────────────────────────────────────────────────────────────────

const FT = 0.3048;        // meters per foot
const MI = 1609.344;      // meters per mile

// Imperial snap distances in meters
const NICE_DISTANCES_M = [
  ...[50, 100, 200, 500, 1000].map(ft => ft * FT),
  ...[0.5, 1, 2, 5, 10, 20, 50, 100, 200, 500].map(mi => mi * MI),
];

function formatImperial(meters) {
  if (meters >= MI) {
    const miles = meters / MI;
    return (Number.isInteger(miles) ? miles : +miles.toFixed(1)) + ' mi';
  }
  return Math.round(meters / FT) + ' ft';
}

function updateScaleBar() {
  const { lat } = map.getCenter();
  const metersPerPx = (40075016.686 * Math.cos(lat * Math.PI / 180)) / (256 * Math.pow(2, map.getZoom()));
  const niceDist = NICE_DISTANCES_M.findLast(d => d <= metersPerPx * 100) ?? NICE_DISTANCES_M[0];
  document.getElementById('scale-line').style.width = `${niceDist / metersPerPx}px`;
  const distText = formatImperial(niceDist);
  document.getElementById('scale-label').textContent =
    document.body.dataset.vibe === 'tomclancy' ? `DIST: ${distText}` : distText;
}

// ── Init ──────────────────────────────────────────────────────────────────────

document.getElementById('compass').addEventListener('click', () => {
  map.easeTo({ bearing: 0, pitch: 0, duration: 300 });
});

loadVibeFonts();
buildPoiPanel();
loadVibes().then(() => {
  document.body.dataset.vibe = currentVibe();
  buildVibePicker();
  initMenu();
  initMap();
  initReport();
  initExport();
});

/* ─── Report modal ─────────────────────────────────────────────────── */
function initReport() {
const modal = document.getElementById('report-modal');
document.getElementById('report-btn').addEventListener('click', () => {
  setMenuOpen(false);
  modal.style.display = 'flex';
  setTimeout(() => document.getElementById('report-text').focus(), 60);
});
document.getElementById('report-close').addEventListener('click', () => {
  modal.style.display = 'none';
});
document.getElementById('report-modal').addEventListener('click', e => {
  if (e.target === document.getElementById('report-modal'))
    modal.style.display = 'none';
});
document.getElementById('report-submit').addEventListener('click', () => {
  const desc = document.getElementById('report-text').value.trim();
  if (!desc) { document.getElementById('report-text').focus(); return; }
  const btn = document.getElementById('report-submit');
  const context = [
    `Reported from ${location.href}`,
    `· active vibe: ${currentVibe()}`,
    `· viewport: ${window.innerWidth}×${window.innerHeight}`,
  ].join('\n');
  btn.textContent = 'Sending…';
  btn.disabled = true;
  fetch('/api/report', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ description: desc, context }),
  })
    .then(r => r.json())
    .then(data => {
      if (data.ok) {
        btn.textContent = 'Sent ✓';
        document.getElementById('report-text').value = '';
        setTimeout(() => {
          modal.style.display = 'none';
          btn.textContent = 'Send report →';
          btn.disabled = false;
        }, 1200);
      } else {
        btn.textContent = 'Send report →';
        btn.disabled = false;
        alert(data.error || 'Something went wrong.');
      }
    })
    .catch(() => {
      btn.textContent = 'Send report →';
      btn.disabled = false;
      alert('Network error — try again.');
    });
});
}

/* ─── Export: a finished sheet (margin, neat line, title band) ─────── */

// Place label layers, most to least title-worthy.
const TITLE_LAYERS = ['label_city_capital', 'label_city', 'label_town', 'label_village', 'label_other', 'label_state', 'label_country_1', 'label_country_2', 'label_country_3'];

// Name of the most prominent place label nearest the centre of the view.
function guessTitle() {
  const { width, height } = map.getCanvas().getBoundingClientRect();
  const cx = width / 2, cy = height / 2;
  for (const id of TITLE_LAYERS) {
    if (!map.getLayer(id)) continue;
    const feats = map.queryRenderedFeatures({ layers: [id] });
    let best = null, bestD = Infinity;
    for (const f of feats) {
      const name = f.properties['name:en'] || f.properties['name:latin'] || f.properties.name;
      if (!name || f.geometry.type !== 'Point') continue;
      const p = map.project(f.geometry.coordinates);
      const d = (p.x - cx) ** 2 + (p.y - cy) ** 2;
      if (d < bestD) { bestD = d; best = name; }
    }
    if (best) return best;
  }
  return '';
}

function formatCoord(v, pos, neg) {
  return `${Math.abs(v).toFixed(4)}° ${v >= 0 ? pos : neg}`;
}

// Opaque version of a CSS colour (UI backgrounds are often translucent).
function opaque(color) {
  const m = color.match(/rgba?\(([^)]+)\)/);
  if (!m) return color;
  const [r, g, b] = m[1].split(',').map(s => parseFloat(s));
  return `rgb(${r}, ${g}, ${b})`;
}

// The visible compass variant as a standalone image.
async function compassImage() {
  const svg = document.getElementById('compass-svg');
  const clone = svg.cloneNode(true);
  clone.removeAttribute('id');
  clone.style.transform = '';
  const hidden = [...svg.children].map(g => getComputedStyle(g).display === 'none');
  [...clone.children].forEach((g, i) => { if (hidden[i]) g.remove(); });
  clone.setAttribute('color', getComputedStyle(svg).color);
  clone.setAttribute('width', '200');
  clone.setAttribute('height', '200');
  const url = URL.createObjectURL(new Blob([new XMLSerializer().serializeToString(clone)], { type: 'image/svg+xml' }));
  try {
    const img = new Image();
    img.src = url;
    await img.decode();
    return img;
  } finally {
    URL.revokeObjectURL(url);
  }
}

// Render the map at `ratio` and wait until every tile is drawn.
function renderAt(ratio) {
  return new Promise(resolve => {
    map.setPixelRatio(ratio);
    map.once('idle', resolve);
    map.triggerRepaint();
  });
}

async function composeSheet() {
  const ratio = Math.max(2, window.devicePixelRatio || 1);
  const prevRatio = map.getPixelRatio();
  await renderAt(ratio);
  await document.fonts.ready;

  const cs = getComputedStyle(document.body);
  const v = name => cs.getPropertyValue(name).trim();
  const paper = opaque(v('--ui-bg'));
  const ink = v('--ui-color-active');
  const dim = v('--ui-color-dim');
  const font = v('--ui-font');

  const src = map.getCanvas();
  const W = src.width / ratio, H = src.height / ratio;   // CSS px
  const m = Math.round(Math.min(W, H) * 0.045);          // margin
  const band = 108;                                       // title band
  const out = document.createElement('canvas');
  out.width = (W + 2 * m) * ratio;
  out.height = (H + 2 * m + band) * ratio;
  const ctx = out.getContext('2d');
  ctx.scale(ratio, ratio);

  // Paper and map
  ctx.fillStyle = paper;
  ctx.fillRect(0, 0, W + 2 * m, H + 2 * m + band);
  ctx.drawImage(src, m, m, W, H);
  await renderAt(prevRatio);

  // Neat line round the map and a hairline border round the sheet
  ctx.strokeStyle = ink;
  ctx.lineWidth = 1.5;
  ctx.strokeRect(m, m, W, H);
  ctx.lineWidth = 0.75;
  ctx.strokeRect(m / 2, m / 2, W + m, H + m + band);

  // Title block, left
  const title = document.getElementById('export-title').value.trim() || guessTitle() || 'Untitled';
  const { lat, lng } = map.getCenter();
  const date = new Date().toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' });
  const sub = [`${formatCoord(lat, 'N', 'S')}  ${formatCoord(lng, 'E', 'W')}`, VIBES[currentVibe()].label, date].join('   ·   ');
  const baseY = m + H + band / 2;
  ctx.textBaseline = 'alphabetic';
  ctx.fillStyle = ink;
  ctx.font = `34px ${font}`;
  ctx.letterSpacing = '0.08em';
  ctx.fillText(title.toUpperCase(), m, baseY + 4);
  ctx.fillStyle = dim;
  ctx.font = `12px ${font}`;
  ctx.letterSpacing = '0.12em';
  ctx.fillText(sub.toUpperCase(), m, baseY + 26);

  // Compass, right
  const cSize = 64;
  const cx = m + W - cSize / 2, cy = baseY - 4;
  const compass = await compassImage();
  ctx.save();
  ctx.translate(cx, cy);
  ctx.rotate(-map.getBearing() * Math.PI / 180);
  ctx.drawImage(compass, -cSize / 2, -cSize / 2, cSize, cSize);
  ctx.restore();

  // Scale bar, left of the compass (same distances as the on-screen bar)
  const line = document.getElementById('scale-line');
  const sw = line.getBoundingClientRect().width;
  const sx = cx - cSize / 2 - 24 - sw;
  ctx.fillStyle = ink;
  ctx.fillRect(sx, cy, sw, 2);
  ctx.fillRect(sx, cy - 5, 1.5, 7);
  ctx.fillRect(sx + sw - 1.5, cy - 5, 1.5, 7);
  ctx.font = `11px ${font}`;
  ctx.letterSpacing = '0.08em';
  ctx.textAlign = 'center';
  ctx.fillText(document.getElementById('scale-label').textContent, sx + sw / 2, cy + 18);
  if (map.getPitch() > 1) {
    ctx.fillStyle = dim;
    ctx.fillText('scale at centre', sx + sw / 2, cy - 10);
  }

  // Attribution, bottom right
  ctx.textAlign = 'right';
  ctx.fillStyle = dim;
  ctx.font = `9px ${font}`;
  ctx.letterSpacing = '0.06em';
  ctx.fillText('Map data © OpenStreetMap contributors · OpenMapTiles · OpenFreeMap · Relief: Natural Earth', m + W, m + H + band - 10);

  return out;
}

function sheetFilename() {
  const title = (document.getElementById('export-title').value.trim() || guessTitle() || 'map')
    .toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
  return `${title}-${currentVibe()}.png`;
}

async function withBusy(btn, fn) {
  const label = btn.textContent;
  btn.disabled = true;
  btn.textContent = 'Rendering…';
  try { await fn(); } finally { btn.disabled = false; btn.textContent = label; }
}

function initExport() {
  const titleInput = document.getElementById('export-title');
  document.getElementById('menu-btn').addEventListener('click', () => {
    if (!titleInput.value) titleInput.placeholder = guessTitle() || 'Title';
  });

  const pngBtn = document.getElementById('export-png');
  pngBtn.addEventListener('click', () => withBusy(pngBtn, async () => {
    const sheet = await composeSheet();
    const blob = await new Promise(r => sheet.toBlob(r, 'image/png'));
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = sheetFilename();
    a.click();
    setTimeout(() => URL.revokeObjectURL(a.href), 1000);
  }));

  const printBtn = document.getElementById('export-print');
  printBtn.addEventListener('click', () => withBusy(printBtn, async () => {
    const sheet = await composeSheet();
    const img = document.getElementById('print-img');
    img.src = sheet.toDataURL('image/png');
    await img.decode();
    setMenuOpen(false);
    window.print();
  }));
}
