from datetime import datetime
from typing import Optional

from pydantic import Field

from app.schemas.base import BaseResponse, PagingResponse, BaseRequest


##################################################
########### REQUEST SCHEMAS ######################
##################################################
class CreateConnectedMcpRequest(BaseRequest):
    id: Optional[str] = None
    mcp_name: str = Field(..., min_length=3, max_length=50)
    url: str = Field(..., min_length=3, max_length=200)
    connection_type: Optional[str] = Field(None, min_length=3, max_length=50)


class UpdateConnectedMcpRequest(BaseRequest):
    mcp_name: Optional[str] = Field(None, min_length=3, max_length=50)
    url: Optional[str] = Field(None, min_length=3, max_length=200)
    connection_type: Optional[str] = Field(None, min_length=3, max_length=50)


##################################################
########### RESPONSE SCHEMAS #####################
##################################################
class CreateConnectedMcpResponse(BaseResponse):
    id: str
    user_id: str
    mcp_name: str
    connection_type: str
    url: str
    created_at: datetime


class GetConnectedMcpResponse(BaseResponse):
    id: str = Field(..., title="Connected App ID", examples=["id"])
    user_id: str = Field(..., title="User ID", examples=["userid"])
    mcp_name: str = Field(..., title="MCP Name", examples=["mcpname"])
    url: Optional[str] = Field(None, title="Auth Scheme", examples=["Bearer"])
    connection_type: Optional[str] = Field(None, title="Auth Value", examples=["authvalue"])
    created_at: Optional[datetime] = Field(None, title="Created At", examples=["2022-01-01T00:00:00Z"])


class GetAllConnectedMcpsRequest(PagingResponse):
    connected_mcps: list[GetConnectedMcpResponse] = Field(..., title="List of connected mcps")


class UpdateConnectedMcpResponse(CreateConnectedMcpResponse):
    pass


class DeleteConnectedMcpResponse(BaseResponse):
    id: str
    user_id: str
