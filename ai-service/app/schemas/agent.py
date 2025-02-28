from typing import Optional

from pydantic import Field

from app.schemas.base import BaseRequest, BaseResponse


##################################################
########### REQUEST SCHEMAS ######################
##################################################
class AgentRequest(BaseRequest):
    input: str = Field(ge=1, le=5000, title="Input", examples=["Hello!"])
    user_id: str = Field(ge=1, le=100, title="User ID", examples=["userid123"])
    thread_id: str = Field(ge=1, le=100, title="Thread ID", examples=["threadid123"])
    agent_name: str = Field(ge=1, le=100, title="Agent Name", examples=["chat-agent"])
    recursion_limit: Optional[int] = Field(None, title="Recursion Limit", examples=[5])

##################################################
########### RESPONSE SCHEMAS #####################
##################################################
class AgentResponse(BaseResponse):
    thread_id: Optional[str] = Field(None, title="Thread ID", examples=["abcdef"])
    output: Optional[str] = Field(None, title="Output", examples=["Hello!"])

class GetAgentNamesResponse(BaseResponse):
    agent_names: list[str] = Field(title="Agent Names", examples=[["chat-agent", "email-agent"]])