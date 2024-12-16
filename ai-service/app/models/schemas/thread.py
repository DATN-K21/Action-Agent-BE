from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, constr

from app.models.schemas.paging import PagingResponse


class CreateThreadRequest(BaseModel):
    userId: UUID
    name: str


class CreateThreadResponse(BaseModel):
    id: UUID
    userId: UUID
    name: str
    createdAt: datetime


class ReadThreadResponse(CreateThreadResponse):
    pass


class ReadListThreadsResponse(PagingResponse):
    threads: list[ReadThreadResponse]


class UpdateThreadRequest(BaseModel):
    name: constr(min_length=1, max_length=50) | None = None


class UpdateThreadResponse(CreateThreadResponse):
    pass


class DeleteThreadResponse(BaseModel):
    id: UUID