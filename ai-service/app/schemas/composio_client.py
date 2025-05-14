from enum import StrEnum
from typing import Optional

from pydantic import Field

from app.schemas.base import BaseResponse

##################################################
################### ENUMS ########################
##################################################


class ComposioSortBy(StrEnum):
    ALPHABET = "alphabet"
    USAGE = "usage"
    NO_SORT = "no_sort"


##################################################
########### REQUEST SCHEMAS ######################
##################################################
class AllActionQueryParams(BaseResponse):
    apps: Optional[str] = Field(..., title="Apps", examples=["app1"])
    actions: Optional[str] = Field(..., title="Actions", examples=["action1"])
    tags: Optional[str] = Field(..., title="Tags", examples=["tag1"])
    use_case: Optional[str] = Field(..., title="Use Case", examples=["use_case1"])
    page: Optional[int] = Field(..., title="Page", examples=[1])
    limit: Optional[int] = Field(..., title="Limit", examples=[10])
    filter_important_actions: Optional[bool] = Field(..., title="Filter Important Actions", examples=[True])
    sort_by: Optional[ComposioSortBy] = Field(..., title="Sort By", examples=[ComposioSortBy.ALPHABET])


##################################################
########### RESPONSE SCHEMAS #####################
##################################################
class BaseAppResponse(BaseResponse):
    app_id: str = Field(..., title="App ID", examples=["12345"], description="Unique identifier (UUID) for the app")
    key: str = Field(..., title="App Key", examples=["app1"], description="Unique key/slug for the app, used in URLs and API references")
    name: str = Field(..., title="App Name", examples=["app1"], description="The name of the app")
    display_name: Optional[str] = Field(..., title="Display Name", examples=["App 1"], description="The display name of the app")
    description: str = Field(..., title="App Description", examples=["This is app1"], description="The description of the app")
    logo: Optional[str] = Field(..., title="Logo", examples=["http://example.com/icon.png"], description="The logo of the app")
    categories: Optional[list[str]] = Field(..., title="Categories", examples=[["category1", "category2"]], description="The categories of the app")
    enabled: Optional[bool] = Field(..., title="Enabled", examples=[True], description="Indicates if the app is enabled")
    created_at: Optional[str] = Field(..., title="Created At", examples=["2023-01-01T00:00:00Z"], description="The creation date of the app")
    updated_at: Optional[str] = Field(..., title="Updated At", examples=["2023-01-01T00:00:00Z"], description="The last update date of the app")
    tags: Optional[list[str]] = Field(..., title="Tags", examples=[["tag1", "tag2"]], description="The tags of the app")
    no_auth: Optional[bool] = Field(..., title="No Auth", examples=[False], description="Indicates if the app has no authentication")


class AppItemMetaResponse(BaseResponse):
    is_custom_app: bool = Field(..., title="Is Custom App", examples=[False])
    trigger_count: int = Field(..., title="Trigger Count", examples=[0])
    actions_count: int = Field(..., title="Actions Count", examples=[11])


class AppItemResponse(BaseAppResponse):
    meta: Optional[AppItemMetaResponse] = Field(
        ...,
        title="Meta",
        examples=[{"is_custom_app": False, "trigger_count": 0, "actions_count": 11}],
        description="Additional metadata about the app",
    )


class TestConnectorResponse(BaseResponse):
    id: str = Field(..., title="Test Connector ID", examples=["12345"], description="Unique identifier (UUID) for the test connector")
    name: str = Field(..., title="Test Connector Name", examples=["Test Connector 1"], description="The name of the test connector")
    auth_scheme: str = Field(
        ..., title="Test Connector Auth Scheme", examples=["oauth2"], description="The authentication schemes supported by the test connector"
    )


class SingleAppResponse(BaseAppResponse):
    auth_schemes: Optional[object] = Field(
        ...,
        title="Auth Schemes",
        examples=[["oauth2"]],
        description="The authentication schemes supported by the app. This contains all the fields and details needed to setup and configure auth for this app.",
    )
    docs: Optional[str] = Field(
        ...,
        title="Docs",
        examples=["foo"],
        description="The documentation URL of the app, if available. Usually it’s a link to the doc to setup and configure the app.",
    )
    get_current_user_endpoint: Optional[str] = Field(
        ...,
        title="Get Current User Endpoint",
        examples=["foo"],
        description="The endpoint to get the current user",
    )
    test_connectors: Optional[list[TestConnectorResponse]] = Field(
        ...,
        title="Test Connectors",
        examples=[[{"id": "12345", "name": "Test Connector 1", "auth_schemes": "oauth2"}]],
        description="The test connectors available for the app. If this is not empty, it means composio allows you to setup this app without configuring and setting up your own auth app.",
    )


class ActionParameterItemResponse(BaseResponse):
    title: str = Field(..., title="Title", examples=["param1"])
    type: str = Field(..., title="Type", examples=["string"])
    properties: Optional[object] = Field(..., title="Properties", examples=[{"param1": "value1", "param2": "value2"}])
    required: Optional[list[str]] = Field(..., title="Required", examples=[["param1", "param2"]])


class BaseActionResponse(BaseResponse):
    name: str = Field(..., title="Action Name", examples=["action1"], description="The name of the action")
    display_name: str = Field(..., title="Action Display Name", examples=["Action 1"], description="The display name of the action")
    description: str = Field(..., title="Action Description", examples=["This is action1"], description="The description of the action")
    logo: str = Field(..., title="Logo", examples=["http://example.com/icon.png"], description="The logo of the action")
    tags: list[str] = Field(..., title="Tags", examples=[["tag1", "tag2"]], description="The tags of the action")
    deprecated: Optional[bool] = Field(
        ..., title="Deprecated", examples=[False], description="Whether the action is deprecated, if true, avoid using this action."
    )


class ActionItemResponse(BaseActionResponse):
    enum: str = Field(..., title="Action Enum", examples=["action1"], description="The enum of the action")


class SingleActionResponse(BaseActionResponse):
    app_key: str = Field(
        ..., title="App Key", examples=["app1"], description="The name of the app that the action belongs to. This is same as app_id."
    )
    app_name: str = Field(..., title="App Name", examples=["app1"], description="The name of the app that the action belongs to")
    version: str = Field(..., title="Version", examples=["1.0"], description="The version of the action")
    available_versions: Optional[list[str]] = Field(
        ..., title="Available Versions", examples=[["1.0", "2.0"]], description="List of availavle versions of the action."
    )
    no_auth: bool = Field(..., title="No Auth", examples=[False], description="Whether or not the action requires auth or not")


class FilterComposioAppsResponse(BaseResponse):
    items: list[AppItemResponse] = Field(..., title="List of all apps", examples=[[]])
    count: int = Field(..., title="Total number of apps", examples=[3])


class FilterComposioSingleAppResponse(BaseResponse):
    data: Optional[SingleAppResponse] = Field(..., title="App details", examples=[{}])  # Only None is returned when the app is not found


class FilterComposioActionsResponse(BaseResponse):
    items: list[ActionItemResponse] = Field(..., title="List of all actions", examples=[[]])
    count: int = Field(..., title="Total number of actions", examples=[3])
    page: int = Field(..., title="Page number", examples=[1])
    total_pages: int = Field(..., title="Total number of pages", examples=[1])


class FilterComposioAppEnumsResponse(BaseResponse):
    items: list[str] = Field(..., title="List of all apps enums", examples=[["GMAIL", "GOOGLE_CANLENDAR"]])
    count: int = Field(..., title="Total number of apps enums", examples=[3])


# Doc: https://docs.composio.dev/api-reference/api-reference/v1/apps/get-apps
class GetAllAppsComposioResponse(BaseResponse):
    success: bool = Field(..., title="Success", examples=[True])
    message: Optional[str] = Field(None, title="Message", examples=["Success"])
    items: list[AppItemResponse] = Field(..., title="List of all apps", examples=[[]])
    count: int = Field(..., title="Total number of apps", examples=[3])


# Doc: https://docs.composio.dev/api-reference/api-reference/v1/apps/get-app
class GetSingleAppComposioResponse(BaseResponse):
    success: bool = Field(..., title="Success", examples=[True])
    message: Optional[str] = Field(None, title="Message", examples=["Success"])
    data: Optional[SingleAppResponse] = Field(..., title="App details", examples=[{}])  # Only None is returned when the app is not found


# Doc: https://docs.composio.dev/api-reference/api-reference/v1/apps/list-app-enums
class GetAllAppsComposioEnumsResponse(BaseResponse):
    success: bool = Field(..., title="Success", examples=[True])
    message: Optional[str] = Field(None, title="Message", examples=["Success"])
    items: list[str] = Field(..., title="List of all apps enums", examples=[["GMAIL", "GOOGLE_CANLENDAR"]])
    count: int = Field(..., title="Total number of apps enums", examples=[3])


# Doc: https://docs.composio.dev/api-reference/api-reference/v1/actions/list-actions-minimal-v-2
class GetAllActionsComposioResponse(BaseResponse):
    success: bool = Field(..., title="Success", examples=[True])
    message: Optional[str] = Field(None, title="Message", examples=["Success"])
    items: list[ActionItemResponse] = Field(..., title="List of all actions", examples=[[]])
    count: int = Field(..., title="Total number of actions", examples=[3])
    page: int = Field(..., title="Page number", examples=[1])
    total_pages: int = Field(..., title="Total number of pages", examples=[1])


# Doc: https://docs.composio.dev/api-reference/api-reference/v1/actions/get-action-v-2
class GetSingleActionComposioResponse(BaseResponse):
    success: bool = Field(..., title="Success", examples=[True])
    message: Optional[str] = Field(None, title="Message", examples=["Success"])
    data: Optional[SingleActionResponse] = Field(..., title="Action details", examples=[{}])  # Only None is returned when the action is not found


# Doc: https://docs.composio.dev/api-reference/api-reference/v1/actions/list-action-enums
class GetAllActionComposioEnumsResponse(BaseResponse):
    success: bool = Field(..., title="Success", examples=[True])
    message: Optional[str] = Field(None, title="Message", examples=["Success"])
    items: list[str] = Field(..., title="List of all actions enums", examples=[["GMAIL_CREATE_EMAIL_DRAFT", "GITHUB_GET_THE_AUTHENTICATED_USER"]])
    count: int = Field(..., title="Total number of actions enums", examples=[3])
