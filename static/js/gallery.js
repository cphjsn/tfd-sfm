// Teaser grid and the per-dataset gallery of interactive replays, both driven by data/scenes.js
// (window.TFDSFM_SCENES, written by scripts/collect_scenes.py).
// Nothing heavy loads up front: a scene shows its last frame until the viewer clicks it, and
// three.js plus the scene's replay data (~6.5 MB) are only fetched then.

const DATA = window.TFDSFM_SCENES;
const MEDIA = "assets/media";
// ?v= on media and replay data (see viewer.js): bump it when files are re-rendered under the same name
const ASSET_VERSION = 2;
const media = (kind, id, ext) => `${MEDIA}/${kind}/${id}.${ext}?v=${ASSET_VERSION}`;
const $ = (id) => document.getElementById(id);

const byId = {};
DATA.datasets.forEach((d) => d.scenes.forEach((s) => { byId[s.id] = { scene: s, dataset: d }; }));

// ---------- teaser: one looping video per dataset, playing only while on screen ----------
const teaser = $("teaserGrid");
const onScreen = new IntersectionObserver((entries) => entries.forEach((e) => {
  if (e.isIntersecting) e.target.play().catch(() => {});
  else e.target.pause();
}));
DATA.teaser.forEach((id) => {
  const entry = byId[id];
  if (!entry) return;
  const cell = document.createElement("div");
  cell.className = "teaser-cell";
  const video = document.createElement("video");
  Object.assign(video, { muted: true, loop: true, playsInline: true, preload: "metadata" });
  video.poster = media("teaser", id, "jpg"); // white-background renders, see the README
  video.src = media("teaser", id, "mp4");
  const label = document.createElement("div");
  label.className = "label";
  label.textContent = `${entry.dataset.name} · ${entry.scene.name}`;
  cell.append(video, label);
  teaser.append(cell);
  onScreen.observe(video);
});

// ---------- gallery: dataset tabs, scene thumbnails and the 3D replay ----------
const tabs = document.querySelector("#datasetTabs ul");
const note = $("datasetNote");
const thumbs = $("sceneThumbs");
const caption = $("sceneCaption");
const placeholder = $("viewerPlaceholder");
const poster = $("viewerPoster");
const controlsRow = document.querySelector(".viewer-controls");

let viewer = null; // created (with three.js) on the first click
let current = null; // the scene shown in the caption
async function getViewer() {
  if (!viewer) {
    const { createViewer } = await import("./viewer.js?v=11"); // ?v=: see index.html
    viewer = createViewer({
      canvas: $("viewerCanvas"), slider: $("viewerSlider"), playBtn: $("viewerPlay"),
      iterLabel: $("viewerIteration"), status: $("viewerStatus"), resetBtn: $("viewerReset"),
    });
  }
  return viewer;
}

async function play(scene) {
  const status = $("viewerStatus");
  placeholder.hidden = true;
  controlsRow.classList.remove("is-idle");
  status.textContent = "Loading…";
  status.hidden = false;
  try {
    (await getViewer()).load(scene.id);
  } catch (e) { // e.g. no WebGL, or three.js could not be fetched from the CDN
    console.error(e);
    status.textContent = `The 3D viewer could not start: ${e.message}`;
  }
}

const fmt = (x) => (x === null || x === undefined ? "–" : x.toFixed(1));

// Shows a scene in the caption and the thumbnails; its replay starts now (a click on its
// thumbnail) or after a click on the poster (a tab switch, the first visit).
function showScene(scene, start) {
  current = scene;
  const parts = [
    `<b>${scene.name}</b>`,
    `${scene.images} images` + (scene.bag ? ` (bag <code>${scene.bag}</code>)` : ""),
    `RRA@5° ${fmt(scene.rra5)}`,
    `RTA@5° ${fmt(scene.rta5)}`,
  ];
  if (scene.mirror) parts.push("the mirror world is selected");
  parts.push(`<a href="${media("gif", scene.id, "gif")}" download>GIF</a>`);
  caption.innerHTML = parts.join('<span class="sep">·</span>');
  thumbs.querySelectorAll(".thumb").forEach((b) => b.classList.toggle("is-active", b.dataset.id === scene.id));
  if (start) {
    play(scene);
  } else {
    if (viewer) viewer.suspend();
    controlsRow.classList.add("is-idle");
    poster.src = media("poster", scene.id, "jpg");
    poster.alt = `${scene.name}, last iteration`;
    placeholder.hidden = false;
  }
}
placeholder.addEventListener("click", () => { if (current) play(current); });

function showDataset(dataset) {
  tabs.querySelectorAll("li").forEach((li) => li.classList.toggle("is-active", li.dataset.key === dataset.key));
  note.textContent = dataset.note || "";
  thumbs.replaceChildren();
  dataset.scenes.forEach((scene) => {
    const b = document.createElement("button");
    b.className = "thumb";
    b.dataset.id = scene.id;
    b.title = scene.name;
    const img = document.createElement("img");
    img.src = media("thumb", scene.id, "jpg");
    img.alt = scene.name;
    img.loading = "lazy";
    const span = document.createElement("span");
    span.textContent = scene.name;
    b.append(img, span);
    b.addEventListener("click", () => showScene(scene, true));
    thumbs.append(b);
  });
  if (dataset.scenes.length) showScene(dataset.scenes[0], false);
}

DATA.datasets.forEach((dataset) => {
  const li = document.createElement("li");
  li.dataset.key = dataset.key;
  const a = document.createElement("a");
  a.textContent = `${dataset.name} (${dataset.scenes.length})`;
  a.addEventListener("click", () => showDataset(dataset));
  li.append(a);
  tabs.append(li);
});

// #dtu, #mip360, #eth3d or #imc in the URL opens that dataset
const linked = DATA.datasets.find((d) => location.hash === `#${d.key}`);
const initial = linked || DATA.datasets[0];
if (initial) showDataset(initial);
if (linked) $("gallery").scrollIntoView();
