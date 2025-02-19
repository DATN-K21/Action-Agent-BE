from sqlalchemy import Column, Index, String

from app.models.base_entity import BaseEntity


class User(BaseEntity):
    __tablename__ = "users"

    username = Column(String, unique=True, nullable=False, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)

    __table_args__ = (
        Index("idx_users_username_email", "username", "email"),  # Ensure it's a tuple
    )
