from sqlalchemy import Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import McpTransport
from app.db_models.base_entity import BaseEntity


class ConnectedMcp(BaseEntity):
    __tablename__ = "connected_mcps"

    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    mcp_name: Mapped[str] = mapped_column(String, nullable=False)
    url: Mapped[str] = mapped_column(String, nullable=False)
    transport: Mapped[McpTransport] = mapped_column(Enum(McpTransport), nullable=False, default=McpTransport.STREAMABLE_HTTP)
    description: Mapped[str | None] = mapped_column(String, nullable=True)

    # Relationships
    skills = relationship("Skill", back_populates="mcp", cascade="all, delete-orphan", passive_deletes=True)