from typing import Any

from sqlalchemy import Column, ForeignKey, String, Enum, JSON
from sqlalchemy.orm import relationship

from app.core.enums import StorageStrategy
from app.db_models.base_entity import BaseEntity


class Skill(BaseEntity):
    __tablename__ = "skills"

    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    name: str = Column(String, unique=True, nullable=False)
    description: str | None = Column(String, nullable=True)
    icon: str | None = Column(String, nullable=True)
    display_name: str | None = Column(String, nullable=True)
    strategy: StorageStrategy | None = Column(
        Enum(StorageStrategy),
        nullable=True,
        default=StorageStrategy.DEFINITION
    )
    tool_definition: dict[str, Any] | None = Column(JSON, default=dict, nullable=True)
    input_parameters: dict[str, Any] | None = Column(JSON, default=dict, nullable=True)
    credentials: dict[str, Any] | None = Column(JSON, default=dict, nullable=True)

    # Relationships
    user = relationship("User", back_populates="skills")
    members = relationship(
        "Member",
        secondary="member_skills_link",
        back_populates="skills"
    )
