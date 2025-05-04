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


class GetListAssistantsResponse(PagingResponse):
    assistants: list[GetAssistantResponse]


class UpdateAssistantResponse(CreateAssistantResponse):
    pass


class DeleteAssistantResponse(BaseResponse):
    id: str
    user_id: str
