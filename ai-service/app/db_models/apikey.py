
from sqlalchemy import Column, ForeignKey, String
from sqlalchemy.orm import relationship

from app.db_models.base_entity import BaseEntity


class ApiKey(BaseEntity):
    __tablename__ = "api_keys"

    # Encrypted version of the API key
    hashed_key = Column(String, nullable=False)

    # Short version or alias of the API key
    short_key = Column(String, nullable=False)

    # Description of the API key, can be None
    description = Column(String, nullable=False)

    # Foreign key referencing team.id
    team_id = Column(String, ForeignKey("teams.id"), nullable=False)

    # Relationship to Team model
    team = relationship("Team", back_populates="apikeys")
