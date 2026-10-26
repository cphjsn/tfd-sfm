#!/usr/bin/env python3
"""Export a --rrd_every recording for the page's 3D viewer (static/js/viewer.js).

Uses the frames of tools/render_gif.py (the snapshots of the reported world), turns them upright
and centres and scales every frame like the GIF, so that the scene fills the view while it grows
from unit depth. The snapshots keep the same subset of matches, so point k is the same match in
every frame and the viewer can interpolate between frames. The final state (all matches) is not
exported.

    python scripts/export_viewer.py <tfdsfm repo> <recording.rrd> data/viewer/<id> [--every 2]

Writes meta.json, colors.bin (uint8 RGB per point), positions.bin (int16 xyz per frame and point,
value / 16384 = normalised coordinate) and cameras.bin (float32 frustum edges per frame: the
estimated cameras, then the ground truth).
"""
import argparse
import json
import os
import sys

import numpy as np


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("tfdsfm", help="the tfdsfm repository (for tools/render_gif.py)")
    ap.add_argument("rrd")
    ap.add_argument("out")
    ap.add_argument("--every", type=int, default=1, help="use every k-th snapshot")
    ap.add_argument("--points", type=int, default=20000, help="points per frame")
    ap.add_argument("--max_cameras", type=int, default=0,
                    help="cameras per frame, evenly spaced (0 = all; the viewer can zoom, unlike the GIFs)")
    args = ap.parse_args()
    sys.path.insert(0, os.path.join(args.tfdsfm, "tools"))
    import render_gif as rg

    frames = rg.load_frames(args.rrd)[:-1][::args.every]  # snapshots only
    Q = rg.upright_rotation(frames[-1]["cameras"])
    frames = [rg.rotate_frame(f, Q) for f in frames]
    n_pts = min(len(f["xyz"]) for f in frames)
    if any(len(f["xyz"]) != n_pts for f in frames):
        print("warning: the snapshots have different point counts, truncating to the smallest")
    idx = np.sort(np.random.default_rng(0).choice(n_pts, min(args.points, n_pts), replace=False))
    rgb = rg.unpack_rgba(frames[-1]["rgb"][:n_pts])[idx]

    positions, cameras, iterations = [], [], []
    n_cams = None
    for f in frames:
        centre, scale = rg.normaliser(f)
        xyz = (f["xyz"][:n_pts][idx] - centre) / scale
        positions.append(np.clip(np.round(xyz * 16384), -32767, 32767).astype(np.int16))
        sets = []
        for cams in (f["cameras"], f["gt_cameras"]):
            keep = len(cams) if args.max_cameras <= 0 else min(len(cams), args.max_cameras)
            shown = np.unique(np.linspace(0, len(cams) - 1, keep).round().astype(int))
            edges = []
            for i in shown:
                R, t, K, wh = cams[i]
                c = -R.T @ t
                _, e = rg.frustum_lines(R, -R @ ((c - centre) / scale), K, wh, 0.06)
                edges.extend(e)
            sets.append(np.asarray(edges, dtype=np.float32).reshape(-1, 2, 3))
        if n_cams is None:
            n_cams = [len(s) for s in sets]
        cameras.append(np.concatenate(sets).reshape(-1))
        t = f["time"]
        iterations.append(int(round(t.total_seconds() * 100)) if hasattr(t, "total_seconds") else int(round(t / 1e7)))

    os.makedirs(args.out, exist_ok=True)
    np.stack(positions).tofile(os.path.join(args.out, "positions.bin"))
    (rgb * 255).round().astype(np.uint8).tofile(os.path.join(args.out, "colors.bin"))
    np.stack(cameras).astype(np.float32).tofile(os.path.join(args.out, "cameras.bin"))
    meta = dict(frames=len(frames), points=int(len(idx)), iterations=iterations, position_scale=16384,
                est_edges=n_cams[0], gt_edges=n_cams[1])
    with open(os.path.join(args.out, "meta.json"), "w") as f:
        json.dump(meta, f)
    size = sum(os.path.getsize(os.path.join(args.out, n)) for n in os.listdir(args.out))
    print(f"{args.out}: {len(frames)} frames, {len(idx)} points, {n_cams} edges, {size / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
