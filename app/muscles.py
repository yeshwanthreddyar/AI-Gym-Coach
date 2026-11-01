"""Which muscles each exercise trains, and reps totals per muscle and per muscle group.

A set's reps count fully toward its primary muscles and at half weight toward its
secondary muscles. Edit the MAP below to change the mapping."""

# exercise: (primary muscles, secondary muscles)
MAP = {
    # Chest
    "Bench press": (["chest"], ["triceps", "shoulders"]),
    "Incline bench press": (["chest"], ["shoulders", "triceps"]),
    "Decline bench press": (["chest"], ["triceps"]),
    "Dumbbell fly": (["chest"], []),
    "Incline dumbbell fly": (["chest"], ["shoulders"]),
    "Cable crossover": (["chest"], []),
    "Push-up": (["chest"], ["triceps", "shoulders", "core"]),
    "Wide push-up": (["chest"], ["shoulders", "triceps"]),
    "Diamond push-up": (["triceps"], ["chest"]),
    "Decline push-up": (["chest"], ["shoulders", "triceps"]),
    "Dips": (["chest", "triceps"], ["shoulders"]),
    "Pec deck": (["chest"], []),
    "Machine chest press": (["chest"], ["triceps", "shoulders"]),
    "Svend press": (["chest"], []),
    "Dumbbell pullover": (["lats", "chest"], ["triceps"]),
    # Back
    "Lat pulldown": (["lats"], ["biceps", "upper_back"]),
    "Pull-up": (["lats"], ["biceps", "upper_back"]),
    "Chin-up": (["lats", "biceps"], ["upper_back"]),
    "Barbell row": (["upper_back", "lats"], ["biceps", "lower_back"]),
    "Dumbbell row": (["lats", "upper_back"], ["biceps"]),
    "Seated cable row": (["upper_back", "lats"], ["biceps"]),
    "T-bar row": (["upper_back", "lats"], ["biceps", "lower_back"]),
    "Single-arm cable row": (["lats", "upper_back"], ["biceps"]),
    "Straight-arm pulldown": (["lats"], []),
    "Face pull": (["upper_back", "shoulders"], []),
    "Deadlift": (["hamstrings", "glutes", "lower_back"], ["quads", "forearms", "core"]),
    "Rack pull": (["lower_back", "glutes"], ["hamstrings", "forearms"]),
    "Inverted row": (["upper_back", "lats"], ["biceps"]),
    "Back extension": (["lower_back"], ["glutes", "hamstrings"]),
    "Meadows row": (["lats"], ["biceps", "upper_back"]),
    # Legs
    "Back squat": (["quads", "glutes"], ["hamstrings", "lower_back", "core"]),
    "Front squat": (["quads"], ["glutes", "core"]),
    "Goblet squat": (["quads"], ["glutes", "core"]),
    "Leg press": (["quads"], ["glutes"]),
    "Lunge": (["quads", "glutes"], ["hamstrings"]),
    "Walking lunge": (["quads", "glutes"], ["hamstrings"]),
    "Bulgarian split squat": (["quads", "glutes"], ["hamstrings"]),
    "Romanian deadlift": (["hamstrings", "glutes"], ["lower_back"]),
    "Leg extension": (["quads"], []),
    "Leg curl": (["hamstrings"], ["calves"]),
    "Hip thrust": (["glutes"], ["hamstrings"]),
    "Glute bridge": (["glutes"], ["hamstrings"]),
    "Step-up": (["quads", "glutes"], ["hamstrings"]),
    "Calf raise": (["calves"], []),
    "Hack squat": (["quads"], ["glutes"]),
    # Shoulders
    "Overhead press": (["shoulders"], ["triceps", "upper_back"]),
    "Dumbbell shoulder press": (["shoulders"], ["triceps"]),
    "Arnold press": (["shoulders"], ["triceps"]),
    "Lateral raise": (["shoulders"], []),
    "Front raise": (["shoulders"], ["chest"]),
    "Rear delt fly": (["shoulders"], ["upper_back"]),
    "Upright row": (["shoulders"], ["biceps", "upper_back"]),
    "Cable lateral raise": (["shoulders"], []),
    "Machine shoulder press": (["shoulders"], ["triceps"]),
    "Pike push-up": (["shoulders"], ["triceps"]),
    "Landmine press": (["shoulders"], ["chest", "triceps"]),
    "Shrug": (["upper_back"], ["shoulders"]),
    "Reverse pec deck": (["shoulders", "upper_back"], []),
    "Handstand push-up": (["shoulders"], ["triceps", "core"]),
    # Arms
    "Barbell curl": (["biceps"], ["forearms"]),
    "Dumbbell curl": (["biceps"], ["forearms"]),
    "Hammer curl": (["biceps"], ["forearms"]),
    "Preacher curl": (["biceps"], []),
    "Concentration curl": (["biceps"], []),
    "Cable curl": (["biceps"], []),
    "Incline curl": (["biceps"], []),
    "Triceps pushdown": (["triceps"], []),
    "Overhead triceps extension": (["triceps"], []),
    "Skull crusher": (["triceps"], []),
    "Close-grip bench press": (["triceps"], ["chest", "shoulders"]),
    "Triceps kickback": (["triceps"], []),
    "Bench dip": (["triceps"], ["chest", "shoulders"]),
    "Reverse curl": (["forearms", "biceps"], []),
    "Wrist curl": (["forearms"], []),
    # Core
    "Plank": (["core"], ["shoulders"]),
    "Side plank": (["core"], ["shoulders"]),
    "Hollow hold": (["core"], []),
    "Crunch": (["core"], []),
    "Bicycle crunch": (["core"], []),
    "Hanging knee raise": (["core"], ["forearms"]),
    "Leg raise": (["core"], []),
    "Russian twist": (["core"], []),
    "Mountain climber": (["core"], ["shoulders", "quads"]),
    "Dead bug": (["core"], []),
    "Bird dog": (["core", "lower_back"], ["glutes"]),
    "Ab wheel rollout": (["core"], ["shoulders", "lats"]),
    "Cable crunch": (["core"], []),
    "Sit-up": (["core"], []),
    "Flutter kick": (["core"], ["quads"]),
}

# Muscle -> the six muscle groups shown on the website
GROUP_OF = {
    "chest": "Chest",
    "upper_back": "Back", "lats": "Back", "lower_back": "Back",
    "quads": "Legs", "hamstrings": "Legs", "glutes": "Legs", "calves": "Legs",
    "shoulders": "Shoulders",
    "biceps": "Arms", "triceps": "Arms", "forearms": "Arms",
    "core": "Core",
}

SECONDARY_WEIGHT = 0.5


def muscles_for(exercise):
    """(primary, secondary) muscles for an exercise. Unknown exercises train nothing recorded."""
    return MAP.get(exercise, ([], []))


def reps_by_muscle(sets, secondary_weight=SECONDARY_WEIGHT):
    """sets: dicts with 'exercise' and 'reps'. Returns {muscle: reps}, rounded to 1 decimal."""
    totals = {}
    for s in sets:
        primary, secondary = muscles_for(s["exercise"])
        for m in primary:
            totals[m] = totals.get(m, 0) + s["reps"]
        for m in secondary:
            totals[m] = totals.get(m, 0) + secondary_weight * s["reps"]
    return {m: round(v, 1) for m, v in totals.items()}


def reps_by_group(sets, secondary_weight=SECONDARY_WEIGHT):
    """Same as reps_by_muscle, summed into the six website groups."""
    groups = {}
    for muscle, reps in reps_by_muscle(sets, secondary_weight).items():
        g = GROUP_OF.get(muscle)
        if g:
            groups[g] = round(groups.get(g, 0) + reps, 1)
    return groups
