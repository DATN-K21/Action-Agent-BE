from sqlalchemy import Enum, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import AssistantType
from app.db_models.base_entity import BaseEntity


class Assistant(BaseEntity):
    __tablename__ = "assistants"

    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    system_prompt: Mapped[str | None] = mapped_column(String, nullable=True)

    # Only have one general assistant per user
    assistant_type: Mapped[AssistantType] = mapped_column(Enum(AssistantType), nullable=False, default=AssistantType.ADVANCED_ASSISTANT)

    # Configuration for the assistant
    provider: Mapped[str | None] = mapped_column(String, nullable=True)  # e.g., 'openai', 'anthropic'
    model_name: Mapped[str | None] = mapped_column(String, nullable=True)  # Name of the model to use with the assistant
    temperature: Mapped[float | None] = mapped_column(Float, nullable=True)  # Controls randomness of the output, e.g., '0.7'

    # Relationships
    user = relationship("User", back_populates="assistants")
    threads = relationship("Thread", back_populates="assistant", cascade="all, delete-orphan")
    teams = relationship("Team", secondary="team_assistant_links", back_populates="assistant")
