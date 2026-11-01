"""Dump per-frame knee angle and torso lean for a time window, to inspect thresholds."""
import argparse
import csv
from app.pose import read_keypoints, angles

p = argparse.ArgumentParser()
p.add_argument("video")
p.add_argument("--exercise", default="squat", choices=["squat", "pushup", "curl"])
p.add_argument("--side", default="r", choices=["l", "r"])
p.add_argument("--start", type=float, required=True)
p.add_argument("--end", type=float, required=True)
p.add_argument("--out", default="angles.csv")
a = p.parse_args()

frames, fps = read_keypoints(a.video)
ang, lean = angles(frames, a.side, a.exercise)
i0, i1 = int(a.start * fps), int(a.end * fps)
with open(a.out, "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["time_s", "angle_deg", "torso_lean_deg"])
    for i in range(i0, min(i1, len(ang))):
        w.writerow([round(i / fps, 2), round(ang[i], 1), round(lean[i], 1)])
seg = ang[i0:i1]
print(f"angle min {seg.min():.1f}, max {seg.max():.1f}, median {sorted(seg)[len(seg)//2]:.1f}")
print(f"wrote {a.out}")