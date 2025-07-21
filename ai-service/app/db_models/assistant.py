from sqlalchemy import Enum, ForeignKey, String
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

    # Confiugration actions for the advanced assistant (Only for advanced assistants - hierarchical units)
    ask_human: Mapped[bool | None] = mapped_column(
        default=False,
        nullable=True,
    )  # Whether to ask human for confirmation before executing the assistant's task
    interrupt: Mapped[bool | None] = mapped_column(default=False, nullable=True)  # Whether to interrupt the assistant's current task
    scheduler_enabled: Mapped[bool | None] = mapped_column(
        default=False,
        nullable=True,
    )  # Whether scheduler functionality is enabled for this assistant
    retrieval_interrupt_skip_enabled: Mapped[bool | None] = mapped_column(
        default=False,
        nullable=True,
    )  # Whether to skip retrieval interrupt for this assistant
    local_llm_enabled: Mapped[bool | None] = mapped_column(
        default=False,
        nullable=True,
    )  # Whether to use local LLM for this assistant

    # Relationships
    user = relationship("User", back_populates="assistants")
    threads = relationship("Thread", back_populates="assistant", cascade="all, delete-orphan")
    teams = relationship("Team", back_populates="assistant")
