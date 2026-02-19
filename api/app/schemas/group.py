from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel

# ── Requests ──────────────────────────────────────────────────────────────────


class GroupCreateRequest(BaseModel):
    name: str
    type: str | None = None
    currency_code: str = "USD"
    cover_image: str | None = None
    # debt_simplification is not settable at creation for now


# ── Responses ─────────────────────────────────────────────────────────────────


class GroupResponse(BaseModel):
    id: uuid.UUID
    name: str
    type: str | None
    currency_code: str
    cover_image: str | None
    invite_code: str
    created_by: uuid.UUID
    created_at: datetime
    debt_simplification: bool  # NEW FIELD

    model_config = {"from_attributes": True}
