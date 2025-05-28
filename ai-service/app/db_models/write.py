from sqlalchemy import (
    Column,
    String,
    Integer,
    LargeBinary,
    PrimaryKeyConstraint,
    ForeignKey,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db_models.base_entity import Base


class Write(Base):
    __tablename__ = "checkpoint_writes"
    __table_args__ = (
        PrimaryKeyConstraint(
            "thread_id", "checkpoint_ns", "checkpoint_id", "task_id", "idx"
        ),
    )

    thread_id = Column(String, ForeignKey("threads.id"), primary_key=True)
    checkpoint_ns = Column(String, nullable=False, server_default="", primary_key=True)
    checkpoint_id = Column(UUID(as_uuid=True), primary_key=True)
    task_id = Column(UUID(as_uuid=True), primary_key=True)
    idx = Column(Integer, primary_key=True)

    channel = Column(String, nullable=False)
    type = Column(String, nullable=True)
    blob = Column(LargeBinary, nullable=False)

    thread = relationship("Thread", back_populates="writes")
