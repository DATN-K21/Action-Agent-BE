from sqlalchemy import Column, ForeignKey, String
from sqlalchemy.orm import relationship

from app.db_models.base_entity import BaseEntity


class McpAssistantLink(BaseEntity):
    __tablename__ = "mcp_assistant_links"

    mcp_id = Column(String, ForeignKey("connected_mcps.id", ondelete="CASCADE"), nullable=False)
    assistant_id = Column(String, ForeignKey("assistants.id", ondelete="CASCADE"), nullable=False)

    # relationship
    assistant = relationship("Assistant", back_populates="mcp_assistant_links", passive_deletes=True)
    mcp = relationship("ConnectedMcp", back_populates="mcp_assistant_links", passive_deletes=True)
