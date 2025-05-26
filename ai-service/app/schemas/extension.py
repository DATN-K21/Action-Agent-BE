# from typing import Any, Literal, Optional
#
# from pydantic import BaseModel, Field
#
# # from app.core.graph.base import ToolCall
# from app.schemas.base import BaseRequest, BaseResponse
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
# class ActiveAccountResponse(BaseResponse):
#     is_existed: bool = Field(..., title="Is existed", examples=[False])
#     redirect_url: Optional[str] = Field(None, title="Redirect URL", examples=["https://example.com"])
#
#
# class GetActionsResponse(BaseResponse):
#     actions: list[str] = Field(..., title="List of actions", examples=[["action1", "action2"]])
#
#
# class GetExtensionsResponse(BaseResponse):
#     extensions: list[str] = Field(..., title="List of extensions", examples=[["extension1", "extension2"]])
#
#
# class DeleteConnectionResponse(BaseResponse):
#     status: Literal["success", "failed"] = Field(..., title="Status of the delete operation", examples=["success"])
#     count: Optional[int] = Field(None, title="Number of records deleted", examples=[1])
#     message: Optional[str] = Field(None, title="Message", examples=["Connection deleted successfully"])
#     error_code: Optional[int] = Field(None, title="Error code", examples=[400])
#
#
# class CheckConnectionResponse(BaseResponse):
#     is_connected: bool = Field(..., title="Is connected", examples=[True])
#
#
# class GetSocketioInfoResponse(BaseResponse):
#     output: str = Field(..., title="Output", examples=["Hello!"])
#
#
# class ExtensionResponse(BaseResponse):
#     user_id: Optional[str] = Field(None, min_length=1, max_length=100, title="User ID", examples=["userid"])
#     thread_id: Optional[str] = Field(None, min_length=1, max_length=100, title="Thread ID", examples=["threadid"])
#     extension_name: Optional[str] = Field(None, min_length=1, max_length=100, title="Extension Name",
#                                           examples=["extension1"])
#     interrupted: Optional[bool] = Field(None, title="Interrupted", examples=[False])
#     streaming: Optional[bool] = Field(None, title="Streaming", examples=[False])
#     output: Optional[str | dict | list[Any]] = Field(None, title="Output", examples=["Hello"])
#
#
# ##################################################
# ########### SOCKETIO REQUEST SCHEMAS #############
# ##################################################
# class SocketioExtensionRequest(BaseRequest):
#     user_id: str = Field(min_length=1, max_length=100, title="User ID", examples=["userid"])
#     thread_id: str = Field(min_length=1, max_length=100, title="Thread ID", examples=["threadid"])
#     extension_name: str = Field(min_length=1, max_length=100, title="Extension Name", examples=["extension1"])
#     input: str = Field(min_length=1, max_length=5000, title="Input", examples=["Hello"])
#     recursion_limit: Optional[int] = Field(20, ge=1, le=50, title="Max Recursion", examples=[20])
#
#
# ##################################################
# ########### SOCKETIO CALLBACK SCHEMAS ############
# ##################################################
# class SocketioExtensionCallback(BaseModel):
#     user_id: str = Field(min_length=1, max_length=100, title="User ID", examples=["userid"])
#     thread_id: str = Field(min_length=1, max_length=100, title="Thread ID", examples=["threadid"])
#     extension_name: str = Field(min_length=1, max_length=100, title="Extension Name", examples=["extension1"])
#     execute: bool = Field(..., title="Continue executing the action", examples=[True])
#     tool_calls: Optional[list[ToolCall]] = Field(None, title="Update args of executing the action",
#                                                  examples=["..."])
#     recursion_limit: Optional[int] = Field(20, ge=1, le=50, title="Max Recursion", examples=[20])
