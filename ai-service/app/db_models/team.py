from typing import Optional

from sqlalchemy import Enum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import WorkflowType
from app.db_models.base_entity import BaseEntity


class Team(BaseEntity):
    __tablename__ = "teams"

    name: Mapped[str] = mapped_column(unique=True, nullable=False)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    assistant_id: Mapped[Optional[str]] = mapped_column(ForeignKey("assistants.id"), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(nullable=True)
    icon: Mapped[Optional[str]] = mapped_column(nullable=True)
    workflow_type: Mapped[WorkflowType] = mapped_column(Enum(WorkflowType), nullable=False, default=WorkflowType.HIERARCHICAL)

    # Relationships
    user = relationship("User", back_populates="teams")
    members = relationship("Member", back_populates="team", cascade="all, delete-orphan")
    graphs = relationship("Graph", back_populates="team", cascade="all, delete-orphan")
    subgraphs = relationship("Subgraph", back_populates="team", cascade="all, delete-orphan")
    apikeys = relationship("ApiKey", back_populates="team", cascade="all, delete-orphan")
    assistant = relationship("Assistant", back_populates="teams")
