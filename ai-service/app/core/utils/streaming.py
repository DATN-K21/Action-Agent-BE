import functools
import json
from enum import StrEnum
from typing import Any, AsyncIterator, Dict, Optional, Sequence, Union

import orjson
from langchain_core.messages import AnyMessage, BaseMessage, message_chunk_to_message
from langchain_core.runnables import Runnable, RunnableConfig
from langgraph.types import Command
from pydantic import BaseModel

from app.core import logging
from app.core.utils.convert_dict_message import convert_dict_message_to_message, convert_dict_message_to_output, \
    convert_dict_message_to_tool_calls
from app.schemas.extension import ExtensionResponse

logger = logging.get_logger(__name__)

MessagesStream = AsyncIterator[Union[list[AnyMessage], str]]


class LanggraphNodeEnum(StrEnum):
    AGENT_NODE = "agent_node"
    ENHANCE_PROMPT_NODE = "enhance_prompt_node"
    SELECT_TOOL_NODE = "select_tool_node"
    EVALUATE_HUMAN_IN_LOOP_NODE = "evaluate_human_in_loop_node"
    HUMAN_EDITING_NODE = "human_editing_node"
    TOOL_NODE = "tool_node"
    GENERATE_NODE = "generate_node"


class Metadata(BaseModel):
    run_id: str
    langgraph_node: str


list_stream_nodes = [
    LanggraphNodeEnum.AGENT_NODE,
    LanggraphNodeEnum.SELECT_TOOL_NODE,
    LanggraphNodeEnum.HUMAN_EDITING_NODE,
    LanggraphNodeEnum.GENERATE_NODE,
]


async def astream_state(
        app: Runnable,
        input_: Union[Sequence[AnyMessage], Dict[str, Any], Command[Any]],
        config: RunnableConfig,
        allow_stream_nodes: Optional[Sequence[LanggraphNodeEnum]] = None,
) -> MessagesStream:
    """Stream messages from the runnable."""
    messages: dict[str, BaseMessage] = {}
    run_id: Optional[str] = None

    async for event in app.astream_events(input_, config, version="v1", stream_mode="all"):
        metadata = event.get("metadata")
        langgraph_node = metadata.get("langgraph_node")

        if event["event"] == "on_chat_model_stream":
            if allow_stream_nodes is None or (langgraph_node in LanggraphNodeEnum.__members__.values()
                                              and LanggraphNodeEnum(langgraph_node) in allow_stream_nodes
            ):
                if run_id != event["run_id"]:
                    run_id = event["run_id"]
                    yield Metadata(run_id=run_id, langgraph_node=langgraph_node).model_dump_json()

                message: BaseMessage = event["data"]["chunk"]  # type: ignore
                if message.id not in messages:
                    messages[message.id] = message  # type: ignore
                else:
                    messages[message.id] += message  # type: ignore
                yield [messages[message.id]]  # type: ignore


def _default(obj) -> Any:
    if hasattr(obj, "dict") and callable(obj.dict):
        return obj.dict()
    raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")


dumps = functools.partial(orjson.dumps, default=_default)


async def to_sse(messages_stream: MessagesStream) -> AsyncIterator[dict]:
    """Consume the stream into an EventSourceResponse"""
    try:
        async for chunk in messages_stream:
            # EventSourceResponse expects a string for data
            # so after serializing into bytes, we decode into utf-8
            # to get a string.

            if isinstance(chunk, str):
                yield {
                    "event": "metadata",
                    "data": orjson.dumps(json.loads(chunk)).decode(),
                }
            else:
                yield {
                    "event": "data",
                    "data": dumps(
                        [message_chunk_to_message(msg) for msg in chunk]  # type: ignore
                    ).decode(),
                }
    except Exception:
        logger.error("error in stream", exc_info=True)
        raise

    # Send an end event to signal the end of the stream
    yield {"event": "end"}


async def format_extension_stream_sse(messages_stream: MessagesStream) -> AsyncIterator[str]:
    interrupted = False
    async for dict_message in to_sse(messages_stream):
        if dict_message.get("event") == "metadata":
            dict_message_data = json.loads(dict_message.get("data"))
            if dict_message_data["langgraph_node"] == LanggraphNodeEnum.HUMAN_EDITING_NODE:
                interrupted = True
        elif interrupted:
            tool_calls = convert_dict_message_to_tool_calls(dict_message)
            if tool_calls is not None:
                data = ExtensionResponse(
                    interrupted=True,
                    streaming=True,
                    output=tool_calls
                ).model_dump_json()

                yield {
                    "event": "data",
                    "data": data,
                }

        else:
            message = convert_dict_message_to_message(dict_message)
            if message is not None:
                data = ExtensionResponse(
                    interrupted=False,
                    streaming=True,
                    output=message
                ).model_dump_json()
                yield {
                    "event": "data",
                    "data": data,
                }

        if dict_message.get("event") == "end":
            yield {"event": "end"}


async def format_extension_interrupt_sse(messages_stream: MessagesStream) -> AsyncIterator[str]:
    async for dict_message in to_sse(messages_stream):
        output = convert_dict_message_to_output(dict_message)
        if output is not None:
            data = ExtensionResponse(
                interrupted=False,
                streaming=True,
                output=output
            ).model_dump_json()
            yield {
                "event": "data",
                "data": data,
            }

        if dict_message.get("event") == "end":
            yield {"event": "end"}
