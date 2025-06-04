from typing import Literal, Optional

from openai import BaseModel
from pydantic import Field

from app.schemas.base import BaseResponse


#
#
# ##################################################
# ########### REQUEST SCHEMAS ######################
# ##################################################
# class HTTPExtensionRequest(BaseRequest):
#     input: str = Field(min_length=1, max_length=5000, title="Input", examples=["Hello"])
#     recursion_limit: Optional[int] = Field(None, ge=1, le=50, title="Max Recursion", examples=[20])
#
#
# class HTTPExtensionCallbackRequest(BaseRequest):
#     execute: bool = Field(..., title="Continue executing the action", examples=[True])
#     tool_calls: Optional[list[ToolCall]] = Field(None, title="Update args of executing the action",
#                                                  examples=["..."])
#     recursion_limit: Optional[int] = Field(None, ge=1, le=50, title="Max Recursion", examples=[20])
#
#
# ##################################################
# ########### RESPONSE SCHEMAS #####################
# ##################################################
class ActiveAccountResponse(BaseResponse):
    is_existed: bool = Field(..., title="Is existed", examples=[False])
    redirect_url: Optional[str] = Field(None, title="Redirect URL", examples=["https://example.com"])


class DeleteConnection(BaseModel):
    status: Literal["success", "failed"] = Field(..., title="Status of the delete operation", examples=["success"])
    count: Optional[int] = Field(None, title="Number of records deleted", examples=[1])
    message: Optional[str] = Field(None, title="Message", examples=["Connection deleted successfully"])
    error_code: Optional[int] = Field(None, title="Error code", examples=[400])


class DeleteConnectionResponse(DeleteConnection, BaseResponse):
    pass


class CheckConnectionResponse(BaseResponse):
    is_connected: bool = Field(..., title="Is connected", examples=[True])