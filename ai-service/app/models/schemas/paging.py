from fastapi import Query
from pydantic import BaseModel, ConfigDict, field_validator


class PagingRequest(BaseModel):
    pageNumber: int = Query(1, ge=1, description='Page number must be 1 or greater')
    maxPerPage: int = Query(10, ge=1, le=100, description='Max per page must be between 1 and 100')

    model_config = ConfigDict(from_attributes=True)

class PagingResponse(BaseModel):
    pageNumber: int
    maxPerPage: int
    totalPage: int
