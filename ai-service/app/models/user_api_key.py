from sqlalchemy import Column, ForeignKey, Index, String

from app.models.base_entity import BaseEntity


class UserApiKey(BaseEntity):
    """
    Represents an API key associated with a user. This model stores the user's ID, the provider of the API key,
    and the encrypted value of the API key. It is used to manage and store API keys securely for different providers.
    """
    __tablename__ = "user_api_keys"

    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    provider = Column(String, nullable=False)
    encrypted_value = Column(String, nullable=False)

    __table_args__ = (
        Index(
            "idx_user_api_keys_user_id_provider",
            "user_id",
            "provider",
            unique=True,
        ),
    )
