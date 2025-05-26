from sqlalchemy import Column, ForeignKey, String
from sqlalchemy.orm import relationship

from app.db_models.base_entity import BaseEntity


class McpAssistant(BaseEntity):
    __tablename__ = "mcp_assistants"

    mcp_id = Column(String, ForeignKey("connected_mcps.id", ondelete="CASCADE"), nullable=False)
    assistant_id = Column(String, ForeignKey("assistants.id", ondelete="CASCADE"), nullable=False)

    # relationship with the Assistant model
    assistant = relationship("Assistant", back_populates="mcp_assistants", passive_deletes=True)
    # relationship with the ConnectedApp model
    mcp = relationship("ConnectedMcp", back_populates="mcp_assistants", passive_deletes=True)
