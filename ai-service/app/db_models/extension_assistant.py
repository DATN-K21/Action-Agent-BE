from sqlalchemy import Column, ForeignKey, String
from sqlalchemy.orm import relationship

from app.db_models.base_entity import BaseEntity


class ExtensionAssistant(BaseEntity):
    __tablename__ = "extension_assistants"

    extension_id = Column(String, ForeignKey("connected_extensions.id", ondelete="CASCADE"), nullable=False)
    assistant_id = Column(String, ForeignKey("assistants.id", ondelete="CASCADE"), nullable=False)

    # relationship with the Assistant model
    assistant = relationship("Assistant", back_populates="extension_assistants", passive_deletes=True)
    # relationship with the ConnectedApp model
    extension = relationship("ConnectedExtension", back_populates="extension_assistants", passive_deletes=True)
