from sqlalchemy import Column, ForeignKey, String

from app.models.base_entity import BaseEntity


class McpAssistant(BaseEntity):
    __tablename__ = "mcp_assistants"

    mcp_id = Column(String, ForeignKey("connected_mcps.id"), nullable=False)
    assistant_id = Column(String, ForeignKey("assistants.id"), nullable=False)
