from typing import Optional, Any

from pydantic import Field

from app.core.utils.models import Action
from app.schemas.base import BaseResponse, BaseRequest


##################################################
########### REQUEST SCHEMAS ######################
##################################################
class McpRequest(BaseRequest):
    input: str = Field(min_length=1, max_length=5000, title="Input", examples=["Hello"])
    recursion_limit: Optional[int] = Field(None, ge=1, le=50, title="Recursion limit", examples=[20])


##################################################
########### RESPONSE SCHEMAS #####################
##################################################
class GetMcpActionsResponse(BaseResponse):
    actions: list[Action] = Field(..., title="List of actions")


class McpResponse(BaseResponse):
    user_id: Optional[str] = Field(None, min_length=1, max_length=100, title="User ID", examples=["userid"])
    thread_id: Optional[str] = Field(None, min_length=1, max_length=100, title="Thread ID", examples=["threadid"])
    output: Optional[str | dict | list[Any]] = Field(None, title="Output", examples=["Hello"])
