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

    owner_id = Column(String, ForeignKey("users.id"), nullable=False)
    last_modified = Column(DateTime, nullable=False, default=datetime.now)
    status = Column(SQLEnum(UploadStatus), nullable=False)
    chunk_size = Column(Integer, nullable=False)
    chunk_overlap = Column(Integer, nullable=False)

    # Relationships
    owner = relationship("User", back_populates="uploads")
    members = relationship(
        "Member",
        secondary="member_uploads_link",  # tên bảng liên kết
        back_populates="uploads",
        cascade="all, delete"
    )
