from typing import Optional, Any

from pydantic import Field

from app.schemas.base import BaseResponse, BaseRequest


##################################################
########### REQUEST SCHEMAS ######################
##################################################
class McpRequest(BaseRequest):
    input: str = Field(min_length=1, max_length=5000, title="Input", examples=["Hello"])
    max_recursion: Optional[int] = Field(None, ge=1, le=20, title="Max Recursion", examples=[10])


##################################################
########### RESPONSE SCHEMAS #####################
##################################################
class GetMcpActionsResponse(BaseResponse):
    actions: list[str] = Field(..., title="List of actions", examples=[["action1", "action2"]])


class GetMcpsResponse(BaseResponse):
    extensions: list[str] = Field(..., title="List of extensions", examples=[["extension1", "extension2"]])


class McpResponse(BaseResponse):
    user_id: Optional[str] = Field(None, min_length=1, max_length=100, title="User ID", examples=["userid"])
    thread_id: Optional[str] = Field(None, min_length=1, max_length=100, title="Thread ID", examples=["threadid"])
    connected_mcp_id: Optional[str] = Field(None, min_length=1, max_length=100, title="Connected MCP ID",
                                            examples=["connected_mcp_id"])
    output: Optional[str | dict | list[Any]] = Field(None, title="Output", examples=["Hello"])
