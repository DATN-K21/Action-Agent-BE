from typing import Literal, Optional

from pydantic import Field

from app.schemas.base import BaseResponse

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


class LogoutAccountResponse(BaseResponse):
    message: str = Field(..., title="Message", examples=["Logout successful"])


class DeleteConnectionResponse(BaseResponse):
    status: Literal["success", "failed"] = Field(..., title="Status of the delete operation", examples=["success"])
    count: Optional[int] = Field(None, title="Number of records deleted", examples=[1])
    message: Optional[str] = Field(None, title="Message", examples=["Connection deleted successfully"])
    error_code: Optional[int] = Field(None, title="Error code", examples=[400])
