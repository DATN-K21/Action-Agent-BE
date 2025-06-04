from pydantic import BaseModel, Field

from app.core.enums import WorkflowType
from app.core.models import ChatMessage, Interrupt
from app.schemas.base import BaseRequest, BaseResponse


class TeamBase(BaseModel):
    name: str = Field(pattern=r"^[a-zA-Z0-9_-]{1,64}$",
                      description="Name of the team, must be 1-64 characters long and can only contain alphanumeric characters, underscores, and hyphens.")
    description: str | None = Field(None, description="Description of the team.")
    icon: str | None = Field(None, description="Icon of the team.")
    workflow_type: WorkflowType = Field(WorkflowType.HIERARCHICAL, description="Workflow type associated with the team, default is 'HIERARCHICAL'.")


##################################################
########### REQUEST SCHEMAS ######################
##################################################

class CreateTeamRequest(TeamBase, BaseRequest):
    pass


class UpdateTeamRequest(TeamBase, BaseRequest):
    name: str | None = Field(None,
                             description="Name of the team, must be 1-64 characters long and can only contain alphanumeric characters, underscores, and hyphens.")
    description: str | None = Field(None, description="Description of the team.")
    icon: str | None = Field(None, description="Icon of the team.")
    workflow_type: str | None = Field(None, description="Workflow associated with the team.")


class ChatTeamRequest(BaseModel):
    messages: list[ChatMessage] = Field(..., description="List of chat messages in the team chat.")
    interrupt: Interrupt | None = Field(None, description="Interrupt associated with the team.")


class ChatTeamPublicRequest(BaseModel):
    message: ChatMessage | None = Field(None, description="List of chat messages in the team chat.")
    interrupt: Interrupt | None = Field(None, description="Interrupt associated with the team.")


##################################################
########### RESPONSE SCHEMAS #####################
##################################################

class TeamResponse(TeamBase, BaseResponse):
    id: int
    user_id: int | None = Field(None, description="ID of the user who owns the team.")


class TeamsResponse(BaseResponse):
    teams: list[TeamResponse] = Field(..., description="List of teams.")
    count: int = Field(..., description="Total count of teams.")
