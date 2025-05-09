from datetime import datetime
from typing import Optional

from pydantic import Field

from app.schemas.base import BaseRequest, BaseResponse, PagingResponse
from app.schemas.connected_extension import GetConnectedExtensionResponse
from app.schemas.connected_mcp import GetConnectedMcpResponse


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
    pass


class UpdateFullInfoAssistantRequest(BaseRequest):
    pass


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


class CreateFullInfoAssistantResponse(BaseResponse):
    pass


class GetFullInfoAssistantResponse(GetAssistantResponse):
    workers: Optional[list[GetConnectedExtensionResponse | GetConnectedMcpResponse]]


class GetFullInfoAssistantsResponse(GetAssistantResponse):
    full_info_assistants: list[GetFullInfoAssistantResponse]


class UpdateFullInfoAssistantResponse(BaseResponse):
    pass
