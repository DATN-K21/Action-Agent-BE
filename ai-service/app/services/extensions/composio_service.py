
import requests
from composio.client.collections import CustomAuthParameter
from composio.client.exceptions import NoItemsFound
from composio_langgraph import App, ComposioToolSet

from app.core import logging
from app.core.settings import env_settings
from app.schemas.connection import DeleteConnectionResponse

logger = logging.get_logger(__name__)


class ComposioService:
    @classmethod
    def initialize_app_connection(cls, user_id: str, app_enum: App, redirect_url: str):
        toolset = ComposioToolSet(api_key=env_settings.COMPOSIO_API_KEY, entity_id=user_id)
        entity = toolset.get_entity()
        try:
            entity.get_connection(app=app_enum)
            return None
        except NoItemsFound:
            request = entity.initiate_connection(app_name=app_enum, redirect_url=f"{redirect_url}/{user_id}")
            return request

    @classmethod
    def get_entity(cls, user_id: str):
        toolset = ComposioToolSet(api_key=env_settings.COMPOSIO_API_KEY, entity_id=user_id)
        entity = toolset.get_entity()
        return entity

    @classmethod
    def get_user_toolset(cls, user_id: str):
        return ComposioToolSet(api_key=env_settings.COMPOSIO_API_KEY, entity_id=user_id)

    @classmethod
    def get_toolset(cls):
        return ComposioToolSet(api_key=env_settings.COMPOSIO_API_KEY)

    @classmethod
    def get_connected_account_toolset(cls, user_id: str, app_enum: App, connected_account_id: str):
        try:
            toolset = ComposioService.get_user_toolset(user_id)

            auth_params = toolset.get_auth_params(connection_id=connected_account_id)
            auth_value = ""

            if not auth_params:
                return toolset

            for parameter in auth_params.parameters:
                if parameter.name == "Authorization":
                    auth_value = parameter.value
                    break

            toolset.add_auth(
                app=app_enum,
                parameters=[
                    CustomAuthParameter(
                        name="Authorization",
                        in_="header",
                        value=auth_value,
                    )
                ],
            )

            return toolset
        except Exception as e:
            logger.error(f"Error fetching authorization value: {str(e)}")
            raise

    @classmethod
    def get_app_enum(cls, app_type: str) -> App:
        return getattr(App, app_type)

    @classmethod
    def delete_connection(cls, connected_account_id: str):
        url = f"https://backend.composio.dev/api/v1/connectedAccounts/{connected_account_id}"
        headers = {"x-api-key": env_settings.COMPOSIO_API_KEY}

        response = requests.request("DELETE", url, headers=headers)
        data = response.json()
        if response.status_code == 200:
            return DeleteConnectionResponse(
                status="success",
                count=data["count"],
                message=None,
                error_code=None,
            )

        return DeleteConnectionResponse(
            status="failed",
            message=data["message"],
            error_code=response.status_code,
            count=None,
        )
