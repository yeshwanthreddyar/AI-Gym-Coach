"""Food database, calorie and protein targets, diet and allergy checks, alternatives, and day plans.

Nutrition values are per 100 g, as approximate common values. They are a starting point;
check important figures against a source such as USDA FoodData Central or the Indian Food
Composition Tables. Guidance only, not medical advice.
"""
from datetime import date as _date  # noqa: F401  (kept for callers that import dates from here)

# name, role, diet, kcal, protein g, carbs g, fat g, allergens, flag
# role: protein, carb, veg, fruit, fat, snack, dish, drink
# diet: vegan (fits everyone), veg (vegetarian and non-vegetarian), nonveg (non-vegetarian only)
# flag: ok (everyday choice) or limit (eat sometimes, with a better swap suggested)
FOODS = [
    ("White rice, cooked", "carb", "vegan", 130, 2.7, 28, 0.3, "", "ok"),
    ("Brown rice, cooked", "carb", "vegan", 111, 2.6, 23, 0.9, "", "ok"),
    ("Chapati (whole wheat, no ghee)", "carb", "vegan", 264, 9, 50, 3.7, "gluten", "ok"),
    ("Oats, cooked in water", "carb", "vegan", 71, 2.5, 12, 1.5, "", "ok"),
    ("Whole wheat bread", "carb", "vegan", 247, 13, 41, 3.4, "gluten", "ok"),
    ("White bread", "carb", "vegan", 265, 9, 49, 3.2, "gluten", "limit"),
    ("Idli", "carb", "vegan", 135, 4, 28, 0.5, "", "ok"),
    ("Plain dosa", "carb", "vegan", 168, 4, 30, 3.7, "", "ok"),
    ("Poha, cooked", "carb", "vegan", 130, 2.5, 26, 2, "", "ok"),
    ("Upma", "carb", "vegan", 150, 3, 25, 4, "gluten", "ok"),
    ("Cooked pasta", "carb", "vegan", 158, 5.8, 31, 0.9, "gluten", "ok"),
    ("Quinoa, cooked", "carb", "vegan", 120, 4.4, 21, 1.9, "", "ok"),
    ("Corn flakes", "carb", "vegan", 357, 7.5, 84, 0.4, "gluten", "limit"),
    ("Boiled potato", "carb", "vegan", 87, 1.9, 20, 0.1, "", "ok"),
    ("Sweet potato, baked", "carb", "vegan", 90, 2, 21, 0.2, "", "ok"),
    ("Dal (toor), cooked", "protein", "vegan", 116, 7, 20, 0.4, "", "ok"),
    ("Moong dal, cooked", "protein", "vegan", 105, 7, 19, 0.4, "", "ok"),
    ("Chickpeas (chana), cooked", "protein", "vegan", 164, 8.9, 27, 2.6, "", "ok"),
    ("Rajma (kidney beans), cooked", "protein", "vegan", 127, 8.7, 23, 0.5, "", "ok"),
    ("Black beans, cooked", "protein", "vegan", 132, 8.9, 24, 0.5, "", "ok"),
    ("Lentils, cooked", "protein", "vegan", 116, 9, 20, 0.4, "", "ok"),
    ("Tofu, firm", "protein", "vegan", 144, 17, 3, 8.7, "soy", "ok"),
    ("Soya chunks, dry", "protein", "vegan", 345, 52, 33, 0.5, "soy", "ok"),
    ("Milk, full fat", "protein", "veg", 61, 3.2, 4.8, 3.3, "milk", "ok"),
    ("Skimmed milk", "protein", "veg", 34, 3.4, 5, 0.1, "milk", "ok"),
    ("Curd (plain, whole milk)", "protein", "veg", 61, 3.5, 4.7, 3.3, "milk", "ok"),
    ("Greek yogurt, plain", "protein", "veg", 59, 10, 3.6, 0.4, "milk", "ok"),
    ("Paneer", "protein", "veg", 265, 18, 1.2, 21, "milk", "ok"),
    ("Cheddar cheese", "fat", "veg", 403, 25, 1.3, 33, "milk", "limit"),
    ("Ghee", "fat", "veg", 900, 0, 0, 100, "milk", "limit"),
    ("Butter", "fat", "veg", 717, 0.9, 0.1, 81, "milk", "limit"),
    ("Egg, whole, boiled", "protein", "nonveg", 155, 13, 1.1, 11, "egg", "ok"),
    ("Egg white, boiled", "protein", "nonveg", 52, 11, 0.7, 0.2, "egg", "ok"),
    ("Chicken breast, cooked", "protein", "nonveg", 165, 31, 0, 3.6, "", "ok"),
    ("Chicken thigh, cooked", "protein", "nonveg", 209, 26, 0, 11, "", "ok"),
    ("Lean beef, cooked", "protein", "nonveg", 250, 26, 0, 15, "", "ok"),
    ("Pork, cooked", "protein", "nonveg", 242, 27, 0, 14, "", "limit"),
    ("Mutton, cooked", "protein", "nonveg", 294, 25, 0, 21, "", "limit"),
    ("Salmon, cooked", "protein", "nonveg", 206, 22, 0, 12, "fish", "ok"),
    ("Tuna, canned in water", "protein", "nonveg", 116, 26, 0, 1, "fish", "ok"),
    ("Prawns, cooked", "protein", "nonveg", 99, 24, 0.2, 0.3, "shellfish", "ok"),
    ("White fish (cod), cooked", "protein", "nonveg", 105, 23, 0, 0.9, "fish", "ok"),
    ("Broccoli, cooked", "veg", "vegan", 35, 2.4, 7, 0.4, "", "ok"),
    ("Spinach, raw", "veg", "vegan", 23, 2.9, 3.6, 0.4, "", "ok"),
    ("Carrot, raw", "veg", "vegan", 41, 0.9, 10, 0.2, "", "ok"),
    ("Tomato", "veg", "vegan", 18, 0.9, 3.9, 0.2, "", "ok"),
    ("Onion", "veg", "vegan", 40, 1.1, 9.3, 0.1, "", "ok"),
    ("Cucumber", "veg", "vegan", 15, 0.7, 3.6, 0.1, "", "ok"),
    ("Bell pepper", "veg", "vegan", 31, 1, 6, 0.3, "", "ok"),
    ("Cauliflower, cooked", "veg", "vegan", 23, 1.8, 4.1, 0.5, "", "ok"),
    ("Cabbage, cooked", "veg", "vegan", 25, 1.3, 5.8, 0.1, "", "ok"),
    ("Okra (bhindi), cooked", "veg", "vegan", 33, 1.9, 7.5, 0.2, "", "ok"),
    ("Brinjal (eggplant), cooked", "veg", "vegan", 35, 0.8, 8.7, 0.2, "", "ok"),
    ("Green peas, cooked", "veg", "vegan", 84, 5.4, 15, 0.2, "", "ok"),
    ("Mushrooms, cooked", "veg", "vegan", 28, 2.5, 4.1, 0.4, "", "ok"),
    ("Apple", "fruit", "vegan", 52, 0.3, 14, 0.2, "", "ok"),
    ("Banana", "fruit", "vegan", 89, 1.1, 23, 0.3, "", "ok"),
    ("Orange", "fruit", "vegan", 47, 0.9, 12, 0.1, "", "ok"),
    ("Mango", "fruit", "vegan", 60, 0.8, 15, 0.4, "", "ok"),
    ("Papaya", "fruit", "vegan", 43, 0.5, 11, 0.3, "", "ok"),
    ("Guava", "fruit", "vegan", 68, 2.6, 14, 1, "", "ok"),
    ("Grapes", "fruit", "vegan", 69, 0.7, 18, 0.2, "", "ok"),
    ("Watermelon", "fruit", "vegan", 30, 0.6, 8, 0.2, "", "ok"),
    ("Blueberries", "fruit", "vegan", 57, 0.7, 14, 0.3, "", "ok"),
    ("Almonds", "fat", "vegan", 579, 21, 22, 50, "tree_nut", "ok"),
    ("Walnuts", "fat", "vegan", 654, 15, 14, 65, "tree_nut", "ok"),
    ("Peanuts, roasted", "fat", "vegan", 567, 26, 16, 49, "peanut", "ok"),
    ("Peanut butter", "fat", "vegan", 588, 25, 20, 50, "peanut", "limit"),
    ("Chia seeds", "fat", "vegan", 486, 17, 42, 31, "", "ok"),
    ("Olive oil", "fat", "vegan", 884, 0, 0, 100, "", "limit"),
    ("Refined vegetable oil", "fat", "vegan", 884, 0, 0, 100, "", "limit"),
    ("Roasted chana (snack)", "snack", "vegan", 364, 19, 61, 6, "", "ok"),
    ("Makhana (fox nuts), roasted", "snack", "vegan", 347, 9.7, 77, 0.1, "", "ok"),
    ("Air-popped popcorn", "snack", "vegan", 387, 13, 78, 4.5, "", "ok"),
    ("Rice cakes, plain", "snack", "vegan", 387, 8, 81, 3, "", "ok"),
    ("Potato chips", "snack", "vegan", 536, 7, 53, 35, "", "limit"),
    ("Sweet biscuits", "snack", "veg", 480, 7, 65, 20, "gluten,milk", "limit"),
    ("Milk chocolate", "snack", "veg", 535, 7.7, 59, 30, "milk", "limit"),
    ("Dark chocolate, 70%", "snack", "vegan", 598, 7.8, 46, 43, "", "limit"),
    ("Ice cream", "snack", "veg", 207, 3.5, 24, 11, "milk", "limit"),
    ("Sugar, white", "snack", "vegan", 387, 0, 100, 0, "", "limit"),
    ("Honey", "snack", "vegan", 304, 0.3, 82, 0, "", "limit"),
    ("Samosa, fried", "snack", "veg", 262, 5, 25, 16, "gluten", "limit"),
    ("Pakora, fried", "snack", "vegan", 250, 6, 20, 16, "", "limit"),
    ("French fries", "snack", "vegan", 312, 3.4, 41, 15, "", "limit"),
    ("Pizza, cheese", "dish", "veg", 266, 11, 33, 10, "gluten,milk", "limit"),
    ("Beef burger", "dish", "nonveg", 295, 17, 24, 14, "gluten", "limit"),
    ("Fried chicken", "dish", "nonveg", 260, 19, 8, 16, "gluten", "limit"),
    ("Chicken biryani", "dish", "nonveg", 190, 9, 24, 6.5, "", "ok"),
    ("Chicken curry, home style", "dish", "nonveg", 150, 11, 5, 10, "", "ok"),
    ("Fish curry", "dish", "nonveg", 120, 14, 3, 6, "fish", "ok"),
    ("Paneer butter masala", "dish", "veg", 180, 8, 9, 13, "milk", "limit"),
    ("Chole (chickpea curry)", "dish", "vegan", 140, 6, 17, 5, "", "ok"),
    ("Dal tadka", "dish", "vegan", 110, 6, 15, 3, "", "ok"),
    ("Sambar", "dish", "vegan", 60, 3, 9, 1.5, "", "ok"),
    ("Egg curry", "dish", "nonveg", 130, 9, 4, 9, "egg", "ok"),
    ("Vegetable pulao", "dish", "vegan", 150, 3, 25, 4, "", "ok"),
    ("Curd rice", "dish", "veg", 120, 3, 17, 4, "milk", "ok"),
    ("Water", "drink", "vegan", 0, 0, 0, 0, "", "ok"),
    ("Green tea", "drink", "vegan", 1, 0, 0.2, 0, "", "ok"),
    ("Black coffee", "drink", "vegan", 2, 0.3, 0, 0, "", "ok"),
    ("Milk tea (chai, with sugar)", "drink", "veg", 40, 1.5, 6, 1.2, "milk", "limit"),
    ("Cola, regular", "drink", "vegan", 42, 0, 10.6, 0, "", "limit"),
    ("Packaged fruit juice", "drink", "vegan", 45, 0.7, 10.4, 0.2, "", "limit"),
    ("Whey protein shake (made with water)", "drink", "veg", 60, 12, 4, 1, "milk", "ok"),
]

DIET_OK = {
    "vegan": {"vegan"},
    "vegetarian": {"vegan", "veg"},
    "non-vegetarian": {"vegan", "veg", "nonveg"},
}
DIET_ALIASES = {"vegan": "vegan", "vegetarian": "vegetarian", "veg": "vegetarian",
                "non-vegetarian": "non-vegetarian", "nonveg": "non-vegetarian",
                "non vegetarian": "non-vegetarian", "non-veg": "non-vegetarian"}

ALLERGY_ALIASES = {
    "milk": "milk", "dairy": "milk", "lactose": "milk",
    "egg": "egg", "eggs": "egg",
    "peanut": "peanut", "peanuts": "peanut",
    "nut": "tree_nut", "nuts": "tree_nut", "tree nut": "tree_nut", "tree nuts": "tree_nut",
    "almond": "tree_nut", "almonds": "tree_nut", "walnut": "tree_nut", "walnuts": "tree_nut",
    "gluten": "gluten", "wheat": "gluten",
    "soy": "soy", "soya": "soy", "soybean": "soy",
    "fish": "fish", "shellfish": "shellfish", "prawn": "shellfish", "prawns": "shellfish",
    "shrimp": "shellfish",
}

ACTIVITY = {"none": 1.2, "yoga": 1.4, "strength": 1.55, "cardio": 1.6, "hiit": 1.7, "sports": 1.65}
GOAL_ALIAS = {"weight_loss": "lose_weight", "lean_body": "lose_weight",
              "muscle_gain": "gain_weight", "maintenance": "maintain"}
GOAL_ADJ = {"lose_weight": -400, "gain_weight": 250, "maintain": 0}   # kcal per day
PROTEIN_PER_KG = {"lose_weight": 1.8, "gain_weight": 1.8, "maintain": 1.6}
GOAL_LABEL = {"lose_weight": "Lose weight", "gain_weight": "Gain weight", "maintain": "Maintain weight"}
GOAL_TIPS = {
    "lose_weight": ["Fill half your plate with vegetables and build each meal around protein.",
                    "Choose whole grains, and keep fried, sugary and creamy foods to a few times a week.",
                    "Drink water in place of sugary drinks."],
    "gain_weight": ["Eat a calorie-dense snack between meals, such as nuts or peanut butter.",
                    "Choose whole grains, paneer, eggs or lean meat, and add ghee or olive oil to meals.",
                    "Eat regularly, every 3 to 4 hours, and don't skip meals."],
    "maintain": ["Keep meals balanced and eat at similar times each day.",
                 "Weigh yourself weekly to check your weight is steady."],
}
GAIN_EXTRA = ["Almonds", "Peanut butter", "Walnuts", "Peanuts, roasted"]


def goal_key(goal):
    """Map old goal names to the current three, and anything unknown to maintain."""
    g = (goal or "maintain").strip().lower()
    g = GOAL_ALIAS.get(g, g)
    return g if g in GOAL_ADJ else "maintain"
KCAL_FLOOR = {"male": 1500, "female": 1200}
MEAL_SHARE = {"breakfast": 0.25, "lunch": 0.35, "snack": 0.10, "dinner": 0.30}

# Protein choices per meal, tried in order. Each diet only gets the entries it is allowed to eat,
# so a non-vegetarian plan mixes meat and fish with vegetarian meals, and a vegetarian or
# vegan plan never receives meat, fish or eggs.
MEAL_PROTEIN = {
    "breakfast": ["Egg, whole, boiled", "Greek yogurt, plain", "Curd (plain, whole milk)",
                  "Paneer", "Tofu, firm", "Egg white, boiled", "Skimmed milk", "Milk, full fat"],
    "lunch": ["Chicken breast, cooked", "Salmon, cooked", "Dal (toor), cooked",
              "Tuna, canned in water", "Paneer", "White fish (cod), cooked", "Tofu, firm",
              "Chickpeas (chana), cooked", "Lean beef, cooked", "Prawns, cooked"],
    "dinner": ["Dal (toor), cooked", "Chicken thigh, cooked", "Paneer", "Chickpeas (chana), cooked",
               "Salmon, cooked", "Tofu, firm", "Egg, whole, boiled", "White fish (cod), cooked"],
}
BREAKFAST_CARB = ["Oats, cooked in water", "Poha, cooked", "Idli", "Plain dosa", "Upma",
                  "Whole wheat bread"]


def _food(name):
    lower = name.strip().lower()
    for f in FOODS:
        if f[0].lower() == lower:
            return f
    return None


def _row(f):
    return {"name": f[0], "role": f[1], "diet": f[2], "kcal": f[3], "protein": f[4],
            "carbs": f[5], "fat": f[6], "allergens": set(x for x in f[7].split(",") if x),
            "flag": f[8]}


def diet_key(diet):
    return DIET_ALIASES.get((diet or "").strip().lower(), "non-vegetarian")


def parse_allergies(text):
    """'milk, nuts, Gluten' -> (set of canonical allergen tags, list of unrecognised words)."""
    if isinstance(text, (list, tuple)):
        text = ",".join(text)
    tags, unknown = set(), []
    for part in (text or "").replace(";", ",").split(","):
        word = part.strip().lower()
        if not word:
            continue
        if word in ALLERGY_ALIASES:
            tags.add(ALLERGY_ALIASES[word])
        else:
            unknown.append(part.strip())
    return tags, unknown


def targets(profile):
    """profile: weight_kg, height_cm, age, sex ('male' or 'female'), workout, goal."""
    w, h, age = float(profile["weight_kg"]), float(profile["height_cm"]), int(profile["age"])
    sex = profile.get("sex", "male")
    bmr = 10 * w + 6.25 * h - 5 * age + (5 if sex == "male" else -161)
    tdee = bmr * ACTIVITY.get(profile.get("workout", "none"), 1.2)
    goal = goal_key(profile.get("goal", "maintain"))
    adjust = int(profile.get("calorie_adjust", 0) or 0)
    floor = KCAL_FLOOR.get(sex, 1200)
    raw = round(tdee + GOAL_ADJ[goal] + adjust)
    kcal = max(raw, floor)
    protein = round(PROTEIN_PER_KG[goal] * w)
    fat = round(0.25 * kcal / 9)
    carbs = max(round((kcal - protein * 4 - fat * 9) / 4), 0)
    return {"kcal": kcal, "protein": protein, "carbs": carbs, "fat": fat,
            "bmr": round(bmr), "tdee": round(tdee), "floor_applied": raw < floor}


def nutrients_for(name, grams):
    f = _food(name)
    if not f:
        return None
    k = grams / 100.0
    return {"kcal": round(f[3] * k, 1), "protein": round(f[4] * k, 1),
            "carbs": round(f[5] * k, 1), "fat": round(f[6] * k, 1)}


def _allowed(row, profile):
    return row["diet"] in DIET_OK[diet_key(profile.get("diet"))] and not (row["allergens"] & profile["_allergy_tags"])


def alternatives(name, profile, n=3):
    """Foods of the same role, fitting the user's diet and allergies, marked ok, with similar calories."""
    f = _food(name)
    if not f:
        return []
    base = _row(f)
    pool = [_row(x) for x in FOODS if x[0] != f[0] and x[1] == f[1] and x[8] == "ok"]
    pool = [r for r in pool if _allowed(r, profile)]
    pool.sort(key=lambda r: (abs(r["kcal"] - base["kcal"]), r["name"]))
    return [r["name"] for r in pool[:n]]


def check_food(name, profile):
    """Status for one food against the user's profile: ok, limit, not_in_diet, blocked or unknown."""
    profile = dict(profile, _allergy_tags=parse_allergies(profile.get("allergies", ""))[0])
    f = _food(name)
    if not f:
        return {"status": "unknown", "message": f"'{name}' is not in the food list yet. Pick the closest item from the search results.",
                "alternatives": []}
    row = _row(f)
    hit = row["allergens"] & profile["_allergy_tags"]
    if hit:
        return {"status": "blocked",
                "message": f"{row['name']} contains {', '.join(sorted(hit))}, which you listed as an allergy. Do not eat it.",
                "alternatives": alternatives(name, profile)}
    if row["diet"] not in DIET_OK[diet_key(profile.get("diet"))]:
        return {"status": "not_in_diet",
                "message": f"{row['name']} does not fit your {diet_key(profile.get('diet'))} diet. Try instead:",
                "alternatives": alternatives(name, profile)}
    if row["flag"] == "limit":
        return {"status": "limit",
                "message": f"{row['name']} is high in calories or sugar or fat. Eat it rarely. A better choice is:",
                "alternatives": alternatives(name, profile)}
    return {"status": "ok", "message": f"{row['name']} fits your plan.", "alternatives": []}


def search_foods(query, profile=None, limit=12):
    q = (query or "").strip().lower()
    if not q:
        return []
    profile = dict(profile or {}, _allergy_tags=parse_allergies((profile or {}).get("allergies", ""))[0])
    hits = [f for f in FOODS if q in f[0].lower()]
    hits.sort(key=lambda f: (not f[0].lower().startswith(q), f[0]))
    out = []
    for f in hits[:limit]:
        r = _row(f)
        out.append({"name": r["name"], "role": r["role"], "kcal_per_100g": r["kcal"],
                    "protein_per_100g": r["protein"], "carbs_per_100g": r["carbs"],
                    "fat_per_100g": r["fat"], "diet": r["diet"], "flag": r["flag"],
                    "fits_diet": r["diet"] in DIET_OK[diet_key((profile or {}).get("diet"))],
                    "has_allergen": bool(r["allergens"] & profile["_allergy_tags"])})
    return out


def totals(entries):
    return {k: round(sum(e[k] for e in entries), 1) for k in ("kcal", "protein", "carbs", "fat")}


def _pick(pool, index):
    return pool[index % len(pool)] if pool else None


def day_plan(profile, day_index=0):
    """Four meals that fit the diet, allergies, and the calorie and protein targets for the day."""
    profile = dict(profile, _allergy_tags=parse_allergies(profile.get("allergies", ""))[0])
    t = targets(profile)
    dk = diet_key(profile.get("diet"))

    def pool(role):
        rows = [_row(f) for f in FOODS if f[1] == role and f[8] == "ok"]
        return sorted([r["name"] for r in rows if _allowed(r, profile)])

    protein_pool, carb_pool = pool("protein"), pool("carb")
    veg_pool, fruit_pool, snack_pool = pool("veg"), pool("fruit"), pool("snack")
    bf_carb = [n for n in BREAKFAST_CARB if _food(n) and _allowed(_row(_food(n)), profile)] or carb_pool
    meals = []
    for i, (meal, share) in enumerate(MEAL_SHARE.items()):
        kcal = t["kcal"] * share
        items = []
        choices = [n for n in MEAL_PROTEIN.get(meal, []) if _food(n) and _allowed(_row(_food(n)), profile)]
        meat = [n for n in choices if _food(n)[2] == "nonveg"]
        plant = [n for n in choices if _food(n)[2] != "nonveg"]
        if dk == "non-vegetarian" and meal == "lunch" and meat:
            choices = meat          # lunch: meat or fish
        elif dk == "non-vegetarian" and meal == "dinner" and plant:
            choices = plant         # dinner: a vegetarian protein, so every day mixes both
        p_name = _pick(choices or protein_pool, day_index + i)
        if p_name:
            pf = _food(p_name)
            grams = min(max(round(t["protein"] * share / pf[4] * 100), 60), 250)
            items.append({"food": p_name, "grams": grams})
            kcal_left = kcal - pf[3] * grams / 100
        else:
            kcal_left = kcal
        c_name = _pick(bf_carb, day_index) if meal == "breakfast" else _pick(carb_pool, day_index + i)
        if c_name and meal != "snack":
            cf = _food(c_name)
            grams = min(max(round(kcal_left * 0.8 / cf[3] * 100), 40), 300)
            items.append({"food": c_name, "grams": grams})
        if meal in ("lunch", "dinner"):
            v_name = _pick(veg_pool, day_index + i)
            if v_name:
                items.append({"food": v_name, "grams": 150})
        if meal == "breakfast":
            f_name = _pick(fruit_pool, day_index)
            if f_name:
                items.append({"food": f_name, "grams": 120})
        if meal == "snack":
            s_name = _pick(snack_pool, day_index) or _pick(fruit_pool, day_index)
            if s_name:
                items.append({"food": s_name, "grams": 60 if _food(s_name)[1] == "snack" else 120})
        entries = []
        for it in items:
            n = nutrients_for(it["food"], it["grams"])
            entries.append({"food": it["food"], "grams": it["grams"], **n})
        meals.append({"meal": meal, "items": entries, "totals": totals(entries)})
    goal = goal_key(profile.get("goal", "maintain"))
    if goal == "gain_weight":
        extra = next((n for n in GAIN_EXTRA if _food(n) and _allowed(_row(_food(n)), profile)), None)
        if extra:
            snack = next(m for m in meals if m["meal"] == "snack")
            snack["items"].append({"food": extra, "grams": 30, **nutrients_for(extra, 30)})
            snack["totals"] = totals(snack["items"])
    all_entries = [e for m in meals for e in m["items"]]
    return {"targets": t, "diet": dk, "goal": goal, "goal_tips": GOAL_TIPS[goal],
            "meals": meals, "totals": totals(all_entries)}
