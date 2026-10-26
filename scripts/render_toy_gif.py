#!/usr/bin/env python3
"""The "Gaussian landmarks, not tracks" GIF of the method section.

The paper's toy example (Fig. 3) solved by TFD-SfM: 24 cameras on a 360-degree ring, 100 3D
points, 4 px noise, a strict cold start (identity cameras, unit depths), the relative-pose chain.
Every match of a point in an image is its own 3D Gaussian, drawn as a disc of radius k sigma
(k = --sigma_scale, exaggerated so that the small Gaussians of the end stay visible), seen from
above the ring:

  left    the ring: estimated (orange) and ground-truth (green) cameras and the Gaussians of all
          matches, one colour per 3D point; the followed match in blue, with the ray from each of
          its two cameras
  right   a window that follows that match, between two images with a large baseline: its two
          Gaussians start far apart (at the cold start each image places the point at its own unit
          depth) and meet while they shrink

The estimate is drawn in its own frame (camera 1 is the fixed reference of the relative-pose
chain), from above the plane of the ring of the final frame. Every frame is centred on its
Gaussians and scaled so that they keep the size of the ground-truth points (the scene grows from
unit depth), so the ground-truth cameras stay where they are. Frames are spaced evenly in
log(iteration) after the first --slow_until iterations, which show every snapshot slowly, since
the Gaussians meet and shrink mostly early.

Input: the trajectories that pba/proba_rewrite/scripts/toy_rrd_compare.py caches in its GIF4 mode
(BASIN_NCAM=24 NOISE_PX=4 SEED=2), dumped together with the toy scene (see README.md).

    python scripts/render_toy_gif.py toy_scene_dump.pkl assets/media/method/toy_landmarks.gif
"""
import argparse
import io
import pickle

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.patches import Circle, Polygon, Rectangle  # noqa: E402
from PIL import Image  # noqa: E402

EST, GT, FAINT, TEXT, SUB = "#e8590c", "#2f9e44", "#ced4da", "#212529", "#6c757d"
POINT_COLOURS = ["#1971c2"]  # the followed point
CAP = 2.0  # largest disc radius drawn in the ring view (scene units; the ring has radius 4)


def umeyama(src, dst):
    """Similarity (s, R, t) with dst ~ s R src + t."""
    mu_s, mu_d = src.mean(0), dst.mean(0)
    sc, dc = src - mu_s, dst - mu_d
    U, S, Vt = np.linalg.svd(sc.T @ dc)
    d = np.sign(np.linalg.det(Vt.T @ U.T))
    R = Vt.T @ np.diag([1, 1, d]) @ U.T
    s = (S * np.array([1, 1, d])).sum() / max((sc ** 2).sum(), 1e-12)
    return s, R, mu_d - s * R @ mu_s


def wedge(center, forward, size):
    """A camera seen from above: a triangle from its centre along its viewing direction."""
    f = forward / (np.linalg.norm(forward) + 1e-12)
    side = np.array([-f[1], f[0]])
    tip = center + size * f
    return [center, tip + 0.45 * size * side, tip - 0.45 * size * side]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("dump", help="toy_scene_dump.pkl")
    ap.add_argument("out", help="output .gif")
    ap.add_argument("--slow_until", type=int, default=600, help="iterations shown at every snapshot, slowly")
    ap.add_argument("--motion_frames", type=int, default=70,
                    help="interpolated frames of the slow part, spent where the Gaussians move")
    ap.add_argument("--slow_fps", type=float, default=8.0, help="frames per second of the slow part")
    ap.add_argument("--start_hold", type=float, default=1.5, help="seconds the cold start is shown")
    ap.add_argument("--frames", type=int, default=30, help="frames after --slow_until, evenly in log(iteration)")
    ap.add_argument("--fps", type=float, default=12.0)
    ap.add_argument("--hold", type=float, default=2.5, help="seconds the last frame is shown")
    ap.add_argument("--scale", type=float, default=1.75, help="resolution multiplier of the 640x320 frame")
    ap.add_argument("--sigma_scale", type=float, default=4.0, help="disc radius = this times sigma (visualisation only)")
    args = ap.parse_args()

    scene = pickle.load(open(args.dump, "rb"))
    traj = scene["cells"][(True, "proba")]["traj"]  # relative poses, Gaussian landmarks
    cen_gt, Rc2w_gt, obs, X_gt = scene["cen_gt"], scene["Rc2w_gt"], scene["obs_cams"], scene["Xw_gt"]
    pairs = [(c, p) for p, o in enumerate(obs) for c in o]  # every match: (image, point)

    # top view of the estimate frame: the final frame's ground truth -> estimate fit gives the ring
    # plane (the toy world has y down) and lines the axes up with the ground truth seen from above
    sF, RF, tF = umeyama(cen_gt, np.asarray(traj[-1][1], float))
    V = np.stack([RF @ [1.0, 0, 0], RF @ [0, 0, 1.0]])  # (2, 3): est -> top-view coordinates
    gt_top = lambda x: np.asarray(x, float)[..., [0, 2]]  # noqa: E731  the ground truth from above
    gt_ctr, gt_rad = gt_top(X_gt).mean(0), np.median(np.linalg.norm(gt_top(X_gt) - gt_top(X_gt).mean(0), axis=1))

    def view(frame):
        """Top-view coordinates of a frame: cameras, Gaussians (images x points x 2), sigmas, all
        centred on the Gaussians and scaled to the size of the ground-truth points."""
        it, cen, Rc, P, sig = frame
        P, cen = np.asarray(P, float) @ V.T, np.asarray(cen, float) @ V.T
        g = np.stack([P[c, p] for c, p in pairs])
        ctr = g.mean(0)
        r = np.median(np.linalg.norm(g - ctr, axis=1)) / gt_rad
        to = lambda x: (x - ctr) / r + gt_ctr  # noqa: E731
        fwd = np.asarray(Rc, float)[:, :, 2] @ V.T
        return it, to(cen), fwd, to(P), np.asarray(sig, float) / r, to

    # the ground-truth cameras in the drawing of the final frame
    to_final = view(traj[-1])[5]
    gt_cam = to_final((sF * (cen_gt @ RF.T) + tF) @ V.T)
    gt_fwd = (RF[None] @ Rc2w_gt)[:, :, 2] @ V.T

    # the followed match: one 3D point in two images with a large baseline, whose two Gaussians lie
    # far apart at the cold start (the largest product of the two distances)
    first = view(traj[0])
    best = None
    for p, o in enumerate(obs):
        for a in range(len(o)):
            for b in range(a + 1, len(o)):
                c1, c2 = int(o[a]), int(o[b])
                baseline = np.linalg.norm(cen_gt[c1] - cen_gt[c2])
                apart = np.linalg.norm(first[3][c1, p] - first[3][c2, p])
                if best is None or baseline * apart > best[0]:
                    best = (baseline * apart, p, [c1, c2], baseline, apart)
    _, zoom_p, pair_cams, baseline, apart = best
    points = [zoom_p]
    print(f"match: point {zoom_p} in images {pair_cams}, baseline {baseline:.2f} (ring diameter 8), "
          f"Gaussians {apart:.2f} apart at the cold start")

    # The Gaussians meet within the first few hundred iterations: that part shows every snapshot
    # (one per 20 iterations) with interpolated frames in between, slowly; the rest is
    # spaced evenly in log(iteration) at the normal speed.
    step = traj[1][0] - traj[0][0]
    slow = [i for i in range(len(traj)) if traj[i][0] <= args.slow_until]
    its = np.geomspace(traj[slow[-1]][0] + step, traj[-1][0], args.frames)
    fast = sorted({min(len(traj) - 1, int(round(it / step))) for it in its} - set(slow))
    views = {i: view(traj[i]) for i in slow + fast}
    states, durations = [], []  # (iteration, cameras, forward, Gaussians, sigmas), milliseconds
    # frames between two snapshots in proportion to how far the zoomed point's Gaussians move
    # (most of it happens in the first few snapshots), at least one
    move = [np.linalg.norm(views[b][3][pair_cams, zoom_p] - views[a][3][pair_cams, zoom_p], axis=1).mean()
            for a, b in zip(slow[:-1], slow[1:])]
    sub = [1 + int(round(args.motion_frames * m / sum(move))) for m in move]
    for (a, b), n_sub in zip(zip(slow[:-1], slow[1:]), sub):
        for u in np.linspace(0, 1, n_sub + 1)[:-1]:
            va, vb = views[a], views[b]
            states.append((int(round((1 - u) * va[0] + u * vb[0])),) + tuple((1 - u) * x + u * y for x, y in zip(va[1:5], vb[1:5])))
            durations.append(int(1000 / args.slow_fps))
    durations[0] = int(1000 * args.start_hold)  # the cold start, Gaussians far apart
    for i in [slow[-1]] + fast:
        states.append(views[i][:5])
        durations.append(int(1000 / args.fps))
    durations[-1] = int(1000 * args.hold)
    ring_half, zoom_min = 5.0, 1.0
    k_sig = args.sigma_scale
    res = args.scale
    images = []
    for n, (it, cen, fwd, P, sig) in enumerate(states):
        mine = P[pair_cams, zoom_p]
        zoom_c = mine.mean(0)  # the window follows the match's two Gaussians and holds both
        zoom_half = max(zoom_min, 1.15 * np.linalg.norm(mine - zoom_c, axis=1).max() + 0.3)

        fig = plt.figure(figsize=(6.4, 3.2), dpi=100 * res)
        main_ax = fig.add_axes([0.0, 0.0, 0.5, 0.9])
        zoom_ax = fig.add_axes([0.53, 0.04, 0.44, 0.82])
        for ax, c, h in ((main_ax, gt_cam.mean(0), ring_half), (zoom_ax, zoom_c, zoom_half)):
            ax.set_xlim(c[0] - h, c[0] + h)
            ax.set_ylim(c[1] - h, c[1] + h)
            ax.set_aspect("equal")
            ax.set_axis_off()
        for c, p in pairs:  # the Gaussians of all other matches, one colour per 3D point
            if not (p == zoom_p and c in pair_cams):
                rad, colour = min(k_sig * sig[c, p], CAP), scene["colors"][p]
                main_ax.add_patch(Circle(P[c, p], rad, facecolor=colour, edgecolor="none", alpha=0.12, zorder=1))
                main_ax.add_patch(Circle(P[c, p], rad, fill=False, edgecolor=colour, linewidth=0.4 * res, alpha=0.6,
                                         zorder=2))
        for colour, p in zip(POINT_COLOURS, points):
            for c in pair_cams:
                for ax in (main_ax, zoom_ax):
                    cap = 0.8 * zoom_half if ax is zoom_ax else CAP
                    rad = min(k_sig * sig[c, p], cap)
                    ax.plot(*np.stack([cen[c], P[c, p]]).T, color=colour, linewidth=0.6 * res, alpha=0.6, zorder=3)
                    ax.add_patch(Circle(P[c, p], rad, facecolor=colour, edgecolor="none", alpha=0.12, zorder=4))
                    ax.add_patch(Circle(P[c, p], rad, fill=False, edgecolor=colour, linewidth=0.9 * res, alpha=0.9,
                                        zorder=4))  # outlines keep overlapping ones apart
                    ax.plot(*P[c, p], "o", color=colour, markersize=1.6 * res, zorder=5)
        for c, f in zip(gt_cam, gt_fwd):  # ground truth, then the estimate on top
            main_ax.add_patch(Polygon(wedge(c, f, 0.45), closed=True, facecolor="none", edgecolor=GT,
                                      linewidth=0.9 * res, zorder=6))
        for c, f in zip(cen, fwd):
            main_ax.add_patch(Polygon(wedge(c, f, 0.45), closed=True, facecolor="none", edgecolor=EST,
                                      linewidth=0.9 * res, zorder=7))
        for ax in (main_ax, zoom_ax):
            ax.add_patch(Rectangle(zoom_c - zoom_half, 2 * zoom_half, 2 * zoom_half, fill=False, edgecolor=SUB,
                                   linewidth=0.6 * res, linestyle=(0, (3, 2)), zorder=8))

        fig.text(0.25, 0.93, "top view of the ring", ha="center", fontsize=8.5, color=TEXT, family="DejaVu Sans")
        fig.text(0.75, 0.93, "one match between 2 images: 2 Gaussians",
                 ha="center", fontsize=8.5, color=TEXT, family="DejaVu Sans")
        fig.text(0.545, 0.80, f"σ = {np.mean(sig[pair_cams, zoom_p]):.2f}  (discs drawn at {k_sig:g}σ)",
                 fontsize=8, color=POINT_COLOURS[0], family="DejaVu Sans")
        fig.text(0.01, 0.02, f"iteration {it:,}", fontsize=8, color=TEXT, family="DejaVu Sans")
        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=100 * res, facecolor="white")
        plt.close(fig)
        images.append(Image.open(buf).convert("RGB"))
        print(f"\rframe {n + 1}/{len(states)}", end="", flush=True)
    print()

    # one palette from the last frame; the background stays exactly white (see tools/render_gif.py)
    palette = images[-1].quantize(colors=255, method=Image.Quantize.MEDIANCUT)
    pal = palette.getpalette()[:255 * 3]
    bg = (255, 255, 255)
    kbg = min(range(len(pal) // 3), key=lambda q: sum((pal[3 * q + c] - bg[c]) ** 2 for c in range(3)))
    pal[3 * kbg:3 * kbg + 3] = bg
    palette.putpalette(pal)
    frames = []
    for im in images:
        q = np.array(im.quantize(palette=palette, dither=Image.Dither.NONE))
        q[np.all(np.asarray(im) == bg, axis=-1)] = kbg
        p = Image.frombytes("P", im.size, q.tobytes())
        p.putpalette(pal)
        frames.append(p)
    frames[0].save(args.out, save_all=True, append_images=frames[1:], duration=durations, loop=0, optimize=True)
    print(f"wrote {args.out} ({len(frames)} frames, points {points})")


if __name__ == "__main__":
    main()
