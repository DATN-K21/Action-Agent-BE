from enum import StrEnum


class AgentType(StrEnum):
    """
    Enum for agent types.
    """

    MULTI = "multi"
    BUILTIN = "builtin"
    COMPOSIO = "composio"
    MCP = "mcp"
