import json

from pydantic import BaseModel


class BinaryScore(BaseModel):
    interrupted: bool


def convert_dict_message_to_binary_score(dict_message: dict) -> BinaryScore | None:
    if dict_message["event"] != "data":
        return None

    data = json.loads(dict_message["data"])
    if isinstance(data, list) and len(data) > 0:
        message = data[-1]
        if message['type'] == 'ai':
            if 'tool_calls' in message and len(message['tool_calls']) > 0:
                tool_call = message['tool_calls'][-1]
                if tool_call["name"] == "BinaryScore":
                    args = tool_call["args"]
                    if "score" in args and args["score"] == "yes":
                        return BinaryScore(interrupted=True)

                    if "score" in args and args["score"] == "no":
                        return BinaryScore(interrupted=False)
    return None


def convert_dict_message_to_tool_call(dict_message: dict) -> dict | None:
    if dict_message["event"] != "data":
        return None

    data = json.loads(dict_message["data"])
    if isinstance(data, list) and len(data) > 0:
        message = data[-1]
        if message['type'] == 'ai':
            if 'tool_calls' in message and len(message['tool_calls']) > 0:
                tool_call = message['tool_calls'][-1]
                if tool_call["name"] != "BinaryScore":
                    return tool_call

    return None


def convert_dict_message_to_message(dict_message: dict) -> dict | None:
    if dict_message["event"] != "data":
        return None

    data = json.loads(dict_message["data"])
    if isinstance(data, list) and len(data) > 0:
        message = data[-1]
        if message['type'] == 'ai':
            if 'tool_calls' in message and len(message['tool_calls']) == 0:
                return message["content"]

    return None
