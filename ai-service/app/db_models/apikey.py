
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db_models.base_entity import BaseEntity

if TYPE_CHECKING:
    pass


class ApiKey(BaseEntity):
    __tablename__ = "api_keys"

    # Encrypted version of the API key
    hashed_key: Mapped[str] = mapped_column(nullable=False)

    # Short version or alias of the API key
    short_key: Mapped[str] = mapped_column(nullable=False)

    # Description of the API key, can be None
    description: Mapped[str] = mapped_column(nullable=False)

    # Foreign key referencing team.id
    team_id: Mapped[str] = mapped_column(ForeignKey("teams.id"), nullable=False)  # Relationship to Team model

    team = relationship("Team", back_populates="apikeys")
