from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    PrimaryKeyConstraint,
    String,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.db_models.base_entity import Base


class Checkpoint(Base):
    __tablename__ = "checkpoints"
    __table_args__ = PrimaryKeyConstraint("thread_id", "checkpoint_id", "checkpoint_ns")

    checkpoint_id = Column(UUID(as_uuid=True), primary_key=True)
    thread_id = Column(String, ForeignKey("threads.id"), primary_key=True)
    checkpoint_ns = Column(String, nullable=False, server_default="", primary_key=True)

    parent_checkpoint_id = Column(UUID(as_uuid=True), nullable=True)
    type = Column(String, nullable=True)

    checkpoint = Column(JSONB, nullable=False, default=dict)
    metadata_ = Column("metadata", JSONB, nullable=False, server_default="{}")

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=func.now(),
        server_default=func.now(),
    )

    thread = relationship("Thread", back_populates="checkpoints")
