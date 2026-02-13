import uuid

from sqlalchemy import (
    Column,
    TIMESTAMP,
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class GroupMember(Base):
    __tablename__ = "group_members"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    group_id = Column(UUID(as_uuid=True), ForeignKey("groups.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    joined_at = Column(TIMESTAMP(timezone=True), server_default="now()", nullable=False)

    __table_args__ = (
        UniqueConstraint("group_id", "user_id", name="uq_group_user"),
    )
