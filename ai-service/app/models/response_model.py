from pydantic import Field, BaseModel

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

class GmailAgentResponse(BaseModel):
    status: int = Field(..., title="Status code", examples=[200])
    message: str
    data: AnswerMessage = Field(..., title="Answer message",
                                examples=[{"tid": "12345abc",
                                           "output": "Hello Jim! How can I help you?."}])