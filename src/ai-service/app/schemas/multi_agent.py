from typing import Optional

from pydantic import Field

from app.schemas.base import BaseRequest, BaseResponse


##################################################
########### REQUEST SCHEMAS ######################
##################################################
class MultiAgentChatRequest(BaseRequest):
    input: str = Field(min_length=1, max_length=8000, title="Input", examples=["Hello!"])
    recursion_limit: Optional[int] = Field(None, ge=1, le=50, title="Recursion Limit", examples=[20])


##################################################
########### RESPONSE SCHEMAS #####################
##################################################
class MultiAgentResponse(BaseResponse):
    user_id: str = Field(..., title="User ID", examples=["user_123"])
    assistant_id: str = Field(..., title="Assistant ID", examples=["assistant_123"])
    thread_id: str = Field(..., title="Thread ID", examples=["abcdef"])
    output: str = Field(..., title="Output", examples=["Hello!"])
