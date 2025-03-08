from datetime import datetime
from typing import Optional

from pydantic import Field

from app.schemas.base import BaseResponse, PagingResponse


##################################################
########### REQUEST SCHEMAS ######################
##################################################


##################################################
########### RESPONSE SCHEMAS #####################
##################################################
class GetConnectedAppResponse(BaseResponse):
    id: str = Field(..., title="Connected App ID", examples=["id"])
    user_id: str = Field(..., title="User ID", examples=["userid"])
    app_name: str = Field(..., title="App Name", examples=["appname"])
    connected_account_id: str = Field(..., title="Connected Account ID", examples=["connectedaccountid"])
    auth_scheme: Optional[str] = Field(None, title="Auth Scheme", examples=["Bearer"])
    auth_value: Optional[str] = Field(None, title="Auth Value", examples=["authvalue"])
    created_at: Optional[datetime] = Field(None, title="Created At", examples=["2022-01-01T00:00:00Z"])


class GetAllConnectedAppsRequest(PagingResponse):
    connected_apps: list[GetConnectedAppResponse] = Field(..., title="List of connected apps")
