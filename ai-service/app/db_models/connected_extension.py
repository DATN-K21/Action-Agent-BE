from sqlalchemy import Column, Enum, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.enums import ConnectionStatus
from app.db_models.base_entity import BaseEntity


class ConnectedExtension(BaseEntity):
    """
    Represents a connected application for a user. This model stores information about the user's connected applications,
    including the application name, account ID, and authentication details.
    """
    __tablename__ = "connected_extensions"

    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    extension_enum = Column(String, nullable=False, unique=True)
    extension_name = Column(String, nullable=False)
    connection_status = Column(Enum(ConnectionStatus), nullable=False, default=ConnectionStatus.PENDING)
    connected_account_id = Column(String, nullable=True)
    auth_value = Column(String, nullable=True)
    auth_scheme = Column(String, nullable=True)

    # Relationships
    skills = relationship("Skill", back_populates="extension", cascade="all, delete-orphan", passive_deletes=True)