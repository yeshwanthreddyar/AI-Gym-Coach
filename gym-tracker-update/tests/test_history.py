from app.history import build_history


def row(day, exercise, reps, weight=50, form=90):
    return {"day": day, "exercise": exercise, "weight": weight, "reps": reps, "form_score": form}


def test_empty_history():
    out = build_history([])
    assert out == {"sessions": [], "by_group": {}, "by_muscle": {}}


def test_sessions_are_grouped_by_day_newest_first():
    rows = [
        row("2026-10-20", "Bench press", 10),
        row("2026-10-20", "Dumbbell curl", 12),
        row("2026-10-24", "Back squat", 8),
    ]
    out = build_history(rows)
    assert [s["day"] for s in out["sessions"]] == ["2026-10-24", "2026-10-20"]
    newest, older = out["sessions"]
    assert newest["total_reps"] == 8
    assert older["total_reps"] == 22
    assert len(older["sets"]) == 2


def test_reps_per_group_in_a_session():
    rows = [row("2026-10-20", "Dumbbell curl", 10)]
    session = build_history(rows)["sessions"][0]
    assert session["by_group"]["Arms"] == 15  # biceps 10 + forearms half-weight 5


def test_totals_across_the_whole_range():
    rows = [
        row("2026-10-20", "Bench press", 10),
        row("2026-10-24", "Bench press", 10),
    ]
    out = build_history(rows)
    assert out["by_muscle"]["chest"] == 20
    assert out["by_group"]["Chest"] == 20 + 0  # triceps and shoulders are counted in their own groups
    assert out["by_group"]["Arms"] == 10  # triceps at half weight: 5 per session
    assert out["by_group"]["Shoulders"] == 10


def test_average_form_for_a_session():
    rows = [row("2026-10-20", "Bench press", 10, form=80),
            row("2026-10-20", "Bench press", 10, form=90)]
    assert build_history(rows)["sessions"][0]["avg_form"] == 85


def test_unknown_exercise_counts_nothing_but_is_listed():
    rows = [row("2026-10-20", "Made up lift", 10)]
    out = build_history(rows)
    assert out["sessions"][0]["total_reps"] == 10
    assert out["by_group"] == {}
