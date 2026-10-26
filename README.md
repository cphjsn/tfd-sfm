# TFD-SfM project page

Static page (Bulma + three.js from CDNs, no build step) for *Track-Free Dense Structure from
Motion* (WACV 2027). Private until the paper links and the code release are ready.

## Preview

```bash
python scripts/serve.py         # then open http://127.0.0.1:8765
```

The gallery's 3D replays load their data with `fetch`, so the page needs to be served over HTTP
(opening `index.html` from disk does not work). `serve.py` is `python -m http.server` plus HTTP
Range requests, which Safari needs to play the teaser videos, and no caching, so edits show up on
a plain reload. Browsers still cache modules loaded with `import()`, and GitHub Pages lets them
cache everything for a while: after editing the page's CSS or JS, bump the `?v=N` in `index.html`
(three places) and in the `import()` of `static/js/gallery.js`. Media and replay data re-rendered under the same name need
`ASSET_VERSION` in `static/js/gallery.js` and the `?v=` of the `fetch` in `static/js/viewer.js` bumped.

## Layout

| path | content |
|---|---|
| `index.html` | the page; `TODO` comments mark the links still to fill in |
| `static/css/index.css` | style |
| `static/js/gallery.js` | teaser grid and the per-dataset gallery (tabs, thumbnails, caption) |
| `static/js/viewer.js` | the gallery's three.js replay of the optimisation, with an iteration slider |
| `data/scenes.js` | the gallery's scenes and their 10k-iteration RRA@5 / RTA@5 (`scripts/collect_scenes.py`) |
| `data/viewer/<id>/` | replay data of every scene, ~6.5 MB each (`scripts/export_viewer.py`) |
| `assets/media/gif/<id>.gif`, `thumb/<id>.jpg`, `poster/<id>.jpg` | per scene: 1280x960 GIF (download link), thumbnail, and last frame (shown until the replay is clicked) |
| `assets/media/teaser/<id>.{mp4,jpg}` | the four teaser videos and their posters: white background, no legend (the caption gives the colours), rendered with `tools/render_gif.py --theme light --no_legend --scale 2 --max_points 150000` and ffmpeg (CRF 23, 12 fps) |
| `assets/media/method/` | the method section's GIFs: `toy_landmarks.gif` (the Gaussians of all matches, one wide-baseline match followed: its 2 Gaussians start apart and meet, toy, discs at 4 sigma), `eth3d_poses.gif` (absolute poses vs relative poses on a spanning tree, ETH3D delivery_area) and `mirror_worlds.gif` (the convex and the concave world of DTU scan82, turntable, both upright, points and cameras in depth order; world 2 framed on all its cameras, world 1 close to the object from the front and zoomed out to all its cameras from behind) |
| `assets/figures/` | figures from the paper, resized for the web |

Scene ids are `<dataset>_<scene>`: `dtu_scan45`, `mip360_room`, `eth3d_courtyard`,
`imc_florence_cathedral_side`, ...

## How the media were made

1. **Runs** (TUM GPU queue): `run_tfdsfm.py --iterations 10001 --keep_rrd --rrd_every 200
   --use_match_cache` for every scene of DTU (the 15 SPARF scans), Mip-NeRF 360 (7), ETH3D (13)
   and IMC2021 (9 scenes, 25-image bags `25bag_000` to `25bag_002`). Outputs in
   `~/tfdsfm_gifs3/<id>/` and, for the first four scenes, `~/tfdsfm_gifs2/` (`--rrd_every 100`).
2. **Selection and metrics**: `scripts/collect_scenes.py` reads the run logs, keeps the IMC bag with
   the highest RTA@5 per scene (best of up to ten bags), writes `data/scenes.js`, the render queue
   and (`--viewer_queue`) the export queue. `scripts/refresh.sh` runs it in a slurm job and starts
   the CPU workers.
3. **Rendering** (TUM CPU queue, `scripts/render_scene.sh`): `tools/render_gif.py --scale 2
   --max_points 150000` of the tfdsfm repository (upright view, green ground-truth cameras drawn
   over the points), then ffmpeg to MP4 (CRF 23, 12 fps) and the poster and thumbnail JPEGs.
4. **3D replays** (TUM CPU queue): `scripts/export_viewer.py <tfdsfm repo> <rrd> <out>/<id> --every N`,
   copied to `data/viewer/`. Every camera is exported (the GIFs draw at most 60, the viewer can zoom).
5. **Method GIFs**:
   - `toy_landmarks.gif`: `scripts/render_toy_gif.py <dump.pkl> assets/media/method/toy_landmarks.gif`.
     The dump holds the trajectories that `pba/proba_rewrite/scripts/toy_rrd_compare.py` caches in its
     GIF4 mode (`fig/.gif4_ncam24_noise4_seed2.pkl`: the paper's toy, 24 cameras, 4 px, seed 2) and the
     toy scene. It was written by a copy of that script with every output path moved to a scratch
     folder and a `pickle.dump` of `cells`, `cen_gt`, `Rc2w_gt`, `pts_of_cam`, `obs_cams`, `colors`
     before `def sample_idx`, run with `BASIN_NCAM=24 NOISE_PX=4 SEED=2 GIF4=1`.
   - `eth3d_poses.gif`: `scripts/render_tree_gif.py <tfdsfm repo> <absolute.rrd> <relative.rrd> out.gif`, the
     recordings of `run_tfdsfm.py --rrd_every 200 --iterations 10001` on delivery_area with
     `--relative_poses false` (`~/tfdsfm_gifs3/abs_eth3d_delivery_area/`) and with the default
     (`~/tfdsfm_gifs3/eth3d_delivery_area/`).
   - `mirror_worlds.gif`: `scripts/render_mirror_gif.py <tfdsfm repo> <dtu_scan82 rrd> <its run log> out.gif --max_points 45000 --frames 60 --scale 1.5`
     (recording `~/tfdsfm_gifs3/dtu_scan82/`, log `~/tfdsfm_gifs3/logs/dtu_scan82.log`).
5. **Results table**: `scripts/paper_table.py <overleaf>/sec/experiments.tex` prints the table rows
   from the paper's main table.

The page shows 10k-iteration runs. The paper's numbers use 30k iterations, which the gallery
intro says.
