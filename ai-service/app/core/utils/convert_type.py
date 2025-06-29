from langchain_core.tools import BaseTool

from app.core.models import ToolInfo


def convert_base_tool_to_tool_info(tool: BaseTool) -> ToolInfo:
    """
    Convert a BaseTool instance to a ToolInfo instance.

    Args:
        tool (BaseTool): The BaseTool instance to convert.

    Returns:
        ToolInfo: The converted ToolInfo instance.
    """
    return ToolInfo(
        description=tool.description,
        tool=tool,
        display_name=tool.name,
        input_parameters=tool.get_input_jsonschema(),
    )
