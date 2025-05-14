from datetime import datetime
from typing import Optional

from pydantic import Field

from app.schemas.base import BaseRequest, BaseResponse, PagingResponse


##################################################
########### REQUEST SCHEMAS ######################
##################################################
class CreateAssistantRequest(BaseRequest):
    id: Optional[str] = None
    name: str = Field(..., min_length=3, max_length=50)
    description: Optional[str] = Field(None, min_length=3, max_length=500)
    type: str = Field(..., min_length=3, max_length=50)


class UpdateAssistantRequest(BaseRequest):
    name: Optional[str] = Field(None, min_length=3, max_length=50)
    description: Optional[str] = Field(None, min_length=3, max_length=500)
    type: Optional[str] = Field(None, min_length=3, max_length=50)


class CreateFullInfoAssistantRequest(BaseRequest):
    id: Optional[str] = None
    name: str = Field(..., min_length=3, max_length=50)
    description: Optional[str] = Field(None, min_length=3, max_length=500)
    type: str = Field(..., min_length=3, max_length=50)
    worker_ids: list[str]


class UpdateFullInfoAssistantRequest(BaseRequest):
    name: Optional[str] = Field(None, min_length=3, max_length=50)
    description: Optional[str] = Field(None, min_length=3, max_length=500)
    type: Optional[str] = Field(None, min_length=3, max_length=50)
    worker_ids: Optional[list[str]] = None


##################################################
########### RESPONSE SCHEMAS #####################
##################################################

class CreateAssistantResponse(BaseResponse):
    id: str
    user_id: str
    name: str
    description: Optional[str]
    type: str
    created_at: datetime


class GetAssistantResponse(BaseResponse):
    id: str
    user_id: str
    name: str
    description: Optional[str]
    type: str
    created_at: datetime


class GetAssistantsResponse(PagingResponse):
    assistants: list[GetAssistantResponse]


class UpdateAssistantResponse(CreateAssistantResponse):
    pass


class DeleteAssistantResponse(BaseResponse):
    id: str
    user_id: str


class ExtensionData(BaseResponse):
    id: str
    extension_name: str
    connected_account_id: str = Field(..., title="Connected Account ID", examples=["connectedaccountid"])
    auth_scheme: Optional[str] = Field(None, title="Auth Scheme", examples=["Bearer"])
    auth_value: Optional[str] = Field(None, title="Auth Value", examples=["authvalue"])
    created_at: Optional[datetime]


class McpData(BaseResponse):
    id: str
    mcp_name: str
    url: Optional[str] = Field(None, title="Auth Scheme", examples=["Bearer"])
    connection_type: Optional[str] = Field(None, title="Auth Value", examples=["authvalue"])
    created_at: Optional[datetime]


class GetFullInfoAssistantResponse(GetAssistantResponse):
    workers: Optional[list[ExtensionData | McpData]]


class GetFullInfoAssistantsResponse(PagingResponse):
    full_info_assistants: list[GetFullInfoAssistantResponse]


class CreateFullInfoAssistantResponse(CreateAssistantResponse):
    workers: Optional[list[ExtensionData | McpData]] = Field(..., title="List of workers")


class UpdateFullInfoAssistantResponse(CreateFullInfoAssistantResponse):
    pass
