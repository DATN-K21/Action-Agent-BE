from typing import Any

from pydantic import Field

from app.schemas.base import BaseResponse


##################################################
########### RESPONSE SCHEMAS #####################
##################################################
class GetHistoryResponse(BaseResponse):
    messages: list[dict[str, Any]] = Field(..., title="List of messages", examples=[{"human": "Hello", "ai": "Hi"}])
