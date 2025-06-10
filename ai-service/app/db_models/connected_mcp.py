from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db_models.base_entity import BaseEntity


class ConnectedMcp(BaseEntity):
    __tablename__ = "connected_mcps"

    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    mcp_name: Mapped[str] = mapped_column(String, nullable=False)
    url: Mapped[str] = mapped_column(String, nullable=False)
    transport: Mapped[str] = mapped_column(String, nullable=False, default="sse")
    description: Mapped[str | None] = mapped_column(String, nullable=True)

    # Relationships
    skills = relationship("Skill", back_populates="mcp", cascade="all, delete-orphan", passive_deletes=True)