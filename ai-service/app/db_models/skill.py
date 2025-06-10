from sqlalchemy import JSON, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import ConnectedServiceType, StorageStrategy
from app.db_models.base_entity import BaseEntity


class Skill(BaseEntity):
    __tablename__ = "skills"

    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    icon: Mapped[str | None] = mapped_column(String, nullable=True)
    display_name: Mapped[str | None] = mapped_column(String, nullable=True)
    strategy: Mapped[StorageStrategy | None] = mapped_column(Enum(StorageStrategy), nullable=True, default=StorageStrategy.DEFINITION)
    tool_definition: Mapped[dict | None] = mapped_column(JSON, default=dict, nullable=True)
    input_parameters: Mapped[dict | None] = mapped_column(JSON, default=dict, nullable=True)
    credentials: Mapped[dict | None] = mapped_column(JSON, default=dict, nullable=True)

    reference_type: Mapped[ConnectedServiceType] = mapped_column(Enum(ConnectedServiceType), nullable=False, default=ConnectedServiceType.NONE)
    extension_id: Mapped[str | None] = mapped_column(String, ForeignKey("connected_extensions.id"), nullable=True)
    mcp_id: Mapped[str | None] = mapped_column(String, ForeignKey("connected_mcps.id"), nullable=True)

    # Relationships
    user = relationship("User", back_populates="skills")
    members = relationship("Member", secondary="member_skill_links", back_populates="skills")
    extension = relationship("ConnectedExtension", back_populates="skills")
    mcp = relationship("ConnectedMcp", back_populates="skills")
