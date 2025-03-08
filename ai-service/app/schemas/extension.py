from typing import Literal, Optional

from pydantic import Field, BaseModel

from app.schemas.base import BaseResponse, BaseRequest


##################################################
########### REQUEST SCHEMAS ######################
##################################################


##################################################
########### RESPONSE SCHEMAS #####################
##################################################
class ActiveAccountResponse(BaseResponse):
    is_existed: bool = Field(..., title="Is existed", examples=[False])
    redirect_url: Optional[str] = Field(None, title="Redirect URL", examples=["https://example.com"])


class GetActionsResponse(BaseResponse):
    actions: list[str] = Field(..., title="List of actions", examples=[["action1", "action2"]])


class GetExtensionsResponse(BaseResponse):
    extensions: list[str] = Field(..., title="List of extensions", examples=[["extension1", "extension2"]])


class DeleteConnectionResponse(BaseResponse):
    status: Literal["success", "failed"] = Field(..., title="Status of the delete operation", examples=["success"])
    count: Optional[int] = Field(None, title="Number of records deleted", examples=[1])
    message: Optional[str] = Field(None, title="Message", examples=["Connection deleted successfully"])
    error_code: Optional[int] = Field(None, title="Error code", examples=[400])


class CheckConnectionResponse(BaseResponse):
    is_connected: bool = Field(..., title="Is connected", examples=[True])


##################################################
########### SOCKETIO REQUEST SCHEMAS #############
##################################################
class ExtensionRequest(BaseRequest):
    user_id: str = Field(min_length=1, max_length=100, title="User ID", examples=["userid"])
    thread_id: str = Field(min_length=1, max_length=100, title="Thread ID", examples=["threadid"])
    extension_name: str = Field(min_length=1, max_length=100, title="Extension Name", examples=["extension1"])
    input: str = Field(min_length=1, max_length=5000, title="Input", examples=["Hello"])
    max_recursion: Optional[int] = Field(5, ge=1, le=20, title="Max Recursion", examples=[5])


##################################################
########### SOCKETIO RESPONSE SCHEMAS ############
##################################################
class ExtensionResponse(BaseRequest):
    user_id: str = Field(min_length=1, max_length=100, title="User ID", examples=["userid"])
    thread_id: str = Field(min_length=1, max_length=100, title="Thread ID", examples=["threadid"])
    extension_name: str = Field(min_length=1, max_length=100, title="Extension Name", examples=["extension1"])
    interrupted: bool = Field(..., title="Interrupted", examples=[False])
    output: str | dict = Field(..., title="Output", examples=["Hello"])


##################################################
########### SOCKETIO CALLBACK SCHEMAS ############
##################################################
class ExtensionCallBack(BaseModel):
    user_id: str = Field(min_length=1, max_length=100, title="User ID", examples=["userid"])
    thread_id: str = Field(min_length=1, max_length=100, title="Thread ID", examples=["threadid"])
    extension_name: str = Field(min_length=1, max_length=100, title="Extension Name", examples=["extension1"])
    input: str = Field(min_length=1, max_length=100, title="Output", examples=["Hello"])
    max_recursion: Optional[int] = Field(5, ge=1, le=20, title="Max Recursion", examples=[5])
