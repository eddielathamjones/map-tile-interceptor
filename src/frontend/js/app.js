'use strict';

// ── Vibe switcher ─────────────────────────────────────────────────────────────

const VIBES = {
  default:      { label: 'Default',     styleUrl: 'https://tiles.openfreemap.org/styles/liberty' },
  noir:         { label: 'Noir',        styleUrl: '/api/tiles/style/noir' },
  mockva:       { label: 'Mockva',      styleUrl: '/api/tiles/style/mockva' },
  vintage:      { label: 'Vintage',     styleUrl: '/api/tiles/style/vintage'     },
  toner:        { label: 'Toner',       styleUrl: '/api/tiles/style/toner'       },
  blueprint:    { label: 'Blueprint',   styleUrl: '/api/tiles/style/blueprint'   },
  dark:         { label: 'Dark',        styleUrl: '/api/tiles/style/dark'        },
  watercolor:   { label: 'Watercolor',  styleUrl: '/api/tiles/style/watercolor'  },
  highcontrast: { label: 'Hi-Contrast', styleUrl: '/api/tiles/style/highcontrast' },
  mario:        { label: 'Mario',       styleUrl: '/api/tiles/style/mario'       },
  simcity:      { label: 'SimCity',     styleUrl: '/api/tiles/style/simcity'     },
  tomclancy:    { label: 'Tom Clancy',  styleUrl: '/api/tiles/style/tomclancy'   },
  deco:         { label: 'Deco',        styleUrl: '/api/tiles/style/deco'        },
  metro:        { label: 'Metro',       styleUrl: '/api/tiles/style/metro'       },
};

const STORAGE_KEY  = 'mti-vibe';
const DEFAULT_VIBE = 'default';

function currentVibe() {
  const saved = localStorage.getItem(STORAGE_KEY);
  return (saved && VIBES[saved]) ? saved : DEFAULT_VIBE;
}

function switchVibe(vibe) {
  if (!VIBES[vibe]) return;
  localStorage.setItem(STORAGE_KEY, vibe);
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

const map = new maplibregl.Map({
  container: 'map',
  style: VIBES[currentVibe()].styleUrl,
  center: [0, 20],
  zoom: 1.8,
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
});

// ── Init ──────────────────────────────────────────────────────────────────────

buildVibePicker();
buildPoiPanel();
