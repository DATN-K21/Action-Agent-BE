import json
from typing import Any

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


def convert_dict_message_to_output(dict_message: dict) -> Any | None:
    if dict_message["event"] != "data":
        return None

    data = json.loads(dict_message["data"])
    if isinstance(data, list) and len(data) > 0:
        message = data[-1]
        if message['type'] == 'ai':
            if 'tool_calls' in message and len(message['tool_calls']) > 0:
                tool_calls = message['tool_calls']
                return tool_calls

            if 'tool_calls' in message and len(message['tool_calls']) == 0:
                return message["content"]
    return None


def convert_dict_message_to_tool_calls(dict_message: dict) -> Any | None:
    if dict_message["event"] != "data":
        return None

    data = json.loads(dict_message["data"])
    if isinstance(data, list) and len(data) > 0:
        message = data[-1]
        if message['type'] == 'ai':
            if 'tool_calls' in message and len(message['tool_calls']) > 0:
                tool_calls = message['tool_calls']
                return tool_calls
    return None


def convert_dict_message_to_message(dict_message: dict) -> Any | None:
    if dict_message["event"] != "data":
        return None

    data = json.loads(dict_message["data"])
    if isinstance(data, list) and len(data) > 0:
        message = data[-1]
        if message['type'] == 'ai':
            if 'tool_calls' in message and len(message['tool_calls']) == 0:
                return message["content"]
    return None
