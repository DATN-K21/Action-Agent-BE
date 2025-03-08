from typing import Any, Dict

from pydantic import Field

from app.schemas.base import BaseResponse


##################################################
########### RESPONSE SCHEMAS #####################
##################################################
class GetHistoryResponse(BaseResponse):
    messages: list[Dict[str, Any]] = Field(..., title="List of messages", examples=[{"human": "Hello", "ai": "Hi"}])
