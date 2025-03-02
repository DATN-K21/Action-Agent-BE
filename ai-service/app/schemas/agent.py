from typing import Optional

from pydantic import Field

from app.schemas.base import BaseRequest, BaseResponse


##################################################
########### REQUEST SCHEMAS ######################
##################################################
class AgentRequest(BaseRequest):
    input: str = Field(min_length=1, max_length=8000, title="Input", examples=["Hello!"])
    thread_id: str = Field(min_length=1, max_length=100, title="Thread ID", examples=["threadid123"])
    agent_name: str = Field(min_length=1, max_length=100, title="Agent Name", examples=["chat-agent"])
    recursion_limit: Optional[int] = Field(None, ge=1, le=100, title="Recursion Limit", examples=[5])


##################################################
########### RESPONSE SCHEMAS #####################
##################################################
class AgentResponse(BaseResponse):
    thread_id: Optional[str] = Field(None, title="Thread ID", examples=["abcdef"])
    output: Optional[str] = Field(None, title="Output", examples=["Hello!"])


class GetAgentsResponse(BaseResponse):
    agent_names: list[str] = Field(title="Agent Names", examples=[["chat-agent", "email-agent"]])
