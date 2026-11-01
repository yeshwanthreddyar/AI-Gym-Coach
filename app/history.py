"""Workout history: groups sets into sessions (one session per day) with reps per muscle group."""
from app.muscles import reps_by_group, reps_by_muscle


def build_history(rows):
    """rows: dicts with day, exercise, weight, reps and form_score (optional).
    Returns sessions newest first, each with its sets, total reps, average form and reps per
    muscle group, plus totals across all the rows."""
    by_day = {}
    for r in rows:
        by_day.setdefault(r["day"], []).append(r)

    sessions = []
    for day in sorted(by_day, reverse=True):
        sets = by_day[day]
        forms = [s["form_score"] for s in sets if s.get("form_score") is not None]
        sessions.append({
            "day": day,
            "sets": [{"exercise": s["exercise"], "weight": s["weight"], "reps": s["reps"],
                      "form_score": s.get("form_score")} for s in sets],
            "total_reps": sum(s["reps"] for s in sets),
            "avg_form": round(sum(forms) / len(forms)) if forms else None,
            "by_group": reps_by_group(sets),
        })
    return {
        "sessions": sessions,
        "by_group": reps_by_group(rows),
        "by_muscle": reps_by_muscle(rows),
    }
