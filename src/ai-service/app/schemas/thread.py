from datetime import datetime
from typing import Optional

from pydantic import Field

from app.schemas.base import BaseRequest, BaseResponse, CursorPagingResponse


##################################################
########### REQUEST SCHEMAS ######################
##################################################
class CreateThreadRequest(BaseRequest):
    id: Optional[str] = None
    title: str = Field(..., min_length=3, max_length=50)
    thread_type: Optional[str] = Field(None, min_length=3, max_length=50)
    assistant_id: Optional[str] = Field(None, min_length=3, max_length=50)


class FilterThreadRequest(BaseRequest):
    thread_type: Optional[str] = Field(None, description="Filter by thread type")
    assistant_id: Optional[str] = Field(None, min_length=3, max_length=50)


class UpdateThreadRequest(BaseRequest):
    title: Optional[str] = Field(None, min_length=3, max_length=50)
    thread_type: Optional[str] = Field(None, min_length=3, max_length=50)
    assistant_id: Optional[str] = Field(None, min_length=3, max_length=50)


##################################################
########### RESPONSE SCHEMAS #####################
##################################################
class CreateThreadResponse(BaseResponse):
    id: str
    user_id: str
    title: str
    thread_type: Optional[str]
    assistant_id: Optional[str]
    created_at: datetime


class GetThreadResponse(CreateThreadResponse):
    pass


class GetThreadsResponse(CursorPagingResponse):
    threads: list[GetThreadResponse]


class UpdateThreadResponse(CreateThreadResponse):
    pass


class DeleteThreadResponse(BaseResponse):
    id: str
    user_id: str
    assistant_id: str
