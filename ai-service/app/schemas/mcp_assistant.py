from datetime import datetime
from typing import Optional

from pydantic import Field

from app.schemas.base import BaseRequest, BaseResponse, PagingResponse


##################################################
########### REQUEST SCHEMAS ######################
##################################################
class CreateMcpAssistantRequest(BaseRequest):
    id: Optional[str] = None
    assistant_id: str = Field(..., min_length=3, max_length=50)
    mcp_id: str = Field(..., min_length=3, max_length=50)


class UpdateMcpAssistantRequest(BaseRequest):
    assistant_id: Optional[str] = Field(None, min_length=3, max_length=50)
    mcp_id: Optional[str] = Field(None, min_length=3, max_length=50)


##################################################
########### RESPONSE SCHEMAS #####################
##################################################
class CreateMcpAssistantResponse(BaseResponse):
    id: str
    assistant_id: str
    mcp_id: str
    created_at: datetime


class GetMcpAssistantResponse(CreateMcpAssistantResponse):
    pass


class GetMcpAssistantsResponse(PagingResponse):
    mcp_assistants: list[GetMcpAssistantResponse]


class UpdateMcpAssistantResponse(CreateMcpAssistantResponse):
    pass


class DeleteMcpAssistantResponse(BaseResponse):
    id: str
    assistant_id: str
    mcp_id: str


class GetMcpOfAssistantResponse(BaseResponse):
    id: str
    user_id: str
    assistant_id: str
    mcp_id: str
    mcp_name: str
    url: str
    connection_type: str
    created_at: Optional[datetime]


class GetMcpsOfAssistantResponse(PagingResponse):
    mcps: list[GetMcpOfAssistantResponse]
