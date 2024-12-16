from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, constr, Field

from app.models.schemas.paging import PagingResponse


class CreateUserRequest(BaseModel):
    userName: constr(min_length=3, max_length=50)
    email: EmailStr
    firstName: constr(min_length=1, max_length=50)
    lastName: constr(min_length=1, max_length=50)


class CreateUserResponse(BaseModel):
    id: UUID
    email: str
    username: str
    firstName: str
    lastName: str
    createdAt: datetime


class ReadUserResponse(BaseModel):
    id: UUID
    username: str
    email: str
    firstName: str
    lastName: str
    createdAt: datetime

class ReadListUsersResponse(PagingResponse):
    users: list[ReadUserResponse]


class UpdateUserRequest(BaseModel):
    username: constr(min_length=3, max_length=50) | None = None
    email: EmailStr | None = None
    firstName: constr(min_length=1, max_length=50) | None = None
    lastName: constr(min_length=1, max_length=50) | None = None


class UpdateUserResponse(ReadUserResponse):
    pass


class DeleteUserResponse(BaseModel):
    id: UUID
