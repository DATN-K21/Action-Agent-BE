from sqlalchemy import Column, ForeignKey, Index, String

from app.models.base_entity import BaseEntity


class Thread(BaseEntity):
    __tablename__ = "threads"

    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=True)
    thread_type = Column(String, nullable=True)

    __table_args__ = (
        Index("idx_threads_user_id_title", "user_id", "title"),  # Ensure it's a tuple
    )
