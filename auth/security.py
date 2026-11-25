"""Security primitives: deliberately dependency-free and safe for the SQLite demo."""
from __future__ import annotations
import base64, hashlib, hmac, os
from functools import wraps

ITERATIONS = 310_000
ROLE_PERMISSIONS = {
    "ADMIN": {"*"},
    "REVENUE_OFFICER": {"upload", "review", "read", "gis", "approve"},
    "SURVEY_OFFICER": {"read", "gis", "geometry", "three_d"},
    "REGISTRATION_OFFICER": {"read", "registration"},
    "TAX_OFFICER": {"read", "tax"},
    "CITIZEN": {"public_read"},
}
def hash_password(password: str, salt: bytes | None = None) -> str:
    salt = salt or os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, ITERATIONS)
    return f"pbkdf2_sha256${ITERATIONS}${base64.b64encode(salt).decode()}${base64.b64encode(digest).decode()}"
def verify_password(password: str, encoded: str) -> bool:
    algo, iterations, salt, digest = encoded.split("$")
    if algo != "pbkdf2_sha256": return False
    expected = hashlib.pbkdf2_hmac("sha256", password.encode(), base64.b64decode(salt), int(iterations))
    return hmac.compare_digest(expected, base64.b64decode(digest))
def allowed(role: str, permission: str) -> bool:
    return "*" in ROLE_PERMISSIONS.get(role, set()) or permission in ROLE_PERMISSIONS.get(role, set())
def require(role: str, permission: str) -> None:
    if not allowed(role, permission): raise PermissionError(f"{role} is not permitted to {permission}")
