from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy import (
    Enum as SQLEnum,
)
from sqlalchemy.orm import relationship

from app.core.enums import UploadStatus
from app.db_models.base_entity import BaseEntity


class Upload(BaseEntity):
    __tablename__ = "uploads"

    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    last_modified = Column(DateTime, nullable=False, default=datetime.now)
    status = Column(SQLEnum(UploadStatus), nullable=False)
    chunk_size = Column(Integer, nullable=False)
    chunk_overlap = Column(Integer, nullable=False)

    name = Column(String, nullable=True)
    description = Column(String, nullable=True)
    file_type = Column(String, nullable=True)
    web_url = Column(String, nullable=True)

    # Relationships
    user = relationship("User", back_populates="uploads")
    members = relationship("Member", secondary="member_uploads_link", back_populates="uploads", cascade="all, delete")
    thread = relationship(
        "Thread",
        secondary="upload_thread_links",
        back_populates="uploads",
        cascade="all, delete",
    )
