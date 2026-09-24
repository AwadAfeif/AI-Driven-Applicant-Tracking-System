"""Application-wide exception hierarchy."""
from __future__ import annotations


class AppError(Exception):
    """Base for all application errors."""


# ─── Auth ────────────────────────────────────────────────────────

class AuthError(AppError):
    """Base for authentication errors."""


class EmailAlreadyRegisteredError(AuthError):
    """A user with this email already exists."""


class InvalidCredentialsError(AuthError):
    """Email not found, or password does not match."""


class InvalidTokenError(AuthError):
    """JWT is malformed, expired, wrong signature, or wrong type."""


class RefreshTokenNotFoundError(AuthError):
    """Refresh token hash not present in the DB."""


class RefreshTokenRevokedError(AuthError):
    """Refresh token was already revoked — potential reuse attack."""


class RefreshTokenExpiredError(AuthError):
    """Refresh token is past its expires_at."""
