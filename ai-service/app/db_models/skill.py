
from sqlalchemy import JSON, Column, Enum, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.enums import StorageStrategy
from app.db_models.base_entity import BaseEntity


class Skill(BaseEntity):
    __tablename__ = "skills"

    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    name = Column(String, unique=True, nullable=False)
    description = Column(String, nullable=True)
    icon = Column(String, nullable=True)
    display_name = Column(String, nullable=True)
    strategy = Column(Enum(StorageStrategy), nullable=True, default=StorageStrategy.DEFINITION)
    tool_definition = Column(JSON, default=dict, nullable=True)
    input_parameters = Column(JSON, default=dict, nullable=True)
    credentials = Column(JSON, default=dict, nullable=True)

    # Relationships
    user = relationship("User", back_populates="skills")
    members = relationship(
        "Member",
        secondary="member_skills_link",
        back_populates="skills"
    )
