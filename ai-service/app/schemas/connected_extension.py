from datetime import datetime
from typing import Optional

from pydantic import Field

from app.core.enums import ConnectionStatus
from app.schemas.base import BaseResponse, PagingResponse

##################################################
########### REQUEST SCHEMAS ######################
##################################################

##################################################
########### RESPONSE SCHEMAS #####################
##################################################
class GetConnectedExtensionResponse(BaseResponse):
    id: str = Field(..., title="Connected App ID", examples=["id"])
    user_id: str = Field(..., title="User ID", examples=["userid"])
    extension_enum: str = Field(..., title="Extension Enum", examples=["extensionenum"])
    extension_name: str = Field(..., title="Extension Name", examples=["extensionname"])
    connection_status: ConnectionStatus = Field(..., title="Connection Status", examples=["PENDING", "CONNECTED", "FAILED"])
    connected_account_id: Optional[str] = Field(None, title="Connected Account ID", examples=["connectedaccountid"])
    auth_scheme: Optional[str] = Field(None, title="Auth Scheme", examples=["Bearer"])
    auth_value: Optional[str] = Field(None, title="Auth Value", examples=["authvalue"])
    created_at: Optional[datetime] = Field(None, title="Created At", examples=["2022-01-01T00:00:00Z"])


class GetConnectedExtensionsResponse(PagingResponse):
    connected_extensions: list[GetConnectedExtensionResponse] = Field(..., title="List of connected extensions")
