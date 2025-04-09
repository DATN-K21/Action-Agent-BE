from datetime import datetime
from typing import Optional

from pydantic import Field

from app.core.enums import MessageFormat, MessageRole
from app.schemas.base import BaseResponse, CursorPagingResponse

##################################################
############ REQUEST SCHEMAS #####################
##################################################


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


class MessageInteruption(BaseResponse):
    """Payload for interruption."""

    question: str
    choices: list[str]
    answer_idx: Optional[int] = None


class GetHistoryMessageResponse(BaseResponse):
    format: MessageFormat = Field(..., title="Format of the message", examples=[MessageFormat.MARKDOWN, MessageFormat.FILE])
    content: str = Field(..., title="Content of the message", examples=["Hello", "Hi"])
    role: MessageRole = Field(..., title="Role of the message", examples=[MessageRole.HUMAN, MessageRole.AI, MessageRole.SYSTEM, MessageRole.TOOL])
    created_at: datetime = Field(..., title="Created at", examples=[datetime(2023, 10, 1, 12, 0, 0)])
    interuption: Optional[MessageInteruption] = Field(
        None,
        title="Payload for interruption",
        examples=[
            {"question": "Do you want to continue?", "choices": ["Yes", "No"], "answer_idx": None},
            {"question": "Do you want to continue?", "choices": ["Yes", "No"], "answer_idx": 1},
        ],
    )


class GetHistoryMessagesResponse(CursorPagingResponse):
    user_id: str = Field(..., title="User ID", examples=["user_123"])
    thread_id: str = Field(..., title="Thread ID", examples=["thread_123"])
    messages: list[GetHistoryMessageResponse] = Field(
        [],
        title="List of messages",
    )
