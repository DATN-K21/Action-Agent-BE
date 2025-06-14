from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field

from app.core.enums import AssistantType, WorkflowType
from app.schemas.base import BaseRequest, BaseResponse, PagingResponse


class AssistantBase(BaseModel):
    name: str = Field(..., min_length=3, max_length=50)
    description: Optional[str] = Field(None, min_length=3, max_length=500)
    system_prompt: Optional[str] = Field(None, min_length=3, max_length=500)


##################################################
########### REQUEST SCHEMAS ######################
##################################################
class CreateAdvancedAssistantRequest(AssistantBase, BaseRequest):
    provider: str = Field(..., min_length=3, max_length=50, description="Provider of the assistant, e.g., 'openai', 'anthropic'")
    model_name: Optional[str] = Field(None, min_length=1, max_length=50, description="Name of the model to use with the assistant")
    temperature: Optional[float] = Field(None, ge=0.0, le=1.0, description="Controls randomness of the output. Higher values mean more randomness")
    ask_human: Optional[bool] = Field(
        None,
        description="Whether to ask human for confirmation before executing the assistant's task. If true, the assistant will ask human for confirmation before executing its task.",
    )
    interrupt: Optional[bool] = Field(
        None,
        description="Whether to interrupt the assistant's current task. If true, the assistant will stop its current task and return immediately.",
    )
    support_units: Optional[list[WorkflowType]] = Field(
        None, description="List of units (teams) to be used by the assistant. If not provided, the assistant will not use any units."
    )
    mcp_ids: Optional[list[str]] = Field(
        None, description="List of MCP IDs to be used by the assistant. If not provided, the assistant will not use any MCPs."
    )  # This is used for hierarchical unit
    extension_ids: Optional[list[str]] = Field(
        None, description="List of extension IDs to be used by the assistant. If not provided, the assistant will not use any extensions."
    )  # This is used for hierarchical unit


class UpdateAdvancedAssistantRequest(AssistantBase, BaseRequest):
    name: Optional[str] = Field(None, min_length=3, max_length=50)
    description: Optional[str] = Field(None, min_length=3, max_length=500)
    system_prompt: Optional[str] = Field(None, min_length=3, max_length=500)
    provider: Optional[str] = Field(None, min_length=3, max_length=50)
    model_name: Optional[str] = Field(None, min_length=1, max_length=50)
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0)
    ask_human: Optional[bool] = Field(
        None,
        description="Whether to ask human for confirmation before executing the assistant's task. If true, the assistant will ask human for confirmation before executing its task.",
    )
    interrupt: Optional[bool] = Field(
        None,
        description="Whether to interrupt the assistant's current task. If true, the assistant will stop its current task and return immediately.",
    )
    support_units: Optional[list[WorkflowType]] = None
    mcp_ids: Optional[list[str]] = None
    extension_ids: Optional[list[str]] = None


class UpdateAssistantConfigRequest(BaseRequest):
    system_prompt: Optional[str] = Field(None, min_length=3, max_length=500)
    provider: Optional[str] = Field(None, min_length=3, max_length=50)
    model_name: Optional[str] = Field(None, min_length=1, max_length=50)
    temperature: Optional[float] = Field(None, ge=0.0, le=1.0)
    ask_human: Optional[bool] = Field(
        None,
        description="Whether to ask human for confirmation before executing the assistant's task. If true, the assistant will ask human for confirmation before executing its task.",
    )
    interrupt: Optional[bool] = Field(
        None,
        description="Whether to interrupt the assistant's current task. If true, the assistant will stop its current task and return immediately.",
    )


##################################################
########### RESPONSE SCHEMAS #####################
##################################################

class CreateAdvancedAssistantResponse(AssistantBase, BaseResponse):
    id: str
    user_id: str
    name: str
    assistant_type: AssistantType
    description: Optional[str]
    system_prompt: Optional[str]
    provider: Optional[str]  # e.g., 'openai', 'anthropic'
    model_name: Optional[str]
    temperature: Optional[float]
    ask_human: Optional[bool] = Field(
        None,
        description="Whether to ask human for confirmation before executing the assistant's task. If true, the assistant will ask human for confirmation before executing its task.",
    )
    interrupt: Optional[bool] = Field(
        None,
        description="Whether to interrupt the assistant's current task. If true, the assistant will stop its current task and return immediately.",
    )
    main_unit: WorkflowType
    support_units: Optional[list[WorkflowType]]  # unit alias team in this case
    mcp_ids: Optional[list[str]] = Field(
        None, description="List of MCP IDs used by the assistant. If not provided, the assistant will not use any MCPs."
    )
    extension_ids: Optional[list[str]] = Field(
        None, description="List of extension IDs used by the assistant. If not provided, the assistant will not use any extensions."
    )
    teams: Optional[list[dict[str, Any]]] = Field(
        None, description="List of teams (units) associated with the assistant. Each team is represented as a dictionary."
    )
    created_at: Optional[datetime] = Field(None, description="Creation timestamp of the assistant")


class GetAdvancedAssistantResponse(CreateAdvancedAssistantResponse):
    pass


class GetGeneralAssistantResponse(BaseResponse):
    id: str
    user_id: str
    name: str
    assistant_type: AssistantType
    description: Optional[str]
    system_prompt: Optional[str]
    provider: str  # e.g., 'openai', 'anthropic'
    model_name: Optional[str]
    temperature: Optional[float]
    ask_human: Optional[bool] = Field(
        None,
        description="Whether to ask human for confirmation before executing the assistant's task. If true, the assistant will ask human for confirmation before executing its task.",
    )
    interrupt: Optional[bool] = Field(
        None,
        description="Whether to interrupt the assistant's current task. If true, the assistant will stop its current task and return immediately.",
    )
    main_unit: WorkflowType  # Always CHATBOT for general assistant
    support_units: list[WorkflowType]  # Always [RAGBOT, SEARCHBOT] for general assistant
    teams: Optional[list[dict[str, Any]]] = Field(
        None, description="List of teams (units) associated with the general assistant. Each team is represented as a dictionary."
    )
    created_at: Optional[datetime] = Field(None, description="Creation timestamp of the assistant")


class GetAssistantsResponse(PagingResponse):
    assistants: list[GetAdvancedAssistantResponse | GetGeneralAssistantResponse]


class UpdateAdvancedAssistantResponse(CreateAdvancedAssistantResponse):
    pass
