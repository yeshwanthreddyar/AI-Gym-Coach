from datetime import date, timedelta
from app.suggestions import suggest

TODAY = date(2026, 10, 24)


def s(exercise, reps, days_ago):
    return {"exercise": exercise, "reps": reps, "day": (TODAY - timedelta(days=days_ago)).isoformat()}


def test_new_user_gets_nothing():
    assert suggest([], TODAY) == []


def test_neglected_group_is_suggested():
    sets = [s("Back squat", 8, 10), s("Bench press", 8, 1)]
    msgs = [x["message"] for x in suggest(sets, TODAY)]
    assert any("legs" in m for m in msgs)
    assert not any("chest" in m for m in msgs)


def test_suggestion_has_reason_from_data():
    sets = [s("Back squat", 8, 10), s("Bench press", 8, 1)]
    legs = [x for x in suggest(sets, TODAY) if "legs" in x["message"]][0]
    assert legs["reason"] == "0 legs reps in the last 7 days."
    assert legs["action"] == "Try Back squat."


def test_imbalance_is_suggested():
    sets = [s("Bench press", 10, d) for d in range(0, 10)] + [s("Leg curl", 5, 2)]
    msgs = [x["message"] for x in suggest(sets, TODAY)]
    assert any("Your chest work is well ahead" in m for m in msgs)


def test_rep_range_for_goal():
    sets = [s("Bench press", 12, 1), s("Bench press", 12, 2), s("Bench press", 12, 3)]
    out = suggest(sets, TODAY, goal="strength")
    assert any("3-6" in x["message"] for x in out)
    out_muscle = suggest(sets, TODAY, goal="muscle")
    assert not any("3-6" in x["message"] for x in out_muscle)


def test_hard_three_days_in_a_row():
    sets = [s("Bench press", 15, d) for d in range(3)] + [s("Bench press", 15, d) for d in range(3)]
    out = suggest(sets, TODAY)
    assert any("lighter chest day" in x["message"] for x in out)


def test_limit_is_respected():
    sets = [s("Back squat", 8, 10), s("Bench press", 8, 10), s("Dumbbell curl", 3, 1)]
    assert len(suggest(sets, TODAY, limit=2)) <= 2
