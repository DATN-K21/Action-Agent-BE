from sqlalchemy import Column, Enum, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.enums import AssistantType
from app.db_models.base_entity import BaseEntity


class Assistant(BaseEntity):
    __tablename__ = "assistants"

    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    system_prompt = Column(String, nullable=True)

    # Only have one general assistant per user
    assistant_type = Column(Enum(AssistantType), nullable=False, default=AssistantType.ADVANCED_ASSISTANT)

    # Relationships
    threads = relationship("Thread", back_populates="assistant", cascade="all, delete-orphan")
    apiKeys = relationship("ApiKey", back_populates="assistant", cascade="all, delete-orphan")
    teams = relationship("Team", secondary="team_assistant_links", back_populates="assistant", cascade="all, delete-orphan")
