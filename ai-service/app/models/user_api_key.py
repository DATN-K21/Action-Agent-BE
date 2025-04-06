from sqlalchemy import Column, ForeignKey, Index, Integer, String

from app.models.base_entity import BaseEntity


class UserApiKey(BaseEntity):
    __tablename__ = "user_api_keys"

    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    provider = Column(Integer, nullable=False)
    encrypted_value = Column(String, nullable=False)

    __table_args__ = (
        Index(
            "idx_user_api_keys_user_id_provider",
            "user_id",
            "provider",
            unique=True,
        ),
    )
