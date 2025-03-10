import json
from typing import Any


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
