from sqlalchemy import Column, ForeignKey, String

from app.db_models.base_entity import BaseEntity


class ConnectedApp(BaseEntity):
    """
    Represents a connected application for a user. This model stores information about the user's connected applications,
    including the application name, account ID, and authentication details.
    """
    __tablename__ = "connected_apps"

    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    app_name = Column(String, nullable=False)
    connected_account_id = Column(String, nullable=False)
    auth_value = Column(String, nullable=True)
    auth_scheme = Column(String, nullable=True)
