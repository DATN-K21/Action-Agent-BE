from datetime import datetime
from typing import Optional

from pydantic import Field

from app.core.enums import McpTransport
from app.schemas.base import BaseRequest, BaseResponse, PagingResponse


##################################################
########### REQUEST SCHEMAS ######################
##################################################
class CreateConnectedMcpRequest(BaseRequest):
    mcp_name: str = Field(..., min_length=3, max_length=50, examples=["mcpname"])
    url: str = Field(..., min_length=3, max_length=200, examples=["url"])
    transport: Optional[McpTransport] = Field(None, examples=[McpTransport.STREAMABLE_HTTP])
    description: Optional[str] = Field(None, min_length=3, max_length=1000, examples=["description"])

class UpdateConnectedMcpRequest(BaseRequest):
    mcp_name: Optional[str] = Field(None, min_length=3, max_length=50, examples=["mcpname"])
    url: Optional[str] = Field(None, min_length=3, max_length=200, examples=["url"])
    transport: Optional[McpTransport] = Field(None, examples=[McpTransport.STREAMABLE_HTTP])
    description: Optional[str] = Field(None, min_length=3, max_length=1000, examples=["description"])

##################################################
########### RESPONSE SCHEMAS #####################
##################################################
class CreateConnectedMcpResponse(BaseResponse):
    id: str
    user_id: str
    mcp_name: str
    transport: McpTransport
    url: str
    description: Optional[str] = None
    created_at: datetime


class GetConnectedMcpResponse(CreateConnectedMcpResponse):
    pass


class GetConnectedMcpsResponse(PagingResponse):
    connected_mcps: list[GetConnectedMcpResponse] = Field(..., title="List of connected mcps")


class UpdateConnectedMcpResponse(CreateConnectedMcpResponse):
    pass
