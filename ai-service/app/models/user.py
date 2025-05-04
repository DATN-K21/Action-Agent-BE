from sqlalchemy import Column, ForeignKey, Index, Integer, String

from app.models.base_entity import BaseEntity


class User(BaseEntity):
    """
    Represents a user in the application. This model stores information about the user's username,
    email, first name, last name, and other related attributes. It is used to manage user accounts
    and their associated data within the application.
    """
    __tablename__ = "users"

    username = Column(String, unique=True, nullable=False, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)

    default_api_key_id = Column(String, ForeignKey("user_api_keys.id", ondelete="SET NULL"), nullable=True)
    remain_trial_tokens = Column(Integer, nullable=False, default=0)

    # threads = relationship(
    #     "Thread",
    #     back_populates="user",
    #     cascade="all, delete-orphan",
    #     passive_deletes=True
    # )
    #
    # connected_apps = relationship(
    #     "ConnectedApp",
    #     back_populates="user",
    #     cascade="all, delete-orphan",
    #     passive_deletes=True
    # )
    #
    # connected_mcps = relationship(
    #     "ConnectedMcp",
    #     back_populates="user",
    #     cascade="all, delete-orphan",
    #     passive_deletes=True
    # )
    #
    # assistants = relationship(
    #     "Assistant",
    #     back_populates="user",
    #     cascade="all, delete-orphan",
    #     passive_deletes=True
    # )

    __table_args__ = (
        Index(
            "idx_users_username_email",
            "username",
            "email",
            unique=True,
        ),
    )
