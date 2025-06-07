
from sqlalchemy import JSON, Column, Enum, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.enums import ConnectedServiceType, StorageStrategy
from app.db_models.base_entity import BaseEntity


class Skill(BaseEntity):
    __tablename__ = "skills"

    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    name = Column(String, unique=True, nullable=False)
    description = Column(String, nullable=True)
    icon = Column(String, nullable=True)
    display_name = Column(String, nullable=True)
    strategy = Column(Enum(StorageStrategy), nullable=True, default=StorageStrategy.DEFINITION)
    skill_type = Column(Enum(StorageStrategy), nullable=True, default=StorageStrategy.DEFINITION)
    tool_definition = Column(JSON, default=dict, nullable=True)
    input_parameters = Column(JSON, default=dict, nullable=True)
    credentials = Column(JSON, default=dict, nullable=True)

    reference_type = Column(Enum(ConnectedServiceType), nullable=False, default=ConnectedServiceType.NONE)
    extension_id = Column(String, ForeignKey("connected_extensions.id"), nullable=True)
    mcp_id = Column(String, ForeignKey("connected_mcps.id"), nullable=True)

    # Relationships
    user = relationship("User", back_populates="skills")
    members = relationship(
        "Member",
        secondary="member_skills_link",
        back_populates="skills"
    )
    extension = relationship("ConnectedExtension", back_populates="skills")
    mcp = relationship("ConnectedMcp", back_populates="skills")
