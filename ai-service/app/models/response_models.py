import orjson
from fastapi import HTTPException, Response
from typing import TypeVar, Generic, Optional

from pydantic import Field, BaseModel, ConfigDict
from starlette.responses import JSONResponse

class AnswerMessage(BaseModel):
    tid: str = Field(..., title="Thread ID", examples=["12345abc"])
    output: str = Field(..., title="Output message", examples=["Hello Jim! How can I help you?."])

class ChatbotResponse(BaseModel):
    status: int = Field(..., title="Status code", examples=[200])
    message: str
    data: AnswerMessage = Field(..., title="Answer message",
                                examples=[{"tid": "12345abc",
                                           "output": "Hello Jim! How can I help you?."}])

class IngestFileResponse(BaseModel):
    status: int = Field(..., title="Status code", examples=[200])
    message: str
    data: AnswerMessage = Field(..., title="Answer message", examples=[{"tid": "12345abc", "output": "File ingested successfully."}])

class RagBotResponse(BaseModel):
    status: int = Field(..., title="Status code", examples=[200])
    message: str
    data: AnswerMessage = Field(..., title="Answer message",
                                examples=[{"tid": "12345abc",
                                           "output": "From the documents you provided, it seems like you are a Vietnamese speaker."}])

class SearchBotResponse(BaseModel):
    status: int = Field(..., title="Status code", examples=[200])
    message: str
    data: AnswerMessage = Field(..., title="Answer message",
                                examples=[{"tid": "12345abc",
                                           "output": "Vietnam's climate varies significantly from north to "
                                                     "south due to its extensive length and diverse geography."}])

class MultiAgentResponse(BaseModel):
    status: int = Field(..., title="Status code", examples=[200])
    message: str
    data: AnswerMessage = Field(..., title="Answer message",
                                examples=[{"tid": "12345abc",
                                           "output": "Hello Jim! How can I help you?."}])

class ExceptionResponse(BaseModel):
    status: int = Field(..., title="Status code", examples=[500])
    message: str = Field(..., title="Message", examples=["An unexpected error occurred."])
    errorStack: str

class ThreadResponse(BaseModel):
    tid: str = Field(..., title="Thread ID", examples=["abcdef"])
    assistant_id: str = Field(..., title="Assistant ID", examples=["12345"])
    user_id: str = Field(..., title="User ID", examples=["12345"])
    name: str = Field(..., title="Name", examples=["Thread 01"])
    updated_at: str = Field(..., title="Updated at", examples=["2022-01-01T00:00:00Z"])


