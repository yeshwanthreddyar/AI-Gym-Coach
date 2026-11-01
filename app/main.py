"""FastAPI backend: accounts and sessions, profiles, check-ins, sets, readiness, plan, progress, pages."""
import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app import analytics as an
from app.auth import (SESSION_DAYS, hash_password, hash_token, new_token, user_code,
                      validate_registration, verify_password)
from app.exercises import EXERCISES as EXERCISE_CATALOG
from app.generator import generate_session

from app.coaching import coach, top_issues
from app.tracking import summarize, streak

from app.suggestions import suggest
from app.history import build_history
from app.nutrition import (ACTIVITY, FOODS, GOAL_LABEL, GOAL_TIPS, check_food, day_plan, diet_key,
                           goal_key, nutrients_for, parse_allergies, search_foods, targets, totals)
from app.goals import remaining_kg, review, status_text, validate_target, weekly_change
from app.tracking import streak

DB = os.getenv("GYM_DB", "gym.db")
REP_LOW, REP_HIGH = 5, 8  # rep range used for progressive overload
STATIC = Path(__file__).parent / "static"
SESSION_COOKIE = "gym_session"

app = FastAPI(title="AI Gym Coach")
app.mount("/static", StaticFiles(directory=STATIC), name="static")


@contextmanager
def conn():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    try:
        yield c
        c.commit()
    finally:
        c.close()


def _migrate(c):
    """Add account columns to databases created by earlier versions."""
    cols = {r["name"] for r in c.execute("PRAGMA table_info(users)")}
    for col in ("username", "email", "password_hash", "created_at"):
        if col not in cols:
            c.execute(f"ALTER TABLE users ADD COLUMN {col} TEXT")
    c.execute("CREATE UNIQUE INDEX IF NOT EXISTS ux_users_username ON users(username COLLATE NOCASE)")
    c.execute("CREATE UNIQUE INDEX IF NOT EXISTS ux_users_email ON users(email)")
    c.execute("CREATE TABLE IF NOT EXISTS sessions(token_hash TEXT PRIMARY KEY, user_id INT, created_at TEXT)")
    scols = {r["name"] for r in c.execute("PRAGMA table_info(sets)")}
    for col in ("flags", "source"):
        if col not in scols:
            c.execute(f"ALTER TABLE sets ADD COLUMN {col} TEXT")
    c.execute("CREATE TABLE IF NOT EXISTS attendance(user_id INT, day TEXT, PRIMARY KEY(user_id, day))")
    c.execute("CREATE TABLE IF NOT EXISTS nutrition_profiles(user_id INTEGER PRIMARY KEY, weight_kg REAL, "
              "height_cm REAL, age INT, sex TEXT, workout TEXT, diet TEXT, allergies TEXT, goal TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS food_log(id INTEGER PRIMARY KEY, user_id INT, day TEXT, food TEXT, "
              "grams REAL, kcal REAL, protein REAL, carbs REAL, fat REAL, flag TEXT)")
    npcols = {r["name"] for r in c.execute("PRAGMA table_info(nutrition_profiles)")}
    for col, typ in (("target_weight", "REAL"), ("calorie_adjust", "INT DEFAULT 0"), ("last_review", "TEXT")):
        if col not in npcols:
            c.execute(f"ALTER TABLE nutrition_profiles ADD COLUMN {col} {typ}")
    c.execute("CREATE TABLE IF NOT EXISTS weight_log(user_id INT, day TEXT, weight_kg REAL, PRIMARY KEY(user_id, day))")


with conn() as c:
    c.executescript("""
    CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY, name TEXT, goal TEXT,
        equipment TEXT, injuries TEXT, leverage_index REAL);
    CREATE TABLE IF NOT EXISTS checkins(user_id INT, day TEXT, sleep_hours REAL,
        soreness TEXT, PRIMARY KEY(user_id, day));
    CREATE TABLE IF NOT EXISTS sets(id INTEGER PRIMARY KEY, user_id INT, day TEXT,
        exercise TEXT, weight REAL, reps INT, form_score INT);
    """)
    _migrate(c)


class UserIn(BaseModel):
    """Legacy profile creation (no password). Kept so older scripts and tests still work."""
    name: str = Field(min_length=1)
    goal: str = "strength"
    equipment: list[str] = []
    injuries: list[str] = []
    leverage_index: float | None = None


class RegisterIn(BaseModel):
    username: str
    email: str
    password: str
    goal: str = "strength"
    equipment: list[str] = []
    injuries: list[str] = []


class LoginIn(BaseModel):
    identifier: str  # username or email
    password: str


class CheckIn(BaseModel):
    user_id: int
    day: date
    sleep_hours: float = Field(ge=0, le=24)
    soreness: list[int] = Field(min_length=1)  # 1-5 per muscle group

    model_config = {"validate_assignment": True}


class SetIn(BaseModel):
    user_id: int
    day: date
    exercise: str = Field(min_length=1)
    weight: float = Field(ge=0)
    reps: int = Field(ge=1)
    form_score: int = Field(default=100, ge=0, le=100)


def _require_user(c, uid):
    if not c.execute("SELECT 1 FROM users WHERE id=?", (uid,)).fetchone():
        raise HTTPException(404, "no such user")


# ---------- accounts and sessions ----------

def _now():
    return datetime.now(timezone.utc)


def _current_user(request, c):
    token = request.cookies.get(SESSION_COOKIE)
    if not token:
        return None
    cutoff = (_now() - timedelta(days=SESSION_DAYS)).isoformat()
    return c.execute(
        "SELECT u.* FROM sessions s JOIN users u ON u.id = s.user_id "
        "WHERE s.token_hash=? AND s.created_at>?", (hash_token(token), cutoff)).fetchone()


def _logged_in(request):
    with conn() as c:
        return _current_user(request, c) is not None


def _start_session(c, response, uid):
    token = new_token()
    c.execute("INSERT INTO sessions(token_hash,user_id,created_at) VALUES(?,?,?)",
              (hash_token(token), uid, _now().isoformat()))
    response.set_cookie(SESSION_COOKIE, token, max_age=SESSION_DAYS * 86400,
                        httponly=True, samesite="lax")


def _user_summary(c, u):
    sets_n = c.execute("SELECT COUNT(*) FROM sets WHERE user_id=?", (u["id"],)).fetchone()[0]
    checkins_n = c.execute("SELECT COUNT(*) FROM checkins WHERE user_id=?", (u["id"],)).fetchone()[0]
    return {
        "id": u["id"],
        "user_code": user_code(u["id"]),
        "username": u["username"] or u["name"],
        "email": u["email"],
        "goal": u["goal"],
        "equipment": json.loads(u["equipment"] or "[]"),
        "injuries": json.loads(u["injuries"] or "[]"),
        "joined": (u["created_at"] or "")[:10] or None,
        "sets_logged": sets_n,
        "checkins": checkins_n,
    }


@app.post("/auth/register")
def register(body: RegisterIn, response: Response):
    username = body.username.strip()
    email = body.email.strip().lower()
    errors = validate_registration(username, email, body.password)
    if errors:
        raise HTTPException(400, " ".join(errors))
    with conn() as c:
        if c.execute("SELECT 1 FROM users WHERE username=? COLLATE NOCASE", (username,)).fetchone():
            raise HTTPException(409, "That username is already taken. Try another.")
        if c.execute("SELECT 1 FROM users WHERE email=?", (email,)).fetchone():
            raise HTTPException(409, "An account with this email already exists. Log in instead.")
        try:
            cur = c.execute(
                "INSERT INTO users(name,goal,equipment,injuries,username,email,password_hash,created_at) "
                "VALUES(?,?,?,?,?,?,?,?)",
                (username, body.goal, json.dumps(body.equipment), json.dumps(body.injuries),
                 username, email, hash_password(body.password), _now().isoformat()))
        except sqlite3.IntegrityError:
            raise HTTPException(409, "That username or email is already in use.")
        uid = cur.lastrowid
        _start_session(c, response, uid)
        summary = _user_summary(c, c.execute("SELECT * FROM users WHERE id=?", (uid,)).fetchone())
    return {"message": f"Account created. Your UserID is {summary['user_code']}.", **summary}


@app.post("/auth/login")
def login(body: LoginIn, response: Response):
    ident = body.identifier.strip()
    with conn() as c:
        u = c.execute("SELECT * FROM users WHERE (username=? COLLATE NOCASE) OR email=?",
                      (ident, ident.lower())).fetchone()
        if not u:
            raise HTTPException(404, "No account found with that username or email.")
        if not u["password_hash"]:
            raise HTTPException(401, "This profile has no password. Please register a new account.")
        if not verify_password(body.password, u["password_hash"]):
            raise HTTPException(401, "Incorrect password. Try again.")
        _start_session(c, response, u["id"])
        summary = _user_summary(c, u)
    return {"message": "Logged in.", **summary}


@app.post("/auth/logout")
def logout(request: Request, response: Response):
    token = request.cookies.get(SESSION_COOKIE)
    if token:
        with conn() as c:
            c.execute("DELETE FROM sessions WHERE token_hash=?", (hash_token(token),))
    response.delete_cookie(SESSION_COOKIE)
    return {"message": "Logged out."}


@app.get("/auth/me")
def me(request: Request):
    with conn() as c:
        u = _current_user(request, c)
        if not u:
            raise HTTPException(401, "Not logged in")
        return _user_summary(c, u)


# ---------- pages ----------

@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/home")


@app.get("/home", include_in_schema=False)
def home_page():
    return FileResponse(STATIC / "home.html")


@app.get("/workouts", include_in_schema=False)
def workouts_page():
    return FileResponse(STATIC / "workouts.html")


@app.get("/workout", include_in_schema=False)
def workout_page():
    return FileResponse(STATIC / "workout.html")


@app.get("/login", include_in_schema=False)
def login_page(request: Request):
    if _logged_in(request):
        return RedirectResponse("/profile", status_code=303)
    return FileResponse(STATIC / "login.html")


@app.get("/register", include_in_schema=False)
def register_page(request: Request):
    if _logged_in(request):
        return RedirectResponse("/onboarding", status_code=303)
    return FileResponse(STATIC / "register.html")


@app.get("/profile", include_in_schema=False)
def profile_page(request: Request):
    if not _logged_in(request):
        return RedirectResponse("/login?next=/profile", status_code=303)
    return FileResponse(STATIC / "profile.html")


@app.get("/tracker", include_in_schema=False)
def tracker_page(request: Request):
    if not _logged_in(request):
        return RedirectResponse("/login?next=/tracker", status_code=303)
    return FileResponse(STATIC / "tracker.html")


@app.get("/diet", include_in_schema=False)
def diet_page(request: Request):
    if not _logged_in(request):
        return RedirectResponse("/login?next=/diet", status_code=303)
    return FileResponse(STATIC / "diet.html")


@app.get("/onboarding", include_in_schema=False)
def onboarding_page(request: Request):
    if not _logged_in(request):
        return RedirectResponse("/login?next=/onboarding", status_code=303)
    return FileResponse(STATIC / "onboarding.html")


@app.get("/start", include_in_schema=False)
def start_journey(request: Request):
    """'Start Journey' target: onboarding for members, registration for guests."""
    target = "/onboarding" if _logged_in(request) else "/register"
    return RedirectResponse(target, status_code=303)


@app.get("/gym", include_in_schema=False)
def gym_page():
    return FileResponse(STATIC / "gym.html")


@app.get("/live", include_in_schema=False)
def live_page():
    return FileResponse(STATIC / "live.html")


@app.get("/exercises")
def exercises():
    return EXERCISE_CATALOG


# ---------- data API ----------

@app.post("/users")
def create_user(u: UserIn):
    with conn() as c:
        cur = c.execute(
            "INSERT INTO users(name,goal,equipment,injuries,leverage_index) VALUES(?,?,?,?,?)",
            (u.name, u.goal, json.dumps(u.equipment), json.dumps(u.injuries), u.leverage_index))
        return {"id": cur.lastrowid}


@app.post("/checkins")
def checkin(ci: CheckIn):
    with conn() as c:
        _require_user(c, ci.user_id)
        c.execute("INSERT OR REPLACE INTO checkins(user_id,day,sleep_hours,soreness) VALUES(?,?,?,?)",
                  (ci.user_id, ci.day.isoformat(), ci.sleep_hours, json.dumps(ci.soreness)))
    return {"ok": True}


@app.post("/sets")
def log_set(s: SetIn):
    with conn() as c:
        _require_user(c, s.user_id)
        cur = c.execute(
            "INSERT INTO sets(user_id,day,exercise,weight,reps,form_score) VALUES(?,?,?,?,?,?)",
            (s.user_id, s.day.isoformat(), s.exercise, s.weight, s.reps, s.form_score))
        return {"id": cur.lastrowid, "e1rm": round(an.epley_1rm(s.weight, s.reps), 1)}


def _readiness(c, uid, day):
    ci = c.execute("SELECT sleep_hours, soreness FROM checkins WHERE user_id=? AND day=?",
                   (uid, day.isoformat())).fetchone()
    if not ci:
        raise HTTPException(409, "log a check-in for this day first")
    rows = c.execute("SELECT day, weight, reps FROM sets WHERE user_id=? AND day>=? AND day<=?",
                     (uid, (day - timedelta(days=28)).isoformat(), day.isoformat())).fetchall()
    vol = lambda rs: sum(r["weight"] * r["reps"] for r in rs)
    acute = vol([r for r in rows if date.fromisoformat(r["day"]) > day - timedelta(days=7)])
    chronic = vol(rows) / 4  # weekly average over 4 weeks
    ratio = acute / chronic if chronic else 1.0
    return an.readiness(ci["sleep_hours"], json.loads(ci["soreness"]), ratio)


@app.get("/users/{uid}/readiness")
def readiness(uid: int, day: date | None = None):
    day = day or date.today()
    with conn() as c:
        _require_user(c, uid)
        score, rec = _readiness(c, uid, day)
    return {"score": score, "recommendation": rec}


@app.get("/users/{uid}/plan")
def plan(uid: int, day: date | None = None):
    day = day or date.today()
    with conn() as c:
        u = c.execute("SELECT * FROM users WHERE id=?", (uid,)).fetchone()
        if not u:
            raise HTTPException(404, "no such user")
        score, rec = _readiness(c, uid, day)
        done = {r["exercise"]: date.fromisoformat(r["d"]) for r in c.execute(
            "SELECT exercise, MAX(day) AS d FROM sets WHERE user_id=? GROUP BY exercise", (uid,))}
    session = generate_session(day.toordinal(), json.loads(u["equipment"]),
                               json.loads(u["injuries"]), done, day, rec)
    return {"readiness": score, "recommendation": rec, "session": session}


@app.get("/users/{uid}/progress/{exercise}")
def progress(uid: int, exercise: str):
    with conn() as c:
        _require_user(c, uid)
        rows = c.execute(
            "SELECT day, weight, reps, form_score FROM sets "
            "WHERE user_id=? AND exercise=? ORDER BY day, id", (uid, exercise)).fetchall()
    weeks = {}
    for r in rows:
        k = date.fromisoformat(r["day"]).isocalendar()[:2]
        weeks[k] = max(weeks.get(k, 0.0), an.epley_1rm(r["weight"], r["reps"]))
    series = [round(weeks[k], 1) for k in sorted(weeks)]
    target = None
    if rows:
        last = rows[-1]
        w, reps, note = an.progressive_overload(
            last["weight"], last["reps"], REP_LOW, REP_HIGH, last["form_score"])
        target = {"weight": w, "reps": reps, "note": note}
    return {"weekly_e1rm": series, "plateau": an.plateau(series), "next_target": target}

class LogSetIn(BaseModel):
    day: date
    exercise: str = Field(min_length=1)
    weight: float = Field(ge=0)
    reps: int = Field(ge=1)
    form_score: int = Field(default=100, ge=0, le=100)
    flags: list[str] = []
    source: str = "camera"  # "camera" or "manual"


@app.post("/api/sets")
def api_log_set(body: LogSetIn, request: Request):
    with conn() as c:
        u = _current_user(request, c)
        if not u:
            raise HTTPException(401, "Log in to save workouts.")
        c.execute("INSERT OR IGNORE INTO attendance(user_id, day) VALUES(?,?)",
                  (u["id"], body.day.isoformat()))
        cur = c.execute(
            "INSERT INTO sets(user_id,day,exercise,weight,reps,form_score,flags,source) "
            "VALUES(?,?,?,?,?,?,?,?)",
            (u["id"], body.day.isoformat(), body.exercise, body.weight, body.reps,
             body.form_score, json.dumps(body.flags), body.source))
    return {"id": cur.lastrowid, "e1rm": round(an.epley_1rm(body.weight, body.reps), 1),
            "coaching": coach(body.flags, body.exercise)}


@app.get("/api/me/progress")
def api_progress(request: Request, period: str = "week", days: int = 180):
    if period not in ("day", "week", "month"):
        raise HTTPException(400, "period must be day, week or month")
    with conn() as c:
        u = _current_user(request, c)
        if not u:
            raise HTTPException(401, "Log in first.")
        since = (date.today() - timedelta(days=days)).isoformat()
        rows = [dict(r) for r in c.execute(
            "SELECT day, exercise, weight, reps, form_score FROM sets "
            "WHERE user_id=? AND day>=?", (u["id"], since))]
        attended = [date.fromisoformat(r["day"]) for r in
                    c.execute("SELECT day FROM attendance WHERE user_id=?", (u["id"],))]
    return {"periods": summarize(rows, period), "streak": streak(attended, date.today()),
            "days_attended": len(attended)}


@app.get("/api/me/attendance")
def api_attendance(request: Request):
    with conn() as c:
        u = _current_user(request, c)
        if not u:
            raise HTTPException(401, "Log in first.")
        days = [r["day"] for r in c.execute(
            "SELECT day FROM attendance WHERE user_id=? ORDER BY day", (u["id"],))]
    return {"days": days}

@app.post("/api/checkin")
def api_checkin(request: Request):
    with conn() as c:
        u = _current_user(request, c)
        if not u:
            raise HTTPException(401, "Log in to check in.")
        today = date.today().isoformat()
        already = c.execute("SELECT 1 FROM attendance WHERE user_id=? AND day=?",
                            (u["id"], today)).fetchone() is not None
        c.execute("INSERT OR IGNORE INTO attendance(user_id, day) VALUES(?,?)", (u["id"], today))
        days = [date.fromisoformat(r["day"]) for r in
                c.execute("SELECT day FROM attendance WHERE user_id=?", (u["id"],))]
    return {"checked_in": True, "already": already,
            "streak": streak(days, date.today()), "days_attended": len(days)}


@app.get("/api/me/suggestions")
def api_suggestions(request: Request):
    with conn() as c:
        u = _current_user(request, c)
        if not u:
            raise HTTPException(401, "Log in first.")
        since = (date.today() - timedelta(days=30)).isoformat()
        rows = [dict(r) for r in c.execute(
            "SELECT day, exercise, reps FROM sets WHERE user_id=? AND day>=?", (u["id"], since))]
        goal = u["goal"] or "general"
    return {"suggestions": suggest(rows, date.today(), goal)}


@app.get("/api/me/summary")
def api_summary(request: Request):
    today = date.today()
    with conn() as c:
        u = _current_user(request, c)
        if not u:
            raise HTTPException(401, "Log in first.")
        attended = [date.fromisoformat(r["day"]) for r in
                    c.execute("SELECT day FROM attendance WHERE user_id=?", (u["id"],))]
        since = (today - timedelta(days=30)).isoformat()
        rows = [dict(r) for r in c.execute(
            "SELECT day, exercise, reps FROM sets WHERE user_id=? AND day>=?", (u["id"], since))]
        goal = u["goal"] or "general"
    return {
        "streak": streak(attended, today),
        "checked_in_today": today in attended,
        "days_attended": len(attended),
        "suggestions": suggest(rows, today, goal),
    }


@app.get("/api/me/history")
def api_history(request: Request, days: int = 30):
    if days < 1 or days > 366:
        raise HTTPException(400, "days must be between 1 and 366")
    today = date.today()
    start = (today - timedelta(days=days - 1)).isoformat()
    with conn() as c:
        u = _current_user(request, c)
        if not u:
            raise HTTPException(401, "Log in first.")
        rows = [dict(r) for r in c.execute(
            "SELECT day, exercise, weight, reps, form_score FROM sets "
            "WHERE user_id=? AND day>=? AND day<=? ORDER BY day, id",
            (u["id"], start, today.isoformat()))]
    return {"from": start, "to": today.isoformat(), **build_history(rows)}


# ---------- nutrition and weight goals ----------

class NutritionProfileIn(BaseModel):
    weight: float = Field(gt=0, le=500)
    unit: str = "kg"            # "kg" or "lb"
    height_cm: float = Field(gt=50, lt=260)
    age: int = Field(ge=13, le=100)
    sex: str = "male"           # "male" or "female"
    workout: str = "none"       # none, yoga, strength, cardio, hiit, sports
    diet: str = "non-vegetarian"
    allergies: str = ""         # comma separated, e.g. "milk, peanuts"
    goal: str = "maintain"      # lose_weight, gain_weight, maintain
    target_weight: float | None = Field(default=None, gt=0, le=500)


class FoodLogIn(BaseModel):
    day: date
    food: str = Field(min_length=1, max_length=120)
    grams: float = Field(gt=0, le=2000)


class WeightIn(BaseModel):
    day: date
    weight: float = Field(gt=0, le=500)
    unit: str = "kg"


def _to_kg(value, unit):
    if unit not in ("kg", "lb"):
        raise HTTPException(400, "unit must be kg or lb")
    return round(value / 2.20462, 1) if unit == "lb" else round(value, 1)


def _profile_dict(row):
    return {"weight_kg": row["weight_kg"], "height_cm": row["height_cm"], "age": row["age"],
            "sex": row["sex"], "workout": row["workout"], "diet": row["diet"],
            "allergies": row["allergies"] or "", "goal": goal_key(row["goal"]),
            "target_weight": row["target_weight"], "calorie_adjust": row["calorie_adjust"] or 0,
            "last_review": row["last_review"]}


def _nutrition_row(c, request):
    u = _current_user(request, c)
    if not u:
        raise HTTPException(401, "Log in first.")
    row = c.execute("SELECT * FROM nutrition_profiles WHERE user_id=?", (u["id"],)).fetchone()
    if not row:
        raise HTTPException(409, "Set up your nutrition profile first.")
    return u, row


def _current_kg(c, row):
    latest = c.execute("SELECT weight_kg FROM weight_log WHERE user_id=? ORDER BY day DESC LIMIT 1",
                       (row["user_id"],)).fetchone()
    return latest["weight_kg"] if latest else row["weight_kg"]


def _current_profile(c, row):
    p = _profile_dict(row)
    p["weight_kg"] = _current_kg(c, row)
    return p


def _weight_logs(c, uid):
    return [(date.fromisoformat(r["day"]), r["weight_kg"]) for r in
            c.execute("SELECT day, weight_kg FROM weight_log WHERE user_id=? ORDER BY day", (uid,))]


def _weight_summary(c, row, today):
    goal = goal_key(row["goal"])
    current = _current_kg(c, row)
    rem = remaining_kg(current, row["target_weight"], goal)
    logs = _weight_logs(c, row["user_id"])
    return {"goal": goal, "goal_label": GOAL_LABEL[goal], "start_kg": row["weight_kg"],
            "current_kg": current, "target_kg": row["target_weight"], "remaining_kg": rem,
            "change_last_7_days_kg": weekly_change(logs, today),
            "calorie_adjust": row["calorie_adjust"] or 0,
            "status": status_text(goal, weekly_change(logs, today), rem),
            "history": [{"day": d.isoformat(), "kg": k} for d, k in logs[-30:]]}


def _review_if_due(c, row, today):
    """Once a week, compare progress with the goal and adjust calories if needed."""
    goal = goal_key(row["goal"])
    last = row["last_review"]
    if last and (today - date.fromisoformat(last)).days < 7:
        return f"Your next diet review is in {7 - (today - date.fromisoformat(last)).days} day(s)."
    change = weekly_change(_weight_logs(c, row["user_id"]), today)
    rem = remaining_kg(_current_kg(c, row), row["target_weight"], goal)
    adjust, message = review(row["calorie_adjust"] or 0, goal, change, rem)
    if change is not None:
        c.execute("UPDATE nutrition_profiles SET calorie_adjust=?, last_review=? WHERE user_id=?",
                  (adjust, today.isoformat(), row["user_id"]))
    return message


def _day_entries(c, uid, day):
    return [dict(r) for r in c.execute(
        "SELECT id, food, grams, kcal, protein, carbs, fat, flag FROM food_log "
        "WHERE user_id=? AND day=? ORDER BY id", (uid, day))]


def _day_summary(entries, t):
    tot = totals(entries)
    return {"entries": entries, "totals": tot, "target_kcal": t["kcal"],
            "remaining_kcal": round(t["kcal"] - tot["kcal"], 1), "protein_target": t["protein"]}


@app.post("/api/nutrition/profile")
def save_nutrition_profile(body: NutritionProfileIn, request: Request):
    if body.sex not in ("male", "female"):
        raise HTTPException(400, "sex must be male or female")
    if body.workout not in ACTIVITY:
        raise HTTPException(400, "workout must be one of: " + ", ".join(ACTIVITY))
    goal = goal_key(body.goal)
    kg = _to_kg(body.weight, body.unit)
    target = None
    if goal != "maintain" and body.target_weight is not None:
        target = _to_kg(body.target_weight, body.unit)
    errors = validate_target(kg, target, goal)
    if errors:
        raise HTTPException(400, errors[0])
    diet = diet_key(body.diet)
    today = date.today().isoformat()
    with conn() as c:
        u = _current_user(request, c)
        if not u:
            raise HTTPException(401, "Log in first.")
        prev = c.execute("SELECT * FROM nutrition_profiles WHERE user_id=?", (u["id"],)).fetchone()
        same_goal = prev is not None and goal_key(prev["goal"]) == goal
        adjust = (prev["calorie_adjust"] or 0) if same_goal else 0
        last_review = prev["last_review"] if same_goal else None
        c.execute("INSERT OR REPLACE INTO nutrition_profiles(user_id,weight_kg,height_cm,age,sex,workout,diet,"
                  "allergies,goal,target_weight,calorie_adjust,last_review) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                  (u["id"], kg, body.height_cm, body.age, body.sex, body.workout, diet,
                   body.allergies, goal, target, adjust, last_review))
        c.execute("INSERT OR REPLACE INTO weight_log(user_id,day,weight_kg) VALUES(?,?,?)", (u["id"], today, kg))
    profile = {"weight_kg": kg, "height_cm": body.height_cm, "age": body.age, "sex": body.sex,
               "workout": body.workout, "diet": diet, "allergies": body.allergies, "goal": goal,
               "target_weight": target, "calorie_adjust": adjust, "last_review": last_review}
    tags, unknown = parse_allergies(body.allergies)
    return {"saved": True, "profile": profile, "targets": targets(profile), "goal_tips": GOAL_TIPS[goal],
            "allergies_recognised": sorted(tags), "allergies_not_recognised": unknown}


@app.get("/api/nutrition/profile")
def get_nutrition_profile(request: Request):
    with conn() as c:
        u, row = _nutrition_row(c, request)
        p = _current_profile(c, row)
    return {"profile": p, "targets": targets(p), "goal_tips": GOAL_TIPS[p["goal"]]}


@app.post("/api/weight")
def log_weight(body: WeightIn, request: Request):
    kg = _to_kg(body.weight, body.unit)
    today = date.today()
    with conn() as c:
        u, row = _nutrition_row(c, request)
        c.execute("INSERT OR REPLACE INTO weight_log(user_id,day,weight_kg) VALUES(?,?,?)",
                  (u["id"], body.day.isoformat(), kg))
        message = _review_if_due(c, row, today)
        row = c.execute("SELECT * FROM nutrition_profiles WHERE user_id=?", (u["id"],)).fetchone()
        summary = _weight_summary(c, row, today)
    return {"saved": True, "review": message, **summary}


@app.get("/api/weight/summary")
def weight_summary(request: Request):
    today = date.today()
    with conn() as c:
        u, row = _nutrition_row(c, request)
        return _weight_summary(c, row, today)


@app.get("/api/foods/search")
def food_search(request: Request, q: str = ""):
    with conn() as c:
        u = _current_user(request, c)
        row = c.execute("SELECT * FROM nutrition_profiles WHERE user_id=?", (u["id"],)).fetchone() if u else None
    return {"results": search_foods(q, _profile_dict(row) if row else {})}


@app.post("/api/food-log")
def add_food(body: FoodLogIn, request: Request):
    canonical = next((f[0] for f in FOODS if f[0].lower() == body.food.strip().lower()), None)
    if not canonical:
        raise HTTPException(400, f"'{body.food}' is not in the food list. Pick it from the search results.")
    with conn() as c:
        u, row = _nutrition_row(c, request)
        profile = _current_profile(c, row)
        check = check_food(canonical, profile)
        if check["status"] == "blocked":
            raise HTTPException(400, check["message"])
        n = nutrients_for(canonical, body.grams)
        cur = c.execute("INSERT INTO food_log(user_id,day,food,grams,kcal,protein,carbs,fat,flag) "
                        "VALUES(?,?,?,?,?,?,?,?,?)",
                        (u["id"], body.day.isoformat(), canonical, body.grams,
                         n["kcal"], n["protein"], n["carbs"], n["fat"], check["status"]))
        entries = _day_entries(c, u["id"], body.day.isoformat())
        day = _day_summary(entries, targets(profile))
    return {"saved": True, "id": cur.lastrowid, "status": check["status"],
            "warning": "" if check["status"] == "ok" else check["message"],
            "alternatives": check["alternatives"], "day": day}


@app.get("/api/food-log")
def get_food_log(request: Request, day: date | None = None):
    day = day or date.today()
    with conn() as c:
        u, row = _nutrition_row(c, request)
        profile = _current_profile(c, row)
        entries = _day_entries(c, u["id"], day.isoformat())
        summary = _day_summary(entries, targets(profile))
    return {"day": day.isoformat(), **summary}


@app.delete("/api/food-log/{entry_id}")
def delete_food(entry_id: int, request: Request):
    with conn() as c:
        u = _current_user(request, c)
        if not u:
            raise HTTPException(401, "Log in first.")
        cur = c.execute("DELETE FROM food_log WHERE id=? AND user_id=?", (entry_id, u["id"]))
        if cur.rowcount == 0:
            raise HTTPException(404, "Entry not found.")
    return {"deleted": True}


@app.get("/api/nutrition/plan")
def nutrition_plan(request: Request, day_index: int = 0):
    with conn() as c:
        u, row = _nutrition_row(c, request)
        plan = day_plan(_current_profile(c, row), day_index)
    return plan
