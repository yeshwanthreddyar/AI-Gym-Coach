"""Group workout sets into day, week and month summaries, and compute attendance streaks."""
from collections import defaultdict
from datetime import date, timedelta

from app.analytics import epley_1rm


def period_key(day, period):
    """Map a date (or ISO string) to its period label: '2026-10-24', '2026-W43' or '2026-10'."""
    d = date.fromisoformat(day) if isinstance(day, str) else day
    if period == "day":
        return d.isoformat()
    if period == "week":
        y, w, _ = d.isocalendar()
        return f"{y}-W{w:02d}"
    if period == "month":
        return d.strftime("%Y-%m")
    raise ValueError("period must be day, week or month")


def summarize(rows, period="week"):
    """rows: dicts with day, exercise, weight, reps, form_score.
    Returns one summary per period that has sets, oldest first. 'improved' compares each
    exercise's best estimated 1RM with the previous period that contained that exercise."""
    groups = defaultdict(list)
    for r in rows:
        groups[period_key(r["day"], period)].append(r)

    out = []
    prev_best = {}
    for key in sorted(groups):
        items = groups[key]
        best = {}
        for r in items:
            e = epley_1rm(r["weight"], r["reps"])
            best[r["exercise"]] = max(best.get(r["exercise"], 0.0), e)
        improved = {ex: round(best[ex] - prev_best[ex], 1) for ex in best if ex in prev_best}
        forms = [r["form_score"] for r in items if r.get("form_score") is not None]
        out.append({
            "period": key,
            "sessions": len({r["day"] for r in items}),
            "sets": len(items),
            "volume": round(sum(r["weight"] * r["reps"] for r in items), 1),
            "avg_form": round(sum(forms) / len(forms)) if forms else None,
            "best_e1rm": {ex: round(v, 1) for ex, v in best.items()},
            "improved": improved,
        })
        prev_best = best
    return out


def streak(attended, today):
    """Consecutive attended days. Counts back from today, or from yesterday if today isn't logged yet."""
    days = set(attended)
    d = today if today in days else today - timedelta(days=1)
    n = 0
    while d in days:
        n += 1
        d -= timedelta(days=1)
    return n
