from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.orm import relationship

from app.core.models import TeamBase
from app.db_models.base_entity import BaseEntity


class Team(TeamBase, BaseEntity):
    __tablename__ = "teams"

    name = Column(String(64), unique=True, nullable=False)
    owner_id = Column(String, ForeignKey("users.id"), nullable=False)

    # Relationships
    owner = relationship("User", back_populates="teams")
    members = relationship(
        "Member",
        back_populates="belongs",
        cascade="all, delete-orphan"
    )
    workflow = Column(String, nullable=False)
    threads = relationship(
        "Thread",
        back_populates="team",
        cascade="all, delete-orphan"
    )
    graphs = relationship(
        "Graph",
        back_populates="team",
        cascade="all, delete-orphan"
    )
    subgraphs = relationship(
        "Subgraph",
        back_populates="team",
        cascade="all, delete-orphan"
    )
    apikeys = relationship(
        "ApiKey",
        back_populates="team",
        cascade="all, delete-orphan"
    )
