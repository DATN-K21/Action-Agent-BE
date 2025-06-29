"""
Tool arguments sanitizer to fix common LLM tool call issues.

This module provides utilities to clean up tool call arguments generated by LLMs,
specifically fixing issues where optional parameters are set to string "null"
instead of actual null values.
"""

from typing import Any, Dict


def sanitize_tool_args(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sanitize tool call arguments by converting string "null" values to actual null.

    This function fixes a common issue where LLMs generate tool calls with optional
    parameters set to the string "null" instead of actual null values, which can
    cause tool execution failures.

    Args:
        args: The original tool call arguments dictionary

    Returns:
        Dict with sanitized arguments where string "null" values are converted to None

    Example:
        >>> args = {"recipient": "test@test.com", "attachment": "null", "is_html": False}
        >>> sanitize_tool_args(args)
        {"recipient": "test@test.com", "attachment": None, "is_html": False}
    """
    if not isinstance(args, dict):
        return args

    sanitized_args = {}

    for key, value in args.items():
        if isinstance(value, str) and value.lower() == "null":
            # Convert string "null" to actual None/null value
            sanitized_args[key] = None
        elif isinstance(value, str) and value.lower() == "none":
            # Also handle "none" which some models might generate
            sanitized_args[key] = None
        elif isinstance(value, dict):
            # Recursively sanitize nested dictionaries
            sanitized_args[key] = sanitize_tool_args(value)
        elif isinstance(value, list):
            # Sanitize list items
            sanitized_args[key] = [
                sanitize_tool_args(item) if isinstance(item, dict) else None if isinstance(item, str) and item.lower() in ["null", "none"] else item
                for item in value
            ]
        else:
            # Keep the original value for all other types
            sanitized_args[key] = value

    return sanitized_args


def sanitize_tool_call(tool_call: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sanitize a complete tool call object including its arguments.

    Args:
        tool_call: Tool call dictionary containing 'name', 'args', 'id', etc.

    Returns:
        Sanitized tool call with cleaned arguments
    """
    if not isinstance(tool_call, dict):
        return tool_call

    sanitized_call = tool_call.copy()

    if "args" in sanitized_call:
        sanitized_call["args"] = sanitize_tool_args(sanitized_call["args"])

    return sanitized_call


def sanitize_tool_calls_list(tool_calls: list) -> list:
    """
    Sanitize a list of tool calls.

    Args:
        tool_calls: List of tool call dictionaries

    Returns:
        List of sanitized tool calls
    """
    if not isinstance(tool_calls, list):
        return tool_calls

    return [sanitize_tool_call(call) for call in tool_calls]
