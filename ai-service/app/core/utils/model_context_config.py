"""
Context Configuration for Different Model Providers

This module provides model-specific context limits and configurations
to optimize context management for different AI model providers.
"""

from typing import Dict, Optional

from app.core.enums import LlmProvider
from app.core.settings import env_settings
from app.core.utils.context_manager import ContextManager

# Model-specific token limits (conservative estimates)
MODEL_CONTEXT_LIMITS: Dict[str, int] = {
    # OpenAI Models
    "gpt-4o": 128000,
    "gpt-4o-mini": 128000,
    "gpt-4o-nano": 16384,  # Conservative limit for nano model
    "gpt-4": 8192,
    "gpt-4-turbo": 128000,
    "gpt-3.5-turbo": 16384,
    # Anthropic Models
    "claude-3-opus": 200000,
    "claude-3-sonnet": 200000,
    "claude-3-haiku": 200000,
    "claude-3-5-sonnet": 200000,
    # Google Models
    "gemini-pro": 30720,
    "gemini-1.5-pro": 1000000,
    "gemini-1.5-flash": 1000000,
    # Default fallback
    "default": env_settings.DEFAULT_CONTEXT_LIMIT,
}

# Provider-specific default limits
PROVIDER_DEFAULT_LIMITS: Dict[LlmProvider, int] = {
    LlmProvider.OPENAI: 16384,
    LlmProvider.ANTHROPIC: 200000,
    LlmProvider.GOOGLE: 30720,
    LlmProvider.MISTRAL: 8192,
    LlmProvider.COHERE: 4096,
    LlmProvider.LOCAL: 4096,
}


def get_context_limit_for_model(model_name: str, provider: Optional[LlmProvider] = None) -> int:
    """
    Get the appropriate context limit for a specific model.

    Args:
        model_name: Name of the model
        provider: Model provider (optional)

    Returns:
        Context limit in tokens
    """
    # First try exact model match
    if model_name in MODEL_CONTEXT_LIMITS:
        limit = MODEL_CONTEXT_LIMITS[model_name]
    elif provider and provider in PROVIDER_DEFAULT_LIMITS:
        limit = PROVIDER_DEFAULT_LIMITS[provider]
    else:
        limit = MODEL_CONTEXT_LIMITS["default"]

    # Use X% of the limit for context to leave room for response
    return int(limit * env_settings.CONTEXT_RATIO)


def create_context_manager_for_model(
    model_name: str,
    provider: Optional[LlmProvider] = None,
    context_ratio: float = env_settings.CONTEXT_RATIO,
) -> ContextManager:
    """
    Create a context manager optimized for a specific model.

    Args:
        model_name: Name of the model
        provider: Model provider (optional)
        context_ratio: Ratio of total context to use (default 0.6)

    Returns:
        Configured ContextManager instance
    """
    # Get base limit for the model
    if model_name in MODEL_CONTEXT_LIMITS:
        base_limit = MODEL_CONTEXT_LIMITS[model_name]
    elif provider and provider in PROVIDER_DEFAULT_LIMITS:
        base_limit = PROVIDER_DEFAULT_LIMITS[provider]
    else:
        base_limit = MODEL_CONTEXT_LIMITS["default"]

    # Calculate context limit
    context_limit = int(base_limit * context_ratio)

    # Adjust settings based on model capabilities
    if model_name.startswith(("gpt-4", "claude-3", "gemini-1.5")):
        # High-end models can handle more complex context
        return ContextManager(
            max_context_tokens=context_limit,
            system_message_priority=True,
            recent_messages_weight=1.3,
            tool_message_weight=1.4,
            min_context_messages=8,
        )
    elif model_name.startswith(("gpt-3.5", "gpt-4o-nano")):
        # Mid-range models need more aggressive optimization
        return ContextManager(
            max_context_tokens=context_limit,
            system_message_priority=True,
            recent_messages_weight=1.8,
            tool_message_weight=1.6,
            min_context_messages=5,
        )
    else:
        # Lower-end models need very aggressive optimization
        return ContextManager(
            max_context_tokens=context_limit,
            system_message_priority=True,
            recent_messages_weight=2.0,
            tool_message_weight=1.8,
            min_context_messages=3,
        )


def get_optimized_format_messages_for_model(
    messages: list,
    model_name: str,
    provider: Optional[LlmProvider] = None,
) -> str:
    """
    Get optimized formatted messages for a specific model.

    Args:
        messages: List of messages to format
        model_name: Name of the model
        provider: Model provider (optional)

    Returns:
        Optimized formatted message string
    """
    context_manager = create_context_manager_for_model(model_name, provider)
    return context_manager.format_optimized_messages(messages)
