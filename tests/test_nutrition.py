from app.nutrition import (FOODS, check_food, targets, search_foods, day_plan,
                           parse_allergies, totals, nutrients_for)

MALE = {"weight_kg": 80, "height_cm": 178, "age": 30, "sex": "male",
        "workout": "strength", "goal": "weight_loss", "diet": "non-vegetarian", "allergies": ""}
VEGAN = dict(MALE, diet="vegan", goal="muscle_gain", allergies="peanut, soy, gluten")


def test_targets_weight_loss_male():
    t = targets(MALE)
    assert 2300 <= t["kcal"] <= 2400          # BMR ~1768, x1.55, minus 400
    assert t["protein"] == 144                # 1.8 g per kg
    assert t["floor_applied"] is False


def test_calorie_floor_applied_for_small_user():
    small = {"weight_kg": 40, "height_cm": 150, "age": 60, "sex": "female",
             "workout": "none", "goal": "weight_loss"}
    t = targets(small)
    assert t["kcal"] == 1200 and t["floor_applied"] is True


def test_parse_allergies_maps_aliases():
    tags, unknown = parse_allergies("Milk, nuts, Wheat, dragonfruit")
    assert tags == {"milk", "tree_nut", "gluten"}
    assert unknown == ["dragonfruit"]


def test_search_respects_query_and_diet():
    hits = search_foods("chick", MALE)
    assert any(h["name"].startswith("Chickpeas") for h in hits)
    assert search_foods("", MALE) == []


def test_ok_food_passes():
    assert check_food("Oats, cooked in water", MALE)["status"] == "ok"


def test_limit_food_gets_a_swap():
    r = check_food("Potato chips", MALE)
    assert r["status"] == "limit"
    assert r["alternatives"], "expected at least one healthier snack"
    assert all(a in {f[0] for f in FOODS if f[8] == "ok"} for a in r["alternatives"])


def test_vegan_user_is_told_about_animal_food():
    r = check_food("Paneer", VEGAN)
    assert r["status"] == "not_in_diet"
    assert r["alternatives"]
    for name in r["alternatives"]:
        food = next(f for f in FOODS if f[0] == name)
        assert food[2] == "vegan"


def test_allergy_blocks_the_food():
    r = check_food("Peanut butter", VEGAN)
    assert r["status"] == "blocked"
    assert "peanut" in r["message"]


def test_unknown_food():
    assert check_food("Dragon fruit smoothie", MALE)["status"] == "unknown"


def test_nutrients_scale_with_grams():
    n = nutrients_for("White rice, cooked", 200)
    assert n["kcal"] == 260 and n["protein"] == 5.4


def test_day_plan_has_four_meals_and_hits_the_target():
    plan = day_plan(MALE, day_index=0)
    assert [m["meal"] for m in plan["meals"]] == ["breakfast", "lunch", "snack", "dinner"]
    target = plan["targets"]["kcal"]
    assert abs(plan["totals"]["kcal"] - target) / target < 0.25


def test_vegan_allergy_plan_is_safe():
    plan = day_plan(VEGAN, day_index=3)
    names = [i["food"] for m in plan["meals"] for i in m["items"]]
    assert names, "plan should not be empty"
    for name in names:
        food = next(f for f in FOODS if f[0] == name)
        assert food[2] == "vegan", name
        assert "peanut" not in food[7] and "soy" not in food[7] and "gluten" not in food[7], name


def test_totals_sum_entries():
    t = totals([{"kcal": 100, "protein": 5, "carbs": 10, "fat": 2},
                {"kcal": 50, "protein": 1, "carbs": 5, "fat": 1}])
    assert t == {"kcal": 150, "protein": 6, "carbs": 15, "fat": 3}


def _foods(plan):
    return [i["food"] for m in plan["meals"] for i in m["items"]]


def _diet_of(name):
    return next(f for f in FOODS if f[0] == name)[2]


def test_vegetarian_plan_has_no_meat_fish_or_eggs():
    veg = dict(MALE, diet="vegetarian")
    for d in range(6):
        for name in _foods(day_plan(veg, day_index=d)):
            assert _diet_of(name) in ("vegan", "veg"), name


def test_vegan_plan_only_has_vegan_food():
    for d in range(6):
        for name in _foods(day_plan(VEGAN, day_index=d)):
            assert _diet_of(name) == "vegan", name


def test_non_vegetarian_plan_has_both_kinds_of_protein():
    nonveg = dict(MALE, diet="non-vegetarian")
    for d in range(6):
        plan = day_plan(nonveg, day_index=d)
        proteins = [i["food"] for m in plan["meals"] for i in m["items"]
                    if next(f for f in FOODS if f[0] == i["food"])[1] == "protein"]
        kinds = {_diet_of(p) for p in proteins}
        assert "nonveg" in kinds, f"day {d}: no meat or fish in {proteins}"
        assert kinds & {"veg", "vegan"}, f"day {d}: no vegetarian protein in {proteins}"
