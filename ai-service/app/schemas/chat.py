from pydantic import Field

from app.schemas.base import BaseRequest, BaseResponse


##################################################
########### REQUEST SCHEMAS ######################
##################################################
class AgentRequest(BaseRequest):
    thread_id: str = Field(..., title="Thread ID", examples=["Enter thread ID here."], max_length=100, min_length=1)
    input: str = Field(..., title="Input message", examples=["Enter prompt here."], max_length=5000, min_length=1)


##################################################
########### RESPONSE SCHEMAS #####################
##################################################
class AgentResponse(BaseResponse):
    success: bool = Field(..., title="Success", examples=[True])
    thread_id: str = Field(..., title="Thread ID", examples=["abcdef"])
    output: str = Field(..., title="Output", examples=["Hello!"])
