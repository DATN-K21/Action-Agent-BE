from requests import request

from app.core.settings import env_settings
from app.schemas.composio_client import (
    AllActionQueryParams,
    GetAllActionsComposioResponse,
    GetAllAppsComposioEnumsResponse,
    GetAllAppsComposioResponse,
    GetSingleActionComposioResponse,
    GetSingleAppComposioResponse,
)
from app.utils.composio_client import sanitize_composio_app_data


class ComposioClient:
    base_url = "https://backend.composio.dev/api/v1/"
    base_url_v2 = "https://backend.composio.dev/api/v2/"
    headers = {
        "x-api-key": env_settings.COMPOSIO_API_KEY,
        "Content-Type": "application/json",
    }

    @classmethod
    def get_all_apps(cls):
        result = request("GET", f"{cls.base_url}apps", headers=cls.headers)
        data = result.json()

        sanitized_data = []
        for item in data["items"]:
            sanitized_item = sanitize_composio_app_data(item)
            sanitized_data.append(sanitized_item)

        if result.status_code == 200:
            return GetAllAppsComposioResponse(
                success=True,
                message=None,
                items=sanitized_data,
                count=len(sanitized_data),
            )

        return GetAllAppsComposioResponse(
            success=False,
            message=data.get("message", "Composio API error"),
            items=[],
            count=0,
        )

    @classmethod
    def get_single_app(cls, app_enum: str):
        result = request("GET", f"{cls.base_url}apps/{app_enum}", headers=cls.headers)
        data = result.json()

        if result.status_code == 200:
            return GetSingleAppComposioResponse(
                success=True,
                message=None,
                data=data,
            )

        return GetSingleAppComposioResponse(
            success=False,
            message=data["message"],
            data=None,
        )

    @classmethod
    def get_all_app_enums(cls):
        result = request("GET", f"{cls.base_url}apps/list/enums", headers=cls.headers)
        data = result.json()
        if result.status_code == 200:
            return GetAllAppsComposioEnumsResponse(
                success=True,
                message=None,
                items=data,
                count=len(data),
            )
        return GetAllAppsComposioEnumsResponse(
            success=False,
            message=data["message"],
            items=[],
            count=0,
        )

    @classmethod
    def get_all_actions(cls, params: AllActionQueryParams):
        result = request("GET", f"{cls.base_url_v2}actions/list/all", headers=cls.headers, params=params.model_dump())
        data = result.json()

        if result.status_code == 200:
            return GetAllActionsComposioResponse(
                success=True,
                message=None,
                items=data["items"],
                count=len(data["items"]),
                page=params.page if params.page else 1,
                total_pages=data["totalPages"],
            )

        return GetAllActionsComposioResponse(
            success=False,
            message=data["message"],
            items=[],
            count=0,
            page=params.page if params.page else 1,
            total_pages=0,
        )

    @classmethod
    def get_single_action(cls, action_enum: str):
        result = request("GET", f"{cls.base_url_v2}actions/{action_enum}", headers=cls.headers)
        data = result.json()

        if result.status_code == 200:
            return GetSingleActionComposioResponse(
                success=True,
                message=None,
                data=data,
            )

        return GetSingleActionComposioResponse(
            success=False,
            message=data["message"],
            data=None,
        )

    @classmethod
    def get_all_action_enums(cls):
        result = request("GET", f"{cls.base_url_v2}actions/list/enums", headers=cls.headers)
        data = result.json()

        if result.status_code == 200:
            return GetAllAppsComposioEnumsResponse(
                success=True,
                message=None,
                items=data,
                count=len(data),
            )

        return GetAllAppsComposioEnumsResponse(
            success=False,
            message=data["message"],
            items=[],
            count=0,
        )
