from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel


# ── Requests ──────────────────────────────────────────────────────────────────

class ExpenseShareItem(BaseModel):
    """A single share entry when creating an expense."""
    debtor_id: uuid.UUID
    creditor_id: uuid.UUID
    amount_owed: Decimal
    percentage: Decimal


class ExpenseCreateRequest(BaseModel):
    description: str
    amount: Decimal
    payer_id: uuid.UUID
    shares: list[ExpenseShareItem]
    category: str | None = None
    date: datetime | None = None


# ── Responses ─────────────────────────────────────────────────────────────────

class ExpenseShareResponse(BaseModel):
    id: uuid.UUID
    debtor_id: uuid.UUID
    creditor_id: uuid.UUID
    amount_owed: Decimal
    percentage: Decimal
    status: str


class ExpenseResponse(BaseModel):
    id: uuid.UUID
    group_id: uuid.UUID
    payer_id: uuid.UUID
    description: str
    amount: Decimal
    category: str | None
    date: datetime
    created_at: datetime
    shares: list[ExpenseShareResponse] = []

