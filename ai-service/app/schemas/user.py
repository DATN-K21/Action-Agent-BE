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
    first_name: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=50)

    @field_validator("email")
    def normalize_email(cls, v: str) -> str:
        return v.lower()


class UpdateUserRequest(BaseModel):
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[EmailStr] = Field(None, max_length=50)
    first_name: Optional[str] = Field(None, min_length=1, max_length=50)
    last_name: Optional[str] = Field(None, min_length=1, max_length=50)


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
    first_name: Optional[str] = Field(None)
    last_name: Optional[str] = Field(None)
    created_at: Optional[datetime] = Field(None)


class GetUsersResponse(PagingResponse):
    users: list[GetUserResponse]


class UpdateUserResponse(GetUserResponse):
    pass


class DeleteUserResponse(BaseResponse):
    id: str = Field(...)
