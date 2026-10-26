#!/usr/bin/env python3
"""The "relative poses on a spanning tree" GIF of the method section, on a real scene.

Two --rrd_every recordings of the same scene, identical but for the pose parameterization:
absolute poses (run_tfdsfm.py --relative_poses false, left) and relative poses chained along the
spanning tree of the view graph (the default, right; the tree is drawn as blue lines between the camera
centres, on top, read from the
rel_pose_path_* entities of its final state). Each run is drawn like tools/render_gif.py (upright,
every frame centred and scaled), estimated cameras orange, ground truth green, with the mean
relative-rotation error of the frame.

    python scripts/render_tree_gif.py <tfdsfm repo> <absolute.rrd> <relative.rrd> out.gif
"""
import argparse
import io
import os
import sys

import numpy as np

TREE = "#1864ab"  # the spanning tree


def rel_rot_err(R_est, R_gt):
    """Mean pairwise relative-rotation error in degrees between two lists of world-to-camera R."""
    n, e = len(R_est), []
    for i in range(n):
        for j in range(i + 1, n):
            d = (R_est[i] @ R_est[j].T) @ (R_gt[i] @ R_gt[j].T).T
            e.append(np.degrees(np.arccos(np.clip((np.trace(d) - 1) / 2, -1, 1))))
    return float(np.mean(e))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("tfdsfm", help="the tfdsfm repository (for tools/render_gif.py)")
    ap.add_argument("abs_rrd", help="recording with absolute poses")
    ap.add_argument("rel_rrd", help="recording with relative poses (the default)")
    ap.add_argument("out", help="output .gif")
    ap.add_argument("--every", type=int, default=1, help="use every k-th snapshot")
    ap.add_argument("--max_points", type=int, default=40000, help="points drawn per panel")
    ap.add_argument("--elev", type=float, default=60.0)
    ap.add_argument("--frame", choices=["cameras", "scene"], default="cameras",
                    help="frame the box around the cameras (default) or the cameras and the central points")
    ap.add_argument("--margin", type=float, default=1.3, help="--frame cameras: half the view in half-extents of the cameras")
    ap.add_argument("--point_alpha", type=float, default=0.6, help="opacity of the points, so that the tree stands out")
    ap.add_argument("--scale", type=float, default=1.75, help="resolution multiplier of the 640x320 frame")
    ap.add_argument("--fps", type=float, default=10.0)
    ap.add_argument("--hold", type=float, default=2.5, help="seconds the last frame is shown")
    args = ap.parse_args()
    sys.path.insert(0, os.path.join(args.tfdsfm, "tools"))
    import render_gif as rg
    import matplotlib.pyplot as plt
    import rerun as rr
    from PIL import Image

    def tree_edges(path):
        """(i, j) camera pairs of the spanning tree: the segments of the rel_pose_path_* strips of
        the final state, matched to the final camera centres."""
        rec = rr.dataframe.load_recording(path)
        entities = sorted({c.entity_path for c in rec.schema().component_columns()})
        w0 = rg.world_frames(rec, entities, 0)
        cen = np.array([-R.T @ t for R, t, _, _ in w0[max(w0)]["cameras"]])
        edges = set()
        for e in entities:
            if e.startswith("/rel_pose_path_"):
                for row in rg.read_entity(rec, e).values():
                    for s in row.get("strips", []):
                        s = np.asarray(s, float).reshape(-1, 3)
                        ids = [int(np.argmin(np.linalg.norm(cen - p, axis=1))) for p in s]
                        edges |= {(min(a, b), max(a, b)) for a, b in zip(ids[:-1], ids[1:]) if a != b}
        return sorted(edges)

    runs = []
    for path, label, tree in ((args.abs_rrd, "optimizing absolute poses", False),
                              (args.rel_rrd, "optimizing relative poses on a spanning tree", True)):
        frames = rg.load_frames(path)
        frames = frames[:-1][::args.every] + frames[-1:]
        Q = rg.upright_rotation(frames[-1]["cameras"])
        frames = [rg.rotate_frame(f, Q) for f in frames]
        fwd = np.mean([R.T @ np.array([0.0, 0.0, 1.0]) for R, _, _, _ in frames[-1]["cameras"]], axis=0)
        azim = float(np.degrees(np.arctan2(-fwd[1], -fwd[0])))
        runs.append(dict(frames=frames, label=label, edges=tree_edges(path) if tree else [], azim=azim))
    n = min(len(r["frames"]) for r in runs)
    print(f"{n} frames; spanning tree with {len(runs[1]['edges'])} edges")

    th = rg.THEMES["light"]
    res, half, cam_size = args.scale, 1.15, 0.06
    rng = np.random.default_rng(0)
    images = []
    for k in range(n):
        fig = plt.figure(figsize=(6.4, 3.2), dpi=100 * res)
        fig.patch.set_facecolor(th["bg"])
        for j, r in enumerate(runs):
            f = r["frames"][k if k < n - 1 else len(r["frames"]) - 1]  # the last frame: the final state
            ax = fig.add_axes([j * 0.5, 0.08, 0.5, 0.8], projection="3d", computed_zorder=False)
            ax.set_facecolor(th["bg"])
            if args.frame == "cameras":  # the box around the estimated cameras, with a margin
                cc = np.array([-R.T @ t for R, t, _, _ in f["cameras"]])
                lo, hi = cc.min(0), cc.max(0)
                centre, scale = (lo + hi) / 2, max((hi - lo).max() / 2 * args.margin / half, 1e-9)
            else:  # the cameras and the central points, as tools/render_gif.py
                centre, scale = rg.normaliser(f)
            xyz = (f["xyz"] - centre) / scale
            rgb = rg.unpack_rgba(f["rgb"]) if len(f["rgb"]) == len(f["xyz"]) else None
            if len(xyz) > args.max_points:
                idx = rng.choice(len(xyz), args.max_points, replace=False)
                xyz, rgb = xyz[idx], (rgb[idx] if rgb is not None else None)
            inside = np.all(np.abs(xyz) < half, axis=1)
            ax.scatter(*xyz[inside].T, c=rgb[inside] if rgb is not None else th["sub"], s=0.8 * res ** 2,
                       alpha=args.point_alpha, linewidths=0, depthshade=False, zorder=1)
            centres = np.array([(-R.T @ t - centre) / scale for R, t, _, _ in f["cameras"]])
            for z, (cams, colour) in enumerate(((f["gt_cameras"], th["gt_cam"]), (f["cameras"], th["cam"])), start=2):
                for R, t, K, wh in cams:
                    c = (-R.T @ t - centre) / scale
                    for e0, e1 in rg.frustum_lines(R, -R @ c, K, wh, cam_size)[1]:
                        ax.plot(*np.stack([e0, e1]).T, color=colour, linewidth=0.8 * res, zorder=z)
            if r["edges"]:  # the spanning tree on top: its edges between camera centres, and the centres
                for i, a in r["edges"]:
                    ax.plot(*np.stack([centres[i], centres[a]]).T, color=TREE, linewidth=1.6 * res, alpha=0.9, zorder=5)
                ax.scatter(*centres.T, color=TREE, s=6 * res ** 2, linewidths=0, depthshade=False, zorder=6)
                fig.text(j * 0.5 + 0.25, 0.86, "blue: spanning tree", ha="center", fontsize=7.5, color=TREE,
                         family="DejaVu Sans")
            for setter in (ax.set_xlim, ax.set_ylim, ax.set_zlim):
                setter(-half, half)
            ax.set_box_aspect((1, 1, 1), zoom=1.3)
            ax.view_init(elev=args.elev, azim=r["azim"])
            ax.set_axis_off()
            # snapshots without ground truth (a degenerate start, see rrd_export.log_snapshot) show no error
            err = (f"{rel_rot_err([R for R, _, _, _ in f['cameras']], [R for R, _, _, _ in f['gt_cameras']]):.1f}°"
                   if len(f["gt_cameras"]) == len(f["cameras"]) else "–")
            fig.text(j * 0.5 + 0.25, 0.92, r["label"], ha="center", fontsize=9, color=th["text"], family="DejaVu Sans")
            fig.text(j * 0.5 + 0.25, 0.03, f"rotation error {err}", ha="center", fontsize=8.5, color=th["sub"],
                     family="DejaVu Sans")
        t = runs[1]["frames"][k if k < n - 1 else -1]["time"]
        it = int(round(t.total_seconds() * 100)) if hasattr(t, "total_seconds") else int(round(t / 1e7))
        fig.text(0.5, 0.03, f"iteration {it:,}", ha="center", fontsize=8, color=th["text"], family="DejaVu Sans")
        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=100 * res, facecolor=th["bg"])
        plt.close(fig)
        images.append(Image.open(buf).convert("RGB"))
        print(f"\rframe {k + 1}/{n}", end="", flush=True)
    print()

    # one palette from the last frame; the background stays exactly white (see tools/render_gif.py)
    palette = images[-1].quantize(colors=255, method=Image.Quantize.MEDIANCUT)
    pal = palette.getpalette()[:255 * 3]
    bg = (255, 255, 255)
    kbg = min(range(len(pal) // 3), key=lambda q: sum((pal[3 * q + c] - bg[c]) ** 2 for c in range(3)))
    pal[3 * kbg:3 * kbg + 3] = bg
    palette.putpalette(pal)
    out = []
    for im in images:
        q = np.array(im.quantize(palette=palette, dither=Image.Dither.NONE))
        q[np.all(np.asarray(im) == bg, axis=-1)] = kbg
        p = Image.frombytes("P", im.size, q.tobytes())
        p.putpalette(pal)
        out.append(p)
    durations = [int(1000 / args.fps)] * (len(out) - 1) + [int(1000 * args.hold)]
    out[0].save(args.out, save_all=True, append_images=out[1:], duration=durations, loop=0, optimize=True)
    print(f"wrote {args.out} ({len(out)} frames)")


if __name__ == "__main__":
    main()
