from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy import Column, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship

from app.db_models.base_entity import BaseEntity


class ApiKey(BaseEntity):
    __tablename__ = "apikeys"

    # Hashed version of the API key
    hashed_key: str = Column(String, nullable=False)

    # Short version or alias of the API key
    short_key: str = Column(String, nullable=False)

    # Foreign key referencing team.id; the team owning this API key
    team_id: str = Column(String, ForeignKey("teams.id"), nullable=False)

    # Description of the API key, can be None
    description: str | None = Column(String, nullable=False)

    # Timestamp when the API key was created, default to current UTC time
    created_at: datetime | None = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(ZoneInfo("UTC")),
    )

    # Relationship to Team model
    team = relationship("Team", back_populates="apikeys")
