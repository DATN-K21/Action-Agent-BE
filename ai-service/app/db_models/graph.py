from sqlalchemy import Column, ForeignKey, DateTime, func, String
from sqlalchemy.orm import relationship

from app.db_models.base_entity import BaseEntity  # Adjust if needed


class Graph(BaseEntity):
    __tablename__ = "graphs"

    # Foreign key referencing user.id; the owner of the graph
    owner_id = Column(String, ForeignKey("users.id"), nullable=False)

    # Relationship to User model for the owner
    owner = relationship("User", back_populates="graphs")

    # Foreign key referencing team.id; the team this graph belongs to
    team_id = Column(String, ForeignKey("teams.id"), nullable=False)

    # Relationship to Team model
    team = relationship("Team", back_populates="graphs")

    # Timestamp for creation time, automatically set by the DB
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
