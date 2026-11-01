"""Gym exercise catalog. Each entry names the joints whose angle drives the rep and the
thresholds for counting and form. Thresholds are starting values, not validated yet.

joint:      (proximal, vertex, distal). The angle is measured at the vertex joint.
low/high:   hysteresis band in degrees. A rep goes above high, then below low, then above high.
depth_max:  a rep must reach this angle or lower to count as full range.
invert:     for rises such as lateral raise, flip the angle (180 - a) so the same logic applies.
lean_check: also flag excess torso lean (squat-type moves only).
"""
from app.biomech import angle_at

HIP_KNEE_ANKLE = ("hip", "knee", "ankle")
SHOULDER_HIP_KNEE = ("shoulder", "hip", "knee")
SHOULDER_ELBOW_WRIST = ("shoulder", "elbow", "wrist")
HIP_SHOULDER_ELBOW = ("hip", "shoulder", "elbow")

EXERCISES = {
    # legs
    "squat":             {"joint": HIP_KNEE_ANKLE, "low": 145, "high": 165, "depth_max": 100, "lean_check": True},
    "leg_press":         {"joint": HIP_KNEE_ANKLE, "low": 100, "high": 160, "depth_max": 90, "lean_check": False},
    "lunge":             {"joint": HIP_KNEE_ANKLE, "low": 120, "high": 160, "depth_max": 100, "lean_check": False},
    "leg_extension":     {"joint": HIP_KNEE_ANKLE, "low": 100, "high": 160, "depth_max": 90, "lean_check": False},
    "leg_curl":          {"joint": HIP_KNEE_ANKLE, "low": 100, "high": 160, "depth_max": 90, "lean_check": False},
    # hinge and glutes
    "deadlift":          {"joint": SHOULDER_HIP_KNEE, "low": 120, "high": 165, "depth_max": 100, "lean_check": False},
    "romanian_deadlift": {"joint": SHOULDER_HIP_KNEE, "low": 120, "high": 165, "depth_max": 110, "lean_check": False},
    "hip_thrust":        {"joint": SHOULDER_HIP_KNEE, "low": 110, "high": 160, "depth_max": 120, "lean_check": False},
    # push
    "pushup":            {"joint": SHOULDER_ELBOW_WRIST, "low": 120, "high": 160, "depth_max": 90, "lean_check": False},
    "bench_press":       {"joint": SHOULDER_ELBOW_WRIST, "low": 90, "high": 160, "depth_max": 90, "lean_check": False},
    "overhead_press":    {"joint": SHOULDER_ELBOW_WRIST, "low": 90, "high": 165, "depth_max": 90, "lean_check": False},
    "triceps_pushdown":  {"joint": SHOULDER_ELBOW_WRIST, "low": 100, "high": 160, "depth_max": 90, "lean_check": False},
    # pull
    "row":               {"joint": SHOULDER_ELBOW_WRIST, "low": 90, "high": 155, "depth_max": 90, "lean_check": False},
    "pulldown":          {"joint": SHOULDER_ELBOW_WRIST, "low": 90, "high": 155, "depth_max": 90, "lean_check": False},
    "curl":              {"joint": SHOULDER_ELBOW_WRIST, "low": 90, "high": 150, "depth_max": 60, "lean_check": False},
    # shoulders (film from the front; --side picks the arm)
    "lateral_raise":     {"joint": HIP_SHOULDER_ELBOW, "low": 130, "high": 155, "depth_max": 100, "lean_check": False, "invert": True},
}


def driving_angle(f, side, ex):
    """Driving angle (degrees) for one frame. f maps names such as 'l_knee' to (x, y)."""
    a, b, c = (f[f"{side}_{j}"] for j in ex["joint"])
    ang = angle_at(a, b, c)
    return 180.0 - ang if ex.get("invert") else ang
