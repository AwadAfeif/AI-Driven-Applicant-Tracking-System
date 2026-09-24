"""Authentication service — business logic for register/login/refresh/logout."""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import NamedTuple

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.exceptions import (
    EmailAlreadyRegisteredError,
    InvalidCredentialsError,
)
from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    hash_refresh_token,
    verify_password,
)
from app.models.m1_identity import User
from app.repositories.refresh_token import RefreshTokenRepository
from app.repositories.user import UserRepository

settings = get_settings()


class RegisterResult(NamedTuple):
    """Returned by AuthService.register()."""

    user: User
    access_token: str
    refresh_token: str


class LoginResult(NamedTuple):
    """Returned by AuthService.login()."""

    user: User
    access_token: str
    refresh_token: str


class AuthService:
    """Coordinates user and refresh-token repositories.

    Owns the transaction boundary: commit() on success, rollback() on error.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.users = UserRepository(session)
        self.refresh_tokens = RefreshTokenRepository(session)

    async def register(
        self,
        *,
        email: str,
        password: str,
        full_name: str,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> RegisterResult:
        """Register a new user and issue the first token pair.

        Atomic: either the user + refresh token are both persisted, or neither.
        The raw refresh token is returned to the caller only — only its
        sha256 hash is stored in the database.
        """
        try:
            if await self.users.email_exists(email):
                raise EmailAlreadyRegisteredError(email)

            password_hash = hash_password(password)
            user = await self.users.create(
                email=email,
                password_hash=password_hash,
                full_name=full_name,
            )

            family_id = uuid.uuid4()
            expires_at = datetime.now(timezone.utc) + timedelta(
                days=settings.REFRESH_TOKEN_EXPIRE_DAYS
            )

            access_token = create_access_token(user.id)
            refresh_token = create_refresh_token(user.id, family_id=family_id)

            await self.refresh_tokens.create(
                user_id=user.id,
                token_hash=hash_refresh_token(refresh_token),
                family_id=family_id,
                expires_at=expires_at,
                ip_address=ip_address,
                user_agent=user_agent,
            )

            await self.session.commit()

            return RegisterResult(
                user=user,
                access_token=access_token,
                refresh_token=refresh_token,
            )
        except Exception:
            await self.session.rollback()
            raise
    async def login(
        self,
        *,
        email: str,
        password: str,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> LoginResult:
        """Authenticate an existing user and issue a new token pair.

        All failure cases (unknown email, wrong password, inactive user)
        raise InvalidCredentialsError — the caller cannot distinguish them.
        Each successful login starts a new refresh-token family.
        """
        try:
            user = await self.users.get_by_email(email)
            if user is None:
                raise InvalidCredentialsError()

            if not verify_password(password, user.password_hash):
                raise InvalidCredentialsError()

            if not user.is_active:
                raise InvalidCredentialsError()

            family_id = uuid.uuid4()
            expires_at = datetime.now(timezone.utc) + timedelta(
                days=settings.REFRESH_TOKEN_EXPIRE_DAYS
            )

            access_token = create_access_token(user.id)
            refresh_token = create_refresh_token(user.id, family_id=family_id)

            await self.refresh_tokens.create(
                user_id=user.id,
                token_hash=hash_refresh_token(refresh_token),
                family_id=family_id,
                expires_at=expires_at,
                ip_address=ip_address,
                user_agent=user_agent,
            )

            await self.session.commit()

            return LoginResult(
                user=user,
                access_token=access_token,
                refresh_token=refresh_token,
            )
        except Exception:
            await self.session.rollback()
            raise
