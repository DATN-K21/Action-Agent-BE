from sqlalchemy import Column, ForeignKey, String
from sqlalchemy.orm import relationship

from app.db_models.base_entity import BaseEntity


class Assistant(BaseEntity):
    __tablename__ = "assistants"

    name = Column(String(64), unique=True, nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)

    description = Column(String, nullable=True)
    icon = Column(String, nullable=True)  # Add an icon field for the team

    # Relationships
    user = relationship("User", back_populates="teams")
    members = relationship("Member", back_populates="belongs", cascade="all, delete-orphan")
    threads = relationship("Thread", back_populates="team", cascade="all, delete-orphan")
    graphs = relationship("Graph", back_populates="team", cascade="all, delete-orphan")
    subgraphs = relationship("Subgraph", back_populates="team", cascade="all, delete-orphan")
    apikeys = relationship("ApiKey", back_populates="team", cascade="all, delete-orphan")
