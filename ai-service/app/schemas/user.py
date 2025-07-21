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
    first_name: str = Field(..., min_length=0, max_length=50)
    last_name: str = Field(..., min_length=0, max_length=50)

    @field_validator("email")
    def normalize_email(cls, v: str) -> str:
        return v.lower()


class UpdateUserRequest(BaseModel):
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[EmailStr] = Field(None, max_length=50)
    first_name: Optional[str] = Field(None, min_length=0, max_length=50)
    last_name: Optional[str] = Field(None, min_length=0, max_length=50)


class SetUserSettingsRequest(BaseModel):
    basic_model_provider: Optional[str] = Field(None, description="Provider for the basic model")
    basic_model_name: Optional[str] = Field(None, description="Name of the basic model")
    basic_model_api_key: Optional[str] = Field(None, description="API key for the basic model")
    basic_model_temperature: float = Field(0.0, ge=0.0, le=1.0, description="Temperature for the basic model")
    basic_model_base_url: Optional[str] = Field(None, description="Base URL for the basic model")

    reasoning_model_provider: Optional[str] = Field(None, description="Provider for the reasoning model")
    reasoning_model_name: Optional[str] = Field(None, description="Name of the reasoning model")
    reasoning_model_api_key: Optional[str] = Field(None, description="API key for the reasoning model")
    reasoning_model_temperature: float = Field(0.0, ge=0.0, le=1.0, description="Temperature for the reasoning model")
    reasoning_model_base_url: Optional[str] = Field(None, description="Base URL for the reasoning model")

    embedding_model_provider: Optional[str] = Field(None, description="Provider for the embedding model")
    embedding_model_name: Optional[str] = Field(None, description="Name of the embedding model")
    embedding_model_api_key: Optional[str] = Field(None, description="API key for the embedding model")
    embedding_model_base_url: Optional[str] = Field(None, description="Base URL for the embedding model")


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
    
class GetUserCreditsResponse(BaseResponse):
    credits: int = Field(0)


class GetUsersResponse(PagingResponse):
    users: list[GetUserResponse]


class UpdateUserResponse(GetUserResponse):
    pass


class DeleteUserResponse(BaseResponse):
    id: str = Field(...)


class GetUserSettingsResponse(BaseResponse):
    basic_model_provider: Optional[str] = Field(None)
    basic_model_name: Optional[str] = Field(None)
    basic_model_api_key: Optional[str] = Field(None)
    basic_model_temperature: float = Field(0.0, ge=0.0, le=1.0)
    basic_model_base_url: Optional[str] = Field(None)

    reasoning_model_provider: Optional[str] = Field(None)
    reasoning_model_name: Optional[str] = Field(None)
    reasoning_model_api_key: Optional[str] = Field(None)
    reasoning_model_temperature: float = Field(0.0, ge=0.0, le=1.0)
    reasoning_model_base_url: Optional[str] = Field(None)

    embedding_model_provider: Optional[str] = Field(None)
    embedding_model_name: Optional[str] = Field(None)
    embedding_model_api_key: Optional[str] = Field(None)
    embedding_model_base_url: Optional[str] = Field(None)