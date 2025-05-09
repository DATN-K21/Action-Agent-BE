from sqlalchemy import Boolean, Column, String
from sqlalchemy.dialects.postgresql import ARRAY

from app.models.base_entity import BaseEntity


class BuiltinAgent(BaseEntity):
    """
    Represents an agent in the application. This model stores information about the agent's name,
    description, and the user who created it. Agents can be used to automate tasks or provide
    assistance within the application.
    """
    __tablename__ = "builtin_agents"

    name = Column(String, nullable=False, unique=True)
    description = Column(String, nullable=True)
    image_url = Column(String, nullable=True)
    tools = Column(ARRAY(String), nullable=True)
    is_public = Column(Boolean, nullable=False, default="False")


class CustomAgent(BaseEntity):
    """
    Represents a custom agent in the application. This model stores information about the agent's
    name, description, and the user who created it. Custom agents can be used to automate tasks or
    provide assistance within the application.
    """
    __tablename__ = "custom_agents"

    name = Column(String, nullable=False, unique=True)
    description = Column(String, nullable=True)
    image_url = Column(String, nullable=True)
    tools = Column(ARRAY(String), nullable=True)
    child_agents = Column(ARRAY(String), nullable=True)
