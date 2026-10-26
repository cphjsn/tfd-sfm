#!/usr/bin/env python3
"""Collect the gallery runs into data/scenes.js and print the render queue (run on the TUM server).

Every scene was run with run_tfdsfm.py --iterations 10001 --keep_rrd --rrd_every N into
<root>/<run>/, with its log in <root>/logs/<run>.log. For IMC2021 each scene was run on several
25-image bags (imc_<scene>_<bag>); the bag with the highest RTA@5 (then RRA@5) is shown.

A render records the recording it was made from (render/src/<id>.txt, see render_scene.sh); a
scene is queued again when its selected recording changes (a better IMC bag finished).

    python collect_scenes.py --js scenes.js --queue render_queue.txt
"""
import argparse
import glob
import json
import os
import re

HOME = os.path.expanduser("~")
ROOTS = [f"{HOME}/tfdsfm_gifs2", f"{HOME}/tfdsfm_gifs3"]  # gifs2: --rrd_every 100, gifs3: --rrd_every 200
RENDER_OUT = f"{HOME}/tfdsfm_gifs3/render"
RENDER_SH = f"{HOME}/tfdsfm_gifs3/page_scripts/render_scene.sh"
VIEWER_OUT = f"{HOME}/tfdsfm_gifs3/viewer"  # data/viewer/<id>/ of the page
EXPORT_PY = f"{HOME}/tfdsfm_gifs3/page_scripts/export_viewer.py"
TFDSFM = f"{HOME}/Desktop/git/tfdsfm"
CONDA = f"source {HOME}/miniconda3/etc/profile.d/conda.sh && conda activate proba"

DTU = ["scan8", "scan21", "scan30", "scan31", "scan34", "scan38", "scan40", "scan41", "scan45", "scan55",
       "scan63", "scan82", "scan103", "scan110", "scan114"]
MIP360 = ["bicycle", "bonsai", "counter", "garden", "kitchen", "room", "stump"]
ETH3D = ["courtyard", "delivery_area", "electro", "facade", "kicker", "meadow", "office", "pipes",
         "playground", "relief", "relief_2", "terrace", "terrains"]
IMC = ["british_museum", "florence_cathedral_side", "lincoln_memorial_statue", "london_bridge",
       "milan_cathedral", "mount_rushmore", "piazza_san_marco", "sagrada_familia", "st_pauls_cathedral"]

# run directory names: the four first GIF runs (tfdsfm_gifs2) have their own names
GIFS2 = {"dtu_scan45": "dtu45", "eth3d_courtyard": "courtyard", "mip360_room": "room"}
IMC_GIFS2 = {"florence_cathedral_side": ["imc_000", "imc_001", "imc_002"]}

DATASETS = [
    ("dtu", "DTU", "The 15 scans of the SPARF protocol, 49 images each.", "dtu", DTU),
    ("mip360", "Mip-NeRF 360", "All 7 scenes of the benchmark.", "mip360", MIP360),
    ("eth3d", "ETH3D", "All 13 high-resolution multi-view training scenes.", "eth3d", ETH3D),
    ("imc", "IMC2021", "All 9 phototourism test scenes. Each is one 25-image bag, the best of up to ten bags "
     "(25bag_000 to 25bag_009).", "imc", IMC),
]
TEASER = ["eth3d_courtyard", "mip360_room", "dtu_scan45", "imc_florence_cathedral_side"]


def find_run(run):
    """(root, run) of a finished run (metrics.txt and an .rrd), or None."""
    for root in ROOTS:
        d = f"{root}/{run}"
        if os.path.exists(f"{d}/metrics.txt") and glob.glob(f"{d}/*.rrd"):
            return root, run
    return None


def parse_log(path):
    """RRA@5, RTA@5, number of images and whether the mirror world was swapped in, from a run log."""
    text = open(path, errors="replace").read()
    res = re.search(r"== Result.*?RRA ([\d. ]+)\| RTA ([\d. ]+)\|", text)
    rra = [float(v) for v in res.group(1).split()] if res else None
    rta = [float(v) for v in res.group(2).split()] if res else None
    n = re.search(r"\[images\] loading (\d+) cameras", text)
    return dict(rra5=rra[2] if rra else None, rta5=rta[2] if rta else None,  # thresholds 1, 3, 5, 10, 30 deg
                images=int(n.group(1)) if n else None,
                mirror="it is swapped in" in text)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--js", required=True, help="output data/scenes.js")
    ap.add_argument("--queue", required=True, help="output render queue (one taskq line per scene not rendered yet)")
    ap.add_argument("--viewer_queue", help="output queue of the 3D-viewer exports not done yet")
    args = ap.parse_args()

    datasets, queue, viewer_queue, missing = [], [], [], []
    for key, name, note, prefix, scenes in DATASETS:
        entries = []
        for scene in scenes:
            sid = f"{prefix}_{scene}"
            if key == "imc":
                runs = IMC_GIFS2.get(scene) or sorted({os.path.basename(p) for root in ROOTS
                                                       for p in glob.glob(f"{root}/imc_{scene}_[0-9][0-9][0-9]")})
            else:
                runs = [GIFS2.get(sid, sid)]
            cands = []
            for run in runs:
                found = find_run(run)
                if found:
                    root, run = found
                    info = parse_log(f"{root}/logs/{run}.log")
                    cands.append((info["rta5"] or -1, info["rra5"] or -1, root, run, info))
            if not cands:
                missing.append(sid)
                continue
            _, _, root, run, info = max(cands)
            bag = None
            if key == "imc":
                m = re.search(r"25bag_(\d+)", open(f"{root}/logs/{run}.log", errors="replace").read())
                bag = f"25bag_{m.group(1)}" if m else None
            entries.append(dict(id=sid, name=scene, bag=bag, **info))
            rrd = glob.glob(f"{root}/{run}/*.rrd")[0]
            src = f"{RENDER_OUT}/src/{sid}.txt"
            stale = os.path.exists(src) and open(src).read().strip() != rrd
            every = 2 if root.endswith("gifs2") else 1
            if not os.path.exists(f"{RENDER_OUT}/mp4/{sid}.mp4") or stale:
                queue.append(f"mkdir -p {RENDER_OUT}/logs && bash {RENDER_SH} {rrd} {RENDER_OUT} {sid} {every} "
                             f"> {RENDER_OUT}/logs/{sid}.log 2>&1")
            vsrc = f"{VIEWER_OUT}/src/{sid}.txt"  # the recording the viewer data was exported from
            if not os.path.exists(vsrc) or open(vsrc).read().strip() != rrd:
                viewer_queue.append(f"mkdir -p {VIEWER_OUT}/logs {VIEWER_OUT}/src && {CONDA} && python {EXPORT_PY} "
                                    f"{TFDSFM} {rrd} {VIEWER_OUT}/{sid} --every {every} > {VIEWER_OUT}/logs/{sid}.log "
                                    f"2>&1 && echo {rrd} > {vsrc}")
        datasets.append(dict(key=key, name=name, note=note, scenes=entries))

    with open(args.js, "w") as f:
        f.write("// Written by scripts/collect_scenes.py: the scenes of the gallery and their 10k-iteration metrics.\n")
        f.write("window.TFDSFM_SCENES = ")
        json.dump(dict(teaser=TEASER, datasets=datasets), f, indent=1)
        f.write(";\n")
    with open(args.queue, "w") as f:
        f.write("".join(q + "\n" for q in queue))
    if args.viewer_queue:
        with open(args.viewer_queue, "w") as f:
            f.write("".join(q + "\n" for q in viewer_queue))
    print(f"{sum(len(d['scenes']) for d in datasets)} scenes, {len(queue)} to render, {len(viewer_queue)} to export, "
          f"missing: {' '.join(missing) or 'none'}")


if __name__ == "__main__":
    main()
