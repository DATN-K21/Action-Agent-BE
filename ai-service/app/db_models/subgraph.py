from typing import Any

from sqlalchemy import Column, ForeignKey, DateTime, func, String, Boolean
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.db_models.base_entity import BaseEntity  # Adjust according to your project structure


class Subgraph(BaseEntity):
    __tablename__ = "subgraphs"

    user_id: str = Column(String, ForeignKey("users.id"), nullable=False)
    team_id: str = Column(String, ForeignKey("teams.id"), nullable=False)
    name: str | None = Column(String, nullable=True)
    description: str | None = Column(String, nullable=True)
    config: dict[Any, Any] = Column(JSONB, nullable=False, default=dict)
    metadata_: dict[Any, Any] = Column(JSONB, nullable=False, default=dict)
    is_public: bool = Column(Boolean, nullable=False, default=False)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=func.now(),
        server_default=func.now(),
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=func.now(),
        onupdate=func.now(),
        server_default=func.now(),
    )

    # Relationships
    user = relationship("User", back_populates="subgraphs")
    team = relationship("Team", back_populates="subgraphs")
