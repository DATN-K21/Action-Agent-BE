"""
Context Management Utility for AI Agent Conversations

This module provides efficient context management to optimize token usage
and prevent exceeding model input limits while preserving conversation quality.
"""

import re
from typing import Optional

from langchain_core.messages import AIMessage, AnyMessage, SystemMessage, ToolMessage

from app.core import logging
from app.core.settings import env_settings

logger = logging.get_logger(__name__)


class ContextManager:
    """
    Manages conversation context to optimize token usage and prevent exceeding model limits.

    Features:
    - Smart truncation based on token limits
    - Priority-based message selection
    - Preservation of important system messages
    - Cost-effective context loading
    """

    def __init__(
        self,
        max_context_tokens: int = env_settings.DEFAULT_CONTEXT_LIMIT,
        system_message_priority: bool = True,
        recent_messages_weight: float = 1.5,
        tool_message_weight: float = 1.2,
        min_context_messages: int = 5,
    ):
        """
        Initialize the context manager.

        Args:
            max_context_tokens: Maximum tokens allowed in context
            system_message_priority: Whether to prioritize system messages
            recent_messages_weight: Weight multiplier for recent messages
            tool_message_weight: Weight multiplier for tool messages
            min_context_messages: Minimum number of messages to keep
        """
        self.max_context_tokens = max_context_tokens
        self.system_message_priority = system_message_priority
        self.recent_messages_weight = recent_messages_weight
        self.tool_message_weight = tool_message_weight
        self.min_context_messages = min_context_messages

    def estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for a given text.
        Uses a simple approximation: ~4 characters per token.

        Args:
            text: Input text to estimate tokens for

        Returns:
            Estimated token count
        """
        if not text:
            return 0

        # Remove extra whitespace and count characters
        cleaned_text = re.sub(r"\s+", " ", text.strip())
        # Approximate: 4 characters per token (conservative estimate)
        return max(1, len(cleaned_text) // 4)

    def get_message_content_text(self, message: AnyMessage) -> str:
        """
        Extract text content from a message, handling different content types.

        Args:
            message: The message to extract content from

        Returns:
            Text content of the message
        """
        if isinstance(message.content, list):
            # Handle messages with mixed content (text + images)
            text_parts = []
            for item in message.content:
                if isinstance(item, dict):
                    if item.get("type") == "text":
                        text_parts.append(item.get("text", ""))
                    elif item.get("type") == "image_url":
                        text_parts.append("[Image]")
            return " ".join(text_parts)
        else:
            return str(message.content) if message.content else ""

    def calculate_message_priority(self, message: AnyMessage, index: int, total_messages: int) -> float:
        """
        Calculate priority score for a message based on various factors.

        Args:
            message: The message to calculate priority for
            index: Position of message in the list (0 = oldest)
            total_messages: Total number of messages

        Returns:
            Priority score (higher = more important)
        """
        base_priority = 1.0

        # Recent messages get higher priority
        recency_factor = (index + 1) / total_messages
        priority = base_priority + (recency_factor * self.recent_messages_weight)

        # System messages get highest priority
        if isinstance(message, SystemMessage) and self.system_message_priority:
            priority *= 3.0

        # Tool messages are important for context
        elif isinstance(message, ToolMessage):
            priority *= self.tool_message_weight

        # AI messages with tool calls are important
        elif isinstance(message, AIMessage) and hasattr(message, "tool_calls") and message.tool_calls:
            priority *= self.tool_message_weight

        return priority

    def optimize_context_messages(self, messages: list[AnyMessage]) -> list[AnyMessage]:
        """
        Optimize message list to fit within token limits while preserving important context.

        Args:
            messages: List of messages to optimize

        Returns:
            Optimized list of messages within token limits
        """
        if not messages:
            return messages

        # Calculate token count for each message
        message_data = []
        total_tokens = 0

        for i, message in enumerate(messages):
            content = self.get_message_content_text(message)
            tokens = self.estimate_tokens(content)
            priority = self.calculate_message_priority(message, i, len(messages))

            message_data.append({"message": message, "content": content, "tokens": tokens, "priority": priority, "index": i})
            total_tokens += tokens

        # If within limits, return original messages
        if total_tokens <= self.max_context_tokens:
            logger.debug(f"Context within limits: {total_tokens}/{self.max_context_tokens} tokens")
            return messages

        # Need to truncate - use smart selection
        logger.info(f"Context exceeds limits: {total_tokens}/{self.max_context_tokens} tokens. Optimizing...")

        # Always preserve system messages first
        system_messages = [data for data in message_data if isinstance(data["message"], SystemMessage)]
        other_messages = [data for data in message_data if not isinstance(data["message"], SystemMessage)]

        # Sort other messages by priority (descending)
        other_messages.sort(key=lambda x: x["priority"], reverse=True)

        # Start with system messages
        selected_messages = system_messages.copy()
        current_tokens = sum(data["tokens"] for data in system_messages)

        # Add other messages in priority order
        for data in other_messages:
            if current_tokens + data["tokens"] <= self.max_context_tokens:
                selected_messages.append(data)
                current_tokens += data["tokens"]
            elif len(selected_messages) < self.min_context_messages:
                # Force include minimum messages even if slightly over limit
                selected_messages.append(data)
                current_tokens += data["tokens"]
                logger.warning(f"Exceeded token limit to maintain minimum context: {current_tokens}/{self.max_context_tokens}")
                break

        # Sort by original index to maintain conversation order
        selected_messages.sort(key=lambda x: x["index"])

        optimized_messages = [data["message"] for data in selected_messages]
        final_tokens = sum(data["tokens"] for data in selected_messages)

        logger.info(f"Context optimized: {len(optimized_messages)}/{len(messages)} messages, {final_tokens}/{self.max_context_tokens} tokens")

        return optimized_messages

    def format_optimized_messages(self, messages: list[AnyMessage]) -> str:
        """
        Format optimized messages to string with context optimization.

        Args:
            messages: List of messages to format

        Returns:
            Formatted message string
        """
        optimized_messages = self.optimize_context_messages(messages)

        message_str = ""
        for message in optimized_messages:
            # Determine message name
            name = (
                message.name
                if message.name
                else (
                    "AI"
                    if isinstance(message, AIMessage)
                    else "Tool"
                    if isinstance(message, ToolMessage)
                    else "System"
                    if isinstance(message, SystemMessage)
                    else "User"
                )
            )

            content = self.get_message_content_text(message)
            message_str += f"{name}: {content}\n\n"

        return message_str


# Global context manager instance with sensible defaults
default_context_manager = ContextManager(
    max_context_tokens=8000,  # Conservative limit for most models
    system_message_priority=True,
    recent_messages_weight=1.5,
    tool_message_weight=1.2,
    min_context_messages=5,
)


def optimize_context_for_model(messages: list[AnyMessage], max_tokens: Optional[int] = None) -> list[AnyMessage]:
    """
    Convenience function to optimize context for model input.

    Args:
        messages: List of messages to optimize
        max_tokens: Maximum tokens allowed (uses default if None)

    Returns:
        Optimized list of messages
    """
    if max_tokens:
        context_manager = ContextManager(max_context_tokens=max_tokens)
        return context_manager.optimize_context_messages(messages)
    else:
        return default_context_manager.optimize_context_messages(messages)


def format_messages_optimized(messages: list[AnyMessage], max_tokens: Optional[int] = None) -> str:
    """
    Convenience function to format messages with context optimization.

    Args:
        messages: List of messages to format
        max_tokens: Maximum tokens allowed (uses default if None)

    Returns:
        Formatted and optimized message string
    """
    if max_tokens:
        context_manager = ContextManager(max_context_tokens=max_tokens)
        return context_manager.format_optimized_messages(messages)
    else:
        return default_context_manager.format_optimized_messages(messages)
