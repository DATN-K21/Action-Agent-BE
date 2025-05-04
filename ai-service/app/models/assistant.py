from sqlalchemy import Column, ForeignKey, String

from app.models.base_entity import BaseEntity


class Assistant(BaseEntity):
    __tablename__ = "assistants"

    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    type = Column(String, nullable=False)

    # extension_assistants = relationship(
    #     "ExtensionAssistant",
    #     back_populates="assistant",
    #     cascade="all, delete-orphan",
    #     passive_deletes=True
    # )
    #
    # mcp_assistants = relationship(
    #     "McpAssistant",
    #     back_populates="assistant",
    #     cascade="all, delete-orphan",
    #     passive_deletes=True
    # )
