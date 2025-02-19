from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.schemas.base import BaseRequest, BaseResponse, PagingResponse


##################################################
########### REQUEST SCHEMAS ######################
##################################################
class CreateUserRequest(BaseRequest):
    id: Optional[str] = None
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr = Field(..., max_length=50)
    firstName: str = Field(..., min_length=1, max_length=50)
    lastName: str = Field(..., min_length=1, max_length=50)

    @field_validator("email")
    def normalize_email(cls, v: str) -> str:
        return v.lower()


class UpdateUserRequest(BaseModel):
    userName: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[EmailStr] = Field(None, max_length=50)
    firstName: Optional[str] = Field(None, min_length=1, max_length=50)
    lastName: Optional[str] = Field(None, min_length=1, max_length=50)


##################################################
########### RESPONSE SCHEMAS #####################
##################################################
class CreateUserResponse(BaseResponse):
    id: str = Field(...)
    email: str = Field(...)
    username: str = Field(...)
    first_name: str = Field(...)
    last_name: str = Field(...)
    created_at: datetime = Field(...)


class GetUserResponse(BaseResponse):
    id: str = Field(...)
    email: Optional[str] = Field(None)
    username: Optional[str] = Field(None)
    firstName: Optional[str] = Field(None)
    lastName: Optional[str] = Field(None)
    createdAt: Optional[str] = Field(None)


class GetListUsersResponse(PagingResponse):
    users: list[GetUserResponse]


class UpdateUserResponse(GetUserResponse):
    pass


class DeleteUserResponse(BaseResponse):
    id: str = Field(...)
