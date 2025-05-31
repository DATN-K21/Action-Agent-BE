from typing import Any

from openai import BaseModel
from pydantic import Field

from app.core.enums import StorageStrategy
from app.schemas.base import BaseRequest, BaseResponse


class SkillBase(BaseModel):
    name: str = Field(..., description="The unique name of the skill")
    description: str | None = Field(None, description="A brief description of the skill")
    icon: str | None = Field(None, description="An icon image of the skill")
    strategy: StorageStrategy | None = Field(None,
                                             description="The storage strategy for the skill, e.g., 'definition', 'file'")
    display_name: str | None = Field(None, description="The display name of the skill")
    tool_definition: dict[str, Any] = Field(dict, description="The tool definition of the skill")
    input_parameters: dict[str, Any] = Field(dict, description="The input parameters of the skill")
    credentials: dict[str, Any] = Field(dict, description="The credentials of the skill")


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
    tool_definition: dict[str, Any] | None = Field(None, description="The tool definition of the skill")
    input_schema: dict[str, Any] | None = Field(None, description="The input schema of the skill")
    credentials: dict[str, Any] | None = Field(None, description="The credentials of the skill")


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
