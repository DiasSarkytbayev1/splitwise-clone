from __future__ import annotations

import uuid
from datetime import datetime
from pydantic import BaseModel, EmailStr


# ── Requests ──────────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    invite_group_id: uuid.UUID | None = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    invite_group_id: uuid.UUID | None = None


# ── Responses ─────────────────────────────────────────────────────────────────

class UserResponse(BaseModel):
    id: uuid.UUID
    name: str
    email: str
    created_at: datetime

    model_config = {"from_attributes": True}
