
from sqlalchemy import Column, ForeignKey, String
from sqlalchemy.orm import relationship

from app.db_models.base_entity import BaseEntity


class ApiKey(BaseEntity):
    __tablename__ = "apikeys"

    # Encrypted version of the API key
    hashed_key = Column(String, nullable=False)

    # Short version or alias of the API key
    short_key = Column(String, nullable=False)

    # Description of the API key, can be None
    description = Column(String, nullable=False)

    # Foreign key referencing assistant.id; the assistant owning this API key
    assistant_id = Column(String, ForeignKey("assistant.id"), nullable=False)

    # Relationship to Team model
    assistant = relationship("Assistant", back_populates="apikeys")
