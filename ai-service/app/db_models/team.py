from sqlalchemy import Column, Enum, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.enums import WorkflowType
from app.db_models.base_entity import BaseEntity


class Team(BaseEntity):
    __tablename__ = "teams"

    name = Column(String, unique=True, nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)

    description = Column(String, nullable=True)
    icon = Column(String, nullable=True)  # Add an icon field for the team

    # Hierarchical is base workflow for advanced assistants
    workflow_type = Column(Enum(WorkflowType), nullable=False, default=WorkflowType.HIERARCHICAL)  # Default workflow type

    # Relationships
    user = relationship("User", back_populates="teams")
    members = relationship("Member", back_populates="team", cascade="all, delete-orphan")
    graphs = relationship("Graph", back_populates="team", cascade="all, delete-orphan")
    subgraphs = relationship("Subgraph", back_populates="team", cascade="all, delete-orphan")
    apikeys = relationship("ApiKey", back_populates="team", cascade="all, delete-orphan")
    assistant = relationship("Assistant", secondary="team_assistant_links", back_populates="teams", cascade="all, delete-orphan")
