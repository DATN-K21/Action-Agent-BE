from typing import Any, Dict

from langchain.tools.base import BaseTool
from pydantic import BaseModel, model_validator

from app.core.enums import ChatMessageType, InterruptDecision, InterruptType


class ToolInfo(BaseModel):
    description: str | None = None
    tool: BaseTool
    display_name: str | None = None
    input_parameters: Dict[str, Any] | None = None
    credentials: Dict[str, Any] | None = None


class ChatMessage(BaseModel):
    type: ChatMessageType
    content: str
    imgdata: str | None = None  # Add imgdata field


class Interrupt(BaseModel):
    interaction_type: InterruptType | None = None
    decision: InterruptDecision
    tool_message: str | None = None


class AssistantChat(BaseModel):
    messages: list[ChatMessage]
    interrupt: Interrupt | None = None


class AssistantChatPublic(BaseModel):
    message: ChatMessage | None = None
    interrupt: Interrupt | None = None

    @model_validator(mode="after")
    def check_either_field(cls: Any, values: Any) -> Any:
        message, interrupt = values.message, values.interrupt
        if not message and not interrupt:
            raise ValueError('Either "message" or "interrupt" must be provided.')
        return values

