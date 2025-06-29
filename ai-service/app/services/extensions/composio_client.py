import requests
from composio.client.collections import ConnectionRequestModel
from composio.client.exceptions import NoItemsFound
from composio_langgraph import App, ComposioToolSet

from app.core import logging
from app.core.settings import env_settings
from app.schemas.extension import DeleteConnection

logger = logging.get_logger(__name__)


class ComposioClient:
    @classmethod
    def get_or_initiate_integration(cls, app_enum: App):
        logger.info(f"Creating integration for {app_enum}")
        toolset = ComposioToolSet(api_key=env_settings.COMPOSIO_API_KEY)
        try:
            result = toolset.client.integrations.get(app_name=str(app_enum))
            if len(result) == 0:
                integration = toolset.create_integration(app=app_enum, force_new_integration=True)
                integration_id = integration.id
                return integration_id
            return result[-1].id
        except Exception as e:
            logger.error(f"Error creating {app_enum} integration: {e}")

    @classmethod
    def initiate_app_connection(cls, user_id: str, connected_extension_id: str, app_enum: App, redirect_url: str) -> ConnectionRequestModel | None:
        toolset = ComposioToolSet(api_key=env_settings.COMPOSIO_API_KEY)
        try:
            toolset.client.get_entity(id=user_id).get_connection(app=app_enum)
            return None
        except NoItemsFound:
            request = toolset.initiate_connection(app=app_enum, entity_id=user_id, redirect_url=f"{redirect_url}/{user_id}/{connected_extension_id}")
            return request

    @classmethod
    def check_app_connection(cls, user_id: str, app_enum: App) -> bool:
        toolset = ComposioToolSet(api_key=env_settings.COMPOSIO_API_KEY)
        try:
            toolset.client.get_entity(id=user_id).get_connection(app=app_enum)
            return True
        except NoItemsFound:
            return False

    @classmethod
    def get_entity(cls, user_id: str):
        toolset = ComposioToolSet(api_key=env_settings.COMPOSIO_API_KEY)
        entity = toolset.client.get_entity(id=user_id)
        return entity

    @classmethod
    def get_user_toolset(cls, user_id: str):
        return ComposioToolSet(api_key=env_settings.COMPOSIO_API_KEY, entity_id=user_id)

    @classmethod
    def get_toolset(cls):
        return ComposioToolSet(api_key=env_settings.COMPOSIO_API_KEY)

    @classmethod
    def get_app_enum(cls, app_type: str) -> App:
        return getattr(App, app_type)

    @classmethod
    def delete_connection(cls, connected_account_id: str) -> DeleteConnection:
        url = f"https://backend.composio.dev/api/v1/connectedAccounts/{connected_account_id}"
        headers = {"x-api-key": env_settings.COMPOSIO_API_KEY}

        response = requests.request("DELETE", url, headers=headers)
        data = response.json()
        if response.status_code == 200:
            return DeleteConnection(
                status="success",
                count=data["count"],
                message=None,
                error_code=None,
            )

        return DeleteConnection(
            status="failed",
            message=data["message"],
            error_code=response.status_code,
            count=None,
        )
