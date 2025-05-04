from sqlalchemy import Column, ForeignKey, String

from app.models.base_entity import BaseEntity


class Assistant(BaseEntity):
    __tablename__ = "assistants"

    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    type = Column(String, nullable=False)
