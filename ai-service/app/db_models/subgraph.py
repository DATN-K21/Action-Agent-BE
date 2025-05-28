from sqlalchemy import Column, ForeignKey, DateTime, func, String
from sqlalchemy.orm import relationship

from app.db_models.base_entity import BaseEntity  # Adjust according to your project structure


class Subgraph(BaseEntity):
    __tablename__ = "subgraphs"

    # Foreign key referencing the user who owns this subgraph
    owner_id = Column(String, ForeignKey("users.id"), nullable=False)

    # Relationship to User model
    owner = relationship("User", back_populates="subgraphs")

    # Foreign key referencing the team this subgraph belongs to
    team_id = Column(String, ForeignKey("teams.id"), nullable=False)

    # Relationship to Team model
    team = relationship("Team", back_populates="subgraphs")

    # Timestamp when the subgraph was created, default to current time in DB server timezone
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=func.now(),
        server_default=func.now(),
    )

    # Timestamp when the subgraph was last updated, auto-updated on each change
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=func.now(),
        onupdate=func.now(),
        server_default=func.now(),
    )
