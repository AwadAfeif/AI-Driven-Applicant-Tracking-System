"""User-related Pydantic schemas."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserPublic(BaseModel):
    """Safe user representation for API responses.

    Never includes password_hash or other sensitive fields.
    """

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: EmailStr
    full_name: str | None
    platform_role: Literal["user", "super_admin"]
    is_active: bool
    created_at: datetime
