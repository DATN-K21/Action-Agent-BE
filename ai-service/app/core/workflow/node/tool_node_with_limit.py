"""
Custom ToolNode with output length limiting for context window management.

This module provides a ToolNode implementation that inherits from LangGraph's ToolNode
and adds intelligent output truncation to prevent context window overflow.
"""

from typing import Any, Dict, List, Optional, Sequence

from langchain_core.messages import AnyMessage, ToolMessage
from langchain_core.messages.utils import count_tokens_approximately
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import BaseTool
from langgraph.prebuilt import ToolNode

from app.core import logging
from app.core.settings import env_settings
from app.core.utils.context_manager import ContextManager

logger = logging.get_logger(__name__)


class ToolNodeWithOutputLimit(ToolNode):
    """
    Enhanced ToolNode that limits tool output length to prevent context window overflow.

    This class inherits from LangGraph's ToolNode and adds intelligent output truncation
    based on token limits while preserving important information.
    """

    def __init__(
        self,
        tools: Sequence[BaseTool],
        *,
        name: str = "tools",
        tags: Optional[list[str]] = None,
        max_output_tokens: Optional[int] = None,
        truncate_strategy: str = "smart",
        preserve_prefix_tokens: int = 500,
        preserve_suffix_tokens: int = 200,
    ):
        """
        Initialize ToolNodeWithOutputLimit.

        Args:
            tools: Sequence of tools to use
            name: Name of the node
            tags: Tags for the node
            max_output_tokens: Maximum tokens allowed for tool output (defaults to conservative limit)
            truncate_strategy: Strategy for truncation ("smart", "prefix", "suffix", "middle")
            preserve_prefix_tokens: Tokens to preserve at the beginning when truncating
            preserve_suffix_tokens: Tokens to preserve at the end when truncating
        """
        super().__init__(tools, name=name, tags=tags)

        # Set default max output tokens to a conservative value
        self.max_output_tokens = max_output_tokens or getattr(env_settings, "MAX_TOOL_OUTPUT_TOKENS", 20000)
        self.truncate_strategy = truncate_strategy
        self.preserve_prefix_tokens = preserve_prefix_tokens
        self.preserve_suffix_tokens = preserve_suffix_tokens

        # Create context manager for token estimation
        self.context_manager = ContextManager()

        logger.info(f"Initialized ToolNodeWithOutputLimit with max_output_tokens={self.max_output_tokens}, strategy={self.truncate_strategy}")

    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count for text."""
        return count_tokens_approximately(text)

    def _truncate_output_smart(self, content: str) -> str:
        """
        Smart truncation that preserves important parts of the output.

        Args:
            content: Original content to truncate

        Returns:
            Truncated content with important parts preserved
        """
        tokens = self._estimate_tokens(content)

        if tokens <= self.max_output_tokens:
            return content

        logger.info(f"Truncating tool output: {tokens} tokens > {self.max_output_tokens} limit")

        if self.truncate_strategy == "prefix":
            # Keep only the beginning
            target_chars = int(len(content) * (self.max_output_tokens / tokens))
            truncated = content[:target_chars]
            return truncated + f"\n\n[... truncated {tokens - self.max_output_tokens} tokens to prevent context overflow]"

        elif self.truncate_strategy == "suffix":
            # Keep only the end
            target_chars = int(len(content) * (self.max_output_tokens / tokens))
            truncated = content[-target_chars:]
            return f"[truncated {tokens - self.max_output_tokens} tokens from beginning...]\n\n" + truncated

        elif self.truncate_strategy == "middle":
            # Keep beginning and end, truncate middle
            prefix_chars = int(len(content) * (self.preserve_prefix_tokens / tokens))
            suffix_chars = int(len(content) * (self.preserve_suffix_tokens / tokens))

            prefix = content[:prefix_chars]
            suffix = content[-suffix_chars:]

            truncated_tokens = tokens - self.preserve_prefix_tokens - self.preserve_suffix_tokens
            return f"{prefix}\n\n[... truncated {truncated_tokens} tokens from middle ...]\n\n{suffix}"

        else:  # "smart" strategy
            # Intelligent truncation based on content structure
            lines = content.split("\n")

            # Try to preserve structure
            if len(lines) > 20:  # If many lines, sample important ones
                # Keep first few lines, last few lines, and some middle content
                preserve_start = min(10, len(lines) // 4)
                preserve_end = min(5, len(lines) // 6)

                start_lines = lines[:preserve_start]
                end_lines = lines[-preserve_end:]

                truncated_content = "\n".join(start_lines)
                truncated_content += (
                    f"\n\n[... truncated {len(lines) - preserve_start - preserve_end} lines (~{tokens - self.max_output_tokens} tokens) ...]\n\n"
                )
                truncated_content += "\n".join(end_lines)

                return truncated_content
            else:
                # For shorter content, use character-based truncation with preservation of key parts
                if tokens > self.max_output_tokens * 1.5:
                    # Heavy truncation needed
                    target_chars = int(len(content) * 0.6)  # Keep 60% of content
                    return content[:target_chars] + f"\n\n[... truncated ~{tokens - self.max_output_tokens} tokens ...]"
                else:
                    # Light truncation
                    target_chars = int(len(content) * (self.max_output_tokens / tokens))
                    return content[:target_chars] + f"\n\n[... truncated {tokens - self.max_output_tokens} tokens ...]"

    def _process_tool_messages(self, messages: List[AnyMessage]) -> List[AnyMessage]:
        """
        Process tool messages to apply output limiting.

        Args:
            messages: List of messages to process

        Returns:
            Processed messages with limited tool outputs
        """
        processed_messages = []

        for message in messages:
            if isinstance(message, ToolMessage):
                original_tokens = self._estimate_tokens(str(message.content))

                if original_tokens > self.max_output_tokens:
                    # Apply truncation
                    truncated_content = self._truncate_output_smart(str(message.content))

                    # Create new ToolMessage with truncated content
                    truncated_message = ToolMessage(
                        content=truncated_content,
                        name=message.name,
                        tool_call_id=message.tool_call_id,
                        artifact=getattr(message, "artifact", None),
                        additional_kwargs=getattr(message, "additional_kwargs", {}),
                    )

                    logger.info(
                        f"Tool output truncated: {original_tokens} -> {self._estimate_tokens(truncated_content)} tokens for tool '{message.name}'"
                    )

                    processed_messages.append(truncated_message)
                else:
                    processed_messages.append(message)
            else:
                processed_messages.append(message)

        return processed_messages

    def invoke(self, input: Dict[str, Any], config: Optional[RunnableConfig] = None) -> Dict[str, Any]:
        """
        Override invoke method to add output limiting.

        Args:
            input: Input dictionary containing messages
            config: Optional configuration

        Returns:
            Output dictionary with limited tool outputs
        """
        # Call parent invoke method
        result = super().invoke(input, config)

        # Process the result to apply output limiting
        if "messages" in result:
            result["messages"] = self._process_tool_messages(result["messages"])

        return result

    async def ainvoke(self, input: Dict[str, Any], config: Optional[RunnableConfig] = None) -> Dict[str, Any]:
        """
        Override async invoke method to add output limiting.

        Args:
            input: Input dictionary containing messages
            config: Optional configuration

        Returns:
            Output dictionary with limited tool outputs
        """
        # Call parent ainvoke method
        result = await super().ainvoke(input, config)

        # Process the result to apply output limiting
        if "messages" in result:
            result["messages"] = self._process_tool_messages(result["messages"])

        return result


def create_tool_node_with_limit(
    tools: Sequence[BaseTool],
    *,
    name: str = "tools",
    max_output_tokens: Optional[int] = None,
    truncate_strategy: str = "smart",
) -> ToolNodeWithOutputLimit:
    """
    Factory function to create a ToolNodeWithOutputLimit instance.

    Args:
        tools: Sequence of tools to use
        name: Name of the node
        max_output_tokens: Maximum tokens allowed for tool output
        truncate_strategy: Strategy for truncation

    Returns:
        ToolNodeWithOutputLimit instance
    """
    return ToolNodeWithOutputLimit(
        tools=tools,
        name=name,
        max_output_tokens=max_output_tokens,
        truncate_strategy=truncate_strategy,
    )
