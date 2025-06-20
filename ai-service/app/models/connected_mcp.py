from sqlalchemy import Column, ForeignKey, String
from sqlalchemy.orm import relationship

from app.models.base_entity import BaseEntity


class ConnectedMcp(BaseEntity):
    __tablename__ = "connected_mcps"

    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    mcp_name = Column(String, nullable=False)
    url = Column(String, nullable=False)
    connection_type = Column(String, nullable=False, default="sse")

    mcp_assistants = relationship(
        "McpAssistant",
        back_populates="mcp",
        cascade="all, delete-orphan",
        passive_deletes=True
    )
