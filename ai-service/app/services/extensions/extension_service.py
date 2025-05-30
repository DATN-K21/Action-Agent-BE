from typing import Any

from pydantic import BaseModel, Field

from app.core import logging

logger = logging.get_logger(__name__)


class ExtensionServiceInfo(BaseModel):
    """
    Holds information about a specific extension service.
    """
    name: str = Field(..., description="The unique identifier name for the service (e.g., 'Maps_directions_api').")
    display_name: str | None = Field(None,
                                     description="A human-readable name for the service (e.g., 'Google Maps Directions API').")
    description: str | None = Field(None, description="A brief description of what the service does.")
    # The actual service object or client. This could be an instantiated class,
    # a function, or any other relevant Python object.
    tool_service_object: Any = Field(None,
                                     description="The actual service instance or a callable to interact with the service.")
    version: str = "1.0"


class ExtensionService:
    """
    Connect to the Extension Service (Extension service container)
    and get information about the available services.
    """

    def __init__(self, service_info: ExtensionServiceInfo):
        pass
