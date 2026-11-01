from datetime import date
import numpy as np
from app.biomech import angle_at, torso_lean, personalized_lean_limit
from app.reps import EXERCISES, Rep, segment_reps, score_rep, attribute_cause
from app import analytics as an
from app.generator import generate_session

FPS = 30


def wave(n=5, mid=125, amp=45):
    """Angle cycles: 2 s per rep, starts at the top."""
    t = np.arange(0, n * 2 + 0.01, 1 / FPS)
    return mid + amp * np.cos(np.pi * t)


def test_angle_and_lean():
    assert abs(angle_at([0, 1], [0, 0], [1, 0]) - 90) < 1e-6
    assert abs(torso_lean(np.array([0.0, 0.0]), np.array([0.0, 1.0]))) < 1e-6


def test_counts_reps_on_clean_wave():
    assert len(segment_reps(wave(), FPS, EXERCISES["squat"])) == 5


def test_flags_incomplete_depth():
    reps = segment_reps(wave(mid=142.5, amp=27.5), FPS, EXERCISES["squat"])  # min ~115 deg
    assert reps and all(r.min_angle > 100 for r in reps)
    for r in reps:
        score_rep(r, EXERCISES["squat"])
        assert "incomplete_depth" in r.flags and r.form_score == 75


def test_leverage_changes_lean_flag():
    lean = np.full(21, 50.0)
    fixed = score_rep(Rep(0, 10, 20, 80, 80, 2.0), EXERCISES["squat"], lean, personalized_lean_limit(1.0))
    personal = score_rep(Rep(0, 10, 20, 80, 80, 2.0), EXERCISES["squat"], lean, personalized_lean_limit(1.3))
    assert "excess_forward_lean" in fixed.flags
    assert "excess_forward_lean" not in personal.flags


def test_attribution():
    assert attribute_cause([Rep(0, 1, 2, 1, 80, 2.0)]) == "none"
    first_bad = [Rep(0, 1, 2, 1, 80, 2.0, flags=["incomplete_depth"])] * 4
    assert attribute_cause(first_bad) == "technique"


def test_epley_and_plateau():
    assert round(an.epley_1rm(100, 5), 1) == 116.7
    assert an.plateau([100, 100.2, 99.9, 100.1]) is True
    assert an.plateau([100, 105, 110, 115]) is False


def test_readiness_and_rest():
    assert an.readiness(8, [1, 1, 1], 1.0) == (100, "push")
    assert an.readiness(5, [5, 5], 1.5) == (0, "rest")
    assert [an.rest_seconds(x) for x in (10, 25, 40)] == [75, 120, 180]


def test_overload():
    assert an.progressive_overload(60, 8, 5, 8, 90) == (62.5, 5, "+2.5 kg, restart at the low end of the range")
    assert an.progressive_overload(60, 6, 5, 8, 90)[1] == 7


def test_generator_respects_injury_and_rest():
    s = generate_session(0, ["barbell", "dumbbell"], ["shoulders"], {}, date(2026, 10, 24), "maintain")
    assert s["split"] == "push"
    assert all("Overhead" not in e["name"] for e in s["exercises"])
    assert generate_session(0, [], [], {}, date(2026, 10, 24), "rest")["exercises"] == []
