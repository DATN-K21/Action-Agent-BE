from sqlalchemy import ForeignKey, Integer, LargeBinary, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db_models.base_entity import Base


class Write(Base):
    __tablename__ = "checkpoint_writes"

    thread_id: Mapped[str] = mapped_column(String, ForeignKey("threads.id"), primary_key=True)
    checkpoint_ns: Mapped[str] = mapped_column(String, nullable=False, server_default="", primary_key=True)
    checkpoint_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    task_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    idx: Mapped[int] = mapped_column(Integer, primary_key=True)

    channel: Mapped[str] = mapped_column(String, nullable=False)
    type: Mapped[str | None] = mapped_column(String, nullable=True)
    blob: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)

    thread = relationship("Thread", back_populates="writes")
