import re
from enum import Enum
from typing import Annotated, Any

from langchain_core.messages import AnyMessage
from langchain_core.tools import BaseTool
from langgraph.graph import add_messages
from pydantic import BaseModel, Field
from typing_extensions import NotRequired, TypedDict

from app.core import logging
from app.core.enums import StorageStrategy
from app.core.rag.pgvector import PGVectorWrapper
from app.core.tools.api_tool import dynamic_api_tool
from app.core.tools.retriever_tool import create_retriever_tool_custom_modified
from app.core.tools.tool_manager import global_tools, tool_manager

logger = logging.get_logger(__name__)


class GraphSkill(BaseModel):
    skill_id: str = Field(description="The id of the skill")
    member_id: str = Field(description="The id of the team that owns the skill. Optional, if not provided, the skill is personal.")
    user_id: str = Field(description="The id of the owner")
    name: str = Field(description="The name of the skill")
    display_name: str | None = Field(description="The display name of the skill. Optional, if not provided, the name will be used.")
    definition: dict[str, Any] | None = Field(
        description="The skill definition. For api tool calling. Optional."
    )

    strategy: StorageStrategy = Field(description="Defines how a skill is persisted or accessed.")

    async def aload_tool_cache(self) -> bool:
        """
        Asynchronously load tools into cache for this skill.
        This method can be called explicitly to ensure tools are cached before accessing the tool property.

        Returns:
            bool: True if cache loading was successful, False otherwise
        """
        try:
            from app.core.utils.tool_cache_loader import aload_tools_to_cache_by_skill

            await aload_tools_to_cache_by_skill(self.skill_id, self.member_id)
            logger.info(f"Successfully loaded cache for skill {self.skill_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to load cache for skill {self.skill_id}: {e}")
            return False

    async def aensure_tool_available(self) -> BaseTool:
        """
        Ensure the tool is available in cache and return it.
        This method will attempt to load the cache if the tool is not found.

        Returns:
            BaseTool: The tool instance

        Raises:
            ValueError: If the tool cannot be loaded or accessed
        """
        if self.strategy == StorageStrategy.GLOBAL_TOOLS:
            return global_tools[self.name].tool

        elif self.strategy == StorageStrategy.PERSONAL_TOOL_CACHE:
            # First, try to get the tool from cache
            try:
                tool_info = await tool_manager.aget_personal_tool(self.user_id, self.name)
                return tool_info.tool
            except Exception:
                # Tool not in cache, try to load it
                logger.info(f"Tool '{self.name}' not found in cache for user '{self.user_id}', attempting to load...")

                cache_loaded = await self.aload_tool_cache()
                if cache_loaded:
                    # Try again after loading cache
                    try:
                        tool_info = await tool_manager.aget_personal_tool(self.user_id, self.name)
                        return tool_info.tool
                    except Exception:
                        raise ValueError(
                            f"Personal tool '{self.name}' not found in cache for user '{self.user_id}' "
                            f"even after cache loading. The skill may not be properly configured."
                        )
                else:
                    raise ValueError(f"Failed to load cache for personal tool '{self.name}' for user '{self.user_id}'")

        elif self.strategy == StorageStrategy.DEFINITION and self.definition:
            return dynamic_api_tool(self.definition)

        else:
            raise ValueError("Skill is not managed and no definition provided.")

    async def aget_tool(self) -> BaseTool:
        if self.strategy == StorageStrategy.GLOBAL_TOOLS:
            return global_tools[self.name].tool
        if self.strategy == StorageStrategy.PERSONAL_TOOL_CACHE:
            try:
                tool_info = await tool_manager.aget_personal_tool(self.user_id, self.name)
                return tool_info.tool
            except KeyError:
                # Attempt to load the tool cache before raising error
                cache_loaded = await self.aload_tool_cache()

                if cache_loaded:
                    # Try one more time after scheduling cache load
                    try:
                        tool_info = await tool_manager.aget_personal_tool(self.user_id, self.name)
                        return tool_info.tool
                    except Exception:
                        # If still not found, provide a helpful error message
                        logger.warning(f"Personal tool '{self.name}' not found in cache for user '{self.user_id}' even after cache loading attempt")
                        raise ValueError(
                            f"Personal tool '{self.name}' not found in cache for user '{self.user_id}'. "
                            f"Cache loading has been scheduled - tool may be available in subsequent requests."
                        )
                else:
                    # Could not load cache, provide informative error
                    raise ValueError(
                        f"Personal tool '{self.name}' not found in cache for user '{self.user_id}'. "
                        f"Unable to load cache automatically. Please ensure the skill is properly configured and cached."
                    )
        elif self.strategy == StorageStrategy.DEFINITION and self.definition:
            return dynamic_api_tool(self.definition)
        else:
            raise ValueError("Skill is not managed and no definition provided.")


class GraphUpload(BaseModel):
    name: str = Field(description="Name of the upload")
    description: str = Field(description="Description of the upload")
    user_id: str = Field(description="Id of the user that owns this upload")
    upload_id: str = Field(description="Id of the upload")

    async def aget_tool(self) -> BaseTool:
        retriever = PGVectorWrapper().retriever(self.user_id, self.upload_id)
        return create_retriever_tool_custom_modified(retriever)


class GraphPerson(BaseModel):
    name: str = Field(description="The name of the person")
    role: str | None = Field(description="Role of the person")
    provider: str | None = Field(description="The provider for the llm model")
    model: str | None = Field(description="The llm model to use for this person")

    temperature: float | None = Field(description="The temperature of the llm model")
    backstory: str | None = Field(description="Description of the person's experience, motives and concerns.")

    @property
    def persona(self) -> str:
        return f"<persona>\nName: {self.name}\nRole: {self.role}\nBackstory: {self.backstory}\n</persona>"


class GraphMember(GraphPerson):
    tools: list[GraphSkill | GraphUpload] = Field(
        description="The list of tools that the person can use."
    )
    interrupt: bool = Field(
        default=False,
        description="Whether to interrupt the person or not before skill use",
    )


# Create a Leader class so we can pass leader as a team member for team within team
class GraphLeader(GraphPerson):
    pass


class GraphTeam(BaseModel):
    name: str = Field(description="The name of the team")
    role: str | None = Field(description="Role of the team leader")
    backstory: str | None = Field(description="Description of the team leader's experience, motives and concerns.")
    members: dict[str, GraphMember | GraphLeader] = Field(
        description="The members of the team"
    )
    provider: str | None = Field(description="The provider of the team leader's llm model")
    model: str | None = Field(description="The llm model to use for this team leader")
    temperature: float | None = Field(description="The temperature of the team leader's llm model")

    @property
    def persona(self) -> str:
        return f"Name: {self.name}\nRole: {self.role}\nBackstory: {self.backstory}\n"


def add_or_replace_messages(
        messages: list[AnyMessage], new_messages: list[AnyMessage]
) -> list[AnyMessage]:
    """Add new messages to the state. If new_messages list is empty, clear messages instead."""
    if not new_messages:
        return []
    else:
        return add_messages(messages, new_messages)  # type: ignore[return-value, arg-type]


def format_messages(messages: list[AnyMessage]) -> str:
    """Format list of messages to string with context optimization"""
    from app.core.utils.context_manager import default_context_manager

    # Use optimized context formatting to manage token usage efficiently
    return default_context_manager.format_optimized_messages(messages)


def format_messages_with_model_context(messages: list[AnyMessage], model_name: str | None = None, provider: str | None = None) -> str:
    """
    Format list of messages to string with model-specific context optimization.

    Args:
        messages: List of messages to format
        model_name: Name of the model being used (for optimization)
        provider: Provider of the model (for optimization)

    Returns:
        Formatted and optimized message string
    """
    from app.core.enums import LlmProvider
    from app.core.utils.model_context_config import get_optimized_format_messages_for_model

    if model_name:
        # Try to convert provider string to enum
        provider_enum = None
        if provider:
            try:
                provider_enum = LlmProvider(provider.lower())
            except ValueError:
                provider_enum = None

        return get_optimized_format_messages_for_model(messages, model_name, provider_enum)
    else:
        # Fallback to default optimization
        return format_messages(messages)


def update_node_outputs(node_outputs: dict[str, Any], new_outputs: dict[str, Any]) -> dict[str, Any]:
    """Update node_outputs with new outputs. If new_outputs is empty, return the original node_outputs."""
    if not new_outputs:
        return node_outputs
    else:
        return {**node_outputs, **new_outputs}


class WorkflowTeamState(TypedDict):
    all_messages: Annotated[list[AnyMessage], add_messages]
    history: Annotated[list[AnyMessage], add_messages]
    messages: Annotated[list[AnyMessage], add_or_replace_messages]
    team: GraphTeam
    next: str
    main_task: list[AnyMessage]
    task: list[AnyMessage]
    node_outputs: Annotated[dict[str, Any], update_node_outputs]  # Modify this line


# When returning teamstate, is it possible to exclude fields that you don't want to update
class ReturnWorkflowTeamState(TypedDict):
    all_messages: NotRequired[list[AnyMessage]]
    history: NotRequired[list[AnyMessage]]
    messages: NotRequired[list[AnyMessage]]
    team: NotRequired[GraphTeam]
    next: NotRequired[str | None]  # Returning None is valid for sequential graphs only
    task: NotRequired[list[AnyMessage]]
    node_outputs: Annotated[NotRequired[dict[str, Any]], update_node_outputs]


def parse_variables(text: str, node_outputs: dict, is_code: bool = False) -> str:
    def replace_variable(match):
        var_path = match.group(1).split(".")
        value = node_outputs
        for key in var_path:
            if key in value:
                value = value[key]
            else:
                return match.group(0)  # If variable not found, keep it as is

        # Convert fullwidth characters to halfwidth characters
        def convert_fullwidth_to_halfwidth(s: str) -> str:
            # Fullwidth character range is 0xFF01 to 0xFF5E
            # Halfwidth character range is 0x0021 to 0x007E
            result = []
            for char in str(s):
                code = ord(char)
                if 0xFF01 <= code <= 0xFF5E:
                    # Convert fullwidth characters to halfwidth characters
                    result.append(chr(code - 0xFEE0))
                else:
                    result.append(char)
            return "".join(result)

        str_value = str(value)
        if is_code:
            # For strings in code, convert fullwidth characters and properly escape
            converted_value = convert_fullwidth_to_halfwidth(str_value)
            # Escape quotes and backslashes
            escaped_value = converted_value.replace('"', '\\"').replace("\\", "\\\\")
            return f'"{escaped_value}"'
        else:
            return str_value

    return re.sub(r"\{([^}]+)\}", replace_variable, text)


class ToolInvokeMessage(BaseModel):
    class MessageType(Enum):
        TEXT = "text"
        IMAGE = "image"
        LINK = "link"
        BLOB = "blob"
        JSON = "json"
        IMAGE_LINK = "image_link"

    type: MessageType = MessageType.TEXT
    """
        plain text, image url or link url
    """
    message: str | bytes | dict | None = None
    meta: dict[str, Any] | None = None
    save_as: str = ""


def create_image_message(image: str, save_as: str = "") -> ToolInvokeMessage:
    """
    create an image message

    :param image: the url of the image
    :return: the image message
    """
    return ToolInvokeMessage(type=ToolInvokeMessage.MessageType.IMAGE, message=image, save_as=save_as)


def create_link_message(link: str, save_as: str = "") -> ToolInvokeMessage:
    """
    create a link message

    :param link: the url of the link
    :return: the link message
    """
    return ToolInvokeMessage(type=ToolInvokeMessage.MessageType.LINK, message=link, save_as=save_as)


def create_text_message(text: str, save_as: str = "") -> ToolInvokeMessage:
    """
    create a text message

    :param text: the text
    :return: the text message
    """
    return ToolInvokeMessage(type=ToolInvokeMessage.MessageType.TEXT, message=text, save_as=save_as)


def create_blob_message(blob: bytes, meta: dict | None = None, save_as: str = "") -> ToolInvokeMessage:
    """
    create a blob message

    :param blob: the blob
    :return: the blob message
    """
    return ToolInvokeMessage(
        type=ToolInvokeMessage.MessageType.BLOB,
        message=blob,
        meta=meta,
        save_as=save_as,
    )


def create_json_message(object: dict) -> ToolInvokeMessage:
    """
    create a json message
    """
    return ToolInvokeMessage(type=ToolInvokeMessage.MessageType.JSON, message=object)
