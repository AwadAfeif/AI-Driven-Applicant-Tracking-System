"""Security utilities: password hashing and JWT tokens."""
from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Literal

import bcrypt
from jose import JWTError, jwt

from app.core.config import get_settings

settings = get_settings()

TokenType = Literal["access", "refresh"]


# ─── Password hashing ────────────────────────────────────────────

def hash_password(password: str) -> str:
    """Hash a plaintext password using bcrypt."""
    salt = bcrypt.gensalt(rounds=settings.BCRYPT_ROUNDS)
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a plaintext password against a bcrypt hash."""
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except (ValueError, TypeError):
        return False


def hash_refresh_token(token: str) -> str:
    """Deterministic sha256 hash of a refresh token JWT for DB storage."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


# ─── JWT creation ────────────────────────────────────────────────

def _create_token(
    *,
    subject: uuid.UUID | str,
    token_type: TokenType,
    expires_delta: timedelta,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": str(subject),
        "type": token_type,
        "iss": settings.JWT_ISSUER,
        "iat": int(now.timestamp()),
        "exp": int((now + expires_delta).timestamp()),
        "jti": str(uuid.uuid4()),
    }
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_access_token(
    subject: uuid.UUID | str,
    expires_delta: timedelta | None = None,
) -> str:
    delta = expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return _create_token(
        subject=subject,
        token_type="access",
        expires_delta=delta,
    )


def create_refresh_token(
    subject: uuid.UUID | str,
    family_id: uuid.UUID | str,
    expires_delta: timedelta | None = None,
) -> str:
    delta = expires_delta or timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    return _create_token(
        subject=subject,
        token_type="refresh",
        expires_delta=delta,
        extra_claims={"family_id": str(family_id)},
    )


# ─── JWT decoding ────────────────────────────────────────────────

def decode_token(
    token: str,
    expected_type: TokenType | None = None,
) -> dict[str, Any]:
    """Decode and validate a JWT.

    Raises:
        JWTError: signature/expiration/issuer invalid.
        ValueError: expected_type set and does not match token's 'type'.
    """
    payload = jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM],
        issuer=settings.JWT_ISSUER,
    )

    if expected_type is not None and payload.get("type") != expected_type:
        raise ValueError(
            f"Invalid token type: expected {expected_type!r}, "
            f"got {payload.get('type')!r}"
        )
    return payload
