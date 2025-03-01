from typing import Dict, Any
from pydantic import Field

from app.schemas.base import BaseResponse


##################################################
########### RESPONSE SCHEMAS #####################
##################################################
class GetHistoryResponse(BaseResponse):
    messages: list[Dict[str, Any]] = Field(..., title="List of history", examples=[{"human": "value1", "ai": "value2"}])