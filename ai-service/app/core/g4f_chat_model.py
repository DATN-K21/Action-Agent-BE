# from __future__ import annotations
#
# from typing import Any, Dict, Self
#
# from g4f.client import AsyncClient, Client
# from g4f.client.stubs import ChatCompletionMessage
# from langchain_core.messages import BaseMessage
# from langchain_openai.chat_models import base
# from langchain_openai.chat_models.base import _convert_message_to_dict, ChatOpenAI
# from pydantic import Field, model_validator
#
#
# def new_convert_message_to_dict(message: BaseMessage) -> dict:
#     message_dict: Dict[str, Any]
#     if isinstance(message, ChatCompletionMessage):
#         message_dict = {"role": message.role, "content": message.content}
#         if message.tool_calls is not None:
#             message_dict["tool_calls"] = [{
#                 "id": tool_call.id,
#                 "type": tool_call.type,
#                 "function": tool_call.function
#             } for tool_call in message.tool_calls]
#             if message_dict["content"] == "":
#                 message_dict["content"] = None
#     else:
#         message_dict = _convert_message_to_dict(message)
#     return message_dict
#
#
# base._convert_message_to_dict = new_convert_message_to_dict
#
#
# class ChatAI(ChatOpenAI):
#     model_name: str = Field(default="gpt-4o", alias="model")
#
#     @model_validator(mode="after")
#     def validate_environment(self) -> Self:
#         client_params = {
#             "api_key": self.openai_api_key.get_secret_value() if self.openai_api_key else None,
#             "provider": self.model_kwargs["provider"] if "provider" in self.model_kwargs else None,
#         }
#         self.root_client = Client(**client_params)
#         self.client = self.root_client.chat.completions
#         self.root_async_client = AsyncClient(
#             **client_params
#         )
#         self.async_client = self.root_async_client.chat.completions
#         return self

from __future__ import annotations

from typing import Any, Dict

from g4f.client import AsyncClient, Client
from g4f.client.stubs import ChatCompletionMessage
from langchain_community.chat_models import openai
from langchain_community.chat_models.openai import ChatOpenAI, BaseMessage, convert_message_to_dict
from pydantic import Field


def new_convert_message_to_dict(message: BaseMessage) -> dict:
    message_dict: Dict[str, Any]
    if isinstance(message, ChatCompletionMessage):
        message_dict = {"role": message.role, "content": message.content}
        if message.tool_calls is not None:
            message_dict["tool_calls"] = [{
                "id": tool_call.id,
                "type": tool_call.type,
                "function": tool_call.function
            } for tool_call in message.tool_calls]
            if message_dict["content"] == "":
                message_dict["content"] = None
    else:
        message_dict = convert_message_to_dict(message)
    return message_dict


openai.convert_message_to_dict = new_convert_message_to_dict


class ChatAI(ChatOpenAI):
    model_name: str = Field(default="gpt-4o", alias="model")

    @classmethod
    def validate_environment(cls, values: dict) -> dict:
        client_params = {
            "api_key": values["api_key"] if "api_key" in values else None,
            "provider": values["model_kwargs"]["provider"] if "provider" in values["model_kwargs"] else None,
        }
        values["client"] = Client(**client_params).chat.completions
        values["async_client"] = AsyncClient(
            **client_params
        ).chat.completions
        return values
