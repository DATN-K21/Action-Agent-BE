from pydantic import Field, BaseModel

class ChatbotRequest(BaseModel):
    tid: str = Field(..., title="Thread ID", examples=["67890def"])
    input: str = Field(..., title="Input message", examples=["Hi! I'm Jim."])

class RagBotRequest(BaseModel):
    tid: str = Field(..., title="Thread ID", examples=["12345abc"])
    input: str = Field(..., title="Input message", examples=["Give me a fact in the documents."])

class SearchBotRequest(BaseModel):
    tid: str = Field(..., title="Thread ID", examples=["12345abc"])
    input: str = Field(..., title="Input message", examples=["What is the weather in Vietnam?"])

class MultiAgentRequest(BaseModel):
    tid: str = Field(..., title="Thread ID", examples=["abcdef"])
    input: str = Field(..., title="Input message", examples=["Hi! I'm Jim."])

class GmailAgentRequest(BaseModel):
    tid: str = Field(..., title="Thread ID", examples=["abcdef"])
    input: str = Field(..., title="Input message", examples=["Hi! I'm Jim."])





