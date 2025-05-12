from typing import Literal, Union, overload

from app.schemas.composio_client import AppItemResponse, SingleAppResponse


@overload
def sanitize_composio_app_data(data: dict, type: Literal["all"]) -> AppItemResponse: ...
@overload
def sanitize_composio_app_data(data: dict, type: Literal["single"]) -> SingleAppResponse: ...
def sanitize_composio_app_data(data: dict, type: Literal["all", "single"] = "all") -> Union[AppItemResponse, SingleAppResponse]:
    sanitized_data = {
        "app_id": data["appId"],
        "key": data["key"],
        "name": data["name"],
        "display_name": data["displayName"] if "displayName" in data else None,
        "description": data["description"],
        "logo": data["logo"] if "logo" in data else None,
        "categories": data["categories"] if "categories" in data else None,
        "tags": data["tags"] if "tags" in data else None,
        "enabled": data["enabled"] if "enabled" in data else True,
        "created_at": data["createdAt"] if "createdAt" in data else None,
        "updated_at": data["updatedAt"] if "updatedAt" in data else None,
        "no_auth": data["no_auth"] if "no_auth" in data else False,
    }
    if data["meta"] is not None and type == "all":
        sanitized_data["meta"] = {
            "is_custom_app": data["meta"]["is_custom_app"] if "is_custom_app" in data["meta"] else False,
            "trigger_count": int(data["meta"]["triggerCount"]) if "triggerCount" in data["meta"] else 0,
            "actions_count": int(data["meta"]["actionsCount"]) if "actionsCount" in data["meta"] else 0,
        }

        return AppItemResponse(**sanitized_data)
    elif type == "single":
        sanitized_data["auth_schemes"] = data["authSchemes"] if "authSchemes" in data else None
        sanitized_data["docs"] = data["docs"] if "docs" in data else None
        sanitized_data["get_current_user_endpoint"] = data["get_current_user_endpoint"] if "get_current_user_endpoint" in data else None
        if "test_connectors" in data:
            sanitized_data["test_connectors"] = [
                {
                    "id": item["id"],
                    "name": item["name"],
                    "auth_schemes": item["auth_schemes"],
                }
                for item in data["test_connectors"]
            ]

        return SingleAppResponse(**sanitized_data)

    raise ValueError(f"Invalid type for sanitization composio app response. Expected 'all' or 'single'; Got {type}.")
