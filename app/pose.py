"""Video -> joint angles with MediaPipe Tasks PoseLandmarker. Needs requirements-cv.txt
and the model file pose_landmarker_full.task (see README).
CLI:  python -m app.pose lift.mp4 squat --side r --start 60 --end 84
"""
import argparse
import json
import os

import numpy as np
from app.biomech import LM, torso_lean, leverage_index, personalized_lean_limit
from app.exercises import EXERCISES, driving_angle
from app.reps import segment_reps, score_rep, attribute_cause

MODEL_PATH = os.getenv("POSE_MODEL", "pose_landmarker_full.task")


def _landmarker(min_conf=0.3):
    import mediapipe as mp
    from mediapipe.tasks import python as mp_python
    from mediapipe.tasks.python import vision

    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(
            f"Pose model not found at {MODEL_PATH}. Download pose_landmarker_full.task "
            "(see README) or set POSE_MODEL to its path.")
    options = vision.PoseLandmarkerOptions(
        base_options=mp_python.BaseOptions(model_asset_path=MODEL_PATH),
        running_mode=vision.RunningMode.VIDEO,
        num_poses=1,
        min_pose_detection_confidence=min_conf,
        min_pose_presence_confidence=min_conf,
        min_tracking_confidence=min_conf)
    return mp, vision.PoseLandmarker.create_from_options(options)


def read_keypoints(path):
    """Return one dict of landmark pixel coordinates per frame (None if no person found)."""
    import cv2
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Video not found: {path}")
    mp, landmarker = _landmarker()
    cap = cv2.VideoCapture(path)
    if not cap.isOpened():
        landmarker.close()
        raise ValueError(f"OpenCV could not open the video: {path}")
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    frames, idx, detected = [], 0, 0
    try:
        while True:
            ok, img = cap.read()
            if not ok:
                break
            rgb = np.ascontiguousarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
            res = landmarker.detect_for_video(mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb),
                                              int(idx * 1000 / fps))
            idx += 1
            if not res.pose_landmarks:
                frames.append(None)
                continue
            detected += 1
            h, w = img.shape[:2]
            lm = res.pose_landmarks[0]
            frames.append({k: np.array([lm[i].x * w, lm[i].y * h]) for k, i in LM.items()})
    finally:
        cap.release()
        landmarker.close()
    print(f"[pose] frames read: {idx}, person detected in: {detected}, fps: {fps:.1f}")
    if idx == 0:
        raise ValueError("OpenCV opened the file but read 0 frames. Try re-exporting it as H.264 MP4.")
    if detected == 0:
        raise ValueError(
            "Read the video but detected no person in any frame. Check that the whole body is "
            "visible, the camera is side-on (or front-on for lateral raise) and still, and the "
            "lighting is good. Rotate phone footage shot in portrait.")
    return frames, fps


def _fill(x):
    """Linearly interpolate frames where the person was not detected."""
    x = np.asarray(x, float)
    ok = ~np.isnan(x)
    if not ok.any():
        raise ValueError("No person detected in the video")
    return np.interp(np.arange(len(x)), np.flatnonzero(ok), x[ok])


def angles(frames, side, exercise):
    ex = EXERCISES[exercise]
    ang, lean = [], []
    for f in frames:
        if f is None:
            ang.append(np.nan)
            lean.append(np.nan)
            continue
        ang.append(driving_angle(f, side, ex))
        lean.append(torso_lean(f[f"{side}_shoulder"], f[f"{side}_hip"]))
    return _fill(ang), _fill(lean)


def analyze_video(path, exercise, side="r", calib_path=None, start=None, end=None):
    ex = EXERCISES[exercise]
    index = 1.0  # population reference when no calibration video is given
    if calib_path:
        cal, _ = read_keypoints(calib_path)
        standing = [f for f in cal[:60] if f is not None]  # roughly the first 2 s, standing
        if not standing:
            raise ValueError("No person detected in the calibration video")
        kp = {n: np.median([f[f"{side}_{n}"] for f in standing], axis=0)
              for n in ("hip", "knee", "ankle", "shoulder")}
        index = leverage_index(kp)
    limit = personalized_lean_limit(index)
    frames, fps = read_keypoints(path)
    ang, lean = angles(frames, side, exercise)
    reps = segment_reps(ang, fps, ex)
    for r in reps:
        score_rep(r, ex, lean[r.start:r.end + 1], limit)
    times = [(r.start / fps, r.end / fps) for r in reps]
    keep = [i for i, (s, e) in enumerate(times)
            if (start is None or s >= start) and (end is None or e <= end)]
    reps = [reps[i] for i in keep]
    times = [times[i] for i in keep]
    return {"exercise": exercise, "reps": len(reps), "leverage_index": round(index, 3),
            "lean_limit_deg": round(limit, 1),
            "rep_times_s": [[round(s, 1), round(e, 1)] for s, e in times],
            "form_scores": [r.form_score for r in reps],
            "flags": [r.flags for r in reps], "cause": attribute_cause(reps)}


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("video")
    p.add_argument("exercise", choices=list(EXERCISES))
    p.add_argument("--side", default="r", choices=["l", "r"])
    p.add_argument("--calib", default=None)
    p.add_argument("--start", type=float, default=None, help="window start, seconds")
    p.add_argument("--end", type=float, default=None, help="window end, seconds")
    a = p.parse_args()
    print(json.dumps(analyze_video(a.video, a.exercise, a.side, a.calib, a.start, a.end), indent=2))
