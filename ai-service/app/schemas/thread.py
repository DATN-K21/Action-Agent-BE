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


class FilterThreadRequest(BaseRequest):
    thread_type: Optional[str] = Field(None, description="Filter by thread type")


class UpdateThreadRequest(BaseRequest):
    title: Optional[str] = Field(None, min_length=3, max_length=50)
    thread_type: Optional[str] = Field(None, min_length=3, max_length=50)


##################################################
########### RESPONSE SCHEMAS #####################
##################################################
class CreateThreadResponse(BaseResponse):
    id: str
    user_id: str
    title: str
    thread_type: Optional[str]
    created_at: datetime


class GetThreadResponse(BaseResponse):
    id: str
    user_id: str
    title: str
    thread_type: Optional[str]
    created_at: datetime


class GetListThreadsResponse(CursorPagingResponse):
    threads: list[GetThreadResponse]


class UpdateThreadResponse(CreateThreadResponse):
    id: str
    user_id: str
    title: str
    created_at: datetime


class DeleteThreadResponse(BaseResponse):
    id: str
    user_id: str