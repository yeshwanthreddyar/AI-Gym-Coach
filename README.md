# AI Gym Coach

AI Gym Coach is a fitness web app with a FastAPI backend and browser pages. It covers:

- **Workouts:** a library of 90 exercises across six muscle groups, with live rep counting from a webcam
- **Form feedback:** depth, forward-lean, and tempo checks, with a plain-language fix and drill
- **Tracking:** daily check-ins with a streak, sets saved per day, reps per muscle group, and history
- **Suggestions:** rule-based advice from your own training data
- **Diet:** calorie and protein targets, diet and allergy checks, a food log, and day plans for vegetarian, non-vegetarian, and vegan eating
- **Weight goals:** a target weight (lose or gain), a weekly weight log, and automatic calorie reviews
- **Accounts:** registration, login, sessions, and a profile page with a UserID

Everything runs locally. Nothing is sent to a third-party service except the MediaPipe pose model and runtime, which the browser downloads once.

> **Medical note:** this app gives general fitness and nutrition guidance, not medical advice. Calorie targets are estimates. Anyone with a medical condition, who is pregnant, or who has a history of an eating disorder should not use calorie targets without a doctor or dietitian.

---

## Contents

1. [Features](#features)
2. [Tech stack](#tech-stack)
3. [Project structure](#project-structure)
4. [Setup (Windows, PowerShell)](#setup-windows-powershell)
5. [Running the app](#running-the-app)
6. [Pages](#pages)
7. [API reference](#api-reference)
8. [Configuration](#configuration)
9. [Tests](#tests)
10. [Camera and rep counting](#camera-and-rep-counting)
11. [Diet and nutrition](#diet-and-nutrition)
12. [Weight goals](#weight-goals)
13. [Security](#security)
14. [Known limitations](#known-limitations)
15. [Troubleshooting](#troubleshooting)
16. [Not built yet](#not-built-yet)

---

## Features

### Accounts
- Register with username, email, password, and fitness goal. Passwords are stored as PBKDF2 hashes.
- Each account gets a UserID such as `GYM-000013`.
- Log in with username, email, or UserID. Sessions use an HTTP-only cookie that lasts 30 days.
- Log out ends the session on the server.

### Workouts
- 90 exercises in six groups: Chest, Back, Legs, Shoulders, Arms, Core. Each has a detail page with cues, an optional photo, and an optional demo video.
- **Auto count (camera):** 74 exercises count reps from a webcam using a joint angle. Each has its own joint, thresholds, and camera view.
- **Tap count:** for lifts that can't be counted from one joint angle, such as shrugs and calf raises.
- **Timer:** for planks and holds.
- **Mirror view:** flips the picture like a mirror. The overlay follows the body.
- **Save set:** saves reps, weight, form score, and flags. The coach panel explains the main form issue and a drill.

### Tracking
- **Check-in:** one per day. Streak counts consecutive days, and a day with a saved set counts as attended.
- **Reps by muscle group:** primary muscles get full reps, and secondary muscles get half (`app/muscles.py`).
- **History:** sessions grouped by day, for 7, 30, or 90 days.
- **Suggestions:** rules flag neglected groups, groups far ahead of others, reps outside your goal's target, and groups trained hard three days running.

### Diet
- **Targets:** calories and protein from weight, height, age, sex, workout, and goal. Calories never drop below 1500 (men) or 1200 (women).
- **Diet types:** vegan, vegetarian (no meat, fish, or eggs), non-vegetarian.
- **Allergies:** milk, egg, peanut, tree nut, gluten, soy, fish, shellfish. Foods containing an allergen are blocked.
- **Food log:** search the food list, enter grams, and see calories and protein for the day. Foods that don't fit your diet get a warning and up to three alternatives.
- **Day plan:** four meals (breakfast, lunch, snack, dinner) that follow your diet and allergies. "Another plan" shows different foods.

### Weight goals
- **Goals:** lose weight, gain weight, or maintain.
- **Target checks:** a loss target must be below your current weight, and a gain target must be above it.
- **Weekly log:** log your weight any time. The page shows the last 7 days' change, the distance to target, and the history.
- **Weekly review:** once a week, progress is compared with the planned rate. Calories change by 150 a day if progress is much slower or faster than planned. The total change is capped at 500 calories a day either way.

### Live camera page
- `/live` and `/gym` are older single-page versions of the counter. They still work, but the workout pages cover the same features.

---

## Tech stack

| Layer | Technology |
|---|---|
| Backend | Python 3.14, FastAPI, Pydantic, SQLite (`sqlite3`) |
| Pose estimation (Python) | MediaPipe Tasks `PoseLandmarker`, OpenCV |
| Pose estimation (browser) | MediaPipe Tasks Vision (WebAssembly), loaded from jsDelivr |
| Frontend | Plain HTML, CSS, and JavaScript (no build step) |
| 3D backgrounds | Three.js 0.160 |
| Tests | pytest |

---

## Project structure

```
ai-gym-coach/
├── app/
│   ├── main.py            FastAPI app: pages, auth, tracking, nutrition and weight routes
│   ├── auth.py            Password hashing, validation, session tokens
│   ├── biomech.py         Joint angles, torso lean, leverage index, lean limit
│   ├── reps.py            Rep segmentation (hysteresis) and per-rep form scoring
│   ├── exercises.py       Exercise catalogue for the Python live counter
│   ├── analytics.py       Estimated 1RM, plateau detection, overload, readiness, rest timer
│   ├── generator.py       Rule-based push/pull/legs session generator
│   ├── pose.py            Video analysis CLI using MediaPipe
│   ├── live.py            Python webcam rep counter (desktop window)
│   ├── calibrate.py       Measures your range of motion for one exercise
│   ├── debug_angles.py    Exports per-frame angles for a time window
│   ├── tracking.py        Day/week/month summaries, attendance streak
│   ├── coaching.py        Form flags to plain-language feedback and drills
│   ├── history.py         Sessions grouped by day with reps per group
│   ├── muscles.py         Exercise to muscle mapping, reps per muscle and group
│   ├── suggestions.py     Rule-based training suggestions
│   ├── nutrition.py       Food database, targets, diet and allergy checks, day plans
│   ├── goals.py           Weight target checks, weekly change, calorie reviews
│   └── static/            Browser pages, scripts, styles, optional media
│       ├── home.html, workouts.html, workout.html, tracker.html, diet.html
│       ├── login.html, register.html, profile.html, onboarding.html
│       ├── live.html, gym.html, index.html, camtest.html (older pages and test page)
│       ├── common.js      Navigation, toast messages, shared helpers
│       ├── data.js        Exercise list and camera settings (browser)
│       ├── style.css      Shared styles
│       ├── bg3d.js        3D background for workout pages
│       └── food3d.js      3D food background for the diet page
├── tests/                 pytest suites (see Tests)
├── requirements.txt       Core dependencies
├── requirements-cv.txt    OpenCV and MediaPipe (only for camera tools)
└── README.md
```

Optional folders you create yourself:

- `app/static/images/`: exercise photos named like `bench-press.jpg`
- `app/static/videos/`: demo videos named like `bench-press.mp4`
- `app/static/models/`: optional local copy of the pose model
- `pose_landmarker_full.task`: the pose model file, in the project root (see Setup)

---

## Setup (Windows, PowerShell)

These steps assume Python 3.14 and PowerShell, run from the project root (the folder that contains `app`).

### 1. Create and activate a virtual environment

```powershell
python -m venv venv
venv\Scripts\Activate.ps1
```

If PowerShell blocks the activation script, run this once and try again:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

### 2. Install the core dependencies

```powershell
python -m pip install -r requirements.txt
```

### 3. Install the camera tools (optional, only for the Python camera scripts)

```powershell
python -m pip install -r requirements-cv.txt
```

The browser camera pages do not need these packages. They download MediaPipe from the internet when first used.

### 4. Get the pose model (only for the Python camera tools)

Download `pose_landmarker_full.task` into the project root:

```powershell
Invoke-WebRequest -Uri "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_full/float16/latest/pose_landmarker_full.task" -OutFile "pose_landmarker_full.task"
```

---

## Running the app

From the project root, with the virtual environment active:

```powershell
python -m uvicorn app.main:app --reload --port 8001
```

Wait for `Uvicorn running on http://127.0.0.1:8001`, then open:

- `http://127.0.0.1:8001/home` for the homepage
- `http://127.0.0.1:8001/docs` for the interactive API documentation

Use port 8001 consistently. An older process can still hold port 8000 on Windows.

### Command-line camera tools

```powershell
python -m app.pose "C:\path\to\video.mp4" squat --side r
python -m app.pose "C:\path\to\video.mp4" squat --side r --start 60 --end 84
python -m app.live squat --side r
python -m app.calibrate bench_press --side l --seconds 20
python -m app.debug_angles "C:\path\to\video.mp4" --start 60 --end 84
```

---

## Pages

| Address | Who | What |
|---|---|---|
| `/` | Everyone | Redirects to `/home` |
| `/home` | Everyone | Homepage with links to diet, progress, and workouts |
| `/workouts` | Everyone | Exercise library with search and muscle-group tabs |
| `/workout?g=Chest&e=Bench%20press` | Everyone | One exercise: counter, save set, rating, tips |
| `/register`, `/login` | Guests | Create an account or log in |
| `/profile` | Logged in | UserID, daily check-in, activity counts |
| `/tracker` | Logged in | Streak, suggestions, reps per muscle group, history |
| `/diet` | Logged in | Goal, targets, weight log, food log, day plans |
| `/onboarding` | Logged in | Welcome page after registering |
| `/gym`, `/live` | Everyone | Older single-page counters |

Logged-in pages redirect to `/login` and return you afterwards.

---

## API reference

Responses are JSON. Errors use `{"detail": "message"}`. "Logged in" means the session cookie from `/auth/login` is sent with the request.

### Accounts

| Method | Path | Notes |
|---|---|---|
| POST | `/auth/register` | Body: `username`, `email`, `password`, `goal`, `equipment`, `injuries`. Logs you in. |
| POST | `/auth/login` | Body: `identifier` (username or email), `password` |
| POST | `/auth/logout` | Ends the session |
| GET | `/auth/me` | Current user, or 401 |

### Workouts and tracking

| Method | Path | Notes |
|---|---|---|
| POST | `/api/sets` | Logged in. Saves a set and records attendance for that day. Returns coaching for the flags. |
| POST | `/api/checkin` | Logged in. One check-in per day. Returns the streak. |
| GET | `/api/me/summary` | Streak, checked-in-today, days attended, suggestions |
| GET | `/api/me/history?days=30` | Sessions with reps per group, totals, and reps per muscle |
| GET | `/api/me/progress?period=day\|week\|month` | Summaries per period, with improvement in estimated 1RM |
| GET | `/api/me/attendance` | List of attended days |
| GET | `/api/me/suggestions` | Suggestions from the last 30 days |

### Diet and weight

| Method | Path | Notes |
|---|---|---|
| POST | `/api/nutrition/profile` | Body: `weight`, `unit` (kg or lb), `height_cm`, `age`, `sex`, `workout`, `diet`, `allergies`, `goal`, `target_weight`. Rejects targets in the wrong direction. |
| GET | `/api/nutrition/profile` | Profile, targets, and goal tips |
| POST | `/api/weight` | Body: `day`, `weight`, `unit`. Logs weight, and runs the weekly review when due. |
| GET | `/api/weight/summary` | Current, target, remaining, 7-day change, status, history |
| GET | `/api/foods/search?q=` | Search with diet and allergy flags |
| POST | `/api/food-log` | Body: `day`, `food`, `grams`. Blocked foods return 400. |
| GET | `/api/food-log?day=` | Entries and totals for a day, with remaining calories |
| DELETE | `/api/food-log/{id}` | Removes one of your entries |
| GET | `/api/nutrition/plan?day_index=0` | Day plan for your diet and allergies |

### Older endpoints

These routes predate the account system. They trust the `user_id` sent in the request, so **anyone can read or change any user's data through them**. Remove them before public use.

- `POST /users`, `POST /checkins`, `POST /sets`
- `GET /users/{uid}/readiness`, `GET /users/{uid}/plan`, `GET /users/{uid}/progress/{exercise}`

Other read-only routes: `/exercises` (the Python exercise list).

---

## Configuration

| Variable | Default | Purpose |
|---|---|---|
| `GYM_DB` | `gym.db` | Path to the SQLite database file. Created automatically. |
| `POSE_MODEL` | `pose_landmarker_full.task` | Path to the pose model for the Python camera tools |

Example:

```powershell
$env:GYM_DB = "C:\data\gym.db"
python -m uvicorn app.main:app --port 8001
```

The database has these tables: `users`, `sessions`, `checkins`, `attendance`, `sets`, `nutrition_profiles`, `food_log`, `weight_log`.

---

## Tests

Run everything:

```powershell
python -m pytest
```

Run one area:

```powershell
python -m pytest tests\test_nutrition.py
python -m pytest tests\test_goals.py
python -m pytest tests\test_muscles.py tests\test_suggestions.py tests\test_history.py tests\test_tracking.py
```

| File | Covers |
|---|---|
| `test_core.py` | Joint angles, rep counting, form flags, leverage, 1RM, plateau, readiness, generator |
| `test_tracking.py` | Period summaries, streaks, coaching messages |
| `test_muscles.py` | Muscle mapping, reps per muscle and group |
| `test_history.py` | Sessions and history totals |
| `test_suggestions.py` | Suggestion rules |
| `test_nutrition.py` | Targets, floors, diet and allergy checks, alternatives, day plans for every diet |
| `test_goals.py` | Goal names, target direction, weekly change, calorie reviews |
| `test_auth.py`, `test_api.py` | Accounts, sessions, and API routes (need FastAPI installed) |

The pure logic tests run without a server. The API tests run through FastAPI's test client.

---

## Camera and rep counting

### How counting works
1. The browser (or Python) finds 33 body landmarks in each frame.
2. The app computes one joint angle for the exercise, for example hip–knee–ankle for squats.
3. A rep is counted when the angle goes below the **low** threshold and returns above the **high** threshold. The gap between them stops small wobbles from counting as reps.
4. Each rep is scored: incomplete depth (−25), excess forward lean on squats (−20), too fast under 0.8 seconds (−10).

### Settings
Each camera exercise has a row in `app/static/data.js` (browser) and `app/exercises.py` (Python), with: joint, low, high, depth limit, camera view, and whether the angle is inverted (for flies and raises). These are starting values. Test each lift and adjust. `app/calibrate.py` measures your own range of motion to suggest values.

### Camera setup
- Presses, rows, curls, squats: film from the **side**.
- Flies, lateral raises, rear delt work: film from the **front**.
- Camera at hip height, whole body in frame, one person, good light.
- The browser only allows camera access on `localhost` or HTTPS.

### Known limits
- Thresholds are not validated for every person. Use calibration and check counts against your own.
- Form checks look at one joint angle and torso lean. They cannot see back rounding, knee cave, or bar path.
- Planks, calf raises, and ab work are timed or tap-counted, not camera-counted.

---

## Diet and nutrition

### Food database
`app/nutrition.py` contains about 115 common foods, each with calories, protein, carbs, and fat per 100 g, a role (protein, carb, veg, fruit, fat, snack, dish, drink), a diet type, allergen tags, and a flag (`ok` or `limit`). The values are approximate. Check important figures against USDA FoodData Central or the Indian Food Composition Tables.

To add a food, add one tuple to the `FOODS` list:

```python
("Food name", "protein", "veg", 120, 10, 2, 8, "milk", "ok"),
#  name       role       diet  kcal  p   c  f  allergens  flag
```

Diet types: `vegan` fits every diet, `veg` fits vegetarian and non-vegetarian, `nonveg` fits non-vegetarian only. Eggs are classed as non-vegetarian.

### Calories and protein
- BMR uses the Mifflin–St Jeor equation.
- Maintenance = BMR × activity factor (none 1.2, yoga 1.4, strength 1.55, cardio 1.6, HIIT 1.7, sports 1.65).
- Goal adjustment: lose weight −400 kcal, gain weight +250 kcal, maintain 0.
- Protein: 1.8 g per kg for losing or gaining, 1.6 g per kg for maintaining.
- Fat is 25% of calories. Carbs fill the rest.
- Calorie floor: 1500 (men) or 1200 (women). When the floor applies, the page says so.

### Day plans
Each plan has four meals with a share of the daily calories: breakfast 25%, lunch 35%, snack 10%, dinner 30%.

- **Vegan:** plant foods only.
- **Vegetarian:** plant foods, dairy, and paneer. No meat, fish, or eggs.
- **Non-vegetarian:** lunch includes meat or fish, and dinner includes a vegetarian protein.
- Gaining weight adds a calorie-dense snack (nuts or peanut butter, filtered by your allergies).

All plans exclude foods containing your allergens.

### Allergy names
You can type these, separated by commas: milk, dairy, lactose, egg, peanut, nut, tree nut, almond, walnut, gluten, wheat, soy, fish, shellfish, prawn, shrimp. Unrecognised words are reported back so you can correct them.

---

## Weight goals

- **Target rules:** losing needs a target below your current weight, and gaining needs a target above it. Targets must be between 30 and 300 kg.
- **Current weight:** the latest weigh-in, or your profile weight if you have none.
- **Weekly change:** the difference between the first and last weigh-in in the last 7 days. At least two weigh-ins are needed.
- **Planned rate:** about 0.36 kg a week for losing and 0.23 kg a week for gaining, from the calorie adjustments and 7,700 kcal per kg.
- **Review:** at most once a week. Progress slower than half the planned rate, or faster than 1.5 times it, changes calories by 150 a day in the right direction. Changes are capped at ±500 kcal a day from the starting target.
- **Stopping:** reviews stop when you're within 0.5 kg of your target.

The weekly rate is a rough estimate. Water and food volume also change body weight.

---

## Security

Implemented:
- Passwords are hashed with PBKDF2-SHA256 (200,000 iterations).
- Session tokens are random. Only a hash of each token is stored.
- Session cookies are HTTP-only and `SameSite=Lax`.
- Account routes and the newer `/api/*` routes check the session.

Not yet implemented, or open:
- **Cookies are not marked `Secure`.** Add `secure=True` when you serve the app over HTTPS.
- **Older endpoints trust `user_id`** (see [Older endpoints](#older-endpoints)).
- **No email verification and no password reset.**
- **No rate limiting** on login or registration.
- **No HTTPS configuration.** The app runs over plain HTTP on `localhost`.
- **Social sign-in buttons are disabled.** They need provider keys.
- **Medical screening is not implemented.** Add a screening question before publishing the diet features.

---

## Known limitations

- **Approximate data:** nutrition values, exercise thresholds, and the calorie review rules are estimates.
- **Small food list:** about 115 foods. Not every food in the world is included.
- **Camera accuracy varies:** lighting, clothing, camera angle, and body proportions all affect counts.
- **Browser support:** Chrome and Edge are tested most. The camera and WebGL need a modern browser.
- **Caching:** browsers can keep old copies of pages and scripts. Use Ctrl+F5 after an update, or clear the site's cached files. The server sends `Cache-Control: no-cache` for pages and static files, which stops most repeats.
- **Local storage:** ratings and community tips on workout pages are saved in the browser only, not on the server.
- **Adaptive plans:** day plans don't change based on what you log. Calorie targets change through the weekly review only.

---

## Troubleshooting

**Port already in use**
```powershell
netstat -ano | findstr :8001
```
Stop the process with `Stop-Process -Id <PID> -Force`, or use another port.

**A page shows old content**
Press Ctrl+Shift+R, or clear the site's cached files in the browser. Check the address is `127.0.0.1:8001`.

**Import error on startup**
Check you're in the project root with the virtual environment active. A `ModuleNotFoundError` names the missing module.

**`Pose model not found`**
Download `pose_landmarker_full.task` into the project root, or set `POSE_MODEL` to its path.

**Camera does not start in the browser**
Allow camera access in the address bar. Close other apps using the camera. Use `localhost`, not a LAN address, unless you serve HTTPS.

**"log a check-in for this day first" or "Set up your nutrition profile first"**
Those messages are expected until you check in or save your diet profile.

**Tests fail with a FastAPI import error**
Install the core requirements: `python -m pip install -r requirements.txt`.

---

## Not built yet

- Community feed, comments, and moderation
- Recovery map (body diagram of readiness by muscle group)
- Per-person camera calibration built into the workout page
- Photo progress tracking
- Password reset and email verification
- Locking down the older `user_id`-based endpoints
- Real food photos and per-exercise written descriptions for all 90 exercises
- A complete food database from USDA or IFCT data
- Screening for medical conditions and eating disorders before diet targets are shown

---

## Licence and credits

Add your licence here. The pose model is provided by MediaPipe (Google) under its own terms. Exercise photos and videos must be your own or properly licensed. Check the licence of any nutrition data you import.
