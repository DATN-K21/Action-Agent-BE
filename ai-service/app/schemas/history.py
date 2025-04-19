
from pydantic import Field

from app.schemas._base import BaseResponse


##################################################
########### RESPONSE SCHEMAS #####################
##################################################
class MessageResponse(BaseResponse):
    role: str = Field(..., title="Role of the message", examples=["human", "ai"])
    content: str = Field(..., title="Content of the message", examples=["Hello", "Hi"])


class GetHistoryResponse(BaseResponse):
    messages: list[MessageResponse] = Field(
        [],
        title="List of messages",
        examples=[[{"role": "human", "content": "Hello"}, {"role": "ai", "content": "Hi"}]],
    )
