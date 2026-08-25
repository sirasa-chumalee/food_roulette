import os
from datetime import datetime, timedelta, timezone

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

security = HTTPBearer(auto_error=False)

# Fail fast on a missing secret. A PUBLIC, committed default like
# "dev-secret-change-this" would let anyone mint a valid token for any user —
# exactly the hole this module exists to close. If JWT_SECRET_KEY isn't set we
# refuse to boot rather than sign with a key an attacker already knows.
_JWT_SECRET = os.getenv("JWT_SECRET_KEY")
if not _JWT_SECRET:
    raise RuntimeError(
        "JWT_SECRET_KEY environment variable is required. "
        "Refusing to sign tokens with a well-known default secret."
    )
SECRET_KEY = _JWT_SECRET

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

password_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        password_hasher.verify(password_hash, password)
        return True
    except VerifyMismatchError:
        return False


def create_access_token(user_id: str) -> str:
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    payload = {
        "sub": user_id,
        "iat": now,
        "exp": expires_at,
    }

    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> str:
    payload = jwt.decode(
        token,
        SECRET_KEY,
        algorithms=[ALGORITHM],
    )

    user_id = payload.get("sub")

    if not user_id:
        raise ValueError("Invalid token")

    return user_id


def get_current_user_id(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> str:
    """Require a valid bearer token and return the authenticated user's id.

    This is the guard every identity-bearing route depends on. Once an endpoint
    takes this dependency, a request without (or with a bad/expired) token is
    rejected with 401 before the handler body runs.

    `HTTPBearer(auto_error=False)` returns None for a missing header instead of
    raising its own 403 — we translate that to a 401 so the whole API speaks one
    status code for authentication failures (see main's error envelope).
    """
    if credentials is None:
        raise HTTPException(status_code=401, detail="Not authenticated")

    token = credentials.credentials

    try:
        return decode_access_token(token)

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=401,
            detail="Token has expired",
        )

    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=401,
            detail="Invalid token",
        )