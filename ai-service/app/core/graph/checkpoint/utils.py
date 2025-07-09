import json
from typing import Any
from uuid import uuid4

from langchain_core.documents import Document
from langchain_core.messages import AIMessage, AnyMessage, HumanMessage, ToolMessage
from langgraph.checkpoint.base import CheckpointTuple

from app.core.graph.messages import ChatResponse
from app.memory.checkpoint import get_checkpointer


def convert_checkpoint_tuple_to_messages(checkpoint_tuple: CheckpointTuple, recursive: bool = True) -> list[ChatResponse]:
    """
    Convert a checkpoint tuple to a list of ChatResponse messages.

    Args:
        checkpoint_tuple (CheckpointTuple): The checkpoint tuple to convert.
        recursive (bool): Whether to recursively extract messages from subgraphs.

    Returns:
        list[ChatResponse]: A list of formatted messages.
    """
    checkpoint = checkpoint_tuple.checkpoint

    # Collect messages from all relevant channels
    all_messages: list[AnyMessage] = []

    # Add messages from primary channels
    all_messages: list[AnyMessage] = checkpoint["channel_values"]["all_messages"] + checkpoint["channel_values"]["messages"]

    # Ensure each message is unique using id
    seen_ids = set()
    unique_messages = []
    for message in all_messages:
        message_id = getattr(message, "id", None)
        if message_id is not None and message_id not in seen_ids:
            seen_ids.add(message_id)
            unique_messages.append(message)
        elif message_id is None:
            # Keep messages without id as they might be unique
            unique_messages.append(message)

    all_messages = unique_messages

    formatted_messages: list[ChatResponse] = []

    for message in all_messages:
        if isinstance(message, HumanMessage):
            content = ""
            imgdata = None

            if isinstance(message.content, list):
                for c in message.content:
                    if isinstance(c, dict):
                        if c.get("type") == "text":
                            content += c.get("text", "")
                        elif c.get("type") == "image_url":
                            imgdata = c.get("image_url", {}).get("url")
            else:
                content = message.content

            formatted_messages.append(
                ChatResponse(
                    type="human",
                    id=message.id if message.id is not None else str(uuid4()),
                    name=message.name or "",
                    content=content,
                    imgdata=imgdata,
                )
            )
        elif isinstance(message, AIMessage):
            # Ensure content is a string, id and name exist
            if isinstance(message.content, str):
                formatted_messages.append(
                    ChatResponse(
                        type="ai",
                        id=message.id if message.id is not None else str(uuid4()),
                        name=message.name or "",
                        tool_calls=getattr(message, "tool_calls", None),
                        content=message.content,
                    )
                )
            else:
                # Handle non-string content gracefully
                formatted_messages.append(
                    ChatResponse(
                        type="ai",
                        id=message.id if message.id is not None else str(uuid4()),
                        name=message.name or "",
                        tool_calls=getattr(message, "tool_calls", None),
                        content=json.dumps(message.content) if message.content else "",
                    )
                )
        elif isinstance(message, ToolMessage) and message.name:
            documents: list[dict[str, Any]] = []
            if message.name == "KnowledgeBase" and message.artifact is not None:
                docs: list[Document] = message.artifact
                for doc in docs:
                    documents.append(
                        {
                            "score": getattr(doc, "metadata", {}).get("score", 0),
                            "content": getattr(doc, "page_content", ""),
                        }
                    )
            tool_call_id = getattr(message, "tool_call_id", str(uuid4()))
            formatted_messages.append(
                ChatResponse(
                    type="tool",
                    id=tool_call_id,
                    name=message.name,
                    tool_output=json.dumps(message.content),
                    documents=json.dumps(documents),
                )
            )
        else:
            continue

    # Process the last message if all_messages is not empty
    if all_messages:
        last_message = all_messages[-1]
        if isinstance(last_message, AIMessage) and hasattr(last_message, "tool_calls") and last_message.tool_calls:
            # Check if any tool in last message is asking for human input
            for tool_call in last_message.tool_calls:
                if tool_call["name"] == "ask-human":
                    formatted_messages.append(
                        ChatResponse(
                            type="interrupt",
                            name="context_input",
                            content=f"{last_message.content}",
                            tool_calls=last_message.tool_calls,
                            id=str(uuid4()),
                        )
                    )
                    break
            else:
                formatted_messages.append(
                    ChatResponse(
                        type="interrupt",
                        name="interrupt",
                        tool_calls=last_message.tool_calls,
                        id=str(uuid4()),
                    )
                )

    return formatted_messages


async def get_checkpoint_tuples(thread_id: str) -> CheckpointTuple | None:
    """
    Retrieve the latest checkpoint tuple for a given thread ID.

    Args:
        thread_id (str): The ID of the thread.

    Returns:
        CheckpointTuple | None: The latest checkpoint tuple or None if not found.
    """
    try:
        checkpointer = await get_checkpointer()
        checkpoint_tuple = await checkpointer.aget_tuple({"configurable": {"thread_id": thread_id}})
        return checkpoint_tuple
    except Exception:
        return None


def beautify_checkpoint_tuple(checkpoint_tuple: CheckpointTuple) -> str:
    """
    Beautify a CheckpointTuple for better readability.

    Args:
        checkpoint_tuple (CheckpointTuple): The checkpoint tuple to beautify.

    Returns:
        str: A formatted string representation of the checkpoint tuple.
    """
    if not checkpoint_tuple:
        return "No checkpoint data available"

    # Extract key information
    config = checkpoint_tuple.config
    checkpoint = checkpoint_tuple.checkpoint

    formatted_output = []
    formatted_output.append("=" * 80)
    formatted_output.append("CHECKPOINT TUPLE SUMMARY")
    formatted_output.append("=" * 80)

    # Config section
    formatted_output.append("\n📋 CONFIG:")
    formatted_output.append(f"  Thread ID: {config.get('configurable', {}).get('thread_id', 'N/A')}")
    formatted_output.append(f"  Checkpoint NS: {config.get('configurable', {}).get('checkpoint_ns', 'N/A')}")
    formatted_output.append(f"  Checkpoint ID: {config.get('configurable', {}).get('checkpoint_id', 'N/A')}")

    # Checkpoint metadata
    formatted_output.append("\n⏱️  CHECKPOINT METADATA:")
    formatted_output.append(f"  Version: {checkpoint.get('v', 'N/A')}")
    formatted_output.append(f"  ID: {checkpoint.get('id', 'N/A')}")
    formatted_output.append(f"  Timestamp: {checkpoint.get('ts', 'N/A')}")
    formatted_output.append(f"  Step: {checkpoint.get('metadata', {}).get('step', 'N/A')}")
    formatted_output.append(f"  Source: {checkpoint.get('metadata', {}).get('source', 'N/A')}")

    # Channel values summary
    channel_values = checkpoint.get("channel_values", {})
    formatted_output.append("\n🔗 CHANNEL VALUES SUMMARY:")

    # Messages count
    all_messages = channel_values.get("all_messages", [])
    messages = channel_values.get("messages", [])
    history = channel_values.get("history", [])

    formatted_output.append(f"  All Messages: {len(all_messages)} items")
    formatted_output.append(f"  Messages: {len(messages)} items")
    formatted_output.append(f"  History: {len(history)} items")
    formatted_output.append(f"  Next Action: {channel_values.get('next', 'N/A')}")

    # Show all channels with their content types and message counts
    formatted_output.append("\n📂 ALL CHANNELS:")
    for key, value in channel_values.items():
        if key in ["team"]:  # Skip team as it's handled separately
            continue

        if isinstance(value, list):
            message_count = sum(1 for item in value if isinstance(item, (HumanMessage, AIMessage, ToolMessage)))
            if message_count > 0:
                formatted_output.append(f"  {key}: {len(value)} items ({message_count} messages)")
            else:
                formatted_output.append(f"  {key}: {len(value)} items")
        elif isinstance(value, (HumanMessage, AIMessage, ToolMessage)):
            formatted_output.append(f"  {key}: 1 message ({type(value).__name__})")
        else:
            formatted_output.append(f"  {key}: {type(value).__name__}")

    # Team information
    team = channel_values.get("team")
    if team:
        formatted_output.append("\n👥 TEAM INFO:")
        formatted_output.append(f"  Name: {getattr(team, 'name', 'N/A')}")
        formatted_output.append(f"  Role: {getattr(team, 'role', 'N/A')}")
        formatted_output.append(f"  Provider: {getattr(team, 'provider', 'N/A')}")
        formatted_output.append(f"  Model: {getattr(team, 'model', 'N/A')}")

        members = getattr(team, "members", {})
        if members:
            formatted_output.append(f"  Members: {len(members)} total")
            for member_id, member in members.items():
                tools_count = len(getattr(member, "tools", []))
                formatted_output.append(f"    - {getattr(member, 'name', member_id)}: {tools_count} tools")

    # Recent messages
    if all_messages:
        formatted_output.append(f"\n💬 RECENT MESSAGES ({min(3, len(all_messages))} of {len(all_messages)}):")
        for i, msg in enumerate(all_messages[-3:], 1):
            msg_type = type(msg).__name__
            content = getattr(msg, "content", "")
            if isinstance(content, list):
                content = f"[Complex content with {len(content)} parts]"
            elif len(str(content)) > 100:
                content = str(content)[:100] + "..."

            formatted_output.append(f"  {i}. {msg_type}: {content}")

    # Pending writes
    pending_writes = getattr(checkpoint_tuple, "pending_writes", [])
    if pending_writes:
        formatted_output.append(f"\n📝 PENDING WRITES: {len(pending_writes)} items")
        for i, write in enumerate(pending_writes[:3], 1):
            if len(write) >= 3:
                formatted_output.append(f"  {i}. {write[1]} - {type(write[2]).__name__}")

    formatted_output.append("\n" + "=" * 80)

    return "\n".join(formatted_output)
