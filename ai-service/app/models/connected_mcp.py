from sqlalchemy import Column, ForeignKey, String

from app.models.base_entity import BaseEntity


class ConnectedMcp(BaseEntity):
    __tablename__ = "connected_mcps"

    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    mcp_name = Column(String, nullable=False)
    url = Column(String, nullable=False)
    connection_type = Column(String, nullable=False, default="sse")
