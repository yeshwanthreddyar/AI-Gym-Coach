"""Rule-based suggestions from a user's recent sets. Each rule gives one message, a reason
taken from the user's own numbers, and an action. At most `limit` suggestions are returned."""
from datetime import date, timedelta

from app.muscles import GROUP_OF, muscles_for

GROUPS = ["Chest", "Back", "Legs", "Shoulders", "Arms", "Core"]
EXAMPLE = {"Chest": "Bench press", "Back": "Lat pulldown", "Legs": "Back squat",
           "Shoulders": "Lateral raise", "Arms": "Dumbbell curl", "Core": "Plank"}
REP_TARGET = {"strength": (3, 6), "muscle": (8, 12), "general": (8, 12),
              "fat_loss": (10, 15), "mobility": (10, 15)}
HARD_DAY_REPS = 30  # reps for one group in a day that count as hard


def _day(s):
    return s["day"] if isinstance(s["day"], date) else date.fromisoformat(s["day"])


def _group_reps(sets):
    out = {g: 0.0 for g in GROUPS}
    for s in sets:
        primary, secondary = muscles_for(s["exercise"])
        for m in primary:
            out[GROUP_OF[m]] += s["reps"]
        for m in secondary:
            out[GROUP_OF[m]] += 0.5 * s["reps"]
    return out


def suggest(sets, today, goal="general", limit=3):
    """sets: dicts with exercise, reps and day (date or ISO string). Returns up to `limit` dicts
    with message, reason and action, most important first."""
    if not sets:
        return []
    sets = [dict(s, _d=_day(s)) for s in sets if _day(s) <= today]
    if not sets:
        return []
    trained_ever = set()
    for s in sets:
        for m in muscles_for(s["exercise"])[0]:
            trained_ever.add(GROUP_OF[m])

    recent7 = [s for s in sets if s["_d"] > today - timedelta(days=7)]
    recent14 = [s for s in sets if s["_d"] > today - timedelta(days=14)]
    out = []

    # 1. A group trained before but not in the last 7 days
    r7 = _group_reps(recent7)
    for g in GROUPS:
        if g in trained_ever and r7[g] == 0:
            out.append({"message": f"Add a {g.lower()} session this week.",
                        "reason": f"0 {g.lower()} reps in the last 7 days.",
                        "action": f"Try {EXAMPLE[g]}."})

    # 2. One group far ahead of the rest over 14 days
    r14 = _group_reps(recent14)
    for g in GROUPS:
        others = [r14[o] for o in GROUPS if o != g]
        avg_others = sum(others) / len(others)
        if r14[g] > 0 and avg_others > 0 and r14[g] > 2 * avg_others:
            low = min((o for o in GROUPS if o != g), key=lambda o: r14[o])
            out.append({"message": f"Your {g.lower()} work is well ahead of {low.lower()}.",
                        "reason": f"{round(r14[g])} {g.lower()} reps vs about {round(avg_others)} on average elsewhere (14 days).",
                        "action": f"Add {low.lower()} sets, for example {EXAMPLE[low]}."})
            break

    # 3. Average reps per set outside the target for the goal
    if len(recent14) >= 3:
        avg = sum(s["reps"] for s in recent14) / len(recent14)
        lo, hi = REP_TARGET.get(goal, REP_TARGET["general"])
        if avg < lo or avg > hi:
            out.append({"message": f"Your sets average {round(avg)} reps. For this goal, aim for {lo}-{hi}.",
                        "reason": f"Average of {len(recent14)} sets in the last 14 days.",
                        "action": f"Adjust the load so most sets land in {lo}-{hi} reps."})

    # 4. Same group hard three days running
    for g in GROUPS:
        days_hard = 0
        for back in range(3):
            d = today - timedelta(days=back)
            day_sets = [s for s in sets if s["_d"] == d]
            if _group_reps(day_sets)[g] >= HARD_DAY_REPS:
                days_hard += 1
        if days_hard == 3:
            out.append({"message": f"Take a lighter {g.lower()} day.",
                        "reason": f"{g} reps were high on each of the last 3 days.",
                        "action": "Use lighter loads or do a different group today."})
            break

    return out[:limit]
