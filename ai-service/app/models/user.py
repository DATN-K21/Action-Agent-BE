from sqlalchemy import Column, ForeignKey, Index, Integer, String

from app.models.base_entity import BaseEntity


class User(BaseEntity):
    __tablename__ = "users"

    username = Column(String, unique=True, nullable=False, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)

    default_api_key_id = Column(String, ForeignKey("user_api_keys.id", ondelete="SET NULL"), nullable=True)
    remain_trial_tokens = Column(Integer, nullable=False, default=0)

    __table_args__ = (
        Index(
            "idx_users_username_email",
            "username",
            "email",
            unique=True,
        ),
    )
