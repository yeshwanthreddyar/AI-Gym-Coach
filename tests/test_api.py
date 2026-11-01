import os
import tempfile

os.environ["GYM_DB"] = os.path.join(tempfile.mkdtemp(), "test.db")
from fastapi.testclient import TestClient  # noqa: E402
from app.main import app  # noqa: E402

client = TestClient(app)


def test_end_to_end():
    uid = client.post("/users", json={"name": "A", "equipment": ["barbell"]}).json()["id"]
    assert client.get(f"/users/{uid}/plan", params={"day": "2026-10-24"}).status_code == 409
    client.post("/checkins", json={"user_id": uid, "day": "2026-10-24", "sleep_hours": 8, "soreness": [1, 2]})
    client.post("/sets", json={"user_id": uid, "day": "2026-10-20", "exercise": "Back squat",
                               "weight": 60, "reps": 8, "form_score": 85})
    plan = client.get(f"/users/{uid}/plan", params={"day": "2026-10-24"}).json()
    assert plan["recommendation"] in {"push", "maintain", "light", "rest"}
    prog = client.get(f"/users/{uid}/progress/Back squat").json()
    assert prog["weekly_e1rm"]
    assert prog["next_target"]["weight"] == 62.5 and prog["next_target"]["reps"] == 5

def test_live_page_and_catalog():
    assert client.get("/live").status_code == 200
    cat = client.get("/exercises").json()
    assert len(cat) == 16
    assert cat["squat"]["joint"] == ["hip", "knee", "ankle"]
