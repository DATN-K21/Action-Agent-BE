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


class UpdateThreadRequest(BaseRequest):
    title: Optional[str] = Field(None, min_length=3, max_length=50)


##################################################
########### RESPONSE SCHEMAS #####################
##################################################
class CreateThreadResponse(BaseResponse):
    id: str
    userId: str
    title: str
    createdAt: datetime


class GetThreadResponse(BaseResponse):
    id: str
    userId: str
    title: str
    createdAt: datetime


class GetListThreadsResponse(CursorPagingResponse):
    threads: list[GetThreadResponse]


class UpdateThreadResponse(CreateThreadResponse):
    id: str
    userId: str
    title: str
    createdAt: datetime


class DeleteThreadResponse(BaseResponse):
    id: str
    userId: str
