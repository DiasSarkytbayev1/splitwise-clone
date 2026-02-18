from __future__ import annotations

import uuid
from decimal import Decimal

from pydantic import BaseModel


class DebtSummaryResponse(BaseModel):
    """Summary of debts between two users in a group."""

    debtor_id: uuid.UUID
    creditor_id: uuid.UUID
    total_owed: Decimal


class SettleResponse(BaseModel):
    """Response after settling a debt."""

    settled_count: int
    message: str
