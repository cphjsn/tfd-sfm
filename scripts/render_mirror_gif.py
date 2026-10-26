#!/usr/bin/env python3
"""The "two worlds against the mirror ambiguity" GIF of the method section.

A --rrd_every recording keeps the snapshots of both worlds that a run optimises: world 1 and the
world started as its mirror image (world 2). This draws the last snapshot of each, the points and
the estimated cameras, on a turntable side by side: the kept world (lower 2D NLL, i.e. higher
likelihood) on the left, the discarded one on the right. On DTU scan82 the kept world has its
cameras on a convex dome over the object and the discarded one on a concave bowl under it.

Both worlds are upright (gravity from their own cameras, as tools/render_gif.py) and framed on
all their cameras and the central points, the discarded world closer to its object (--margin) when
seen from the front (its cameras' side) and zoomed out to all its cameras when seen from behind,
blending with the azimuth. Points and cameras are drawn in depth order, so that a camera behind the
object is hidden by it and one in front of it is not. --pitch instead turns the
discarded world (about a horizontal axis, its shape unchanged) until its cameras look at the object
at the same elevation as those of the kept world.

    python scripts/render_mirror_gif.py <tfdsfm repo> <recording.rrd> <run.log> out.gif
"""
import argparse
import io
import os
import re
import sys

import numpy as np


def selection(log):
    """(kept world 0/1, [2D NLL of world 1, of world 2]) from the [world selection] line of a run log."""
    text = open(log, errors="replace").read()
    m = re.search(r"the mirror world has the lower EMA 2D NLL \(([\d.]+) < ([\d.]+)\)", text)
    if m:
        return 1, [float(m.group(2)), float(m.group(1))]
    m = re.search(r"world 0 kept \(EMA 2D NLL ([\d.]+) <= ([\d.]+) of the mirror world\)", text)
    if m:
        return 0, [float(m.group(1)), float(m.group(2))]
    raise SystemExit(f"{log}: no [world selection] line")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("tfdsfm", help="the tfdsfm repository (for tools/render_gif.py)")
    ap.add_argument("rrd")
    ap.add_argument("log", help="the run's log (world selection and NLLs)")
    ap.add_argument("out", help="output .gif")
    ap.add_argument("--labels", nargs=2, default=["convex", "concave"], metavar=("KEPT", "DISCARDED"),
                    help="the shape of the kept and of the discarded world")
    ap.add_argument("--frames", type=int, default=72, help="frames of one turn")
    ap.add_argument("--elev", type=float, default=15.0)
    ap.add_argument("--pitch", action="store_true", help="pitch the discarded world (see above)")
    ap.add_argument("--margin", type=float, nargs=2, default=[0.0, 4.5], metavar=("KEPT", "DISCARDED"),
                    help="per world, > 0: frame the object (central 80%% of the points) with this many "
                         "half-extents, cameras outside the view left out; 0: frame all cameras and the "
                         "central points")
    ap.add_argument("--no_back_zoom", dest="back_zoom", action="store_false",
                    help="keep the discarded world's framing when it is seen from behind (default: zoom out to "
                         "all its cameras, blending with the azimuth)")
    ap.add_argument("--depth_slices", type=int, default=16, help="depth slices of the points (painter's order)")
    ap.add_argument("--max_points", type=int, default=80000, help="points drawn per world")
    ap.add_argument("--scale", type=float, default=1.75, help="resolution multiplier of the 640x320 frame")
    ap.add_argument("--fps", type=float, default=12.0)
    args = ap.parse_args()
    sys.path.insert(0, os.path.join(args.tfdsfm, "tools"))
    import render_gif as rg
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Line3DCollection
    import rerun as rr
    from PIL import Image

    kept, nll = selection(args.log)
    rec = rr.dataframe.load_recording(args.rrd)
    entities = sorted({c.entity_path for c in rec.schema().component_columns()})
    worlds = [rg.world_frames(rec, entities, w) for w in (0, 1)]
    t_final = max(worlds[0])
    for w in worlds:  # the final state is the selected world again, under world 0's entities
        w.pop(t_final, None)
    t_last = sorted(set(worlds[0]) & set(worlds[1]))[-1]

    th = rg.THEMES["light"]
    res, half, cam_size = args.scale, 1.15, 0.06
    rng = np.random.default_rng(0)
    def mean_view(f):
        """The unit mean viewing direction of a frame's cameras."""
        v = np.mean([R.T @ np.array([0.0, 0.0, 1.0]) for R, _, _, _ in f["cameras"]], axis=0)
        return v / np.linalg.norm(v)

    def pitch(a, b):
        """The rotation taking unit a onto unit b (Rodrigues)."""
        axis, c = np.cross(a, b), float(a @ b)
        s = np.linalg.norm(axis)
        if s < 1e-9:
            return np.eye(3)
        k = axis / s
        K = np.array([[0, -k[2], k[1]], [k[2], 0, -k[0]], [-k[1], k[0], 0]])
        return np.eye(3) + s * K + (1 - c) * K @ K

    upright = [rg.rotate_frame(worlds[w][t_last], rg.upright_rotation(worlds[w][t_last]["cameras"]))
               for w in (kept, 1 - kept)]
    if args.pitch:  # the discarded world: same azimuth, the kept world's elevation
        a, b = mean_view(upright[1]), mean_view(upright[0])
        target = np.append(a[:2] / np.linalg.norm(a[:2]) * np.linalg.norm(b[:2]), b[2])
        upright[1] = rg.rotate_frame(upright[1], pitch(a, target / np.linalg.norm(target)))
        print(f"pitched the discarded world by {np.degrees(np.arccos(np.clip(a @ target / np.linalg.norm(target), -1, 1))):.0f} deg")
    panels = []  # kept world first
    for j, (w, f) in enumerate(zip((kept, 1 - kept), upright)):
        scene = rg.normaliser(f)  # the box around all cameras and the central points (as tools/render_gif.py)
        if args.margin[j] > 0:  # the object (central 80% of the points) with a margin
            lo, hi = np.percentile(f["xyz"], 10, axis=0), np.percentile(f["xyz"], 90, axis=0)
            near = ((lo + hi) / 2, (hi - lo).max() / 2 * args.margin[j] / half)
        else:
            near = scene
        # the discarded world zooms out to all its cameras when seen from behind (--back_zoom)
        far = scene if (j == 1 and args.back_zoom) else near
        rgb = rg.unpack_rgba(f["rgb"]) if len(f["rgb"]) == len(f["xyz"]) else None
        idx = rng.choice(len(f["xyz"]), min(args.max_points, len(f["xyz"])), replace=False)
        won = j == 0
        panels.append(dict(xyz=f["xyz"][idx], rgb=None if rgb is None else rgb[idx], cameras=f["cameras"],
                           near=near, far=far,
                           title=f"world {w + 1}: {args.labels[j]}",
                           note=(f"higher likelihood (2D NLL {nll[w]:.2f}): kept" if won
                                 else f"lower likelihood (2D NLL {nll[w]:.2f}): discarded"),
                           colour=th["gt_cam"] if won else th["sub"], weight="bold" if won else "normal"))

    images = []
    for k in range(args.frames):
        azim = 180.0 + 360.0 * k / args.frames  # starts behind the cameras (see tools/render_gif.py)
        fig = plt.figure(figsize=(6.4, 3.2), dpi=100 * res)
        fig.patch.set_facecolor(th["bg"])
        for j, p in enumerate(panels):
            ax = fig.add_axes([j * 0.5, 0.08, 0.5, 0.8], projection="3d", computed_zorder=False)
            ax.set_facecolor(th["bg"])
            # the view: near framing seen from the front (azimuth 180, the cameras' side), far from behind
            wgt = (1 - np.cos(np.radians(azim - 180.0))) / 2
            centre = (1 - wgt) * p["near"][0] + wgt * p["far"][0]
            scale = (1 - wgt) * p["near"][1] + wgt * p["far"][1]
            xyz = (p["xyz"] - centre) / scale
            keep = np.all(np.abs(xyz) < half, axis=1)
            xyz, rgb = xyz[keep], (p["rgb"][keep] if p["rgb"] is not None else None)
            cams = []  # cameras in the view: mplot3d does not clip, frustums leaving it are left out
            for R, t, K, wh in p["cameras"]:
                c = (-R.T @ t - centre) / scale
                edges = np.array(rg.frustum_lines(R, -R @ c, K, wh, cam_size)[1])
                if np.all(np.abs(edges) < half):
                    cams.append((c, edges))
            # Painter's order: mplot3d sorts whole artists, so the points are split into depth slices
            # and the slices and the cameras are drawn from far to near (depth along the view direction).
            el, az = np.radians(args.elev), np.radians(azim)
            toward_viewer = np.array([np.cos(el) * np.cos(az), np.cos(el) * np.sin(az), np.sin(el)])
            depth = xyz @ toward_viewer
            cuts = np.quantile(depth, np.linspace(0, 1, args.depth_slices + 1))
            items = []  # (depth, draw)
            for a, b in zip(cuts[:-1], cuts[1:]):
                sel = (depth >= a) & (depth <= b)
                items.append(((a + b) / 2, ("points", sel)))
            for c, edges in cams:
                items.append((float(c @ toward_viewer), ("camera", edges)))
            for z, (_, (kind, what)) in enumerate(sorted(items, key=lambda it: it[0]), start=1):
                if kind == "points":
                    ax.scatter(*xyz[what].T, c=rgb[what] if rgb is not None else th["sub"],
                               s=0.8 * res ** 2, linewidths=0, depthshade=False, zorder=z)
                else:
                    ax.add_collection3d(Line3DCollection(what, colors=th["cam"], linewidths=0.8 * res, zorder=z))
            for setter in (ax.set_xlim, ax.set_ylim, ax.set_zlim):
                setter(-half, half)
            ax.set_box_aspect((1, 1, 1), zoom=1.55)
            ax.view_init(elev=args.elev, azim=azim)
            ax.set_axis_off()
            fig.text(j * 0.5 + 0.25, 0.92, p["title"], ha="center", fontsize=9, color=th["text"], family="DejaVu Sans")
            fig.text(j * 0.5 + 0.25, 0.03, p["note"], ha="center", fontsize=8.5, color=p["colour"],
                     weight=p["weight"], family="DejaVu Sans")
        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=100 * res, facecolor=th["bg"])
        plt.close(fig)
        images.append(Image.open(buf).convert("RGB"))
        print(f"\rframe {k + 1}/{args.frames}", end="", flush=True)
    print()

    # one palette from the first frame; the background stays exactly white (see tools/render_gif.py)
    palette = images[0].quantize(colors=255, method=Image.Quantize.MEDIANCUT)
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
    out[0].save(args.out, save_all=True, append_images=out[1:], duration=int(1000 / args.fps), loop=0, optimize=True)
    print(f"wrote {args.out} ({len(out)} frames, kept world {kept + 1})")


if __name__ == "__main__":
    main()
