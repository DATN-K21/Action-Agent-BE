from typing import Generic, Optional, TypeVar

from fastapi.responses import ORJSONResponse
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


##################################################
############## BASE REQUEST ######################
##################################################
class BaseRequest(BaseModel):
    class Config:
        from_attributes = True  # Enable attribute-based mapping
        alias_generator = to_camel  # Converts field names to snake_case
        populate_by_name = True  # Allows field name population even if alias is used
        max_number_errors = 1  # Maximum number of errors to display in case of validation error
        validate_asignment = True  # Validate assignment of values to fields
        cache_strings = "all"


class PagingRequest(BaseRequest):
    page_number: int = Field(1, ge=1, description="Page number must be 1 or greater")
    max_per_page: int = Field(10, ge=1, le=100, description="Max per page must be between 1 and 100")


class CursorPagingRequest(BaseRequest):
    cursor: Optional[str] = Field(None, description="Cursor for pagination")
    max_per_page: int = Field(10, ge=1, le=100, description="Max per page must be between 1 and 100")


##################################################
############## BASE RESPONSE #####################
##################################################
class BaseResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True, alias_generator=to_camel, populate_by_name=True, validate_assignment=True, cache_strings="all"
    )


T = TypeVar("T", bound=BaseResponse)


class ResponseWrapper(BaseModel, Generic[T]):
    status: int = Field(200, description="HTTP status code")
    message: Optional[str] = Field(None, description="Response message")
    data: Optional[T] = Field(None, description="Response data")

    def __init__(self, status: int = 200, data: Optional[T] = None, message: Optional[str] = None):
        super().__init__(status=status, data=data, message=message)

    def to_response(self) -> ORJSONResponse:
        return ORJSONResponse(
            status_code=self.status,
            content=self.model_dump(),
        )

    @classmethod
    def wrap(cls, status: int, data: Optional[T] = None, message: Optional[str] = None) -> "ResponseWrapper[T]":
        return ResponseWrapper(status=status, data=data, message=message)


class PagingResponse(BaseResponse):
    page_number: int
    max_per_page: int
    total_page: int


class CursorPagingResponse(BaseResponse):
    cursor: Optional[str] = Field(None, description="Cursor for pagination")
    next_cursor: Optional[str] = Field(None, description="Next cursor for pagination")
    prev_cursor: Optional[str] = Field(None, description="Previous cursor for pagination")
