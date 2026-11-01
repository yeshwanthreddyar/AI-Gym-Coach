"""Weight goals: target checks, weekly change, and calorie reviews.

A review runs at most once a week. If progress is much slower or faster than the goal's
planned rate, calories for the day change by a fixed step, within a set limit."""
from app.nutrition import GOAL_ADJ, GOAL_LABEL, goal_key

KCAL_PER_KG = 7700          # approximate energy in 1 kg of body weight
STEP_KCAL = 150             # change per review
MAX_ADJUST_KCAL = 500       # limit on the total change from the starting target, either way


def intended_rate(goal):
    """kg per week the goal aims for. Negative when losing, positive when gaining."""
    return GOAL_ADJ[goal_key(goal)] * 7 / KCAL_PER_KG


def validate_target(current_kg, target_kg, goal):
    """Returns a list of error messages. Empty means the target is valid for this goal."""
    g = goal_key(goal)
    if g == "maintain":
        return []
    if target_kg is None:
        return ["Enter the weight you want to reach."]
    errors = []
    if not 30 <= target_kg <= 300:
        errors.append("Target weight must be between 30 and 300 kg.")
    if g == "gain_weight" and target_kg <= current_kg:
        errors.append(f"To gain weight, your target ({target_kg} kg) must be higher than "
                      f"your current weight ({current_kg} kg).")
    if g == "lose_weight" and target_kg >= current_kg:
        errors.append(f"To lose weight, your target ({target_kg} kg) must be lower than "
                      f"your current weight ({current_kg} kg).")
    return errors


def remaining_kg(current_kg, target_kg, goal):
    g = goal_key(goal)
    if g == "maintain" or target_kg is None:
        return None
    if g == "lose_weight":
        return round(current_kg - target_kg, 2)
    return round(target_kg - current_kg, 2)


def weekly_change(logs, today):
    """logs: (date, kg) pairs, oldest first. Change from the first to the last weigh-in in the
    last 7 days, or None if there are fewer than two weigh-ins in that window."""
    from datetime import timedelta
    window = [kg for d, kg in logs if today - timedelta(days=7) <= d <= today]
    if len(window) < 2:
        return None
    return round(window[-1] - window[0], 2)


def review(adjust, goal, change, remaining):
    """Returns (new_adjust, message). adjust is the current calorie change in kcal per day."""
    g = goal_key(goal)
    if change is None:
        return adjust, "Log your weight at least twice in a week to get a diet review."

    if g == "maintain":
        if change > 0.5:
            step, why = -100, f"You gained {change:.1f} kg this week"
        elif change < -0.5:
            step, why = 100, f"You lost {-change:.1f} kg this week"
        else:
            return adjust, "Your weight is steady. Keep going."
    else:
        if remaining is not None and remaining <= 0.5:
            return adjust, "You've reached your target weight. Consider switching to maintenance."
        rate = abs(intended_rate(g))
        progress = -change if g == "lose_weight" else change   # positive means toward the goal
        if progress < 0.5 * rate:
            step = -STEP_KCAL if g == "lose_weight" else STEP_KCAL
            why = "Progress is slower than planned"
        elif progress > 1.5 * rate:
            step = STEP_KCAL if g == "lose_weight" else -STEP_KCAL
            why = "Progress is faster than planned"
        else:
            return adjust, f"On track: about {abs(change):.1f} kg this week."

    new = max(-MAX_ADJUST_KCAL, min(MAX_ADJUST_KCAL, adjust + step))
    if new == adjust:
        return adjust, f"{why}, but calories are already at the limit of the change allowed."
    verb = "reduced" if new < adjust else "raised"
    return new, f"{why}, so calories were {verb} by {abs(new - adjust)} a day."


def status_text(goal, change, remaining):
    g = goal_key(goal)
    if g == "maintain":
        return "Maintaining your weight. Log weekly to keep an eye on it."
    if change is None:
        return "Log your weight at least twice in a week to see your progress."
    if remaining is not None and remaining <= 0.5:
        return "Target reached."
    if change < 0:
        moved = f"lost {abs(change):.1f} kg"
    elif change > 0:
        moved = f"gained {change:.1f} kg"
    else:
        moved = "kept the same weight"
    return f"You {moved} this week. {remaining:.1f} kg to go."


__all__ = ["GOAL_LABEL", "intended_rate", "validate_target", "remaining_kg", "weekly_change",
           "review", "status_text", "goal_key"]
