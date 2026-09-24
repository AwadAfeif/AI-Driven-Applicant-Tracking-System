"""User repository — data access layer."""
from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.m1_identity import User


class UserRepository:
    """Data-access layer for the User model.

    No business logic — only DB access.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        stmt = select(User).where(User.id == user_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        # Uses functional unique index uq_users_email_lower (LOWER(email)).
        stmt = select(User).where(func.lower(User.email) == email.lower())
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def email_exists(self, email: str) -> bool:
        return await self.get_by_email(email) is not None

    async def create(
        self,
        *,
        email: str,
        password_hash: str,
        full_name: str | None = None,
        platform_role: str = "user",
    ) -> User:
        user = User(
            email=email,
            password_hash=password_hash,
            full_name=full_name,
            platform_role=platform_role,
        )
        self.session.add(user)
        await self.session.flush()  # assigns id without committing
        return user