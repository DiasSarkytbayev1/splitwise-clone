import uuid

from sqlalchemy import (
    Column,
    Enum,
    ForeignKey,
    Numeric,
)
from sqlalchemy.dialects.postgresql import UUID

from api.app.database import Base


class ExpenseShare(Base):
    """How an expense is split between a debtor and a creditor."""

    __tablename__ = "expense_shares"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    expense_id = Column(
        UUID(as_uuid=True), ForeignKey("expenses.id", ondelete="CASCADE"), nullable=False
    )
    debtor_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    creditor_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    amount_owed = Column(Numeric(12, 2), nullable=False)
    percentage = Column(Numeric(5, 2), nullable=False)

    # "pending" | "settled"
    status = Column(
        Enum("pending", "settled", name="expense_share_status_enum"),
        nullable=False,
        default="pending",
    )
