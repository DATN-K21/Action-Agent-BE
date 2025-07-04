import json
from typing import Any
from uuid import uuid4

from langchain_core.documents import Document
from langchain_core.messages import AIMessage, AnyMessage, HumanMessage, ToolMessage
from langgraph.checkpoint.base import CheckpointTuple

from app.core.graph.messages import ChatResponse
from app.memory.checkpoint import get_checkpointer


async def get_subgraph_checkpoints(checkpoint: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Extract checkpoints from subgraphs in hierarchical workflows.

    Args:
        checkpoint (dict): The parent checkpoint containing possible subgraphs.

    Returns:
        list[dict]: A list of subgraph checkpoints.
    """
    subgraph_checkpoints = []

    # Look for subgraph states in the checkpoint
    subgraphs = checkpoint.get("subgraphs", {})
    if isinstance(subgraphs, dict):
        for subgraph_name, subgraph_data in subgraphs.items():
            if isinstance(subgraph_data, dict) and "checkpoint" in subgraph_data:
                subgraph_checkpoints.append(subgraph_data["checkpoint"])

                # Recursively check if this subgraph has nested subgraphs
                nested_checkpoints = await get_subgraph_checkpoints(subgraph_data["checkpoint"])
                subgraph_checkpoints.extend(nested_checkpoints)

    return subgraph_checkpoints


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

    # Safe access to channel_values and its sub-keys
    channel_values = checkpoint.get("channel_values", {})
    all_messages: list[AnyMessage] = channel_values.get("all_messages", []) + channel_values.get("messages", [])

    # Also check for messages in other possible locations
    node_values = checkpoint.get("node_values", {})
    for node_name, node_data in node_values.items():
        if isinstance(node_data, dict):
            node_messages = node_data.get("messages", [])
            if node_messages:
                all_messages.extend(node_messages)

    # Check for messages in thread history if it exists
    thread_history = checkpoint.get("thread_history", [])
    if thread_history and isinstance(thread_history, list):
        all_messages.extend(thread_history)

    # Extract messages from subgraphs in hierarchical workflows if recursive is enabled
    if recursive:
        # Look for subgraph states in the checkpoint - try multiple possible keys
        subgraph_keys = ["subgraphs", "checkpoint_ns", "nested_checkpoints"]
        for subgraph_key in subgraph_keys:
            subgraphs = checkpoint.get(subgraph_key, {})
            if isinstance(subgraphs, dict):
                for subgraph_name, subgraph_data in subgraphs.items():
                    if isinstance(subgraph_data, dict):
                        # Try different ways to access subgraph checkpoint data
                        subgraph_checkpoint = subgraph_data
                        if "checkpoint" in subgraph_data:
                            subgraph_checkpoint = subgraph_data["checkpoint"]

                        # Extract messages from subgraph channel_values
                        subgraph_channel_values = subgraph_checkpoint.get("channel_values", {})
                        if subgraph_channel_values:
                            subgraph_messages = subgraph_channel_values.get("all_messages", []) + subgraph_channel_values.get("messages", [])
                            all_messages.extend(subgraph_messages)

                        # Also check subgraph node_values
                        subgraph_node_values = subgraph_checkpoint.get("node_values", {})
                        for sub_node_name, sub_node_data in subgraph_node_values.items():
                            if isinstance(sub_node_data, dict):
                                sub_node_messages = sub_node_data.get("messages", [])
                                if sub_node_messages:
                                    all_messages.extend(sub_node_messages)

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
        elif isinstance(message, ToolMessage) and message.name:
            documents: list[dict[str, Any]] = []
            if message.name == "KnowledgeBase" and hasattr(message, "artifact"):
                try:
                    docs: list[Document] = message.artifact
                    for doc in docs:
                        if isinstance(doc, Document) and hasattr(doc, "metadata") and "score" in doc.metadata:
                            documents.append(
                                {
                                    "score": doc.metadata["score"],
                                    "content": doc.page_content,
                                }
                            )
                except (AttributeError, TypeError, KeyError):
                    # Handle any errors while processing documents
                    pass

            # Get tool_call_id safely
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
        # Log the error if needed
        # logger.error(f"Error retrieving checkpoint for thread {thread_id}")
        return None
