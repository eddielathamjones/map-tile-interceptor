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
  'Press Start 2P', 'Share Tech Mono', 'Poiret One', 'IM Fell English', 'Bebas Neue',
  'Atkinson Hyperlegible', 'Inter', 'Fredoka:wght@500;600', 'Barlow Condensed:wght@600', 'Federo',
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
  const sep = document.createElement('span');
  sep.textContent = '|';
  sep.style.cssText = 'color:var(--ui-border,rgba(255,255,255,0.12)); font-size:0.7rem; padding:0 2px; align-self:center;';
  picker.appendChild(sep);
  const reportBtn = document.createElement('button');
  reportBtn.id = 'report-btn';
  reportBtn.textContent = '⚑ report';
  reportBtn.title = 'Report an issue or suggestion';
  picker.appendChild(reportBtn);
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
  15.24,    // 50 ft
  30.48,    // 100 ft
  60.96,    // 200 ft
  152.4,    // 500 ft
  304.8,    // 1000 ft
  804.67,   // 0.5 mi
  1609.34,  // 1 mi
  3218.69,  // 2 mi
  8046.72,  // 5 mi
  16093.44, // 10 mi
  32186.88, // 20 mi
  80467.2,  // 50 mi
  160934.4, // 100 mi
  321868.8, // 200 mi
  804672,   // 500 mi
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
  initMap();
  initReport();
});

/* ─── Report modal ─────────────────────────────────────────────────── */
function initReport() {
const modal = document.getElementById('report-modal');
document.getElementById('report-btn').addEventListener('click', () => {
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
