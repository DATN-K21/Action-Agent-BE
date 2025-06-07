from datetime import datetime
from typing import Optional

from pydantic import Field

from app.schemas.base import BaseRequest, BaseResponse, PagingResponse


##################################################
########### REQUEST SCHEMAS ######################
##################################################
class CreateConnectedMcpRequest(BaseRequest):
    mcp_name: str = Field(..., min_length=3, max_length=50, examples=["mcpname"])
    url: str = Field(..., min_length=3, max_length=200, examples=["url"])
    connection_type: Optional[str] = Field(None, min_length=3, max_length=50, examples=["streamable_http"])
    description: Optional[str] = Field(None, min_length=3, max_length=200, examples=["description"])

class UpdateConnectedMcpRequest(BaseRequest):
    mcp_name: Optional[str] = Field(None, min_length=3, max_length=50, examples=["mcpname"])
    url: Optional[str] = Field(None, min_length=3, max_length=200, examples=["url"])
    connection_type: Optional[str] = Field(None, min_length=3, max_length=50, examples=["streamable_http"])
    description: Optional[str] = Field(None, min_length=3, max_length=200, examples=["description"])

##################################################
########### RESPONSE SCHEMAS #####################
##################################################
class CreateConnectedMcpResponse(BaseResponse):
    id: str
    user_id: str
    mcp_name: str
    connection_type: str
    url: str
    description: Optional[str] = None
    created_at: datetime


class GetConnectedMcpResponse(CreateConnectedMcpResponse):
    pass


class GetConnectedMcpsResponse(PagingResponse):
    connected_mcps: list[GetConnectedMcpResponse] = Field(..., title="List of connected mcps")


class UpdateConnectedMcpResponse(CreateConnectedMcpResponse):
    pass
