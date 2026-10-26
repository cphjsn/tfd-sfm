#!/bin/bash
# Renders one --rrd_every recording for the project page, on a TUM CPU node:
#   gif/<name>.gif     1280x960 GIF (tools/render_gif.py --scale 2), every camera (as the 3D replay)
#   mp4/<name>.mp4     H.264 copy of the GIF at 12 fps, what the page plays
#   poster/<name>.jpg  last frame, shown before the video loads
#   thumb/<name>.jpg   320x240 centre of the last frame, the scene selector
# Usage: render_scene.sh <recording.rrd> <out_dir> <name> <every>
#   <every>: use every k-th snapshot, so that the GIF has ~51 frames (2 for --rrd_every 100 at
#   10k iterations, 1 for --rrd_every 200).
set -euo pipefail
rrd=$1; out=$2; name=$3; every=$4
source ~/miniconda3/etc/profile.d/conda.sh
conda activate proba
mkdir -p "$out"/gif "$out"/mp4 "$out"/poster "$out"/thumb
cd ~/Desktop/git/tfdsfm
src="$out/src/$name.txt"  # the recording the GIF was rendered from
if [ ! -f "$out/gif/$name.gif" ] || { [ -f "$src" ] && [ "$(cat "$src")" != "$rrd" ]; }; then
    python tools/render_gif.py "$rrd" "$out/gif/$name.gif" --every "$every" --scale 2 --max_points 150000 \
        --max_cameras 100000
fi  # else: the GIF of this recording exists and is only re-encoded
ffmpeg -y -loglevel error -i "$out/gif/$name.gif" -vf fps=12 -movflags +faststart -pix_fmt yuv420p \
    -c:v libx264 -crf 23 "$out/mp4/$name.mp4"
python - "$out" "$name" <<'EOF'
import sys
from PIL import Image
out, name = sys.argv[1:]
im = Image.open(f"{out}/gif/{name}.gif")
im.seek(im.n_frames - 1)
last = im.convert("RGB")
last.save(f"{out}/poster/{name}.jpg", quality=90)
W, H = last.size  # the thumbnail is the central 70% of the frame, where the scene is
last.crop((round(0.15 * W), round(0.12 * H), round(0.85 * W), round(0.82 * H))).resize((320, 240), Image.LANCZOS) \
    .save(f"{out}/thumb/{name}.jpg", quality=85)
EOF
mkdir -p "$out/src"
echo "$rrd" > "$src"
echo "rendered $name"
