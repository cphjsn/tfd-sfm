#!/bin/bash
# Queue the renders of the finished page runs and make sure CPU render workers exist (TUM server).
# Run it from the login node: collect_scenes.py itself runs in a short slurm job.
#   bash ~/tfdsfm_gifs3/page_scripts/refresh.sh
set -euo pipefail
P=~/tfdsfm_gifs3/page_scripts
Q=~/queues/tfdsfm_render.txt
NEW=~/tfdsfm_gifs3/render_new.txt
srun --gres=gpu:0 --cpus-per-task=1 --mem=2G --time=00:10:00 --job-name=collect bash -c \
    "source ~/miniconda3/etc/profile.d/conda.sh && conda activate proba && python $P/collect_scenes.py --js ~/tfdsfm_gifs3/scenes.js --queue $NEW"
touch "$Q" "$Q.running"
# renders already queued or running are left out (a finished render has its MP4 and is not in NEW)
until mkdir "$Q.lockdir" 2>/dev/null; do sleep 1; done
added=$(grep -vxF -f <(cat "$Q" "$Q.running") "$NEW" | tee -a "$Q" | wc -l || true)
rmdir "$Q.lockdir"
pending=$(wc -l < "$Q")
workers=$(squeue -u "$USER" --noheader -o "%j" | grep -c "^render_w" || true)
echo "queued $added new renders, $pending pending, $workers render workers"
if [ "$pending" -gt 0 ] && [ "$workers" -lt 4 ]; then
    cd ~/Desktop/git/proba && bash scripts/tasks_definition.sh "" "$Q" --slurm $((4 - workers)) "$P/render_cpu.sh" false | grep -c Submitted
fi
