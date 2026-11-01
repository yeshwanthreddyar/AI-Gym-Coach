from datetime import date, timedelta
from app.goals import (validate_target, remaining_kg, weekly_change, review, status_text,
                       intended_rate)
from app.nutrition import goal_key, targets

TODAY = date(2026, 10, 31)


def days_ago(n):
    return TODAY - timedelta(days=n)


def test_goal_keys_and_old_names():
    assert goal_key("weight_loss") == "lose_weight"
    assert goal_key("lean_body") == "lose_weight"
    assert goal_key("muscle_gain") == "gain_weight"
    assert goal_key("maintenance") == "maintain"
    assert goal_key("something else") == "maintain"


def test_gain_target_must_be_higher():
    assert validate_target(70, 65, "gain_weight")
    assert validate_target(70, 70, "gain_weight")
    assert validate_target(70, 75, "gain_weight") == []


def test_lose_target_must_be_lower():
    assert validate_target(70, 75, "lose_weight")
    assert validate_target(70, 70, "lose_weight")
    assert validate_target(70, 65, "lose_weight") == []


def test_target_required_and_in_range():
    assert validate_target(70, None, "lose_weight")
    assert validate_target(70, 20, "lose_weight")
    assert validate_target(70, 400, "gain_weight")


def test_maintain_needs_no_target():
    assert validate_target(70, None, "maintain") == []


def test_remaining_kg_direction():
    assert remaining_kg(80, 72, "lose_weight") == 8
    assert remaining_kg(60, 66, "gain_weight") == 6
    assert remaining_kg(70, None, "maintain") is None


def test_weekly_change_uses_last_seven_days():
    logs = [(days_ago(20), 90.0), (days_ago(6), 81.0), (days_ago(0), 80.2)]
    assert weekly_change(logs, TODAY) == -0.8


def test_weekly_change_needs_two_weigh_ins():
    assert weekly_change([(days_ago(1), 80.0)], TODAY) is None
    assert weekly_change([(days_ago(20), 80.0), (days_ago(15), 79.0)], TODAY) is None


def test_lose_too_slowly_reduces_calories():
    new, msg = review(0, "lose_weight", -0.05, 5)
    assert new == -150 and "slower" in msg


def test_lose_too_fast_raises_calories():
    new, msg = review(0, "lose_weight", -1.5, 5)
    assert new == 150 and "faster" in msg


def test_lose_on_track_changes_nothing():
    new, msg = review(0, "lose_weight", -0.36, 5)
    assert new == 0 and "On track" in msg


def test_gain_too_slowly_raises_calories():
    new, _ = review(0, "gain_weight", 0.0, 5)
    assert new == 150


def test_gain_too_fast_reduces_calories():
    new, _ = review(0, "gain_weight", 1.0, 5)
    assert new == -150


def test_adjustment_is_capped():
    new, msg = review(500, "gain_weight", 0.0, 5)
    assert new == 500 and "limit" in msg


def test_no_review_without_data():
    new, msg = review(150, "lose_weight", None, 5)
    assert new == 150 and "twice" in msg


def test_reached_target_stops_reviews():
    new, msg = review(0, "lose_weight", -0.3, 0.2)
    assert new == 0 and "reached" in msg


def test_maintain_review():
    assert review(0, "maintain", 1.0, None)[0] == -100
    assert review(0, "maintain", -1.0, None)[0] == 100
    assert review(0, "maintain", 0.2, None)[0] == 0


def test_status_text_mentions_change_and_remaining():
    txt = status_text("lose_weight", -0.8, 7.2)
    assert "lost 0.8 kg" in txt and "7.2 kg to go" in txt


def test_calorie_adjust_changes_targets():
    base = {"weight_kg": 80, "height_cm": 178, "age": 30, "sex": "male",
            "workout": "strength", "goal": "lose_weight", "calorie_adjust": 0}
    more = dict(base, calorie_adjust=150)
    assert targets(more)["kcal"] - targets(base)["kcal"] == 150


def test_intended_rate_signs():
    assert intended_rate("lose_weight") < 0 < intended_rate("gain_weight")
