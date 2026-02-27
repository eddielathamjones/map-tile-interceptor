'use strict';

// ── Vibe switcher ───────────────────────────────────────────────────────────────

const VIBES = {
  default:      { label: 'Default',     styleUrl: 'https://tiles.openfreemap.org/styles/liberty' },
  noir:         { label: 'Noir',        styleUrl: '/api/tiles/style/noir' },
  vintage:      { label: 'Vintage',     styleUrl: '/api/tiles/style/vintage',     hidden: true },
  toner:        { label: 'Toner',       styleUrl: '/api/tiles/style/toner',       hidden: true },
  blueprint:    { label: 'Blueprint',   styleUrl: '/api/tiles/style/blueprint',   hidden: true },
  dark:         { label: 'Dark',        styleUrl: '/api/tiles/style/dark',        hidden: true },
  watercolor:   { label: 'Watercolor',  styleUrl: '/api/tiles/style/watercolor',  hidden: true },
  highcontrast: { label: 'Hi-Contrast', styleUrl: '/api/tiles/style/highcontrast', hidden: true },
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
  for (const [key, { label, hidden }] of Object.entries(VIBES)) {
    if (hidden) continue;
    const btn = document.createElement('button');
    btn.dataset.vibe = key;
    btn.textContent  = label;
    if (key === active) btn.classList.add('active');
    btn.addEventListener('click', () => switchVibe(key));
    picker.appendChild(btn);
  }
}

// ── Map init ───────────────────────────────────────────────────────────────────

const map = new maplibregl.Map({
  container: 'map',
  style: VIBES[currentVibe()].styleUrl,
  center: [0, 20],
  zoom: 1.8,
  minZoom: 1,
  maxZoom: 10,
  attributionControl: { compact: true },
});

// ── Init ──────────────────────────────────────────────────────────────────────

buildVibePicker();
