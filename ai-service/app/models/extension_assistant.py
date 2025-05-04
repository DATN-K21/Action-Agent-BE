from sqlalchemy import Column, ForeignKey, String

from app.models.base_entity import BaseEntity


class ExtensionAssistant(BaseEntity):
    __tablename__ = "extension_assistants"

    extension_id = Column(String, ForeignKey("connected_apps.id"), nullable=False)
    assistant_id = Column(String, ForeignKey("assistants.id"), nullable=False)
