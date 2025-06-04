
from sqlalchemy import Column, DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.db_models.base_entity import BaseEntity  # Adjust if needed


class Graph(BaseEntity):
    __tablename__ = "graphs"

    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    team_id = Column(String, ForeignKey("teams.id"), nullable=False)
    name = Column(String, nullable=False, unique=True)
    description = Column(String, nullable=True)
    config = Column(JSONB, nullable=False, server_default="{}")
    metadata_ = Column(JSONB, nullable=False, server_default="{}")
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=func.now(),
        server_default=func.now(),
    )

    # Timestamp for last update time, automatically updated on change
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=func.now(),
        onupdate=func.now(),
        server_default=func.now(),
    )

    # Relationships
    user = relationship("User", back_populates="graphs")
    team = relationship("Team", back_populates="graphs")
