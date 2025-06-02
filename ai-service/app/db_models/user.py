from sqlalchemy import Column, ForeignKey, Index, Integer, String
from sqlalchemy.orm import relationship

from app.db_models.base_entity import BaseEntity


class User(BaseEntity):
    """
    Represents a user in the application. This model stores information about the user's username,
    email, first name, last name, and other related attributes. It is used to manage user accounts
    and their associated data within the application.
    """
    __tablename__ = "users"

    username = Column(String, unique=True, nullable=False, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    language = Column(String, default="en-US")

    default_api_key_id = Column(String, ForeignKey("user_api_keys.id", ondelete="SET NULL"), nullable=True)
    remain_trial_tokens = Column(Integer, nullable=False, default=0)

    assistants = relationship("Assistant", back_populates="user")
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
