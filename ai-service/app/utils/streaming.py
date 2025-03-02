import functools
from typing import Any, AsyncIterator, Dict, Optional, Sequence, Union

import orjson
from langchain_core.messages import AnyMessage, BaseMessage, message_chunk_to_message
from langchain_core.runnables import Runnable, RunnableConfig
from langgraph.types import Command

from app.core import logging

logger = logging.get_logger(__name__)

MessagesStream = AsyncIterator[Union[list[AnyMessage], str]]


async def astream_state(
    app: Runnable,
    input_: Union[Sequence[AnyMessage], Dict[str, Any], Command[Any]],
    config: RunnableConfig,
) -> MessagesStream:
    """Stream messages from the runnable."""
    root_run_id: Optional[str] = None
    messages: dict[str, BaseMessage] = {}

    async for event in app.astream_events(input_, config, version="v1", stream_mode="values", exclude_tags=["nostream"]):
        if event["event"] == "on_chain_start" and not root_run_id:
            root_run_id = event["run_id"]
            yield root_run_id
        elif event["event"] == "on_chain_stream" and event["run_id"] == root_run_id:
            new_messages: list[BaseMessage] = []

            # event["data"]["chunk"] is a Sequence[AnyMessage] or a Dict[str, Any]
            state_chunk_msgs: Union[Sequence[AnyMessage], Dict[str, Any]] = event["data"]["chunk"]  # type: ignore
            if isinstance(state_chunk_msgs, dict):
                state_chunk_msgs = event["data"]["chunk"].get("messages")  # type: ignore

            for msg in state_chunk_msgs:
                msg_id = msg["id"] if isinstance(msg, dict) else msg.id  # type: ignore
                if msg_id in messages and msg == messages[msg_id]:
                    continue
                else:
                    messages[msg_id] = msg  # type: ignore
                    new_messages.append(msg)  # type: ignore
            if new_messages:
                yield new_messages  # type: ignore
        elif event["event"] == "on_chat_model_stream":
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
                    "data": orjson.dumps({"run_id": chunk}).decode(),
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
