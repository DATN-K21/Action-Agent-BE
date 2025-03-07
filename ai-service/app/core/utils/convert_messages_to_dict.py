from typing import Any, Dict, Sequence

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage

from app.utils.enums import MessageName


def convert_messages_to_dicts(messages: Sequence[BaseMessage]) -> Sequence[Dict[str, Any]]:  # type: ignore
    for message in messages:
        if isinstance(message, HumanMessage):
            yield {"human": message.content}  # type: ignore
        if isinstance(message, AIMessage):
            if message.name == MessageName.AI:
                yield {"ai": message.content}  # type: ignore
            if message.name == MessageName.TOOL:
                yield {"tool": message.content}  # type: ignore
