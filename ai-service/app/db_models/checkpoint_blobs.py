from sqlalchemy import (
    Column,
    ForeignKey,
    LargeBinary,
    PrimaryKeyConstraint,
    String,
)
from sqlalchemy.orm import relationship

from app.db_models.base_entity import Base


class CheckpointBlobs(Base):
    __tablename__ = "checkpoint_blobs"
    __table_args__ = PrimaryKeyConstraint("thread_id", "checkpoint_ns", "channel", "version")

    thread_id = Column(String, ForeignKey("threads.id"), primary_key=True)
    checkpoint_ns = Column(String, nullable=False, server_default="", primary_key=True)
    channel = Column(String, primary_key=True)
    version = Column(String, primary_key=True)
    type = Column(String, nullable=False)
    blob = Column(LargeBinary, nullable=True)

    thread = relationship("Thread", back_populates="checkpoint_blobs")
