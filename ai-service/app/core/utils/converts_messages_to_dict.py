from typing import Sequence, Dict, Any

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage

from app.utils.enums import MessageName


def converts_messages_to_dicts(messages: Sequence[BaseMessage]) -> Sequence[Dict[str, Any]]:
    for message in messages:
        if isinstance(message, HumanMessage):
            yield {"human": message.content}
        if isinstance(message, AIMessage):
            if message.name == MessageName.AI:
                yield {"ai": message.content}
            if message.name == MessageName.TOOL:
                yield {"tool": message.content}