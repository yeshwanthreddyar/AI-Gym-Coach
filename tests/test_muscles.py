import os
import re
from app.muscles import MAP, GROUP_OF, muscles_for, reps_by_muscle, reps_by_group


def test_known_and_unknown_exercises():
    assert muscles_for("Bench press") == (["chest"], ["triceps", "shoulders"])
    assert muscles_for("Not a real lift") == ([], [])


def test_primary_full_secondary_half():
    totals = reps_by_muscle([{"exercise": "Bench press", "reps": 10}])
    assert totals["chest"] == 10
    assert totals["triceps"] == 5
    assert totals["shoulders"] == 5


def test_totals_add_up_across_sets():
    sets = [
        {"exercise": "Back squat", "reps": 8},
        {"exercise": "Back squat", "reps": 8},
        {"exercise": "Leg extension", "reps": 12},
    ]
    totals = reps_by_muscle(sets)
    assert totals["quads"] == 28
    assert totals["glutes"] == 16  # primary for back squat, two sets of 8
    assert totals["hamstrings"] == 8


def test_group_totals():
    sets = [
        {"exercise": "Dumbbell curl", "reps": 10},
        {"exercise": "Triceps pushdown", "reps": 10},
    ]
    groups = reps_by_group(sets)
    assert groups["Arms"] == 20 + 5  # biceps 10 + forearms 5 + triceps 10
    assert "Legs" not in groups


def test_every_muscle_maps_to_a_group():
    used = set()
    for primary, secondary in MAP.values():
        used.update(primary)
        used.update(secondary)
    assert used <= set(GROUP_OF), used - set(GROUP_OF)


def test_map_has_all_89_exercises():
    assert len(MAP) == 89


def test_map_matches_website_data_if_present():
    """If app/static/data.js exists, every exercise listed there must have a mapping."""
    path = os.path.join(os.path.dirname(__file__), "..", "app", "static", "data.js")
    if not os.path.exists(path):
        return
    text = open(path, encoding="utf8").read()
    names = re.findall(r"([A-Za-z][A-Za-z\- ]*?):(?:pu|pl|hg|sq|cu|ra|cr|m|t)(?=[,\"])", text)
    missing = sorted(set(names) - set(MAP))
    assert not missing, f"no muscle mapping for: {missing}"
