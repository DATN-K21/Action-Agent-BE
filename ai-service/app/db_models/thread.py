from sqlalchemy import Column, ForeignKey, String
from sqlalchemy.orm import relationship

from app.db_models.base_entity import BaseEntity
from app.db_models.upload_thread_link import UploadThreadLink


class Thread(BaseEntity):
    """
    Represents a thread in the application. This model stores information about the thread's title,
    type, and the user who created it. Threads can be used to organize conversations or discussions
    within the application.
    """
    __tablename__ = "threads"

    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String, nullable=True)
    assistant_id = Column(String, ForeignKey("assistants.id"), nullable=True)

    # Relationships
    assistant = relationship("Assistant", back_populates="threads")
    checkpoints = relationship(
        "Checkpoint",
        back_populates="thread",
        cascade="all, delete-orphan"
    )
    checkpoint_blobs = relationship(
        "CheckpointBlobs",
        back_populates="thread",
        cascade="all, delete-orphan"
    )
    writes = relationship(
        "Write",
        back_populates="thread",
        cascade="all, delete-orphan"
    )
    uploads = relationship("Upload", secondary=UploadThreadLink.__tablename__, back_populates="threads", cascade="all, delete")
