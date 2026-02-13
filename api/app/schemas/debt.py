from __future__ import annotations

import uuid
from decimal import Decimal
from pydantic import BaseModel


class DebtSummaryResponse(BaseModel):
    debtor_id: uuid.UUID
    creditor_id: uuid.UUID
    total_owed: Decimal


class SettleRequest(BaseModel):
    debtor_id: uuid.UUID
    creditor_id: uuid.UUID


class SettleResponse(BaseModel):
    settled_count: int
    message: str
