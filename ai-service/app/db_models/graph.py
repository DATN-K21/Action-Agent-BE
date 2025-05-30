from datetime import datetime
from typing import Any

from sqlalchemy import Column, ForeignKey, DateTime, func, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.db_models.base_entity import BaseEntity  # Adjust if needed


class Graph(BaseEntity):
    __tablename__ = "graphs"

    user_id: str = Column(String, ForeignKey("users.id"), nullable=False)
    team_id: str = Column(String, ForeignKey("teams.id"), nullable=False)
    name = Column(String(64), nullable=False, unique=True)
    description: str | None = Column(String, nullable=True)
    config: dict[Any, Any] = Column(JSONB, nullable=False, server_default="{}")
    metadata_: dict[Any, Any] = Column(JSONB, nullable=False, server_default="{}")
    created_at: datetime = Column(
        DateTime(timezone=True),
        nullable=False,
        default=func.now(),
        server_default=func.now(),
    )

    # Timestamp for last update time, automatically updated on change
    updated_at: datetime = Column(
        DateTime(timezone=True),
        nullable=False,
        default=func.now(),
        onupdate=func.now(),
        server_default=func.now(),
    )

    # Relationships
    user = relationship("User", back_populates="graphs")
    team = relationship("Team", back_populates="graphs")
