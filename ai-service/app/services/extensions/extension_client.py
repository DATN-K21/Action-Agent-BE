from typing import Dict, List, Optional

import httpx
from composio import App
from composio_langgraph import Action
from pydantic import BaseModel, ConfigDict, Field

from app.core import logging
from app.core.settings import env_settings
from app.services.extensions.extension_service import ExtensionService

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
    service_object: ExtensionService | None = Field(None, description="The actual service instance or a callable to interact with the service.")
    version: str = "1.0"
    # Additional fields from extension service
    key: str | None = Field(None, description="The unique key identifier from extension service.")
    logo: str | None = Field(None, description="Logo URL for the service.")
    categories: List[str] | None = Field(default_factory=list, description="Categories the service belongs to.")
    tags: List[str] | None = Field(default_factory=list, description="Tags associated with the service.")
    enabled: bool = Field(True, description="Whether the service is enabled.")
    actions_count: int = Field(0, description="Number of actions available in the service.")
    docs: str | None = Field(None, description="Documentation URL for the service.")

    model_config = ConfigDict(arbitrary_types_allowed=True)


class ExtensionClient:
    """
    Connect to the Extension Service (Extension service container)
    and get information about the available services.
    """

    def __init__(self, base_url: str | None = None, timeout: int = 30):
        """
        Initialize the ExtensionClient.

        Args:
            base_url: Base URL of the extension service. If None, uses environment setting.
            timeout: Request timeout in seconds.
        """
        self.base_url = base_url or env_settings.EXTENSION_SERVICE_URL
        self.timeout = timeout

        if not self.base_url:
            raise ValueError("Extension service URL is not configured. Please set EXTENSION_SERVICE_URL in settings.")

        # Remove trailing slash if present
        self.base_url = self.base_url.rstrip("/")
        logger.info(f"ExtensionClient initialized with base URL: {self.base_url}")

    async def _amake_request(self, method: str, endpoint: str, **kwargs) -> Dict:
        """
        Make an HTTP request to the extension service.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (without base URL)
            **kwargs: Additional arguments for the request

        Returns:
            Response data as dictionary

        Raises:
            Exception: If request fails or response indicates error
        """
        url = f"{self.base_url}{endpoint}"

        try:
            logger.debug(f"Making {method} request to: {url}")

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.request(method, url, **kwargs)

                if response.status_code != 200:
                    error_msg = f"Request failed with status {response.status_code}: {response.text}"
                    logger.error(error_msg)
                    raise Exception(error_msg)

                response_data = response.json()

                # Check if response indicates an error
                if response_data.get("status") == "error":
                    error_msg = f"Extension service returned error: {response_data.get('message', 'Unknown error')}"
                    logger.error(error_msg)
                    raise Exception(error_msg)

                logger.debug(f"Request successful: {response_data.get('message', 'No message')}")
                return response_data

        except httpx.RequestError as e:
            error_msg = f"Network error when connecting to extension service: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg) from e
        except Exception as e:
            if "Extension service returned error" in str(e) or "Request failed with status" in str(e):
                raise
            error_msg = f"Unexpected error during request: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg) from e

    async def aget_extension_service_info(self, service_key: str) -> Optional[ExtensionServiceInfo]:
        """
        Get detailed information about a specific extension service.

        Args:
            service_key: The unique key/identifier of the service

        Returns:
            ExtensionServiceInfo object if found, None otherwise
        """
        try:
            logger.info(f"Fetching service info for key: {service_key}")
            response_data = await self._amake_request("GET", f"/apps/{service_key}")

            app_data = response_data.get("data")
            if not app_data:
                logger.warning(f"No data returned for service key: {service_key}")
                return None

            # Fetch actions for this app
            actions_data = await self.aget_app_actions(service_key)

            # Extract action enums from the actions data
            action_enums = [action.get("enum", "") for action in actions_data if action.get("enum")]

            # Convert action enums to Composio Action enums
            composio_actions = self._convert_action_enums_to_composio_actions(action_enums)

            # Convert app key to Composio App enum
            try:
                app_enum = getattr(App, service_key.upper())
                logger.info(f"Successfully converted app key to enum: {service_key} -> {app_enum}")
            except AttributeError:
                logger.error(f"App enum not found in Composio for key: {service_key}")
                app_enum = None

            # Create ExtensionService if we have both app enum and actions
            extension_service = None
            if app_enum is not None:
                try:
                    extension_service = ExtensionService(name=service_key, app_enum=app_enum, supported_actions=composio_actions)
                    logger.info(f"Successfully created ExtensionService for {service_key} with {len(composio_actions)} actions")
                except Exception as e:
                    logger.error(f"Failed to create ExtensionService for {service_key}: {str(e)}")
                    extension_service = None

            # Map extension service data to ExtensionServiceInfo
            service_info = ExtensionServiceInfo(
                name=app_data.get("key", service_key),
                display_name=app_data.get("displayName") or app_data.get("name"),
                description=app_data.get("description"),
                key=app_data.get("key"),
                logo=app_data.get("logo"),
                categories=app_data.get("categories", []),
                tags=app_data.get("tags", []),
                enabled=app_data.get("enabled", False),
                actions_count=app_data.get("actionsCount", 0),
                docs=app_data.get("docs"),
                service_object=extension_service,
            )

            logger.info(f"Successfully retrieved service info for: {service_key}")
            return service_info

        except Exception as e:
            logger.error(f"Failed to get service info for {service_key}: {str(e)}")
            return None

    async def aget_all_extension_services_info(self, page: int = 1, limit: int = 100) -> List[ExtensionServiceInfo]:
        """
        Get information about all available extension services.

        Args:
            page: Page number for pagination
            limit: Number of services per page

        Returns:
            List of ExtensionServiceInfo objects
        """
        try:
            logger.info(f"Fetching all services info (page: {page}, limit: {limit})")
            response_data = await self._amake_request("GET", "/apps", params={"page": page, "limit": limit})

            apps_data = response_data.get("data", [])
            metadata = response_data.get("metadata", {})

            services_info = []
            for app_data in apps_data:
                app_key = app_data.get("key", "")

                # Fetch actions for this app
                actions_data = await self.aget_app_actions(app_key)
                action_enums = [action.get("enum", "") for action in actions_data if action.get("enum")]
                composio_actions = self._convert_action_enums_to_composio_actions(action_enums)

                # Convert app key to Composio App enum
                extension_service = None
                try:
                    app_enum = getattr(App, app_key.upper())
                    extension_service = ExtensionService(name=app_key, app_enum=app_enum, supported_actions=composio_actions)
                    logger.debug(f"Created ExtensionService for {app_key} with {len(composio_actions)} actions")
                except AttributeError:
                    logger.warning(f"App enum not found in Composio for key: {app_key}")
                except Exception as e:
                    logger.error(f"Failed to create ExtensionService for {app_key}: {str(e)}")

                service_info = ExtensionServiceInfo(
                    name=app_key,
                    display_name=app_data.get("displayName") or app_data.get("name"),
                    description=app_data.get("description"),
                    key=app_data.get("key"),
                    logo=app_data.get("logo"),
                    categories=app_data.get("categories", []),
                    tags=app_data.get("tags", []),
                    enabled=app_data.get("enabled", False),
                    actions_count=app_data.get("actionsCount", 0),
                    docs=app_data.get("docs"),
                    service_object=extension_service,
                )
                services_info.append(service_info)

            logger.info(f"Successfully retrieved {len(services_info)} services info from {metadata.get('total', 'unknown')} total services")
            return services_info

        except Exception as e:
            logger.error(f"Failed to get all services info: {str(e)}")
            return []

    async def asearch_extension_services(self, query: str, page: int = 1, limit: int = 100) -> List[ExtensionServiceInfo]:
        """
        Search for extension services by name, display name, or description.

        Args:
            query: Search query string
            page: Page number for pagination
            limit: Number of services per page

        Returns:
            List of ExtensionServiceInfo objects matching the search query
        """
        logger.info(f"Searching services with query: {query}")
        all_services = await self.aget_all_extension_services_info(page=page, limit=limit)

        query_lower = query.lower()
        matching_services = []

        for service in all_services:
            # Search in name, display_name, description, and tags
            if (
                query_lower in (service.name or "").lower()
                or query_lower in (service.display_name or "").lower()
                or query_lower in (service.description or "").lower()
                or any(query_lower in tag.lower() for tag in (service.tags or []))
            ):
                matching_services.append(service)

        logger.info(f"Found {len(matching_services)} services matching query: {query}")
        return matching_services

    async def aget_services_by_category(self, category: str, page: int = 1, limit: int = 100) -> List[ExtensionServiceInfo]:
        """
        Get extension services filtered by category.

        Args:
            category: Category to filter by
            page: Page number for pagination
            limit: Number of services per page

        Returns:
            List of ExtensionServiceInfo objects matching the category
        """
        logger.info(f"Fetching services by category: {category}")
        all_services = await self.aget_all_extension_services_info(page=page, limit=limit)

        # Filter services by category
        filtered_services = [service for service in all_services if category.lower() in [cat.lower() for cat in (service.categories or [])]]

        logger.info(f"Found {len(filtered_services)} services in category: {category}")
        return filtered_services

    async def ahealth_check(self) -> bool:
        """
        Check if the extension service is healthy and accessible.

        Returns:
            True if service is healthy, False otherwise
        """
        try:
            logger.debug("Performing health check on extension service")
            # Try to get the first page of apps as a health check
            await self._amake_request("GET", "/apps", params={"page": 1, "limit": 1})
            logger.info("Extension service health check passed")
            return True
        except Exception as e:
            logger.error(f"Extension service health check failed: {str(e)}")
            return False

    async def aget_app_actions(self, app_key: str) -> List[Dict]:
        """
        Get all actions for a specific app from the extension service.

        Args:
            app_key: The unique key/identifier of the app

        Returns:
            List of action dictionaries
        """
        try:
            logger.info(f"Fetching actions for app: {app_key}")
            response_data = await self._amake_request("GET", "/actions", params={"appKey": app_key})

            actions_data = response_data.get("data", [])
            if not actions_data:
                logger.warning(f"No actions returned for app: {app_key}")
                return []

            logger.info(f"Successfully retrieved {len(actions_data)} actions for app: {app_key}")
            return actions_data

        except Exception as e:
            logger.error(f"Failed to get actions for app {app_key}: {str(e)}")
            return []

    def _convert_action_enums_to_composio_actions(self, action_enums: List[str]) -> List[Action]:
        """
        Convert action enum strings to Composio Action enums.

        Args:
            action_enums: List of action enum strings

        Returns:
            List of Composio Action enums
        """
        actions = []
        for action_enum in action_enums:
            try:
                action = getattr(Action, action_enum)
                actions.append(action)
                logger.debug(f"Successfully converted action enum: {action_enum}")
            except AttributeError:
                logger.warning(f"Action enum not found in Composio: {action_enum}")
                continue

        logger.info(f"Converted {len(actions)} out of {len(action_enums)} action enums")
        return actions


extension_client = ExtensionClient()