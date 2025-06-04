from typing import Any

from openai import BaseModel
from pydantic import Field

from app.core.enums import ConnectedServiceType, StorageStrategy
from app.schemas.base import BaseRequest, BaseResponse


class SkillBase(BaseModel):
    name: str = Field(..., description="The unique name of the skill")
    description: str | None = Field(None, description="A brief description of the skill")
    icon: str | None = Field(None, description="An icon image of the skill")
    strategy: StorageStrategy | None = Field(None,
                                             description="The storage strategy for the skill, e.g., 'definition', 'file'")
    display_name: str | None = Field(None, description="The display name of the skill")
    tool_definition: dict[str, Any] = Field(default_factory=dict, description="The tool definition of the skill")
    input_parameters: dict[str, Any] = Field(default_factory=dict, description="The input parameters of the skill")
    credentials: dict[str, Any] = Field(default_factory=dict, description="The credentials of the skill")

    reference_type: ConnectedServiceType = Field(
        ConnectedServiceType.NONE, description="The type of connected service for the skill, e.g., 'none', 'extension', 'mcp'"
    )
    extension_id: str | None = Field(None, description="The ID of the extension associated with the skill, if applicable")
    mcp_id: str | None = Field(None, description="The ID of the MCP associated with the skill, if applicable")

##################################################
########### REQUEST SCHEMAS ######################
##################################################

class CreateSkillRequest(SkillBase, BaseRequest):
    pass


class SkillUpdateRequest(SkillBase, BaseRequest):
    name: str | None = Field(None, description="The unique name of the skill")
    description: str | None = Field(None, description="A brief description of the skill")
    managed: bool | None = Field(None, description="The managed status of the skill")
    display_name: str | None = Field(None, description="The display name of the skill")
    tool_definition: dict[str, Any] | None = Field(default_factory=dict, description="The tool definition of the skill")
    input_schema: dict[str, Any] | None = Field(None, description="The input schema of the skill")
    credentials: dict[str, Any] | None = Field(default_factory=dict, description="The credentials of the skill")

    reference_type: ConnectedServiceType | None = Field(
        None, description="The type of connected service for the skill, e.g., 'none', 'extension', 'mcp'"
    )
    extension_id: str | None = Field(None, description="The ID of the extension associated with the skill, if applicable")
    mcp_id: str | None = Field(None, description="The ID of the MCP associated with the skill, if applicable")


class ValidateToolDefinitionRequest(BaseRequest):
    tool_definition: dict[str, Any]


##################################################
########### RESPONSE SCHEMAS #####################
##################################################

class SkillResponse(SkillBase, BaseResponse):
    id: str


class SkillsResponse(BaseResponse):
    skills: list[SkillResponse]
    count: int
