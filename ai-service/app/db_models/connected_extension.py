from sqlalchemy import Enum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import ConnectionStatus
from app.db_models.base_entity import BaseEntity


class ConnectedExtension(BaseEntity):
    """
    Represents a connected application for a user. This model stores information about the user's connected applications,
    including the application name, account ID, and authentication details.
    """
    __tablename__ = "connected_extensions"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    extension_enum: Mapped[str] = mapped_column(nullable=False, unique=True)
    extension_name: Mapped[str] = mapped_column(nullable=False)
    connection_status: Mapped[ConnectionStatus] = mapped_column(Enum(ConnectionStatus), nullable=False, default=ConnectionStatus.PENDING)
    connected_account_id: Mapped[str | None] = mapped_column(nullable=True)
    auth_value: Mapped[str | None] = mapped_column(nullable=True)
    auth_scheme: Mapped[str | None] = mapped_column(nullable=True)

    # Relationships
    skills = relationship("Skill", back_populates="extension", cascade="all, delete-orphan", passive_deletes=True)