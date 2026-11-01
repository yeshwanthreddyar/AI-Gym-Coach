"""Calibrate thresholds for one exercise from your own reps.
Run:  python -m app.calibrate bench_press --side l --seconds 20
Do 5-6 full reps during the countdown. It prints suggested low/high/depth_max values.
"""
import argparse
import time

import numpy as np
from app.biomech import LM
from app.exercises import EXERCISES, driving_angle


def suggest(angles, margin=0.15):
    """Turn a list of measured angles into thresholds spanning the real range of motion."""
    lo, hi = np.percentile(angles, 5), np.percentile(angles, 95)
    span = hi - lo
    return {
        "low": round(lo + 0.30 * span),       # bottom of the rep must drop below this
        "high": round(hi - 0.20 * span),      # top of the rep must rise above this
        "depth_max": round(lo + margin * span),  # full range: reach close to the bottom
        "measured_min": round(lo, 1),
        "measured_max": round(hi, 1),
    }


def main():
    import cv2
    from app.pose import _landmarker

    p = argparse.ArgumentParser()
    p.add_argument("exercise", choices=list(EXERCISES))
    p.add_argument("--side", default="r", choices=["l", "r"])
    p.add_argument("--camera", type=int, default=0)
    p.add_argument("--seconds", type=float, default=20)
    a = p.parse_args()

    ex = EXERCISES[a.exercise]
    mp, landmarker = _landmarker()
    cap = cv2.VideoCapture(a.camera)
    if not cap.isOpened():
        landmarker.close()
        raise SystemExit(f"Could not open camera {a.camera}")

    samples, start = [], time.monotonic()
    print(f"Get ready... recording {a.seconds:.0f} s. Do 5-6 full reps.")
    try:
        while time.monotonic() - start < a.seconds:
            ok, img = cap.read()
            if not ok:
                break
            h, w = img.shape[:2]
            ts = int((time.monotonic() - start) * 1000)
            rgb = np.ascontiguousarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
            res = landmarker.detect_for_video(mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb), ts)
            if res.pose_landmarks:
                lm = res.pose_landmarks[0]
                f = {k: np.array([lm[i].x * w, lm[i].y * h]) for k, i in LM.items()}
                samples.append(driving_angle(f, a.side, ex))
            left = a.seconds - (time.monotonic() - start)
            cv2.putText(img, f"Recording: {left:4.1f}s  reps: do full range", (20, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
            cv2.imshow("calibrate", img)
            cv2.waitKey(1)
    finally:
        cap.release()
        landmarker.close()
        cv2.destroyAllWindows()

    if len(samples) < 30:
        raise SystemExit("Too few frames with a detected person. Check framing and lighting.")
    s = suggest(samples)
    print(f"\nMeasured angle range: {s['measured_min']} to {s['measured_max']} degrees")
    print("Replace this entry in app/exercises.py:\n")
    print(f'    "{a.exercise}": {{"joint": {ex["joint"]}, "low": {s["low"]}, "high": {s["high"]}, '
          f'"depth_max": {s["depth_max"]}, "lean_check": {ex["lean_check"]}'
          + (', "invert": True' if ex.get("invert") else "") + "},")


if __name__ == "__main__":
    main()
