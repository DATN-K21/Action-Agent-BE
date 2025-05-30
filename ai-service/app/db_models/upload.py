from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    ForeignKey,
    DateTime,
    Enum as SQLEnum, String,
)
from sqlalchemy.orm import relationship

from app.core.enums import UploadStatus
from app.db_models.base_entity import BaseEntity


class Upload(BaseEntity):
    __tablename__ = "uploads"

    user_id: str = Column(String, ForeignKey("users.id"), nullable=False)
    last_modified: datetime = Column(DateTime, nullable=False, default=datetime.now)
    status: str = Column(SQLEnum(UploadStatus), nullable=False)
    chunk_size: int = Column(Integer, nullable=False)
    chunk_overlap: int = Column(Integer, nullable=False)

    name: str | None = Column(String, nullable=True)
    description: str | None = Column(String, nullable=True)
    file_type: str | None = Column(String, nullable=True)
    web_url: str | None = Column(String, nullable=True)

    # Relationships
    user = relationship("User", back_populates="uploads")
    members = relationship(
        "Member",
        secondary="member_uploads_link",  # tên bảng liên kết
        back_populates="uploads",
        cascade="all, delete"
    )
