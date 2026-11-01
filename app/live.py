"""Live webcam rep counter with on-screen form feedback.
Run:  python -m app.live bench_press --side l      (press q to quit)
"""
import argparse
import time
from collections import deque

import numpy as np
from app.biomech import LM, torso_lean, personalized_lean_limit
from app.exercises import EXERCISES, driving_angle
from app.reps import Rep, score_rep


class LiveCounter:
    """Streaming version of segment_reps(): feed one sample at a time."""

    def __init__(self, ex, lean_limit, smooth_n=5):
        self.ex, self.limit = ex, lean_limit
        self.buf = deque(maxlen=smooth_n)
        self.state, self.lo = "top", np.inf
        self.t_start, self.lean_win = None, []
        self.reps = []

    def update(self, angle, lean, t):
        self.buf.append(angle)
        v = float(np.mean(self.buf))
        ex = self.ex
        if self.state == "top":
            if v > ex["high"]:
                self.t_start, self.lean_win = t, [lean]
            elif v < ex["low"]:
                self.state, self.lo = "bottom", v
                if self.t_start is None:
                    self.t_start = t
                self.lean_win.append(lean)
            return None
        self.lean_win.append(lean)
        self.lo = min(self.lo, v)
        if v > ex["high"]:
            rep = Rep(0, 0, 0, rom=0.0, min_angle=float(self.lo), tempo_s=t - self.t_start)
            score_rep(rep, ex, np.array(self.lean_win), self.limit)
            self.reps.append(rep)
            self.state, self.lo, self.lean_win = "top", np.inf, []
            return rep
        return None


def read_angle(f, side, exercise):
    ex = EXERCISES[exercise]
    return driving_angle(f, side, ex), torso_lean(f[f"{side}_shoulder"], f[f"{side}_hip"])


def run(cap, landmarker, mp, cv2, side, exercise, counter):
    start = time.monotonic()
    last_msg = ""
    while True:
        ok, img = cap.read()
        if not ok:
            break
        h, w = img.shape[:2]
        ts = int((time.monotonic() - start) * 1000)
        rgb = np.ascontiguousarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        res = landmarker.detect_for_video(mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb), ts)
        status = "no person detected"
        if res.pose_landmarks:
            lm = res.pose_landmarks[0]
            f = {k: np.array([lm[i].x * w, lm[i].y * h]) for k, i in LM.items()}
            angle, lean = read_angle(f, side, exercise)
            done = counter.update(angle, lean, time.monotonic() - start)
            status = f"angle {angle:5.1f}"
            if done:
                flags = ", ".join(done.flags) or "good form"
                last_msg = f"rep {len(counter.reps)}: {done.form_score}/100 ({flags})"
        font = cv2.FONT_HERSHEY_SIMPLEX
        cv2.putText(img, f"Reps: {len(counter.reps)}", (20, 50), font, 1.5, (0, 255, 0), 3)
        cv2.putText(img, last_msg, (20, 90), font, 0.8, (255, 255, 255), 2)
        cv2.putText(img, status, (20, h - 20), font, 0.7, (200, 200, 200), 2)
        cv2.imshow("AI Gym Coach - live", img)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break


def main():
    import cv2
    from app.pose import _landmarker

    p = argparse.ArgumentParser()
    p.add_argument("exercise", choices=list(EXERCISES))
    p.add_argument("--side", default="r", choices=["l", "r"])
    p.add_argument("--camera", type=int, default=0)
    p.add_argument("--leverage", type=float, default=1.0)
    a = p.parse_args()

    mp, landmarker = _landmarker()
    cap = cv2.VideoCapture(a.camera)
    if not cap.isOpened():
        landmarker.close()
        raise SystemExit(f"Could not open camera {a.camera}")
    counter = LiveCounter(EXERCISES[a.exercise], personalized_lean_limit(a.leverage))
    try:
        run(cap, landmarker, mp, cv2, a.side, a.exercise, counter)
    finally:
        cap.release()
        landmarker.close()
        cv2.destroyAllWindows()

    print(f"Total reps: {len(counter.reps)}")
    for i, r in enumerate(counter.reps, 1):
        print(f"  rep {i}: score {r.form_score}, flags {r.flags or 'none'}, tempo {r.tempo_s:.1f}s")


if __name__ == "__main__":
    main()
