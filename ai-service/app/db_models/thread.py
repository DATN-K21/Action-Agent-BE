from sqlalchemy import Column, ForeignKey, String, Enum as SQLEnum
from sqlalchemy.orm import relationship

from app.core.enums import ThreadType
from app.db_models.base_entity import BaseEntity


class Thread(BaseEntity):
    """
    Represents a thread in the application. This model stores information about the thread's title,
    type, and the user who created it. Threads can be used to organize conversations or discussions
    within the application.
    """
    __tablename__ = "threads"

    user_id: str = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title: str | None = Column(String, nullable=True)
    thread_type: str | None = Column(SQLEnum(ThreadType), nullable=True)
    assistant_id: str | None = Column(String, ForeignKey("assistants.id"), nullable=True)
    team_id: str | None = Column(String, ForeignKey("teams.id"), nullable=True)
    query: str | None = Column(String, nullable=True)

    # Relationships
    team = relationship("Team", back_populates="threads")
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
