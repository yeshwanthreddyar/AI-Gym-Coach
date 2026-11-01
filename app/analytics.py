"""Log analytics, readiness, progressive overload, rest timer, weekly report payload."""
import numpy as np


def epley_1rm(weight, reps):
    if reps <= 0:
        return 0.0
    return float(weight) if reps == 1 else float(weight * (1 + reps / 30))


def plateau(weekly_best_e1rm, min_weeks=4, tol=0.005):
    """Flat if the slope over the last `min_weeks` weeks is under `tol` of the mean, per week."""
    y = [v for v in weekly_best_e1rm if v]
    if len(y) < min_weeks:
        return False
    y = np.array(y[-min_weeks:])
    slope = np.polyfit(np.arange(len(y)), y, 1)[0]
    return bool(abs(slope) / y.mean() < tol)


def progressive_overload(weight, reps, low, high, form):
    """Return (next_weight, next_reps, note) from the last set."""
    if form < 60:
        return weight, low, "hold: fix form before adding load"
    if reps >= high and form >= 80:
        return round(weight + 2.5, 1), low, "+2.5 kg, restart at the low end of the range"
    if reps < high:
        return weight, min(reps + 1, high), "add one rep"
    return weight, high, "hold: form below 80 at the top of the range"


def readiness(sleep_hours, soreness, load_ratio):
    """Weighted 0-100 score: sleep 40, soreness 30, training load 30."""
    sleep_pts = 40 * np.clip((sleep_hours - 5) / 3, 0, 1)
    sore_pts = 30 * np.clip((5 - np.mean(soreness)) / 4, 0, 1)
    load_pts = 30 if load_ratio <= 1.1 else 15 if load_ratio <= 1.3 else 0
    score = round(float(sleep_pts + sore_pts + load_pts))
    rec = "push" if score >= 75 else "maintain" if score >= 55 else "light" if score >= 35 else "rest"
    return score, rec


def rest_seconds(velocity_drop_pct):
    """Rest by velocity loss across the last set: <15% short, 15-30% medium, >30% long."""
    if velocity_drop_pct < 15:
        return 75
    return 120 if velocity_drop_pct <= 30 else 180


def weekly_volume(sets):
    """sets: dicts with muscles, weight, reps. Returns volume (kg x reps) per muscle."""
    out = {}
    for s in sets:
        for m in s["muscles"]:
            out[m] = out.get(m, 0) + s["weight"] * s["reps"]
    return out


def weekly_report_payload(sets, readiness_scores, prs, form_avgs):
    """Structured facts for an LLM to narrate. The prompt must restrict it to these numbers."""
    return {"volume_by_muscle": weekly_volume(sets), "prs": prs,
            "avg_form_by_exercise": form_avgs, "readiness_by_day": readiness_scores}
