import os
import tempfile

os.environ["GYM_DB"] = os.path.join(tempfile.mkdtemp(), "auth.db")
from fastapi.testclient import TestClient  # noqa: E402
from app.main import app  # noqa: E402
from app.auth import validate_registration, hash_password, verify_password  # noqa: E402

GOOD = {"username": "alex_lifts", "email": "alex@example.com", "password": "strong123", "goal": "strength"}


def new_client():
    return TestClient(app)


def test_password_hashing():
    h = hash_password("abc12345")
    assert verify_password("abc12345", h)
    assert not verify_password("wrong", h)


def test_validation_rules():
    assert validate_registration("ab", "x@y.com", "abc12345")
    assert validate_registration("alex", "not-an-email", "abc12345")
    assert validate_registration("alex", "a@b.com", "short1")
    assert validate_registration("alex", "a@b.com", "onlyletters")
    assert validate_registration("alex", "a@b.com", "abc12345") == []


def test_register_returns_user_id_and_logs_in():
    c = new_client()
    r = c.post("/auth/register", json=GOOD)
    assert r.status_code == 200
    body = r.json()
    assert body["user_code"].startswith("GYM-")
    assert body["username"] == "alex_lifts"
    assert c.get("/auth/me").status_code == 200


def test_duplicate_username_and_email_rejected():
    new_client().post("/auth/register", json={**GOOD, "username": "dup_user", "email": "dup@example.com"})
    r1 = new_client().post("/auth/register", json={**GOOD, "username": "DUP_USER", "email": "other@example.com"})
    assert r1.status_code == 409 and "taken" in r1.json()["detail"]
    r2 = new_client().post("/auth/register", json={**GOOD, "username": "other_user", "email": "dup@example.com"})
    assert r2.status_code == 409 and "email" in r2.json()["detail"]


def test_invalid_registration_rejected():
    r = new_client().post("/auth/register", json={**GOOD, "username": "x", "password": "nope"})
    assert r.status_code == 400


def test_login_by_username_or_email():
    new_client().post("/auth/register", json={**GOOD, "username": "log_one", "email": "log1@example.com"})
    assert new_client().post("/auth/login", json={"identifier": "LOG_ONE", "password": "strong123"}).status_code == 200
    assert new_client().post("/auth/login", json={"identifier": "log1@example.com", "password": "strong123"}).status_code == 200


def test_login_error_messages():
    new_client().post("/auth/register", json={**GOOD, "username": "log_two", "email": "log2@example.com"})
    r = new_client().post("/auth/login", json={"identifier": "log_two", "password": "wrong999"})
    assert r.status_code == 401 and "Incorrect password" in r.json()["detail"]
    r = new_client().post("/auth/login", json={"identifier": "ghost_user", "password": "x"})
    assert r.status_code == 404 and "No account" in r.json()["detail"]


def test_logout_ends_session():
    c = new_client()
    c.post("/auth/register", json={**GOOD, "username": "log_three", "email": "log3@example.com"})
    assert c.get("/auth/me").status_code == 200
    assert c.post("/auth/logout").status_code == 200
    assert c.get("/auth/me").status_code == 401


def test_profile_requires_login():
    r = new_client().get("/profile", follow_redirects=False)
    assert r.status_code == 303 and r.headers["location"].startswith("/login")


def test_profile_data_matches_registration():
    c = new_client()
    reg = c.post("/auth/register", json={**GOOD, "username": "log_five", "email": "log5@example.com"}).json()
    c2 = new_client()
    c2.post("/auth/login", json={"identifier": "log_five", "password": "strong123"})
    me = c2.get("/auth/me").json()
    assert me["user_code"] == reg["user_code"]
    assert me["email"] == "log5@example.com"


def test_start_journey_never_returns_member_to_register():
    c = new_client()
    c.post("/auth/register", json={**GOOD, "username": "log_four", "email": "log4@example.com"})
    r = c.get("/start", follow_redirects=False)
    assert r.status_code == 303 and r.headers["location"] == "/onboarding"
    assert c.get("/register", follow_redirects=False).headers["location"] == "/onboarding"


def test_start_journey_for_guest_goes_to_register():
    r = new_client().get("/start", follow_redirects=False)
    assert r.headers["location"] == "/register"
