"""Joint geometry and body-proportion-aware form thresholds."""
import numpy as np

# MediaPipe Pose landmark indices (33-point model)
LM = {"l_shoulder": 11, "r_shoulder": 12, "l_elbow": 13, "r_elbow": 14,
      "l_wrist": 15, "r_wrist": 16, "l_hip": 23, "r_hip": 24,
      "l_knee": 25, "r_knee": 26, "l_ankle": 27, "r_ankle": 28}


def angle_at(a, b, c):
    """Interior angle at point b (degrees) for the path a-b-c. Accepts (..., 2) arrays."""
    ba, bc = np.asarray(a, float) - b, np.asarray(c, float) - b
    cos = (ba * bc).sum(-1) / (np.linalg.norm(ba, axis=-1) * np.linalg.norm(bc, axis=-1) + 1e-9)
    return np.degrees(np.arccos(np.clip(cos, -1.0, 1.0)))


def torso_lean(shoulder, hip):
    """Degrees from vertical; 0 means upright. Image y grows downward."""
    v = np.asarray(shoulder, float) - np.asarray(hip, float)
    return np.degrees(np.arctan2(np.abs(v[..., 0]), -v[..., 1]))


def leverage_index(kp):
    """Femur-to-torso ratio from one standing frame. kp keys: hip, knee, ankle, shoulder."""
    d = lambda a, b: float(np.linalg.norm(np.asarray(kp[a]) - np.asarray(kp[b])))
    return d("hip", "knee") / max(d("shoulder", "hip"), 1e-6)


REF_INDEX = 1.0  # population reference; heuristic until fit on multi-person recordings


def personalized_lean_limit(index, base=45.0, slope=20.0, lo=35.0, hi=65.0):
    """Torso-lean limit (deg) shifted by leverage. Longer femurs relative to torso
    naturally allow more forward lean, so the limit goes up. Slope is a heuristic
    to be fit on your own calibration data."""
    return float(np.clip(base + slope * (index - REF_INDEX), lo, hi))
