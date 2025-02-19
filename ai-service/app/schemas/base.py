from datetime import datetime
from typing import Generic, Optional, TypeVar

from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.utils.string import to_snake_case


##################################################
############## BASE REQUEST ######################
##################################################
class BaseRequest(BaseModel):
    class Config:
        from_attributes = True  # Enable attribute-based mapping
        alias_generator = to_snake_case  # Converts field names to snake_case
        populate_by_name = True  # Allows field name population even if alias is used


class PagingRequest(BaseRequest):
    pageNumber: int = Field(1, ge=1, description="Page number must be 1 or greater")
    maxPerPage: int = Field(10, ge=1, le=100, description="Max per page must be between 1 and 100")


class CursorPagingRequest(BaseRequest):
    cursor: Optional[str] = Field(None, description="Cursor for pagination")
    maxPerPage: int = Field(10, ge=1, le=100, description="Max per page must be between 1 and 100")


##################################################
############## BASE RESPONSE #####################
##################################################
class BaseResponse(BaseModel):
    class Config:
        from_attributes = True  # Enable attribute-based mapping
        alias_generator = to_snake_case  # Converts field names to snake_case
        populate_by_name = True  # Allows field name population even if alias is used


T = TypeVar("T", bound=BaseResponse)


class ResponseWrapper(BaseModel, Generic[T]):
    def __init__(
        self,
        status: int,
        data: Optional[T] = None,
        message: Optional[str] = None,
    ):
        self.status = status
        self.data = data
        self.message = message

    def to_response(self) -> JSONResponse:
        return JSONResponse(
            status_code=self.status,
            content=self.model_dump(),
        )

    @classmethod
    def wrap(cls, status: int, data: Optional[T] = None, message: Optional[str] = None) -> "ResponseWrapper[T]":
        return cls(status=status, data=data, message=message)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }


class PagingResponse(BaseResponse):
    pageNumber: int
    maxPerPage: int
    totalPage: int


class CursorPagingResponse(BaseResponse):
    cursor: Optional[str] = Field(None, description="Cursor for pagination")
    nextCursor: Optional[str] = Field(None, description="Next cursor for pagination")
    prevCursor: Optional[str] = Field(None, description="Previous cursor for pagination")
