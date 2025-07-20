from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field

from app.core.enums import AssistantType, WorkflowType
from app.schemas.base import BaseRequest, BaseResponse, PagingResponse


class AssistantBase(BaseModel):
    name: str = Field(..., min_length=3, max_length=100)
    description: Optional[str] = Field(None, min_length=3, max_length=5000)
    system_prompt: Optional[str] = Field(None, min_length=3, max_length=5000)


class CreateAdvancedAssistantCustomLLMRequest(BaseModel):
    provider: str = Field(..., description="The provider of the custom LLM, e.g., 'openai', 'anthropic'")
    model: str = Field(..., description="The model of the custom LLM, e.g., 'gpt-3.5-turbo', 'claude-2'")
    temperature: float = Field(0.0, ge=0.0, le=1.0, description="Temperature for the custom LLM's responses")
    base_url: Optional[str] = Field(None, description="Base URL for the custom LLM API")
    api_key: Optional[str] = Field(None, description="API key for the custom LLM API")


##################################################
########### REQUEST SCHEMAS ######################
##################################################
class CreateAdvancedAssistantRequest(AssistantBase, BaseRequest):
    ask_human: Optional[bool] = Field(
        None,
        description="Whether to ask human for confirmation before executing the assistant's task. If true, the assistant will ask human for confirmation before executing its task.",
    )
    interrupt: Optional[bool] = Field(
        None,
        description="Whether to interrupt the assistant's current task. If true, the assistant will stop its current task and return immediately.",
    )
    scheduler_enabled: Optional[bool] = Field(
        None,
        description="Whether scheduler functionality is enabled for this assistant. If true, the assistant can create and manage scheduled tasks.",
    )
    retrieval_interrupt_skip_enabled: Optional[bool] = Field(
        None,
        description="Whether to skip retrieval interrupt for this assistant. If true, the assistant will not interrupt the retrieval process.",
    )
    support_units: Optional[list[WorkflowType]] = Field(
        None,
        description="List of units (teams) to be used by the assistant. If not provided, the assistant will not use any units.",
        examples=[
            '["searchbot","ragbot"]',  # Main unit for the assistant
        ],
    )
    mcp_ids: Optional[list[str]] = Field(
        None, description="List of MCP IDs to be used by the assistant. If not provided, the assistant will not use any MCPs."
    )  # This is used for hierarchical unit
    extension_ids: Optional[list[str]] = Field(
        None, description="List of extension IDs to be used by the assistant. If not provided, the assistant will not use any extensions."
    )  # This is used for hierarchical unit

    # TODO: refactor code
    base_model: Optional[CreateAdvancedAssistantCustomLLMRequest] = Field(
        None,
        description="Configuration for the base model of the assistant. If not provided, the assistant will use the default model configuration.",
    )
    reasoning_model: Optional[CreateAdvancedAssistantCustomLLMRequest] = Field(
        None,
        description="Configuration for the reasoning model of the assistant. If not provided, the assistant will use the default model configuration.",
    )
    embedding_model: Optional[CreateAdvancedAssistantCustomLLMRequest] = Field(
        None,
        description="Configuration for the embedding model of the assistant. If not provided, the assistant will use the default model configuration.",
    )


class UpdateAdvancedAssistantRequest(AssistantBase, BaseRequest):
    name: Optional[str] = Field(None, min_length=3, max_length=100)
    description: Optional[str] = Field(None, min_length=3, max_length=5000)
    system_prompt: Optional[str] = Field(None, min_length=3, max_length=5000)
    ask_human: Optional[bool] = Field(
        None,
        description="Whether to ask human for confirmation before executing the assistant's task. If true, the assistant will ask human for confirmation before executing its task.",
    )
    interrupt: Optional[bool] = Field(
        None,
        description="Whether to interrupt the assistant's current task. If true, the assistant will stop its current task and return immediately.",
    )
    scheduler_enabled: Optional[bool] = Field(
        None,
        description="Whether scheduler functionality is enabled for this assistant.",
    )
    retrieval_interrupt_skip_enabled: Optional[bool] = Field(
        None,
        description="Whether to skip retrieval interrupt for this assistant. If true, the assistant will not interrupt the retrieval process.",
    )
    support_units: Optional[list[WorkflowType]] = None
    mcp_ids: Optional[list[str]] = None
    extension_ids: Optional[list[str]] = None

    # TODO: refactor code
    base_model: Optional[CreateAdvancedAssistantCustomLLMRequest] = Field(
        None,
        description="Configuration for the base model of the assistant. If not provided, the assistant will use the default model configuration.",
    )
    reasoning_model: Optional[CreateAdvancedAssistantCustomLLMRequest] = Field(
        None,
        description="Configuration for the reasoning model of the assistant. If not provided, the assistant will use the default model configuration.",
    )
    embedding_model: Optional[CreateAdvancedAssistantCustomLLMRequest] = Field(
        None,
        description="Configuration for the embedding model of the assistant. If not provided, the assistant will use the default model configuration.",
    )


class UpdateAssistantConfigRequest(BaseRequest):
    system_prompt: Optional[str] = Field(None, min_length=3, max_length=500)
    ask_human: Optional[bool] = Field(
        None,
        description="Whether to ask human for confirmation before executing the assistant's task. If true, the assistant will ask human for confirmation before executing its task.",
    )
    interrupt: Optional[bool] = Field(
        None,
        description="Whether to interrupt the assistant's current task. If true, the assistant will stop its current task and return immediately.",
    )
    scheduler_enabled: Optional[bool] = Field(
        None,
        description="Whether scheduler functionality is enabled for this assistant.",
    )
    retrieval_interrupt_skip_enabled: Optional[bool] = Field(
        None,
        description="Whether to skip retrieval interrupt for this assistant. If true, the assistant will not interrupt the retrieval process.",
    )


##################################################
########### RESPONSE SCHEMAS #####################
##################################################


class CreateAdvancedAssistantResponse(BaseResponse):
    id: str
    user_id: str
    name: str
    assistant_type: AssistantType
    description: Optional[str]
    system_prompt: Optional[str]
    ask_human: Optional[bool] = Field(
        None,
        description="Whether to ask human for confirmation before executing the assistant's task. If true, the assistant will ask human for confirmation before executing its task.",
    )
    interrupt: Optional[bool] = Field(
        None,
        description="Whether to interrupt the assistant's current task. If true, the assistant will stop its current task and return immediately.",
    )
    scheduler_enabled: Optional[bool] = Field(
        None,
        description="Whether scheduler functionality is enabled for this assistant.",
    )
    retrieval_interrupt_skip_enabled: Optional[bool] = Field(
        None,
        description="Whether to skip retrieval interrupt for this assistant. If true, the assistant will not interrupt the retrieval process.",
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
