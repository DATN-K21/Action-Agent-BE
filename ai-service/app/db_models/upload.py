from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy import (
    Enum as SQLEnum,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import UploadStatus
from app.db_models.base_entity import BaseEntity


class Upload(BaseEntity):
    __tablename__ = "uploads"

    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), nullable=False)
    last_modified: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now)
    status: Mapped[UploadStatus] = mapped_column(SQLEnum(UploadStatus), nullable=False)
    chunk_size: Mapped[int] = mapped_column(Integer, nullable=False)
    chunk_overlap: Mapped[int] = mapped_column(Integer, nullable=False)

    name: Mapped[str | None] = mapped_column(String, nullable=True)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    file_type: Mapped[str | None] = mapped_column(String, nullable=True)
    web_url: Mapped[str | None] = mapped_column(String, nullable=True)

    thread_id: Mapped[str | None] = mapped_column(String, ForeignKey("threads.id", ondelete="CASCADE"), nullable=True)
    is_global: Mapped[bool] = mapped_column(default=True, nullable=False)
    failed_reason: Mapped[str | None] = mapped_column(String, nullable=True)

    # Relationships
    thread = relationship("Thread", back_populates="uploads")
    user = relationship("User", back_populates="uploads")
    members = relationship("Member", secondary="member_upload_links", back_populates="uploads")
