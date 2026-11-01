"""Rule-based session generator: push/pull/legs rotation, ranked by time since each lift."""
from datetime import date

CATALOG = [
    {"name": "Back squat", "split": "legs", "muscles": ["quads", "glutes"], "equipment": "barbell"},
    {"name": "Leg press", "split": "legs", "muscles": ["quads"], "equipment": "machine"},
    {"name": "Romanian deadlift", "split": "legs", "muscles": ["hamstrings"], "equipment": "barbell"},
    {"name": "Push-up", "split": "push", "muscles": ["chest", "triceps"], "equipment": "bodyweight"},
    {"name": "Bench press", "split": "push", "muscles": ["chest", "triceps"], "equipment": "barbell"},
    {"name": "Overhead press", "split": "push", "muscles": ["shoulders", "triceps"], "equipment": "barbell"},
    {"name": "Barbell row", "split": "pull", "muscles": ["back", "biceps"], "equipment": "barbell"},
    {"name": "Lat pulldown", "split": "pull", "muscles": ["back"], "equipment": "machine"},
    {"name": "Bicep curl", "split": "pull", "muscles": ["biceps"], "equipment": "dumbbell"},
]
SPLITS = ["push", "pull", "legs"]


def generate_session(day_index, equipment, injuries, last_done, today, rec):
    """last_done: exercise name -> date last performed. Least recently done lifts come first."""
    if rec == "rest":
        return {"split": None, "exercises": [], "note": "Rest day: readiness is low."}
    split = SPLITS[day_index % 3]
    have = set(equipment) | {"bodyweight"}
    pool = [e for e in CATALOG
            if e["split"] == split and e["equipment"] in have and not set(e["muscles"]) & set(injuries)]
    pool.sort(key=lambda e: last_done.get(e["name"], date.min))
    light = rec == "light"
    n, sets, reps = (3, 3, "10-12") if light else (4, 4, "6-10")
    plan = [{"name": e["name"], "sets": sets, "reps": reps, "target_weight": None} for e in pool[:n]]
    return {"split": split, "exercises": plan,
            "note": "Light session: fewer sets, lighter load." if light else ""}
