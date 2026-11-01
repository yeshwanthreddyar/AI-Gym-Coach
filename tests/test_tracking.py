from datetime import date
from app.tracking import period_key, summarize, streak
from app.coaching import coach, top_issues


def test_period_keys():
    assert period_key("2026-10-24", "day") == "2026-10-24"
    assert period_key("2026-10-24", "month") == "2026-10"
    assert period_key("2026-10-24", "week") == "2026-W43"


def test_weekly_summary_and_improvement():
    rows = [
        {"day": "2026-10-05", "exercise": "Back squat", "weight": 60, "reps": 8, "form_score": 80},
        {"day": "2026-10-05", "exercise": "Back squat", "weight": 60, "reps": 8, "form_score": 90},
        {"day": "2026-10-12", "exercise": "Back squat", "weight": 65, "reps": 8, "form_score": 85},
    ]
    weeks = summarize(rows, "week")
    assert len(weeks) == 2
    w1, w2 = weeks
    assert w1["period"] == "2026-W41" and w1["sessions"] == 1 and w1["sets"] == 2
    assert w1["volume"] == 960 and w1["avg_form"] == 85
    assert w1["improved"] == {}
    assert abs(w2["improved"]["Back squat"] - 6.3) < 0.05


def test_monthly_summary_groups_by_month():
    rows = [
        {"day": "2026-09-30", "exercise": "Bench press", "weight": 50, "reps": 5, "form_score": 100},
        {"day": "2026-10-01", "exercise": "Bench press", "weight": 52.5, "reps": 5, "form_score": 100},
    ]
    months = summarize(rows, "month")
    assert [m["period"] for m in months] == ["2026-09", "2026-10"]


def test_empty_summary():
    assert summarize([], "week") == []


def test_streak():
    today = date(2026, 10, 24)
    assert streak([date(2026, 10, 22), date(2026, 10, 23), date(2026, 10, 24)], today) == 3
    assert streak([date(2026, 10, 21), date(2026, 10, 22), date(2026, 10, 23)], today) == 3
    assert streak([date(2026, 10, 20), date(2026, 10, 24)], today) == 1
    assert streak([], today) == 0


def test_coaching_messages():
    ok = coach([])
    assert ok["items"] == [] and "Good form" in ok["summary"]
    bad = coach(["too_fast", "incomplete_depth", "too_fast"])
    assert "rushing" in bad["summary"].lower()
    assert [i["flag"] for i in bad["items"]] == ["too_fast", "incomplete_depth"]
    assert all({"issue", "fix", "drill"} <= set(i) for i in bad["items"])


def test_top_issues():
    top = top_issues([["too_fast"], ["too_fast", "incomplete_depth"], ["incomplete_depth"], ["too_fast"]], n=2)
    assert top[0]["flag"] == "too_fast" and top[0]["count"] == 3
    assert top[1]["flag"] == "incomplete_depth" and top[1]["count"] == 2
