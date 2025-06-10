from datetime import datetime
from typing import Optional

from sqlalchemy import (
    DateTime,
    ForeignKey,
    String,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db_models.base_entity import Base


class Checkpoint(Base):
    __tablename__ = "checkpoints"

    checkpoint_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    thread_id: Mapped[str] = mapped_column(String, ForeignKey("threads.id"), primary_key=True)
    checkpoint_ns: Mapped[str] = mapped_column(String, nullable=False, server_default="", primary_key=True)

    parent_checkpoint_id: Mapped[Optional[UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    type: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    checkpoint: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, nullable=False, server_default="{}")

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=func.now(),
        server_default=func.now(),
    )

    thread = relationship("Thread", back_populates="checkpoints")
