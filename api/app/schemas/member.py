from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr

# ── Requests ──────────────────────────────────────────────────────────────────


class AddMemberRequest(BaseModel):
    user_id: uuid.UUID | None = None
    email: EmailStr | None = None


# ── Responses ─────────────────────────────────────────────────────────────────


class MemberResponse(BaseModel):
    id: uuid.UUID
    group_id: uuid.UUID
    user_id: uuid.UUID
    joined_at: datetime
    # Nested user info
    user_name: str | None = None
    user_email: str | None = None

    model_config = {"from_attributes": True}


class InviteCodeResponse(BaseModel):
    invite_code: str
