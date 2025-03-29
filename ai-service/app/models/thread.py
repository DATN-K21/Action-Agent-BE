from sqlalchemy import Column, ForeignKey, String

from app.models.base_entity import BaseEntity


class Thread(BaseEntity):
    __tablename__ = "threads"

    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=True)
    thread_type = Column(String, nullable=True)
