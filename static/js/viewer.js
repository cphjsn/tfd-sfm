// Interactive replay of the cold-start optimisation: the point cloud and cameras of every
// snapshot (data/viewer/<id>/, written by scripts/export_viewer.py), with an iteration slider.
// Point k is the same match in every snapshot, so frames are interpolated linearly.
import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";

const FPS = 12; // snapshots per second during playback, as the GIFs

// ui: {canvas, slider, playBtn, iterLabel, status, resetBtn}. Returns {load(id), suspend()}.
export function createViewer(ui) {
  const { canvas, slider, playBtn, iterLabel, status, resetBtn } = ui;
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.setClearColor(0x101010);
  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(40, 4 / 3, 0.01, 100);
  camera.up.set(0, 0, 1);
  const controls = new OrbitControls(camera, canvas);
  controls.enableDamping = true;

  const pointGeom = new THREE.BufferGeometry();
  const points = new THREE.Points(pointGeom, new THREE.PointsMaterial({ size: 0.012, vertexColors: true, sizeAttenuation: true }));
  const estGeom = new THREE.BufferGeometry();
  const gtGeom = new THREE.BufferGeometry();
  const estLines = new THREE.LineSegments(estGeom, new THREE.LineBasicMaterial({ color: 0xff922b }));
  const gtLines = new THREE.LineSegments(gtGeom, new THREE.LineBasicMaterial({ color: 0x51cf66 }));
  scene.add(points, gtLines, estLines);

  let data = null; // {meta, positions (Int16Array), cameras (Float32Array)}
  let playing = true;
  let loadToken = 0;
  const cache = new Map(); // id -> promise of the loaded data

  // The render loop only runs with a scene loaded, the canvas on screen and the tab in front,
  // and not while the gallery shows a poster over the canvas (suspend()).
  let visible = false, running = false, suspended = false, last = performance.now();
  const active = () => data && visible && !document.hidden && !suspended;
  function wake() {
    if (running || !active()) return;
    running = true;
    last = performance.now();
    requestAnimationFrame(tick);
  }
  new IntersectionObserver((entries) => { visible = entries[0].isIntersecting; wake(); }).observe(canvas);
  document.addEventListener("visibilitychange", wake);

  function resetView() {
    // behind the cameras at 30 degrees elevation, as tools/render_gif.py (+x = their mean viewing direction)
    const r = 4.0, elev = Math.PI / 6;
    camera.position.set(-r * Math.cos(elev), 0, r * Math.sin(elev));
    controls.target.set(0, 0, 0);
    controls.update();
  }

  function resize() {
    const w = canvas.clientWidth, h = canvas.clientHeight;
    const pr = renderer.getPixelRatio();
    if (canvas.width !== Math.round(w * pr) || canvas.height !== Math.round(h * pr)) {
      renderer.setSize(w, h, false);
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
    }
  }

  function setPlaying(p, label) {
    playing = p;
    playBtn.textContent = label || (p ? "Pause" : "Play");
  }

  function setFrame(x) {
    if (!data) return;
    const { meta, positions, cameras } = data;
    const n = meta.frames;
    const i0 = Math.min(Math.floor(x), n - 1), i1 = Math.min(i0 + 1, n - 1), a = x - i0;
    const P = meta.points, s = 1 / meta.position_scale;
    const pos = pointGeom.attributes.position.array;
    const o0 = i0 * P * 3, o1 = i1 * P * 3;
    for (let k = 0; k < P * 3; k++) pos[k] = ((1 - a) * positions[o0 + k] + a * positions[o1 + k]) * s;
    pointGeom.attributes.position.needsUpdate = true;

    const per = (meta.est_edges + meta.gt_edges) * 6; // floats per frame
    const est = estGeom.attributes.position.array, gt = gtGeom.attributes.position.array;
    const c0 = i0 * per, c1 = i1 * per, ne = meta.est_edges * 6;
    for (let k = 0; k < ne; k++) est[k] = (1 - a) * cameras[c0 + k] + a * cameras[c1 + k];
    for (let k = 0; k < meta.gt_edges * 6; k++) gt[k] = (1 - a) * cameras[c0 + ne + k] + a * cameras[c1 + ne + k];
    estGeom.attributes.position.needsUpdate = true;
    gtGeom.attributes.position.needsUpdate = true;

    const it = Math.round((1 - a) * meta.iterations[i0] + a * meta.iterations[i1]);
    iterLabel.textContent = `iteration ${it.toLocaleString("en-US")}`;
  }

  function fetchScene(id) {
    if (!cache.has(id)) {
      const base = `data/viewer/${id}`;
      const get = (name, kind) => fetch(`${base}/${name}?v=2`).then((r) => {  // ?v=: see gallery.js
        if (!r.ok) throw new Error(`${name}: HTTP ${r.status}`);
        return kind === "json" ? r.json() : r.arrayBuffer();
      });
      const p = Promise.all([get("meta.json", "json"), get("positions.bin"), get("colors.bin"), get("cameras.bin")]);
      p.catch(() => cache.delete(id)); // allow a retry
      cache.set(id, p);
    }
    return cache.get(id);
  }

  async function load(id) {
    const token = ++loadToken;
    suspended = false;
    status.textContent = "Loading…";
    status.hidden = false;
    let parts;
    try {
      parts = await fetchScene(id);
    } catch (e) {
      if (token === loadToken) status.textContent = `Could not load ${id} (${e.message}). Serve the page over HTTP.`;
      return;
    }
    if (token !== loadToken) return; // another scene was picked meanwhile
    const [meta, pos, col, cam] = parts;
    data = { meta, positions: new Int16Array(pos), cameras: new Float32Array(cam) };
    pointGeom.setAttribute("position", new THREE.BufferAttribute(new Float32Array(meta.points * 3), 3));
    pointGeom.setAttribute("color", new THREE.BufferAttribute(new Uint8Array(col), 3, true));
    estGeom.setAttribute("position", new THREE.BufferAttribute(new Float32Array(meta.est_edges * 6), 3));
    gtGeom.setAttribute("position", new THREE.BufferAttribute(new Float32Array(meta.gt_edges * 6), 3));
    slider.max = String(meta.frames - 1);
    slider.value = "0";
    resetView();
    setFrame(0);
    status.hidden = true;
    setPlaying(true);
    wake();
  }

  slider.addEventListener("input", () => { setPlaying(false); setFrame(parseFloat(slider.value)); });
  playBtn.addEventListener("click", () => {
    if (data && parseFloat(slider.value) >= data.meta.frames - 1) slider.value = "0";
    setPlaying(!playing);
  });
  resetBtn.addEventListener("click", resetView);

  function tick(now) {
    const dt = Math.min((now - last) / 1000, 0.1);
    last = now;
    resize();
    if (playing && data) {
      const x = Math.min(parseFloat(slider.value) + dt * FPS, data.meta.frames - 1);
      slider.value = String(x);
      setFrame(x);
      if (x >= data.meta.frames - 1) setPlaying(false, "Replay");
    }
    controls.update();
    renderer.render(scene, camera);
    if (active()) requestAnimationFrame(tick);
    else running = false;
  }
  resetView();
  return { load, suspend: () => { suspended = true; } };
}
