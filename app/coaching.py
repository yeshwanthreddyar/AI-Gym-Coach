"""Turn rep flags into plain-language feedback, a fix, and a drill."""
from collections import Counter

ISSUES = {
    "incomplete_depth": {
        "issue": "Not reaching full depth",
        "fix": "Lower until the joint reaches the target depth before you press back up. "
               "If you can't get there with control, reduce the load.",
        "drill": "Pause at the bottom for 2 seconds on every rep, or use a box at target height.",
    },
    "excess_forward_lean": {
        "issue": "Leaning too far forward",
        "fix": "Keep your chest up and brace your core. Keep your weight over the middle of your foot.",
        "drill": "Goblet squats with a light dumbbell held at the chest.",
    },
    "too_fast": {
        "issue": "Rushing the rep",
        "fix": "Control the lowering phase. Aim for about 2 seconds down and 1 second up.",
        "drill": "Tempo reps: 3 seconds down, 1 second pause, then up.",
    },
}

SUMMARY_OK = "Good form on this set. Keep it up."


def coach(flags, exercise=None):
    """Feedback for one set. 'exercise' is accepted so exercise-specific advice can be added later."""
    seen = []
    for f in flags or []:
        if f in ISSUES and f not in seen:
            seen.append(f)
    if not seen:
        return {"summary": SUMMARY_OK, "items": []}
    items = [{"flag": f, **ISSUES[f]} for f in seen]
    main = ISSUES[seen[0]]["issue"].lower()
    return {"summary": f"Main thing to work on: {main}.", "items": items}


def top_issues(flag_lists, n=3):
    """Most common form issues across many sets (e.g. the last week)."""
    c = Counter(f for flags in flag_lists for f in flags if f in ISSUES)
    return [{"flag": f, "count": k, **ISSUES[f]} for f, k in c.most_common(n)]
