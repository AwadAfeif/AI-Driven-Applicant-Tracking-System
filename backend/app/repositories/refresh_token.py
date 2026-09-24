"""Refresh token repository — data access layer."""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.m1_identity import RefreshToken


class RefreshTokenRepository:
    """Data-access layer for the RefreshToken model.

    No JWT parsing, no hashing — those belong to the security layer.
    This class only persists and retrieves rows.

    All timestamps are server-generated (func.now()) to comply with Rule 3.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        *,
        user_id: uuid.UUID,
        token_hash: str,
        family_id: uuid.UUID,
        expires_at: datetime,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> RefreshToken:
        """Insert a new refresh token row.

        token_hash must already be sha256-hashed by the caller
        (see security.hash_refresh_token).
        family_id must be reused when rotating within the same session family.
        """
        token = RefreshToken(
            user_id=user_id,
            token_hash=token_hash,
            family_id=family_id,
            expires_at=expires_at,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        self.session.add(token)
        await self.session.flush()
        return token

    async def get_by_hash(self, token_hash: str) -> RefreshToken | None:
        stmt = select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id(self, token_id: uuid.UUID) -> RefreshToken | None:
        stmt = select(RefreshToken).where(RefreshToken.id == token_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def revoke(
        self,
        token: RefreshToken,
        *,
        replaced_by_id: uuid.UUID | None = None,
    ) -> None:
        """Revoke a single token.

        When rotating, pass replaced_by_id = the id of the new token.
        """
        token.revoked_at = func.now()
        if replaced_by_id is not None:
            token.replaced_by_id = replaced_by_id
        await self.session.flush()

    async def revoke_family(self, family_id: uuid.UUID) -> int:
        """Revoke all active tokens in a family.

        Used on reuse-attack detection: if an already-revoked token is
        presented, the entire family is compromised.

        Returns the number of rows updated.
        """
        stmt = (
            update(RefreshToken)
            .where(
                RefreshToken.family_id == family_id,
                RefreshToken.revoked_at.is_(None),
            )
            .values(revoked_at=func.now())
        )
        result = await self.session.execute(stmt)
        await self.session.flush()
        return result.rowcount or 0

    async def revoke_all_for_user(self, user_id: uuid.UUID) -> int:
        """Revoke all active tokens for a user — logout from all devices.

        Returns the number of rows updated.
        """
        stmt = (
            update(RefreshToken)
            .where(
                RefreshToken.user_id == user_id,
                RefreshToken.revoked_at.is_(None),
            )
            .values(revoked_at=func.now())
        )
        result = await self.session.execute(stmt)
        await self.session.flush()
        return result.rowcount or 0