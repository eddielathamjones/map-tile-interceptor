'use strict';

// Per-vibe effects that a map stylesheet can't express: overlays drawn over
// the map, toggles in the menu's Effects section, click behaviours and small
// animations. app.js calls vibeFx.apply(vibe) on every style load; each vibe's
// setup registers its own cleanup, so switching vibe undoes the last one.

(() => {
  const reducedMotion = matchMedia('(prefers-reduced-motion: reduce)').matches;
  let cleanup = [];
  let current = null;

  // ── Small helpers that register their own undo ─────────────────────────────

  function listen(target, event, fn) {
    if (target === map) {
      map.on(event, fn);
      cleanup.push(() => map.off(event, fn));
    } else {
      target.addEventListener(event, fn);
      cleanup.push(() => target.removeEventListener(event, fn));
    }
  }

  function every(ms, fn) {
    const id = setInterval(fn, ms);
    cleanup.push(() => clearInterval(id));
  }

  function el(tag, className, parent = document.getElementById('fx-layer')) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    parent.appendChild(node);
    cleanup.push(() => node.remove());
    return node;
  }

  function remember(key, value) {
    try {
      if (value === undefined) return localStorage.getItem(`mti-fx-${key}`);
      localStorage.setItem(`mti-fx-${key}`, value);
    } catch { /* storage unavailable: effects just don't persist */ }
    return null;
  }

  // A button in the menu's Effects section. `options` cycles through labels;
  // a plain on/off toggle passes ['Off', 'On'].
  function toggle(key, name, options, onChange) {
    const box = document.getElementById('fx-toggles');
    const btn = document.createElement('button');
    let index = Math.max(0, options.indexOf(remember(key)));
    const render = () => {
      btn.textContent = `${name}: ${options[index]}`;
      btn.classList.toggle('active', index > 0);
    };
    btn.addEventListener('click', () => {
      index = (index + 1) % options.length;
      remember(key, options[index]);
      render();
      onChange(options[index]);
    });
    box.appendChild(btn);
    document.getElementById('fx-section').hidden = false;
    cleanup.push(() => btn.remove());
    render();
    onChange(options[index]);
  }

  function layersWhere(test) {
    return map.getStyle().layers.filter(test);
  }

  // ── Mario ───────────────────────────────────────────────────────────────────

  // Building treatments; the first matches mario.mcss.
  const MARIO_BLOCKS = {
    'Plaster': { tile: 'fx:mario-plaster', color: '#f8d0a0', edge: '#c08040' },
    'Hard block': { tile: 'fx:mario-block', color: '#e09038', edge: '#883800' },
    'Castle stone': { tile: 'fx:mario-stone', color: '#9c9c9c', edge: '#3c3c3c' },
    'Brick': { tile: 'fx:mario-brick', color: '#c84c0c', edge: '#8c3408' },
  };

  function animateWater(frames) {
    if (reducedMotion || !map.getLayer('water')) return;
    let i = 0;
    every(550, () => {
      i = (i + 1) % frames.length;
      if (map.getLayer('water')) map.setPaintProperty('water', 'fill-pattern', frames[i]);
    });
  }

  // A square-wave blip for button presses, like a menu cursor.
  let audio = null;
  function blip(freq = 880) {
    audio ??= new AudioContext();
    const osc = audio.createOscillator();
    const gain = audio.createGain();
    osc.type = 'square';
    osc.frequency.setValueAtTime(freq, audio.currentTime);
    osc.frequency.setValueAtTime(freq * 1.5, audio.currentTime + 0.05);
    gain.gain.setValueAtTime(0.06, audio.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.001, audio.currentTime + 0.12);
    osc.connect(gain).connect(audio.destination);
    osc.start();
    osc.stop(audio.currentTime + 0.13);
  }

  function marioSound() {
    let on = false;
    const onClick = e => { if (on && e.target.closest('#menu button')) blip(); };
    listen(document, 'click', onClick);
    toggle('mario-sound', 'Sound', ['Off', 'On'], v => { on = v === 'On'; if (on) blip(660); });
  }

  const mario = () => {
    animateWater(['fx:mario-water', 'fx:mario-water-2']);
    toggle('mario-blocks', 'Buildings', Object.keys(MARIO_BLOCKS), name => {
      const b = MARIO_BLOCKS[name];
      if (map.getLayer('building')) {
        map.setPaintProperty('building', 'fill-pattern', b.tile);
        map.setPaintProperty('building', 'fill-color', b.color);
      }
      if (map.getLayer('building::after')) map.setPaintProperty('building::after', 'line-color', b.edge);
      if (map.getLayer('building-3d')) map.setPaintProperty('building-3d', 'fill-extrusion-pattern', b.tile);
    });
    marioSound();
  };

  const mariounder = () => {
    animateWater(['fx:mario-ug-water', 'fx:mario-ug-water-2']);
    marioSound();
  };

  // ── Tom Clancy ──────────────────────────────────────────────────────────────

  const pad = n => String(n).padStart(2, '0');
  const MONTHS = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC'];

  function dtg(d = new Date()) {
    return `${pad(d.getUTCDate())}${pad(d.getUTCHours())}${pad(d.getUTCMinutes())}${pad(d.getUTCSeconds())}Z ` +
           `${MONTHS[d.getUTCMonth()]} ${String(d.getUTCFullYear()).slice(2)}`;
  }

  function dm(v, pos, neg) {
    const a = Math.abs(v);
    const deg = Math.floor(a);
    return `${deg}°${((a - deg) * 60).toFixed(2).padStart(5, '0')}'${v >= 0 ? pos : neg}`;
  }

  // Lat/long ticks along the frame edges, at a step that gives ~6 per side.
  function gridTicks() {
    const box = el('div', 'tc-ticks');
    const STEPS = [0.0005, 0.001, 0.002, 0.005, 0.01, 0.02, 0.05, 0.1, 0.2, 0.5, 1, 2, 5, 10, 20];
    const draw = () => {
      box.replaceChildren();
      if (Math.abs(map.getBearing()) > 1 || map.getPitch() > 5) return;   // edges only hold flat and north-up
      const b = map.getBounds();
      const h = map.getContainer().clientHeight;
      const lngStep = STEPS.find(s => (b.getEast() - b.getWest()) / s <= 7) ?? 20;
      const latStep = STEPS.find(s => (b.getNorth() - b.getSouth()) / s <= 5) ?? 20;
      for (let lng = Math.ceil(b.getWest() / lngStep) * lngStep; lng < b.getEast(); lng += lngStep) {
        const x = map.project([lng, b.getNorth()]).x;
        for (const edge of ['top', 'bottom']) {
          const t = document.createElement('span');
          t.className = `tick tick-${edge}`;
          t.style.left = `${x}px`;
          t.textContent = dm(lng, 'E', 'W');
          box.appendChild(t);
        }
      }
      for (let lat = Math.ceil(b.getSouth() / latStep) * latStep; lat < b.getNorth(); lat += latStep) {
        const y = map.project([b.getWest(), lat]).y;
        if (y < 40 || y > h - 40) continue;
        for (const edge of ['left', 'right']) {
          const t = document.createElement('span');
          t.className = `tick tick-${edge}`;
          t.style.top = `${y}px`;
          t.textContent = dm(lat, 'N', 'S');
          box.appendChild(t);
        }
      }
    };
    listen(map, 'move', draw);
    draw();
  }

  function banners() {
    const top = el('div', 'tc-banner tc-banner-top');
    const bottom = el('div', 'tc-banner tc-banner-bottom');
    const draw = () => {
      const { lat, lng } = map.getCenter();
      top.textContent = `// UNCLASSIFIED // EXERCISE EXERCISE EXERCISE // DTG ${dtg()} //`;
      bottom.textContent = `// GRID ${dm(lat, 'N', 'S')} ${dm(lng, 'E', 'W')} // ALT Z${map.getZoom().toFixed(1)} ` +
                           `// HDG ${pad(Math.round((map.getBearing() + 360) % 360)).padStart(3, '0')} //`;
    };
    every(1000, draw);
    listen(map, 'move', draw);
    draw();
  }

  // Click a feature: brackets close on it and a readout types out.
  function targetLock() {
    let lock = null;
    const clear = () => { lock?.remove(); lock = null; };
    listen(map, 'click', e => {
      clear();
      const feats = map.queryRenderedFeatures(e.point);
      const f = feats.find(x => x.layer.type === 'symbol') ?? feats[0];
      lock = el('div', 'tc-lock');
      lock.style.left = `${e.point.x}px`;
      lock.style.top = `${e.point.y}px`;
      const read = document.createElement('pre');
      lock.appendChild(read);
      const name = f?.properties?.name_en || f?.properties?.name || 'UNKNOWN';
      const cls = (f?.properties?.class || f?.layer?.['source-layer'] || 'CONTACT').toUpperCase();
      const conf = 70 + (Math.abs(Math.round(e.lngLat.lat * 1000)) % 29);
      const lines = ['TGT ACQ', `${dm(e.lngLat.lat, 'N', 'S')} ${dm(e.lngLat.lng, 'E', 'W')}`,
                     `${cls} // ${String(name).toUpperCase()}`, `CONF ${conf}%`];
      let i = 0;
      const typeLine = () => {
        if (!lock || i >= lines.length) return;
        read.textContent += (i ? '\n' : '') + lines[i++];
        setTimeout(typeLine, reducedMotion ? 0 : 220);
      };
      typeLine();
    });
    listen(map, 'movestart', clear);
    cleanup.push(clear);
  }

  // Sentinel-2 cloudless imagery (EOX, CC BY-NC-SA 4.0), greyed and tinted
  // phosphor green under the vector roads, like recon footage.
  function satellite() {
    const SRC = 'tc-sat', LAYER = 'tc-sat', TINT = 'tc-sat-tint';
    let rec = null;
    const remove = () => {
      for (const id of [TINT, LAYER]) if (map.getLayer(id)) map.removeLayer(id);
      if (map.getSource(SRC)) map.removeSource(SRC);
      rec?.remove(); rec = null;
    };
    cleanup.push(remove);
    toggle('tc-sat', 'Sat pass', ['Off', 'On'], v => {
      remove();
      if (v !== 'On') return;
      map.addSource(SRC, {
        type: 'raster', tileSize: 256, maxzoom: 15,
        tiles: ['https://tiles.maps.eox.at/wmts/1.0.0/s2cloudless-2020_3857/default/g/{z}/{y}/{x}.jpg'],
        attribution: 'Sentinel-2 cloudless by <a href="https://s2maps.eu" target="_blank" rel="noopener">EOX IT Services GmbH</a> (contains modified Copernicus Sentinel data 2020)',
      });
      const before = map.getStyle().layers.find(l => l['source-layer'] === 'transportation')?.id;
      map.addLayer({ id: LAYER, type: 'raster', source: SRC,
                     paint: { 'raster-saturation': -1, 'raster-contrast': 0.25, 'raster-brightness-max': 0.55 } }, before);
      map.addLayer({ id: TINT, type: 'background', paint: { 'background-color': '#00ff41', 'background-opacity': 0.16 } }, before);
      rec = el('div', 'tc-rec');
      let frame = 0;
      const tick = setInterval(() => { if (rec) rec.textContent = `● REC  FRM ${String(++frame).padStart(6, '0')}`; }, 40);
      cleanup.push(() => clearInterval(tick));
    });
  }

  const tomclancy = () => {
    gridTicks();
    banners();
    if (!reducedMotion) el('div', 'tc-sweep');
    targetLock();
    satellite();
  };

  // ── Deco ────────────────────────────────────────────────────────────────────

  const deco = () => {
    if (!reducedMotion) el('div', 'deco-sheen');
  };

  // ── Blueprint ───────────────────────────────────────────────────────────────

  // Roads draw themselves in, motorways first, like a plotter pen.
  function plotterReveal() {
    if (reducedMotion) return;
    const order = id => (/motorway|trunk/.test(id) ? 0 : /primary/.test(id) ? 1 : /secondary|tertiary/.test(id) ? 2
                        : /minor|street|link/.test(id) ? 3 : 4);
    for (const l of layersWhere(l => l.type === 'line' && l['source-layer'] === 'transportation')) {
      const target = map.getPaintProperty(l.id, 'line-opacity') ?? 1;
      map.setPaintProperty(l.id, 'line-opacity-transition', { duration: 0, delay: 0 });
      map.setPaintProperty(l.id, 'line-opacity', 0);
      requestAnimationFrame(() => {
        if (!map.getLayer(l.id)) return;
        map.setPaintProperty(l.id, 'line-opacity-transition', { duration: 700, delay: 300 + order(l.id) * 450 });
        map.setPaintProperty(l.id, 'line-opacity', target);
      });
    }
  }

  const blueprint = () => {
    el('div', 'bp-aged');
    plotterReveal();
  };

  // ── Nouveau ─────────────────────────────────────────────────────────────────

  // Poster mode: the view cropped into a tall arched panel, with the place
  // name lettered in a cartouche below, like a Mucha poster.
  function posterFrame() {
    let svg = null;
    const NS = 'http://www.w3.org/2000/svg';
    const draw = () => {
      if (!svg) return;
      const { clientWidth: W, clientHeight: H } = map.getContainer();
      const pw = Math.min(W - 48, H * 0.62), ph = H - 48 - 64;
      const x0 = (W - pw) / 2, y0 = 24, r = pw / 2;
      const panel = `M${x0},${y0 + ph} V${y0 + r} A${r},${r} 0 0 1 ${x0 + pw},${y0 + r} V${y0 + ph} Z`;
      const title = (document.getElementById('export-title').value.trim() || guessTitle() || '').toUpperCase();
      svg.setAttribute('viewBox', `0 0 ${W} ${H}`);
      svg.innerHTML = `
        <path fill="#efe2c2" fill-rule="evenodd" d="M0,0 H${W} V${H} H0 Z ${panel}"/>
        <path d="${panel}" fill="none" stroke="#3d2a20" stroke-width="5"/>
        <path d="${panel}" fill="none" stroke="#e0ac3e" stroke-width="2" transform="translate(0 0)" stroke-dasharray="1 7" stroke-linecap="round"/>
        <rect x="${x0 - 10}" y="${y0 + ph + 10}" width="${pw + 20}" height="44" rx="22" fill="#3d2a20"/>
        <rect x="${x0 - 6}" y="${y0 + ph + 14}" width="${pw + 12}" height="36" rx="18" fill="none" stroke="#e0ac3e" stroke-width="1.5"/>
        <text x="${W / 2}" y="${y0 + ph + 39}" text-anchor="middle" fill="#f6ecd2"
              font-family="Federo, Georgia, serif" font-size="20" letter-spacing="4"></text>`;
      svg.querySelector('text').textContent = title;    // map data or typed title, never markup
    };
    toggle('nv-poster', 'Poster', ['Off', 'On'], v => {
      svg?.remove(); svg = null;
      if (v !== 'On') return;
      svg = document.createElementNS(NS, 'svg');
      svg.setAttribute('class', 'nv-poster');
      document.getElementById('fx-layer').appendChild(svg);
      cleanup.push(() => svg?.remove());
      draw();
    });
    listen(map, 'moveend', draw);
    listen(window, 'resize', draw);
  }

  const nouveau = () => posterFrame();

  // ── Noir ────────────────────────────────────────────────────────────────────

  // Rain on the lens: short streaks running down, drawn on a canvas.
  function rain() {
    let canvas = null, frame = 0;
    const stop = () => { cancelAnimationFrame(frame); canvas?.remove(); canvas = null; };
    cleanup.push(stop);
    toggle('noir-rain', 'Weather', ['Dry', 'Raining'], v => {
      stop();
      if (v !== 'Raining') return;
      canvas = el('canvas', 'noir-rain');
      const ctx = canvas.getContext('2d');
      const drops = Array.from({ length: 140 }, () => ({ x: Math.random(), y: Math.random(), v: 0.4 + Math.random() }));
      const step = () => {
        const { clientWidth: w, clientHeight: h } = canvas;
        if (canvas.width !== w) { canvas.width = w; canvas.height = h; }
        ctx.clearRect(0, 0, w, h);
        ctx.strokeStyle = 'rgba(216, 210, 194, 0.22)';
        ctx.lineWidth = 1;
        ctx.beginPath();
        for (const d of drops) {
          const x = d.x * w, y = d.y * h;
          ctx.moveTo(x, y);
          ctx.lineTo(x - 2, y + 14 * d.v);
          if (!reducedMotion) d.y += 0.012 * d.v;
          if (d.y > 1) { d.y = -0.05; d.x = Math.random(); }
        }
        ctx.stroke();
        if (!reducedMotion) frame = requestAnimationFrame(step);
      };
      step();
    });
  }

  // Click the map to mark a scene: a chalk outline and a typed caption.
  function crimeScenes() {
    const markers = [];
    const CHALK = `<svg viewBox="0 0 60 90" width="40" height="60" aria-hidden="true"><path fill="none" stroke="#e8e4da" stroke-width="2.5" stroke-linejoin="round"
      d="M30,6 c6,0 9,5 9,10 c0,5 -3,9 -7,10 l10,4 l14,-8 l3,4 l-14,12 l-4,14 l6,30 l-6,2 l-10,-24 l-10,24 l-6,-2 l6,-30 l-4,-14 l-14,-12 l3,-4 l14,8 l10,-4 c-4,-1 -7,-5 -7,-10 c0,-5 3,-10 9,-10 z"/></svg>`;
    listen(map, 'click', e => {
      const box = [[e.point.x - 40, e.point.y - 40], [e.point.x + 40, e.point.y + 40]];
      const near = map.queryRenderedFeatures(box).filter(f => f.properties?.name && f.layer.type === 'symbol');
      const road = near.find(f => f.layer['source-layer'] === 'transportation_name') ?? near[0];
      const where = road ? (road.properties.name_en || road.properties.name) : `${e.lngLat.lat.toFixed(3)}, ${e.lngLat.lng.toFixed(3)}`;
      const mins = Math.abs(Math.round(e.lngLat.lng * 1e4)) % 60;
      const node = document.createElement('div');
      node.className = 'noir-scene';
      node.innerHTML = CHALK;
      const caption = document.createElement('span');
      caption.textContent = `LAST SEEN: ${where}, 2:${String(mins).padStart(2, '0')} A.M.`;   // map data, never HTML
      node.appendChild(caption);
      node.addEventListener('click', ev => { ev.stopPropagation(); marker.remove(); });
      const marker = new maplibregl.Marker({ element: node, anchor: 'bottom' }).setLngLat(e.lngLat).addTo(map);
      markers.push(marker);
      if (markers.length > 3) markers.shift().remove();
    });
    cleanup.push(() => markers.forEach(m => m.remove()));
  }

  const noir = () => {
    el('div', 'noir-blinds');
    rain();
    crimeScenes();
  };

  // ── Registry ────────────────────────────────────────────────────────────────

  const VIBE_FX = { mario, mariounder, tomclancy, deco, blueprint, nouveau, noir };

  window.vibeFx = {
    apply(vibe) {
      cleanup.reverse().forEach(fn => { try { fn(); } catch { /* layer already gone with the old style */ } });
      cleanup = [];
      document.getElementById('fx-section').hidden = true;
      current = vibe;
      VIBE_FX[vibe]?.();
    },
    get current() { return current; },
  };
})();
