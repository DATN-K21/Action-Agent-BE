from typing import Optional, Any

from pydantic import BaseModel, Field, model_validator

from app.core.enums import ChatMessageType, InterruptType, InterruptDecision


class ChatMessage(BaseModel):
    type: ChatMessageType
    content: str
    imgdata: str | None = None  # 添加 imgdata 字段


class Interrupt(BaseModel):
    interaction_type: InterruptType | None = None
    decision: InterruptDecision
    tool_message: str | None = None


class TeamChat(BaseModel):
    messages: list[ChatMessage]
    interrupt: Interrupt | None = None


class TeamChatPublic(BaseModel):
    message: ChatMessage | None = None
    interrupt: Interrupt | None = None

    @model_validator(mode="after")
    def check_either_field(cls: Any, values: Any) -> Any:
        message, interrupt = values.message, values.interrupt
        if not message and not interrupt:
            raise ValueError('Either "message" or "interrupt" must be provided.')
        return values


class MemberBase(BaseModel):
    name: str = Field(..., pattern=r"^[a-zA-Z0-9_-]{1,64}$")
    backstory: Optional[str] = None
    role: str
    type: str  # one of: leader, worker, freelancer
    owner_of: Optional[int] = None
    position_x: float
    position_y: float
    source: Optional[int] = None
    provider: str = ""
    model: str = ""
    temperature: float = 0.1
    interrupt: bool = False


class TeamBase(BaseModel):
    name: str = Field(..., pattern=r"^[a-zA-Z0-9_-]{1,64}$")
    description: Optional[str] = None
    icon: Optional[str] = None  # Add an icon field for the team
