from typing import Literal, Optional

from openai import BaseModel
from pydantic import Field

from app.db_models import Skill, Upload
from app.schemas.base import BaseRequest, BaseResponse


class MemberBase(BaseModel):
    name: str = Field(pattern=r"^[a-zA-Z0-9_-]{1,64}$")
    backstory: Optional[str] = Field(None, max_length=1000, description="A brief backstory of the member")
    role: Optional[str] = Field(None, max_length=100, description="The role of the member")
    type: Literal['leader', 'worker', 'freelancer']  # Enforces specific values
    position_x: float = Field(..., description="X coordinate of the member's position")
    position_y: float = Field(..., description="Y coordinate of the member's position")
    source: Optional[int] = Field(None, description="The source of the member")
    provider: str = Field(..., description="The provider of the member, e.g., 'openai', 'anthropic'")
    model: str = Field(..., description="The model of the member, e.g., 'gpt-3.5-turbo', 'claude-2'")
    temperature: float = Field(0, ge=0.0, le=1.0, description="Temperature for the member's responses")
    interrupt: bool = Field(False, description="Whether the member is interrupted")


##################################################
########### REQUEST SCHEMAS ######################
##################################################

class CreateMemberRequest(MemberBase, BaseRequest):
    pass


class UpdateMemberRequest(MemberBase, BaseRequest):
    name: str | None = Field(None, description="The name of the member to update", pattern=r"^[a-zA-Z0-9_-]{1,64}$")
    backstory: str | None = Field(None, description="A brief backstory of the member")
    role: str | None = Field(None, description="The role of the member")
    type: str | None = Field(None, description="The type of the member")
    team_id: int | None = Field(None, description="The id of the member")
    position_x: float | None = Field(None, description="X coordinate of the member's position")
    position_y: float | None = Field(None, description="Y coordinate of the member's position")
    skills: list["Skill"] | None = Field(None, description="List of skills associated with the member")
    uploads: list["Upload"] | None = Field(None, description="List of uploads associated with the member")
    provider: str | None = Field(None, description="The provider of the member, e.g., 'openai', 'anthropic'")
    model: str | None = Field(None, description="The model of the member")
    temperature: float | None = Field(None, ge=0.0, le=1.0, description="Temperature for the member's responses")
    interrupt: bool | None = Field(None, description="Whether the member is interrupted")


##################################################
########### RESPONSE SCHEMAS #####################
##################################################

class MemberResponse(MemberBase, BaseResponse):
    id: int
    belongs_to: int
    skills: list["Skill"]
    uploads: list["Upload"]


class MembersResponse(BaseResponse):
    members: list[MemberResponse]
    count: int
