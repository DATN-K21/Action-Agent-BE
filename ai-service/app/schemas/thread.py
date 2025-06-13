from datetime import datetime
from typing import Optional

from pydantic import Field

from app.core.graph.messages import ChatResponse
from app.schemas.base import BaseRequest, BaseResponse, CursorPagingResponse


##################################################
########### REQUEST SCHEMAS ######################
##################################################
class CreateThreadRequest(BaseRequest):
    id: Optional[str] = None
    title: str = Field(..., min_length=3, max_length=50)
    assistant_id: str = Field(..., min_length=3, max_length=50)


class UpdateThreadRequest(BaseRequest):
    title: Optional[str] = Field(None, min_length=3, max_length=50)
    assistant_id: Optional[str] = Field(None, min_length=3, max_length=50)


##################################################
########### RESPONSE SCHEMAS #####################
##################################################
class CreateThreadResponse(BaseResponse):
    id: str
    user_id: str
    title: str
    assistant_id: Optional[str]
    created_at: datetime


class GetThreadResponse(CreateThreadResponse):
    assistant: Optional[dict] = Field(None, description="Details of the assistant associated with the thread")


class GetThreadsResponse(CursorPagingResponse):
    threads: list[GetThreadResponse]


class UpdateThreadResponse(CreateThreadResponse):
    pass


class GetHistoryResponse(BaseResponse):
    user_id: str
    thread_id: str
    assistant_id: Optional[str] = None
    messages: list[ChatResponse] = Field(
        default_factory=list,
        description="List of messages in the thread, formatted as per the application's message schema",
    )
