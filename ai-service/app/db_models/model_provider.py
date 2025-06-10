from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.utils.security import security_manager
from app.db_models.base_entity import BaseEntity


class ModelProvider(BaseEntity):
    __tablename__ = "model_providers"

    # Provider name with a max length of 64 characters, cannot be null
    provider_name: Mapped[str] = mapped_column(String(64), nullable=False)

    # Optional base URL string column
    base_url: Mapped[str | None] = mapped_column(String, nullable=True)

    # Optional API key stored as a string (encrypted)
    api_key: Mapped[str | None] = mapped_column(String, nullable=True)

    # Optional icon URL or identifier
    icon: Mapped[str | None] = mapped_column(String, nullable=True)

    # Optional description with max length of 256 characters
    description: Mapped[str | None] = mapped_column(String(256), nullable=True)

    # Relationship to Models table, cascade deletes models when provider is deleted
    models = relationship(
        "Model",
        back_populates="provider",
        cascade="all, delete-orphan"
    )

    @property
    def encrypted_api_key(self) -> str | None:
        """Return the encrypted API key for API responses."""
        if self.api_key:
            return self.api_key  # Already encrypted
        return None

    @property
    def decrypted_api_key(self) -> str | None:
        """Return the decrypted API key for internal business logic."""
        if self.api_key:
            return security_manager.decrypt_api_key(self.api_key)
        return None

    def set_api_key(self, value: str | None) -> None:
        """Set and encrypt the API key."""
        if value:
            self.api_key = security_manager.encrypt_api_key(value)
        else:
            self.api_key = None
