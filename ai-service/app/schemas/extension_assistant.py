from datetime import datetime
from typing import Optional

from pydantic import Field

from app.schemas.base import BaseRequest, BaseResponse, PagingResponse


##################################################
########### REQUEST SCHEMAS ######################
##################################################
class CreateExtensionAssistantRequest(BaseRequest):
    id: Optional[str] = None
    assistant_id: str = Field(..., min_length=3, max_length=50)
    extension_id: str = Field(..., min_length=3, max_length=50)


class UpdateExtensionAssistantRequest(BaseRequest):
    assistant_id: Optional[str] = Field(None, min_length=3, max_length=50)
    extension_id: Optional[str] = Field(None, min_length=3, max_length=50)


##################################################
########### RESPONSE SCHEMAS #####################
##################################################
class CreateExtensionAssistantResponse(BaseResponse):
    id: str
    assistant_id: str
    extension_id: str
    created_at: datetime


class GetExtensionAssistantResponse(CreateExtensionAssistantResponse):
    pass


class GetExtensionAssistantsResponse(PagingResponse):
    extension_assistants: list[GetExtensionAssistantResponse]


class UpdateExtensionAssistantResponse(CreateExtensionAssistantResponse):
    pass


class DeleteExtensionAssistantResponse(BaseResponse):
    id: str
    assistant_id: str
    extension_id: str


class GetExtensionOfAssistantResponse(BaseResponse):
    id: str
    user_id: str
    assistant_id: str
    extension_id: str
    extension_name: str
    connected_account_id: str = Field(..., title="Connected Account ID", examples=["connectedaccountid"])
    auth_scheme: Optional[str] = Field(None, title="Auth Scheme", examples=["Bearer"])
    auth_value: Optional[str] = Field(None, title="Auth Value", examples=["authvalue"])
    created_at: Optional[datetime]


class GetExtensionsOfAssistantResponse(PagingResponse):
    extensions: list[GetExtensionOfAssistantResponse]


class DeleteAllExtensionsOfAssistantResponse(BaseResponse):
    extension_assistants: list[DeleteExtensionAssistantResponse]
