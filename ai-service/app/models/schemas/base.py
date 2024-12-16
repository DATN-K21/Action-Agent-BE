from datetime import datetime
from typing import TypeVar, Generic, Optional, Type
from uuid import UUID

from pydantic import BaseModel, Field
from starlette.responses import JSONResponse

T = TypeVar("T")


class BaseResponse(BaseModel, Generic[T]):
    status: int = Field(..., description="HTTP status code")
    message: Optional[str] = Field(None, description="Error or success message")
    data: Optional[T] = Field(None, description="Response data")

    def to_response(self) -> JSONResponse:
        return JSONResponse(
            status_code=self.status,
            content=self.model_dump(exclude_none=True),
        )

    @classmethod
    def success(cls: Type["BaseResponse"], status: int, data: T) -> "BaseResponse[T]":
        return cls(status=status, message=None, data=data)

    @classmethod
    def error(cls: Type["BaseResponse"], status: int, message: str) -> "BaseResponse[T]":
        return cls(status=status, message=message, data=None)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: str,
        }
