
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage

from app.core.enums import MessageName
from app.schemas.history import MessageResponse


def convert_messages_to_dicts(messages: list[BaseMessage]) -> list[MessageResponse]:  # type: ignore
    for message in messages:
        if isinstance(message, HumanMessage):
            yield MessageResponse(role="human", content=message.content)  # type: ignore
        if isinstance(message, AIMessage):
            if message.name == MessageName.AI:
                yield MessageResponse(role="ai", content=message.content)  # type: ignore
            if message.name == MessageName.TOOL:
                yield MessageResponse(role="tool", content=message.content)  # type: ignore
