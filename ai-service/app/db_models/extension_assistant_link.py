from sqlalchemy import Column, ForeignKey, String
from sqlalchemy.orm import relationship

from app.db_models.base_entity import BaseEntity


class ExtensionAssistantLink(BaseEntity):
    __tablename__ = "extension_assistant_links"

    extension_id = Column(String, ForeignKey("connected_extensions.id", ondelete="CASCADE"), nullable=False)
    assistant_id = Column(String, ForeignKey("assistants.id", ondelete="CASCADE"), nullable=False)

    # relationships
    assistant = relationship("Assistant", back_populates="extension_assistant_links", passive_deletes=True)
    extension = relationship("ConnectedExtension", back_populates="extension_assistant_links", passive_deletes=True)
