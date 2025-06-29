from sqlalchemy import ForeignKey, LargeBinary
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db_models.base_entity import Base


class CheckpointBlobs(Base):
    __tablename__ = "checkpoint_blobs"

    thread_id: Mapped[str] = mapped_column(ForeignKey("threads.id"), primary_key=True)
    checkpoint_ns: Mapped[str] = mapped_column(nullable=False, server_default="", primary_key=True)
    channel: Mapped[str] = mapped_column(primary_key=True)
    version: Mapped[str] = mapped_column(primary_key=True)
    type: Mapped[str] = mapped_column(nullable=False)
    blob: Mapped[bytes] = mapped_column(LargeBinary, nullable=True)

    thread = relationship("Thread", back_populates="checkpoint_blobs")
