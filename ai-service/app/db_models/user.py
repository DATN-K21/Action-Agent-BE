from sqlalchemy import ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db_models.base_entity import BaseEntity


class User(BaseEntity):
    """
    Represents a user in the application. This model stores information about the user's username,
    email, first name, last name, and other related attributes. It is used to manage user accounts
    and their associated data within the application.
    """
    __tablename__ = "users"

    username: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    first_name: Mapped[str | None] = mapped_column(String, nullable=True)
    last_name: Mapped[str | None] = mapped_column(String, nullable=True)
    language: Mapped[str] = mapped_column(String, default="en-US")

    default_api_key_id: Mapped[str | None] = mapped_column(String, ForeignKey("user_api_keys.id", ondelete="SET NULL"), nullable=True)
    remain_trial_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    assistants = relationship("Assistant", back_populates="user")
    teams = relationship("Team", back_populates="user")
    skills = relationship("Skill", back_populates="user")
    uploads = relationship("Upload", back_populates="user")
    graphs = relationship("Graph", back_populates="user")
    subgraphs = relationship("Subgraph", back_populates="user")

    __table_args__ = (
        Index(
            "idx_users_username_email",
            "username",
            "email",
            unique=True,
        ),
    )
