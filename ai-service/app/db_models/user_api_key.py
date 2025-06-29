from sqlalchemy import ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column

from app.db_models.base_entity import BaseEntity


class UserApiKey(BaseEntity):
    """
    Represents an API key associated with a user. This model stores the user's ID, the provider of the API key,
    and the encrypted value of the API key. It is used to manage and store API keys securely for different providers.
    """
    __tablename__ = "user_api_keys"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    provider: Mapped[str] = mapped_column(nullable=False)
    encrypted_value: Mapped[str] = mapped_column(nullable=False)

    __table_args__ = (
        Index(
            "idx_user_api_keys_user_id_provider",
            "user_id",
            "provider",
            unique=True,
        ),
    )
