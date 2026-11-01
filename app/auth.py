"""Registration checks, password hashing, and session tokens (standard library only)."""
import hashlib
import hmac
import re
import secrets

USERNAME_RE = re.compile(r"^[A-Za-z0-9_]{3,20}$")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
ITERATIONS = 200_000
SESSION_DAYS = 30


def validate_registration(username, email, password):
    """Return a list of error messages. An empty list means the input is valid."""
    errors = []
    if not USERNAME_RE.match(username or ""):
        errors.append("Username must be 3-20 characters: letters, numbers or underscore.")
    if not EMAIL_RE.match(email or ""):
        errors.append("Enter a valid email address.")
    if len(password or "") < 8:
        errors.append("Password must be at least 8 characters.")
    elif not (re.search(r"[A-Za-z]", password) and re.search(r"\d", password)):
        errors.append("Password must include at least one letter and one number.")
    return errors


def hash_password(password):
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, ITERATIONS)
    return f"pbkdf2_sha256${ITERATIONS}${salt.hex()}${digest.hex()}"


def verify_password(password, stored):
    try:
        algo, iters, salt_hex, digest_hex = stored.split("$")
    except (AttributeError, ValueError):
        return False
    if algo != "pbkdf2_sha256":
        return False
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt_hex), int(iters))
    return hmac.compare_digest(digest.hex(), digest_hex)


def new_token():
    return secrets.token_urlsafe(32)


def hash_token(token):
    """Only a hash of the session token is stored, so a leaked database cannot be used to log in."""
    return hashlib.sha256(token.encode()).hexdigest()


def user_code(uid):
    return f"GYM-{uid:06d}"
