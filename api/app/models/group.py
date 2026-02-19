import secrets
import string
import uuid

from sqlalchemy import (
    TIMESTAMP,
    Boolean,
    Column,
    ForeignKey,
    String,
    text,
)
from sqlalchemy.dialects.postgresql import UUID

from api.app.database import Base


def _generate_invite_code(length: int = 8) -> str:
    """Generate a random alphanumeric invite code."""
    alphabet = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


class Group(Base):
    __tablename__ = "groups"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    name = Column(String(255), nullable=False)
    type = Column(String(100), nullable=True)
    currency_code = Column(String(10), nullable=False, default="USD")
    cover_image = Column(String(500), nullable=True)
    invite_code = Column(
        String(20), unique=True, nullable=False, default=_generate_invite_code, index=True
    )

    debt_simplification = Column(Boolean, nullable=False, default=False, server_default=text("false"))

    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    created_at = Column(
        TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"), nullable=False
    )
