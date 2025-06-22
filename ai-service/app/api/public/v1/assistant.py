import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from fastapi import APIRouter, Depends, Header
from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import SessionDep
from app.core import logging
from app.core.constants import SYSTEM
from app.core.enums import AssistantType, ConnectedServiceType, StorageStrategy, WorkflowType
from app.core.settings import env_settings
from app.core.tools.tool_manager import create_unique_key, global_tools, tool_manager
from app.core.utils.convert_type import convert_base_tool_to_tool_info
from app.core.utils.general_assistant_helpers import GeneralAssistantHelpers
from app.db_models.assistant import Assistant
from app.db_models.connected_extension import ConnectedExtension
from app.db_models.connected_mcp import ConnectedMcp
from app.db_models.member import Member
from app.db_models.member_skill_link import MemberSkillLink
from app.db_models.member_upload_link import MemberUploadLink
from app.db_models.skill import Skill
from app.db_models.team import Team
from app.db_models.thread import Thread
from app.schemas.assistant import (
    CreateAdvancedAssistantRequest,
    CreateAdvancedAssistantResponse,
    GetAdvancedAssistantResponse,
    GetAssistantsResponse,
    GetGeneralAssistantResponse,
    UpdateAdvancedAssistantRequest,
    UpdateAdvancedAssistantResponse,
    UpdateAssistantConfigRequest,
)
from app.schemas.base import MessageResponse, PagingRequest, ResponseWrapper
from app.services.extensions import extension_service_manager
from app.services.mcps.mcp_service import McpService

logger = logging.get_logger(__name__)

router = APIRouter(prefix="/assistant", tags=["Assistant"])


# ================================
# HELPER FUNCTIONS
# ================================


def _extract_support_units(assistant: Assistant) -> List[WorkflowType]:
    """
    Extract support units from the assistant object.
    This function identifies which workflow types are used as support units
    by excluding the main unit type from the teams.

    Args:
        assistant: The assistant object containing teams

    Returns:
        List of workflow types used as support units
    """
    support_units = []

    # Determine main unit based on assistant type
    main_unit = WorkflowType.CHATBOT

    # Extract support units from teams (exclude main unit)
    for team in assistant.teams:
        if team.workflow_type and team.workflow_type != main_unit:
            support_units.append(team.workflow_type)

    return support_units


async def _abuild_assistant_query(
    session: AsyncSession,
    user_id: Optional[str] = None,
    user_role: Optional[str] = None,
    assistant_type: Optional[AssistantType] = None,
    assistant_id: Optional[str] = None,
    page_number: int = 1,
    max_per_page: int = 10,
) -> Tuple[Any, Any, int]:
    """
    Build and execute assistant query with filters and pagination.

    Args:
        session: Database session
        user_id: User ID for filtering (None for admin users)
        user_role: User role for access control
        assistant_type: Filter by assistant type
        assistant_id: Specific assistant ID to query
        page_number: Page number for pagination
        max_per_page: Maximum items per page

    Returns:
        Tuple of (query_result, count_result, total_pages)
    """
    # Build base query
    query = (
        select(Assistant)
        .select_from(Assistant)
        .options(selectinload(Assistant.teams).selectinload(Team.members))
        .where(Assistant.is_deleted.is_(False))
    )

    count_query = select(func.count(Assistant.id)).select_from(Assistant).where(Assistant.is_deleted.is_(False))

    # Apply filters
    if assistant_id:
        query = query.where(Assistant.id == assistant_id)
        count_query = count_query.where(Assistant.id == assistant_id)

    if user_role not in ["admin", "superuser"] and user_id:
        query = query.where(Assistant.user_id == user_id)
        count_query = count_query.where(Assistant.user_id == user_id)

    if assistant_type:
        query = query.where(Assistant.assistant_type == assistant_type)
        count_query = count_query.where(Assistant.assistant_type == assistant_type)

    # Get count
    count_result = await session.execute(count_query)
    count = count_result.scalar_one()

    if count == 0:
        return None, count, 0

    # Calculate pagination
    total_pages = (count + max_per_page - 1) // max_per_page
    offset = (page_number - 1) * max_per_page

    # Apply pagination
    query = query.offset(offset).limit(max_per_page)

    # Execute query
    result = await session.execute(query)
    return result, count, total_pages


def _format_team_data(teams: List[Team]) -> List[Dict[str, Any]]:
    """
    Format team data for API response.

    Args:
        teams: List of team objects

    Returns:
        List of formatted team dictionaries
    """
    return [
        {
            "id": team.id,
            "name": team.name,
            "description": team.description,
            "workflow_type": team.workflow_type,
            "members": [
                {
                    "id": member.id,
                    "name": member.name,
                    "type": member.type,
                    "role": member.role,
                }
                for member in team.members
            ],
        }
        for team in teams
    ]


def _format_assistant_response(
    assistant: Assistant,
    teams_data: List[Dict[str, Any]],
    mcp_ids: Optional[List[str]] = None,
    extension_ids: Optional[List[str]] = None,
) -> GetAdvancedAssistantResponse | GetGeneralAssistantResponse:
    """
    Format assistant data for API response.
    Returns either GetGeneralAssistantResponse or GetAdvancedAssistantResponse based on assistant type.

    Args:
        assistant: Assistant object
        teams_data: Formatted team data
        mcp_ids: List of MCP IDs for advanced assistants
        extension_ids: List of extension IDs for advanced assistants

    Returns:
        GetGeneralAssistantResponse for general assistants or GetAdvancedAssistantResponse for advanced assistants
    """  # Import here to avoid circular imports
    from app.core.settings import env_settings

    if assistant.assistant_type == AssistantType.GENERAL_ASSISTANT:
        return GetGeneralAssistantResponse(
            id=assistant.id,
            user_id=assistant.user_id,
            name=assistant.name,
            assistant_type=assistant.assistant_type,
            description=assistant.description,
            system_prompt=assistant.system_prompt,
            provider=assistant.provider or env_settings.OPENAI_PROVIDER,
            model_name=assistant.model_name or env_settings.LLM_BASIC_MODEL,
            temperature=assistant.temperature if assistant.temperature is not None else env_settings.BASIC_MODEL_TEMPERATURE,
            ask_human=None,
            interrupt=None,
            main_unit=WorkflowType.CHATBOT,
            support_units=_extract_support_units(assistant),
            teams=teams_data,
            created_at=assistant.created_at,
        )
    elif assistant.assistant_type == AssistantType.ADVANCED_ASSISTANT:
        return GetAdvancedAssistantResponse(
            id=assistant.id,
            user_id=assistant.user_id,
            name=assistant.name,
            assistant_type=assistant.assistant_type,
            description=assistant.description,
            system_prompt=assistant.system_prompt,
            provider=assistant.provider or env_settings.OPENAI_PROVIDER,
            model_name=assistant.model_name or env_settings.LLM_BASIC_MODEL,
            temperature=assistant.temperature if assistant.temperature is not None else env_settings.BASIC_MODEL_TEMPERATURE,
            ask_human=assistant.ask_human,
            interrupt=assistant.interrupt,
            main_unit=WorkflowType.CHATBOT,
            support_units=_extract_support_units(assistant),
            teams=teams_data,
            created_at=assistant.created_at,
            mcp_ids=mcp_ids,
            extension_ids=extension_ids,
        )
    else:
        # Default to general assistant response for unknown types
        return GetGeneralAssistantResponse(
            id=assistant.id,
            user_id=assistant.user_id,
            name=assistant.name,
            assistant_type=assistant.assistant_type,
            description=assistant.description,
            system_prompt=assistant.system_prompt,
            provider=assistant.provider or env_settings.OPENAI_PROVIDER,
            model_name=assistant.model_name or env_settings.LLM_BASIC_MODEL,
            temperature=assistant.temperature if assistant.temperature is not None else env_settings.BASIC_MODEL_TEMPERATURE,
            ask_human=None,
            interrupt=None,
            main_unit=WorkflowType.CHATBOT,
            support_units=_extract_support_units(assistant),
            teams=teams_data,
            created_at=assistant.created_at,
        )


async def _acreate_hierarchical_team(
    session: AsyncSession, assistant: Assistant, request: CreateAdvancedAssistantRequest, user_id: str
) -> Tuple[Team, Member]:
    """
    Create a hierarchical team for an advanced assistant support unit.

    Args:
        session: Database session
        assistant: The assistant object
        request: Request data
        user_id: User ID

    Returns:
        Created team object
    """
    # Create hierarchical team
    hierarchical_team_id = str(uuid.uuid4())
    hierarchical_team_name = create_unique_key(id_=hierarchical_team_id, name="Hierarchical Unit")
    hierarchical_team = Team(
        id=hierarchical_team_id,
        name=hierarchical_team_name,
        description="Execute user tasks based on integrated workers' tools.",
        workflow_type=WorkflowType.HIERARCHICAL,
        user_id=user_id,
        assistant_id=assistant.id,
    )
    session.add(hierarchical_team)
    await session.flush()

    # Create root member (leader) for the hierarchical team
    root_member_id = str(uuid.uuid4())
    root_member_name = create_unique_key(id_=root_member_id, name="Leader")
    root_member = Member(
        id=root_member_id,
        name=root_member_name,
        team_id=hierarchical_team.id,
        backstory="Leader of the hierarchical team for advanced assistant.",
        role="Gather inputs, outputs from your team and answer the question.",
        type="root",
        provider=request.provider or env_settings.ANTHROPIC_PROVIDER,
        model=request.model_name or env_settings.LLM_REASONING_MODEL,
        temperature=request.temperature if request.temperature is not None else env_settings.REASONING_MODEL_TEMPERATURE,
        interrupt=False,
        position_x=0.0,
        position_y=0.0,
    )
    session.add(root_member)
    await session.flush()

    return hierarchical_team, root_member


async def _acreate_main_team(
    session: AsyncSession, assistant: Assistant, request: CreateAdvancedAssistantRequest, user_id: str
) -> Tuple[Team, Member]:
    """
    Create the main chatbot team for an advanced assistant.

    Args:
        session: Database session
        assistant: The assistant object
        request: Request data
        user_id: User ID

    Returns:
        Created team and root member objects
    """
    # Create main chatbot team
    main_team_id = str(uuid.uuid4())
    main_team_name = create_unique_key(id_=main_team_id, name="Chatbot Unit")
    main_team = Team(
        id=main_team_id,
        name=main_team_name,
        description="Main chatbot unit for handling small talk and basic user interactions.",
        workflow_type=WorkflowType.CHATBOT,
        user_id=user_id,
        assistant_id=assistant.id,
    )
    session.add(main_team)
    await session.flush()

    # Create root member (chatbot) for the main team
    root_member_id = str(uuid.uuid4())
    root_member_name = create_unique_key(id_=root_member_id, name="Chatbot Unit Root")
    root_member = Member(
        id=root_member_id,
        name=root_member_name,
        team_id=main_team.id,
        backstory="A friendly chatbot assistant specialized in natural conversation and general assistance. Provides helpful responses to greetings, engages in meaningful small talk, and answers user questions using available tools. Focuses on being conversational and supportive without trying to take over the conversation flow.",
        role="Respond naturally to greetings and small talk. Answer user questions directly using available search and knowledge tools when needed. Provide helpful information and maintain a friendly conversational tone. Do not ask users what they want - simply respond to what they've said.",
        type="chatbot",
        provider=request.provider or env_settings.OPENAI_PROVIDER,
        model=request.model_name or env_settings.LLM_BASIC_MODEL,
        temperature=request.temperature if request.temperature is not None else env_settings.BASIC_MODEL_TEMPERATURE,
        interrupt=False,
        position_x=0.0,
        position_y=0.0,
        created_by=SYSTEM,
    )
    session.add(root_member)
    await session.flush()

    # Create search skills for the chatbot
    await _acreate_search_skills(session, root_member.id, user_id)

    return main_team, root_member


async def _acreate_mcp_member_with_skills(
    session: AsyncSession,
    connected_mcp: ConnectedMcp,
    team_id: str,
    root_member_id: str,
    request: CreateAdvancedAssistantRequest,
) -> None:
    """
    Create a member with MCP skills for a team.

    Args:
        session: Database session
        connected_mcp: Connected MCP object
        team_id: Team ID to add member to
        root_member_id: Root member ID for source reference
        request: Request data containing provider/model info
    """
    # Create member
    member_id = str(uuid.uuid4())
    member_name = create_unique_key(id_=member_id, name=connected_mcp.mcp_name)
    member = Member(
        id=member_id,
        name=member_name,
        team_id=team_id,
        backstory=connected_mcp.description if connected_mcp.description is not None else None,
        role="Execute actions based on provided tasks using binding tools and return the results",
        type="worker",
        source=root_member_id,
        provider=request.provider or env_settings.ANTHROPIC_PROVIDER,
        model=request.model_name or env_settings.LLM_REASONING_MODEL,
        temperature=request.temperature if request.temperature is not None else env_settings.REASONING_MODEL_TEMPERATURE,
        interrupt=request.interrupt if request.interrupt is not None else False,
        position_x=0.0,
        position_y=0.0,
    )
    session.add(member)
    await session.flush()

    # Load MCP tools and create skills using proper connection format
    connections = {}
    connections[connected_mcp.mcp_name] = {
        "url": connected_mcp.url,
        "transport": connected_mcp.transport,
    }

    # Use the existing MCP service to get tool info
    tool_infos = await McpService.aget_mcp_tool_info(connections=connections)

    # Create skills and links
    for tool_info in tool_infos:
        skill_id = str(uuid.uuid4())
        skill_name = create_unique_key(id_=skill_id, name=tool_info.display_name)
        skill = Skill(
            id=skill_id,
            name=skill_name,
            user_id=connected_mcp.user_id,
            description=tool_info.description,
            icon="",
            display_name=tool_info.display_name,
            strategy=StorageStrategy.PERSONAL_TOOL_CACHE,
            input_parameters=tool_info.input_parameters,
            reference_type=ConnectedServiceType.MCP,
            mcp_id=connected_mcp.id,
        )
        session.add(skill)
        await session.flush()

        # Link skill to member
        member_skill_link = MemberSkillLink(
            member_id=member.id,
            skill_id=skill.id,
        )
        session.add(member_skill_link)
        await session.flush()

        # Add tool to cache
        await tool_manager.aadd_personal_tool(
            user_id=connected_mcp.user_id,
            tool_key=skill_name,
            tool_info=tool_info,
        )


async def _acreate_extension_member_with_skills(
    session: AsyncSession,
    connected_extension: ConnectedExtension,
    team_id: str,
    root_member_id: str,
    request: CreateAdvancedAssistantRequest,
) -> None:
    """
    Create a member with extension skills for a team.

    Args:
        session: Database session
        connected_extension: Connected extension object
        team_id: Team ID to add member to
        root_member_id: Root member ID for source reference
        request: Request data containing provider/model info
    """
    # Create member
    member_id = str(uuid.uuid4())
    member_name = create_unique_key(id_=member_id, name=connected_extension.extension_name)
    member = Member(
        id=member_id,
        name=member_name,
        team_id=team_id,
        backstory="",
        role="Execute actions based on provided tasks using binding tools and return the results",
        type="worker",
        source=root_member_id,
        provider=request.provider or env_settings.ANTHROPIC_PROVIDER,
        model=request.model_name or env_settings.LLM_REASONING_MODEL,
        temperature=request.temperature if request.temperature is not None else env_settings.REASONING_MODEL_TEMPERATURE,
        interrupt=request.interrupt if request.interrupt is not None else False,
        position_x=0.0,
        position_y=0.0,
    )
    session.add(member)
    await session.flush()

    # Load extension tools and create skills
    extension_service_info = extension_service_manager.get_service_info(service_enum=connected_extension.extension_enum)

    if not extension_service_info or not extension_service_info.service_object:
        raise ValueError(f"Extension service info for {connected_extension.extension_enum} not found or service object is None.")

    extension_service = extension_service_info.service_object
    tools = extension_service.get_authed_tools(user_id=connected_extension.user_id)
    tool_infos = [convert_base_tool_to_tool_info(tool) for tool in tools]

    # Create skills and links
    for tool_info in tool_infos:
        skill_id = str(uuid.uuid4())
        skill_name = create_unique_key(id_=skill_id, name=tool_info.display_name)
        skill = Skill(
            id=skill_id,
            name=skill_name,
            user_id=connected_extension.user_id,
            description=tool_info.description,
            icon="",
            display_name=tool_info.display_name,
            strategy=StorageStrategy.PERSONAL_TOOL_CACHE,
            input_parameters=tool_info.input_parameters,
            reference_type=ConnectedServiceType.EXTENSION,
            extension_id=connected_extension.id,
        )
        session.add(skill)
        await session.flush()

        # Link skill to member
        member_skill_link = MemberSkillLink(
            member_id=member.id,
            skill_id=skill.id,
        )
        session.add(member_skill_link)
        await session.flush()

        # Add tool to cache
        await tool_manager.aadd_personal_tool(
            user_id=connected_extension.user_id,
            tool_key=skill_name,
            tool_info=tool_info,
        )


async def _acreate_support_team(
    session: AsyncSession,
    assistant: Assistant,
    workflow_type: WorkflowType,
    request: CreateAdvancedAssistantRequest,
    user_id: str,
) -> Team:
    """
    Create a support team for specific workflow type.

    Args:
        session: Database session
        assistant: Assistant object
        workflow_type: Type of workflow for the support team
        request: Request data
        user_id: User ID

    Returns:
        Created support team
    """
    # Create support team
    support_team_id = str(uuid.uuid4())
    str_workflow_type = workflow_type.value
    support_team_name = create_unique_key(id_=support_team_id, name=f"{str_workflow_type} Support Unit")
    support_team = Team(
        id=support_team_id,
        name=support_team_name,
        description=f"Support unit for {str_workflow_type} in advanced assistant.",
        workflow_type=workflow_type,
        user_id=user_id,
        assistant_id=assistant.id,
    )
    session.add(support_team)
    await session.flush()

    # Create root member for the support team
    support_root_member_id = str(uuid.uuid4())
    support_root_member_name = create_unique_key(id_=support_root_member_id, name=f"{str_workflow_type} Support Root")
    support_root_member = Member(
        id=support_root_member_id,
        name=support_root_member_name,
        team_id=support_team.id,
        backstory=f"Unit for advanced assistant: {str_workflow_type}.",
        role="Answer the user's question.",
        type=f"{str_workflow_type}",
        provider=request.provider or env_settings.OPENAI_PROVIDER,
        model=request.model_name or env_settings.LLM_BASIC_MODEL,
        temperature=request.temperature if request.temperature is not None else env_settings.BASIC_MODEL_TEMPERATURE,
        interrupt=False,
        position_x=0.0,
        position_y=0.0,
    )
    session.add(support_root_member)
    await session.flush()

    if workflow_type == WorkflowType.SEARCHBOT:
        await _acreate_search_skills(session, support_root_member.id, user_id)

    return support_team


async def _acreate_search_skills(session: SessionDep, member_id: str, user_id: str) -> None:
    """Create search skills for SEARCHBOT workflow type."""
    # DuckDuckGo search skill
    ddg_tool_info = global_tools.get("duckduckgo-search")
    if not ddg_tool_info:
        raise ValueError("DuckDuckGo search tool not found in global tools.")

    ddg_skill_id = str(uuid.uuid4())
    ddg_skill = Skill(
        id=ddg_skill_id,
        name="duckduckgo-search",
        user_id=user_id,
        description=ddg_tool_info.description,
        icon="",
        display_name=ddg_tool_info.display_name,
        strategy=StorageStrategy.GLOBAL_TOOLS,
        input_parameters=ddg_tool_info.input_parameters,
        reference_type=ConnectedServiceType.NONE,
    )
    session.add(ddg_skill)
    await session.flush()

    member_skill_link = MemberSkillLink(
        member_id=member_id,
        skill_id=ddg_skill.id,
    )
    session.add(member_skill_link)
    await session.flush()

    # Wikipedia search skill
    wikipedia_tool_info = global_tools.get("wikipedia")
    if not wikipedia_tool_info:
        raise ValueError("Wikipedia tool not found in global tools.")

    wikipedia_skill_id = str(uuid.uuid4())
    wikipedia_skill = Skill(
        id=wikipedia_skill_id,
        name="wikipedia",
        user_id=user_id,
        description=wikipedia_tool_info.description,
        icon="",
        display_name=wikipedia_tool_info.display_name,
        strategy=StorageStrategy.GLOBAL_TOOLS,
        input_parameters=wikipedia_tool_info.input_parameters,
        reference_type=ConnectedServiceType.NONE,
    )
    session.add(wikipedia_skill)
    await session.flush()

    member_skill_link = MemberSkillLink(
        member_id=member_id,
        skill_id=wikipedia_skill.id,
    )
    session.add(member_skill_link)
    await session.flush()


async def _adelete_members_with_service_type(session: AsyncSession, team: Team, service_type: ConnectedServiceType) -> None:
    """
    Delete members and their skills based on service type.

    Args:
        session: Database session
        team: Team object containing members
        service_type: Type of service to filter members by
    """
    member_ids_to_delete = []

    for member in team.members:
        if member.type == "worker":
            # Check if this member has skills of the specified service type
            statement = (
                select(Skill)
                .select_from(Skill)
                .join(MemberSkillLink, Skill.id == MemberSkillLink.skill_id)
                .where(MemberSkillLink.member_id == member.id, Skill.reference_type == service_type)
            )

            skill_result = await session.execute(statement)
            skills = skill_result.scalars().all()

            if skills:
                member_ids_to_delete.append(member.id)

    # Delete member skills and skills first, then members
    if member_ids_to_delete:
        # Get all skill IDs associated with these members before deleting links
        skills_statement = (
            select(Skill.id)
            .select_from(Skill)
            .join(MemberSkillLink, Skill.id == MemberSkillLink.skill_id)
            .where(MemberSkillLink.member_id.in_(member_ids_to_delete), Skill.reference_type == service_type)
        )
        skills_result = await session.execute(skills_statement)
        skill_ids = skills_result.scalars().all()  # Delete member skill links
        await session.execute(delete(MemberSkillLink).where(MemberSkillLink.member_id.in_(member_ids_to_delete)))

        # Delete member upload links
        await session.execute(delete(MemberUploadLink).where(MemberUploadLink.member_id.in_(member_ids_to_delete)))

        # Delete skills associated with these members
        if skill_ids:
            await session.execute(delete(Skill).where(Skill.id.in_(skill_ids)))

        # Delete members
        await session.execute(delete(Member).where(Member.id.in_(member_ids_to_delete)))


async def _ahard_delete_assistant_cascade(session: AsyncSession, assistant_id: str) -> None:
    """
    Delete an assistant and all related entities in cascade.

    Args:
        session: Database session
        assistant_id: ID of the assistant to delete
    """
    # Update threads that reference this assistant to set assistant_id to null and mark as deleted
    await session.execute(
        update(Thread).where(Thread.assistant_id == assistant_id).values(assistant_id=None, is_deleted=True, deleted_at=datetime.now())
    )

    # Get all team IDs associated with the assistant
    teams_statement = select(Team.id).select_from(Team).where(Team.assistant_id == assistant_id)
    teams_result = await session.execute(teams_statement)
    team_ids = teams_result.scalars().all()

    if team_ids:  # Get all member IDs from these teams
        members_statement = select(Member.id).where(Member.team_id.in_(team_ids))
        members_result = await session.execute(members_statement)
        member_ids = members_result.scalars().all()

        if member_ids:
            # Get all skill IDs associated with these members before deleting links
            skills_statement = (
                select(Skill.id)
                .select_from(Skill)
                .join(MemberSkillLink, Skill.id == MemberSkillLink.skill_id)
                .where(MemberSkillLink.member_id.in_(member_ids))
            )
            skills_result = await session.execute(skills_statement)
            skill_ids = skills_result.scalars().all()  # Delete member skill links
            await session.execute(delete(MemberSkillLink).where(MemberSkillLink.member_id.in_(member_ids)))

            # Delete member upload links
            await session.execute(delete(MemberUploadLink).where(MemberUploadLink.member_id.in_(member_ids)))

            # Delete skills associated with these members
            if skill_ids:
                await session.execute(delete(Skill).where(Skill.id.in_(skill_ids)))

            # Delete members
            await session.execute(delete(Member).where(Member.id.in_(member_ids)))

        # Delete teams
        await session.execute(delete(Team).where(Team.id.in_(team_ids)))

    # Finally, delete the assistant
    await session.execute(delete(Assistant).where(Assistant.id == assistant_id))


async def _aget_main_team_for_assistant(session: AsyncSession, assistant_id: str, user_id: str) -> Optional[Team]:
    """
    Get the main chatbot team for an assistant.

    Args:
        session: Database session
        assistant_id: ID of the assistant
        user_id: User ID

    Returns:
        Main team or None if not found
    """
    statement = (
        select(Team)
        .select_from(Team)
        .options(selectinload(Team.members))
        .where(
            Team.user_id == user_id,
            Team.assistant_id == assistant_id,
            Team.workflow_type == WorkflowType.CHATBOT,
            Team.is_deleted.is_(False),
        )
    )

    result = await session.execute(statement)
    return result.scalar_one_or_none()


def _update_assistant_basic_info(assistant: Assistant, request: UpdateAdvancedAssistantRequest) -> None:
    """
    Update basic assistant information (name, description, system_prompt).

    Args:
        assistant: Assistant entity to update
        request: Update request data
    """
    if request.name:
        setattr(assistant, "name", request.name)
    if request.description:
        setattr(assistant, "description", request.description)
    if request.system_prompt:
        setattr(assistant, "system_prompt", request.system_prompt)
    if request.provider:
        setattr(assistant, "provider", request.provider)
    if request.model_name:
        setattr(assistant, "model_name", request.model_name)
    if request.temperature is not None:
        setattr(assistant, "temperature", request.temperature)
    if request.ask_human is not None:
        setattr(assistant, "ask_human", request.ask_human)
    if request.interrupt is not None:
        setattr(assistant, "interrupt", request.interrupt)


async def _aupdate_mcp_members(
    session: AsyncSession,
    hierarchical_team: Team,
    request: UpdateAdvancedAssistantRequest,
    user_id: str,
) -> None:
    """
    Update MCP members for the hierarchical team by deleting existing ones and creating new ones.

    Args:
        session: Database session
        hierarchical_team: Hierarchical team to update members for
        request: Update request containing new MCP IDs
        user_id: User ID
    """
    # Only delete existing MCP members if new ones are provided
    if request.mcp_ids is not None:
        await _adelete_members_with_service_type(session, hierarchical_team, ConnectedServiceType.MCP)

        # If empty list provided, just return after deletion (remove all)
        if len(request.mcp_ids) == 0:
            return

        # Get root member ID for linking new MCP members
        root_member_id = None
        for member in hierarchical_team.members:
            if member.type == "root":
                root_member_id = member.id
                break

        if not root_member_id:
            raise ValueError("Root member not found in hierarchical team")

        # Create new MCP members and their skills
        for mcp_id in request.mcp_ids:
            statement = select(ConnectedMcp).where(
                ConnectedMcp.id == mcp_id,
                ConnectedMcp.user_id == user_id,
                ConnectedMcp.is_deleted.is_(False),
            )

            result = await session.execute(statement)
            connected_mcp = result.scalar_one_or_none()

            if connected_mcp:
                # Create member
                member_id = str(uuid.uuid4())
                member_name = create_unique_key(id_=member_id, name=connected_mcp.mcp_name)
                member = Member(
                    id=member_id,
                    name=member_name,
                    team_id=hierarchical_team.id,
                    backstory=connected_mcp.description if connected_mcp.description is not None else None,
                    role="Execute actions based on provided tasks using binding tools and return the results",
                    type="worker",
                    source=root_member_id,
                    provider=request.provider or env_settings.ANTHROPIC_PROVIDER,
                    model=request.model_name or env_settings.LLM_REASONING_MODEL,
                    temperature=request.temperature if request.temperature is not None else env_settings.REASONING_MODEL_TEMPERATURE,
                    interrupt=request.interrupt if request.interrupt is not None else False,
                    position_x=0.0,
                    position_y=0.0,
                )
                session.add(member)
                await session.flush()

                # Create MCP skills using proper connection format
                connections = {}
                connections[connected_mcp.mcp_name] = {
                    "url": connected_mcp.url,
                    "transport": connected_mcp.transport,
                }
                tool_infos = await McpService.aget_mcp_tool_info(connections=connections)

                # Create skills and link them to the member
                for tool_info in tool_infos:
                    skill_id = str(uuid.uuid4())
                    skill_name = create_unique_key(id_=skill_id, name=tool_info.display_name)
                    skill = Skill(
                        id=skill_id,
                        name=skill_name,
                        user_id=user_id,
                        description=tool_info.description,
                        icon="",
                        display_name=tool_info.display_name,
                        strategy=StorageStrategy.PERSONAL_TOOL_CACHE,
                        input_parameters=tool_info.input_parameters,
                        reference_type=ConnectedServiceType.MCP,
                        mcp_id=connected_mcp.id,
                    )
                    session.add(skill)
                    await session.flush()

                    # Link skill to member
                    member_skill_link = MemberSkillLink(
                        member_id=member.id,
                        skill_id=skill.id,
                    )
                    session.add(member_skill_link)
                    await session.flush()

                    # Add tool to cache
                    await tool_manager.aadd_personal_tool(
                        user_id=user_id,
                        tool_key=skill_name,
                        tool_info=tool_info,
                    )


async def _aupdate_extension_members(
    session: AsyncSession,
    hierarchical_team: Team,
    request: UpdateAdvancedAssistantRequest,
    user_id: str,
) -> None:
    """
    Update extension members for the hierarchical team by deleting existing ones and creating new ones.

    Args:
        session: Database session
        hierarchical_team: Hierarchical team to update members for
        request: Update request containing new extension IDs
        user_id: User ID
    """
    # Only delete existing extension members if new ones are provided
    if request.extension_ids is not None:
        await _adelete_members_with_service_type(session, hierarchical_team, ConnectedServiceType.EXTENSION)

        # If empty list provided, just return after deletion (remove all)
        if len(request.extension_ids) == 0:
            return

        # Get root member ID for linking new extension members
        root_member_id = None
        for member in hierarchical_team.members:
            if member.type == "root":
                root_member_id = member.id
                break

        if not root_member_id:
            raise ValueError("Root member not found in hierarchical team")

        # Create new extension members and their skills
        for extension_id in request.extension_ids:
            statement = select(ConnectedExtension).where(
                ConnectedExtension.id == extension_id,
                ConnectedExtension.user_id == user_id,
                ConnectedExtension.is_deleted.is_(False),
            )
            result = await session.execute(statement)
            connected_extension = result.scalar_one_or_none()

            if connected_extension:
                # Create member
                member_id = str(uuid.uuid4())
                member_name = create_unique_key(id_=member_id, name=connected_extension.extension_name)
                member = Member(
                    id=member_id,
                    name=member_name,
                    team_id=hierarchical_team.id,
                    backstory="",
                    role="Execute actions based on provided tasks using binding tools and return the results",
                    type="worker",
                    source=root_member_id,
                    provider=request.provider or env_settings.ANTHROPIC_PROVIDER,
                    model=request.model_name or env_settings.LLM_REASONING_MODEL,
                    temperature=request.temperature if request.temperature is not None else env_settings.REASONING_MODEL_TEMPERATURE,
                    interrupt=request.interrupt if request.interrupt is not None else False,
                    position_x=0.0,
                    position_y=0.0,
                )
                session.add(member)
                await session.flush()

                # Create extension skills
                extension_service_info = extension_service_manager.get_service_info(service_enum=connected_extension.extension_enum)

                if not extension_service_info or not extension_service_info.service_object:
                    raise ValueError(f"Extension service info for {connected_extension.extension_enum} not found or service object is None.")

                extension_service = extension_service_info.service_object
                tools = extension_service.get_authed_tools(user_id=connected_extension.user_id)
                tool_infos = [convert_base_tool_to_tool_info(tool) for tool in tools]

                # Create skills and link them to the member
                for tool_info in tool_infos:
                    skill_id = str(uuid.uuid4())
                    skill_name = create_unique_key(id_=skill_id, name=tool_info.display_name)
                    skill = Skill(
                        id=skill_id,
                        name=skill_name,
                        user_id=user_id,
                        description=tool_info.description,
                        icon="",
                        display_name=tool_info.display_name,
                        strategy=StorageStrategy.PERSONAL_TOOL_CACHE,
                        input_parameters=tool_info.input_parameters,
                        reference_type=ConnectedServiceType.EXTENSION,
                        extension_id=connected_extension.id,
                    )
                    session.add(skill)
                    await session.flush()

                    # Link skill to member
                    member_skill_link = MemberSkillLink(
                        member_id=member.id,
                        skill_id=skill.id,
                    )
                    session.add(member_skill_link)
                    await session.flush()

                    # Add tool to cache
                    await tool_manager.aadd_personal_tool(
                        user_id=user_id,
                        tool_key=skill_name,
                        tool_info=tool_info,
                    )


async def _aupdate_support_units(
    session: AsyncSession,
    assistant: Assistant,
    request: UpdateAdvancedAssistantRequest,
    user_id: str,
) -> None:
    """
    Update support units by deleting existing support teams and creating new ones.

    Args:
        session: Database session
        assistant: Assistant to update support units for
        request: Update request containing new support units
        user_id: User ID
    """  # Only update support units if they are provided in the request
    if request.support_units is not None:
        # Delete all support teams (except chatbot team and hierarchical team)
        all_teams_statement = select(Team).select_from(Team).where(Team.assistant_id == assistant.id)
        all_teams_result = await session.execute(all_teams_statement)
        all_teams = all_teams_result.scalars().all()

        # Find teams to delete (except the chatbot team and hierarchical team)
        teams_to_delete = [
            team.id for team in all_teams if team.workflow_type != WorkflowType.CHATBOT and team.workflow_type != WorkflowType.HIERARCHICAL
        ]

        if teams_to_delete:
            # Get member IDs before deleting teams
            member_statement = select(Member.id).where(Member.team_id.in_(teams_to_delete))
            member_result = await session.execute(member_statement)
            member_ids = member_result.scalars().all()

            if member_ids:
                # Get all skill IDs associated with these members before deleting links
                skills_statement = (
                    select(Skill.id)
                    .select_from(Skill)
                    .join(MemberSkillLink, Skill.id == MemberSkillLink.skill_id)
                    .where(MemberSkillLink.member_id.in_(member_ids))
                )
                skills_result = await session.execute(skills_statement)
                skill_ids = skills_result.scalars().all()  # Delete member skill links
                await session.execute(delete(MemberSkillLink).where(MemberSkillLink.member_id.in_(member_ids)))

                # Delete member upload links
                await session.execute(delete(MemberUploadLink).where(MemberUploadLink.member_id.in_(member_ids)))

                # Delete skills associated with these members
                if skill_ids:
                    await session.execute(delete(Skill).where(Skill.id.in_(skill_ids)))

            # Delete members
            await session.execute(delete(Member).where(Member.team_id.in_(teams_to_delete)))

            # Delete teams
            await session.execute(delete(Team).where(Team.id.in_(teams_to_delete)))

        # Create new support teams if any are provided
        if len(request.support_units) > 0:
            for unit in request.support_units:
                # Create a support team for each unit
                support_team_id = str(uuid.uuid4())
                support_team_name = create_unique_key(id_=support_team_id, name=f"Support Unit - {unit}")
                support_team = Team(
                    id=support_team_id,
                    name=support_team_name,
                    description=f"Support unit for {unit} in advanced assistant.",
                    workflow_type=unit,
                    user_id=user_id,
                    assistant_id=assistant.id,
                )
                session.add(support_team)
                await session.flush()

                # Create root member for the support team
                support_root_member_id = str(uuid.uuid4())
                support_root_member_name = create_unique_key(id_=support_root_member_id, name=f"{unit} Support Root")
                support_root_member = Member(
                    id=support_root_member_id,
                    name=support_root_member_name,
                    team_id=support_team.id,
                    backstory=f"Unit for advanced assistant: {unit}.",
                    role="Answer the user's question.",
                    type=f"{unit}",
                    provider=request.provider or env_settings.OPENAI_PROVIDER,
                    model=request.model_name or env_settings.LLM_BASIC_MODEL,
                    temperature=request.temperature if request.temperature is not None else env_settings.BASIC_MODEL_TEMPERATURE,
                    interrupt=False,
                    position_x=0.0,
                    position_y=0.0,
                )
                session.add(support_root_member)
                await session.flush()

                # Load skill for SEARCHBOT unit
                if unit == WorkflowType.SEARCHBOT:
                    await _acreate_search_skills(session, support_root_member.id, user_id)


def _format_update_response(assistant: Assistant, request: UpdateAdvancedAssistantRequest) -> UpdateAdvancedAssistantResponse:
    """
    Format the response data for updated assistant.

    Args:
        assistant: Updated assistant entity
        request: Original update request    Returns:
        Formatted response object
    """
    # Format teams data using existing helper
    teams_data = _format_team_data(assistant.teams)

    return UpdateAdvancedAssistantResponse(
        id=assistant.id,
        user_id=assistant.user_id,
        name=assistant.name,
        assistant_type=AssistantType(assistant.assistant_type),  # Convert string to enum
        description=assistant.description,
        system_prompt=assistant.system_prompt,
        provider=request.provider,
        model_name=request.model_name,
        temperature=request.temperature,
        ask_human=assistant.ask_human,
        interrupt=assistant.interrupt,
        main_unit=WorkflowType.CHATBOT,
        support_units=request.support_units or _extract_support_units(assistant),
        mcp_ids=request.mcp_ids,
        extension_ids=request.extension_ids,
        teams=teams_data,
        created_at=assistant.created_at,  # type: ignore
    )


async def _aextract_service_ids_from_team(session: AsyncSession, team: Team) -> Tuple[List[str], List[str]]:
    """
    Extract MCP IDs and extension IDs from the members of a hierarchical team.

    This function examines all worker members in the team and extracts the unique
    MCP and extension IDs from their associated skills.

    Args:
        session: Database session
        team: Team object containing members

    Returns:
        Tuple of (mcp_ids, extension_ids) lists
    """
    mcp_ids = []
    extension_ids = []

    # Get all worker members (MCPs and extensions are created as worker members)
    worker_members = [member for member in team.members if member.type == "worker"]

    if not worker_members:
        return mcp_ids, extension_ids

    # Get all member IDs to query their skills
    member_ids = [member.id for member in worker_members]

    # Query skills associated with these members that have MCP or extension references
    skills_statement = (
        select(Skill)
        .select_from(Skill)
        .join(MemberSkillLink, Skill.id == MemberSkillLink.skill_id)
        .where(
            MemberSkillLink.member_id.in_(member_ids),
            Skill.reference_type.in_([ConnectedServiceType.MCP, ConnectedServiceType.EXTENSION]),
            Skill.is_deleted.is_(False),
        )
    )

    skills_result = await session.execute(skills_statement)
    skills = skills_result.scalars().all()

    # Extract unique MCP and extension IDs
    for skill in skills:
        if skill.reference_type == ConnectedServiceType.MCP and skill.mcp_id is not None:
            if skill.mcp_id not in mcp_ids:
                mcp_ids.append(skill.mcp_id)
        elif skill.reference_type == ConnectedServiceType.EXTENSION and skill.extension_id is not None:
            if skill.extension_id not in extension_ids:
                extension_ids.append(skill.extension_id)

    return mcp_ids, extension_ids


async def _asoft_delete_assistant_cascade(session: AsyncSession, assistant_id: str) -> None:
    """
    Soft delete an assistant and all related entities by setting is_deleted=True.

    Args:
        session: Database session
        assistant_id: ID of the assistant to soft delete
    """
    # Update threads that reference this assistant to mark as deleted
    await session.execute(
        update(Thread).where(Thread.assistant_id == assistant_id, Thread.is_deleted.is_(False)).values(is_deleted=True, deleted_at=datetime.now())
    )

    # Get all team IDs associated with the assistant
    teams_statement = select(Team.id).select_from(Team).where(Team.assistant_id == assistant_id, Team.is_deleted.is_(False))
    teams_result = await session.execute(teams_statement)
    team_ids = teams_result.scalars().all()

    if team_ids:
        # Get all member IDs from these teams
        members_statement = select(Member.id).where(Member.team_id.in_(team_ids), Member.is_deleted.is_(False))
        members_result = await session.execute(members_statement)
        member_ids = members_result.scalars().all()

        if member_ids:
            # Get all skill IDs associated with these members before soft deleting
            skills_statement = (
                select(Skill.id)
                .select_from(Skill)
                .join(MemberSkillLink, Skill.id == MemberSkillLink.skill_id)
                .where(MemberSkillLink.member_id.in_(member_ids), Skill.is_deleted.is_(False))
            )
            skills_result = await session.execute(skills_statement)
            skill_ids = skills_result.scalars().all()

            # Soft delete member skill links
            await session.execute(
                update(MemberSkillLink)
                .where(MemberSkillLink.member_id.in_(member_ids), MemberSkillLink.is_deleted.is_(False))
                .values(is_deleted=True, deleted_at=datetime.now())
            )

            # Soft delete member upload links
            await session.execute(
                update(MemberUploadLink)
                .where(MemberUploadLink.member_id.in_(member_ids), MemberUploadLink.is_deleted.is_(False))
                .values(is_deleted=True, deleted_at=datetime.now())
            )

            # Soft delete skills associated with these members
            if skill_ids:
                await session.execute(
                    update(Skill).where(Skill.id.in_(skill_ids), Skill.is_deleted.is_(False)).values(is_deleted=True, deleted_at=datetime.now())
                )

            # Soft delete members
            await session.execute(
                update(Member).where(Member.id.in_(member_ids), Member.is_deleted.is_(False)).values(is_deleted=True, deleted_at=datetime.now())
            )

        # Soft delete teams
        await session.execute(
            update(Team).where(Team.id.in_(team_ids), Team.is_deleted.is_(False)).values(is_deleted=True, deleted_at=datetime.now())
        )

    # Finally, soft delete the assistant
    await session.execute(
        update(Assistant).where(Assistant.id == assistant_id, Assistant.is_deleted.is_(False)).values(is_deleted=True, deleted_at=datetime.now())
    )


def _update_assistant_config_info(assistant: Assistant, request: UpdateAssistantConfigRequest) -> None:
    """
    Update configuration-specific assistant information.

    Args:
        assistant: Assistant entity to update
        request: Update request data containing configuration fields
    """
    if request.system_prompt is not None:
        setattr(assistant, "system_prompt", request.system_prompt)
    if request.provider is not None:
        setattr(assistant, "provider", request.provider)
    if request.model_name is not None:
        setattr(assistant, "model_name", request.model_name)
    if request.temperature is not None:
        setattr(assistant, "temperature", request.temperature)
    if request.ask_human is not None:
        setattr(assistant, "ask_human", request.ask_human)
    if request.interrupt is not None:
        setattr(assistant, "interrupt", request.interrupt)


async def _aupdate_member_configurations(
    session: AsyncSession,
    main_team: Team,
    assistant: Assistant,
    request: UpdateAssistantConfigRequest,
) -> None:
    """
    Update configuration of existing members without deleting them.

    This function updates the configuration of existing MCP and extension members
    to reflect the new assistant configuration settings.

    Args:
        session: Database session
        main_team: Main team containing members to update
        assistant: Assistant being updated (contains updated config)
        request: Update request containing configuration changes
    """
    # Get the updated configuration values
    updated_provider = request.provider or assistant.provider
    updated_model_name = request.model_name or assistant.model_name
    updated_temperature = request.temperature if request.temperature is not None else assistant.temperature
    updated_interrupt = request.interrupt if request.interrupt is not None else assistant.interrupt

    # Update configuration for all worker members
    for member in main_team.members:
        # Update member configuration fields
        if updated_provider:
            member.provider = updated_provider
        if updated_model_name:
            member.model = updated_model_name
        if updated_temperature is not None:
            member.temperature = updated_temperature
        if updated_interrupt is not None:
            member.interrupt = updated_interrupt

        # Mark member as modified
        member.updated_at = datetime.now()

    # Commit the changes to the session
    await session.flush()


# ================================
# API ENDPOINTS
# ================================


@router.get("/get-all", summary="Get assistants of a user.", response_model=ResponseWrapper[GetAssistantsResponse])
async def aget_assistants(
    session: SessionDep,
    assistant_type: AssistantType | None = None,
    paging: PagingRequest = Depends(),
    x_user_id: str = Header(None),
    x_user_role: str = Header(None),
):
    """
    List all assistants for a user with pagination.
    Returns either GetGeneralAssistantResponse or GetAdvancedAssistantResponse based on assistant type.
    """
    try:
        page_number = paging.page_number if paging.page_number else 1
        max_per_page = paging.max_per_page if paging.max_per_page else 10  # Use helper function to build and execute query
        result, count, total_pages = await _abuild_assistant_query(
            session=session,
            user_id=x_user_id,
            user_role=x_user_role,
            assistant_type=assistant_type,
            page_number=page_number,
            max_per_page=max_per_page,
        )

        if count == 0:
            return ResponseWrapper.wrap(
                status=200,
                data=GetAssistantsResponse(assistants=[], page_number=page_number, max_per_page=max_per_page, total_page=0),
            ).to_response()

        assistants = result.scalars().all()

        # Format responses using helper function
        # Each assistant will return either GetGeneralAssistantResponse or GetAdvancedAssistantResponse
        wrapped_assistants = []
        for assistant in assistants:
            assistant_teams = _format_team_data(assistant.teams)  # For advanced assistants, extract MCP and extension IDs from hierarchical team
            mcp_ids = None
            extension_ids = None
            if assistant.assistant_type == AssistantType.ADVANCED_ASSISTANT:
                # Find the hierarchical team (support unit containing MCPs and extensions)
                hierarchical_team = next((team for team in assistant.teams if team.workflow_type == WorkflowType.HIERARCHICAL), None)
                if hierarchical_team:
                    mcp_ids, extension_ids = await _aextract_service_ids_from_team(session, hierarchical_team)

            # Format response based on assistant type (General or Advanced)
            formatted_response = _format_assistant_response(assistant, assistant_teams, mcp_ids=mcp_ids, extension_ids=extension_ids)
            wrapped_assistants.append(formatted_response)

        return ResponseWrapper.wrap(
            status=200,
            data=GetAssistantsResponse(assistants=wrapped_assistants, page_number=page_number, max_per_page=max_per_page, total_page=total_pages),
        ).to_response()

    except Exception as e:
        logger.exception(f"Error fetching assistants: {e}")
        return ResponseWrapper.wrap(status=500, message="Internal Server Error").to_response()


@router.get(
    "/get-or-create-general-assistant",
    summary="Get or create general assistant for a user",
    response_model=ResponseWrapper[GetGeneralAssistantResponse],
)
async def aget_or_create_general_assistant(
    session: SessionDep,
    x_user_id: str = Header(None),
):
    """
    Get or create a general assistant for the user.

    This endpoint checks if a general assistant already exists for the user.
    If it does, it returns the existing assistant. If not, it creates a new one.

    Returns:
        Response with either existing or newly created general assistant data.
    """
    try:
        result = await GeneralAssistantHelpers.check_user_has_general_assistant(session=session, user_id=x_user_id)
        if result:
            # User has general assistant - get existing one
            assistant = await GeneralAssistantHelpers.get_user_general_assistant(session=session, user_id=x_user_id)

            if not assistant:
                return ResponseWrapper.wrap(status=404, message="General assistant not found").to_response()

            # Format teams data using helper function
            teams_data = _format_team_data(assistant.teams)

            # Format response as general assistant
            response = _format_assistant_response(assistant=assistant, teams_data=teams_data)

            return ResponseWrapper.wrap(status=200, data=response).to_response()
        else:
            # User doesn't have general assistant - create new one
            assistant = await GeneralAssistantHelpers.create_general_assistant(
                session=session,
                user_id=x_user_id,
                name="General Assistant",
                description="A helpful general assistant for everyday tasks and conversations.",
                system_prompt="You are a helpful, friendly, and knowledgeable general assistant. Help users with their questions, tasks, and conversations. Use your available tools when needed to provide accurate and helpful information.",
            )

            # Commit the creation
            await session.commit()

            # Get the created assistant with teams loaded
            created_assistant = await GeneralAssistantHelpers.get_user_general_assistant(session=session, user_id=x_user_id)

            if not created_assistant:
                return ResponseWrapper.wrap(status=500, message="Failed to create general assistant").to_response()

            # Format teams data using helper function
            teams_data = _format_team_data(created_assistant.teams)

            # Format response as general assistant
            response = _format_assistant_response(assistant=created_assistant, teams_data=teams_data)

            return ResponseWrapper.wrap(status=201, data=response).to_response()

    except Exception as e:
        logger.error(f"Error in get or create general assistant: {e}")
        await session.rollback()
        return ResponseWrapper.wrap(status=500, message="Internal Server Error").to_response()


@router.post("/create", summary="Create an advanced assistant.", response_model=ResponseWrapper[CreateAdvancedAssistantResponse])
async def acreate_advanced_assistant(
    session: SessionDep,
    request: CreateAdvancedAssistantRequest,
    x_user_id: str = Header(None),
):
    """
    Create an advanced assistant with hierarchical workflow using helper functions.

    This function creates:
    1. A new assistant instance
    2. A main chatbot team with root member
    3. A hierarchical team with root member (An advanced assistant always has a hierarchical team - support unit)
    4. MCP members and their skills (if specified)
    5. Extension members and their skills (if specified)
    6. Support teams for different workflow types (if specified)

    Args:
        session: Database session
        request: Request data for creating the assistant
        x_user_id: User ID from header

    Returns:
        Response with created assistant data
    """
    try:
        # Create the main assistant instance
        new_assistant = Assistant(
            id=str(uuid.uuid4()),
            user_id=x_user_id,
            name=request.name,
            description=request.description,
            system_prompt=request.system_prompt,
            assistant_type=AssistantType.ADVANCED_ASSISTANT,
            provider=request.provider or env_settings.OPENAI_API_BASE_URL,
            model_name=request.model_name or env_settings.LLM_BASIC_MODEL,
            temperature=request.temperature if request.temperature is not None else env_settings.BASIC_MODEL_TEMPERATURE,
        )
        session.add(new_assistant)
        await session.flush()  # Ensure assistant exists before creating teams

        # Create the main chatbot team using helper function
        await _acreate_main_team(session, new_assistant, request, x_user_id)

        # Create hierarchical team as support unit if MCP or extension IDs provided
        hierarchical_team = None
        hierarchical_root_member = None
        if request.mcp_ids or request.extension_ids:
            hierarchical_team, hierarchical_root_member = await _acreate_hierarchical_team(session, new_assistant, request, x_user_id)
            if not hierarchical_team or not hierarchical_root_member:
                raise ValueError("Failed to create hierarchical team or root member")

        # Create MCP members and their skills using helper function
        if request.mcp_ids and hierarchical_team and hierarchical_root_member:
            for mcp_id in request.mcp_ids:
                # Load connected MCP
                mcp_statement = select(ConnectedMcp).where(
                    ConnectedMcp.id == mcp_id, ConnectedMcp.user_id == x_user_id, ConnectedMcp.is_deleted.is_(False)
                )
                mcp_result = await session.execute(mcp_statement)
                connected_mcp = mcp_result.scalar_one_or_none()

                if connected_mcp:
                    await _acreate_mcp_member_with_skills(
                        session,
                        connected_mcp,
                        hierarchical_team.id,
                        hierarchical_root_member.id,
                        request,
                    )

        # Create extension members and their skills using helper function
        if request.extension_ids and hierarchical_team and hierarchical_root_member:
            for extension_id in request.extension_ids:
                # Load connected extension
                ext_statement = select(ConnectedExtension).where(
                    ConnectedExtension.id == extension_id,
                    ConnectedExtension.user_id == x_user_id,
                    ConnectedExtension.is_deleted.is_(False),
                )
                ext_result = await session.execute(ext_statement)
                connected_extension = ext_result.scalar_one_or_none()

                if connected_extension:
                    await _acreate_extension_member_with_skills(
                        session,
                        connected_extension,
                        hierarchical_team.id,
                        hierarchical_root_member.id,
                        request,
                    )

        # Create another support teams for each workflow type using helper function
        if request.support_units:
            for workflow_type in request.support_units:
                await _acreate_support_team(session, new_assistant, workflow_type, request, x_user_id)

        # Commit all changes
        await session.commit()

        # Fetch the complete assistant with teams for response
        assistant_statement = (
            select(Assistant).options(selectinload(Assistant.teams).selectinload(Team.members)).where(Assistant.id == new_assistant.id)
        )
        assistant_result = await session.execute(assistant_statement)
        created_assistant = assistant_result.scalar_one()  # Format teams data for response using helper function
        teams_data = _format_team_data(created_assistant.teams)

        # Create response using helper function
        response = CreateAdvancedAssistantResponse(
            id=created_assistant.id,
            user_id=x_user_id,
            name=request.name,
            assistant_type=AssistantType.ADVANCED_ASSISTANT,
            description=request.description,
            system_prompt=request.system_prompt,
            provider=request.provider,
            model_name=request.model_name,
            temperature=request.temperature,
            ask_human=request.ask_human,
            interrupt=request.interrupt,
            main_unit=WorkflowType.CHATBOT,
            support_units=request.support_units,
            mcp_ids=request.mcp_ids,
            extension_ids=request.extension_ids,
            teams=teams_data,
            created_at=created_assistant.created_at,
        )

        return ResponseWrapper.wrap(status=201, data=response).to_response()

    except Exception as e:
        logger.error(f"Error creating advanced assistant: {e}")
        await session.rollback()
        return ResponseWrapper.wrap(status=500, message="Internal Server Error").to_response()


@router.get(
    "/{assistant_id}/get-detail",
    summary="Get assistant details.",
    response_model=ResponseWrapper[GetGeneralAssistantResponse | GetAdvancedAssistantResponse],
)
async def aget_assistant_by_id(session: SessionDep, assistant_id: str, x_user_id: str = Header(None), x_user_role: str = Header(None)):
    """
    Get details of an assistant by its ID using helper functions.

    Args:
        session: Database session
        assistant_id: ID of the assistant to retrieve
        x_user_id: User ID from header
        x_user_role: User role from header

    Returns:
        Response with assistant details
    """
    try:
        # Use helper function to build and execute query for single assistant
        result, count, _ = await _abuild_assistant_query(
            session=session, user_id=x_user_id, user_role=x_user_role, assistant_id=assistant_id, page_number=1, max_per_page=1
        )

        if count == 0:
            return ResponseWrapper.wrap(status=404, message="Assistant not found").to_response()

        assistant = result.scalar_one()

        # Format teams data using helper function
        teams_data = _format_team_data(assistant.teams)  # Extract MCP and extension IDs if this is an advanced assistant
        mcp_ids = None
        extension_ids = None

        if assistant.assistant_type == AssistantType.ADVANCED_ASSISTANT:
            # Find the hierarchical team
            hierarchical_team = None
            for team in assistant.teams:
                if team.workflow_type == WorkflowType.HIERARCHICAL:
                    hierarchical_team = team
                    break

            if hierarchical_team:
                mcp_ids, extension_ids = await _aextract_service_ids_from_team(session, hierarchical_team)

        # Format response using helper function
        response = _format_assistant_response(
            assistant=assistant,
            teams_data=teams_data,
            mcp_ids=mcp_ids,
            extension_ids=extension_ids,
        )

        return ResponseWrapper.wrap(status=200, data=response).to_response()

    except Exception as e:
        logger.error(f"Error fetching assistant details: {e}")
        return ResponseWrapper.wrap(status=500, message="Internal Server Error").to_response()


@router.patch(
    "{assistant_id}/update-advanced-assistant",
    summary="Update advanced assistant information.",
    response_model=ResponseWrapper[UpdateAdvancedAssistantResponse],
)
async def aupdate_advanced_assistant(
    session: SessionDep,
    assistant_id: str,
    request: UpdateAdvancedAssistantRequest,
    x_user_id: str = Header(None),
):
    """
    Update an assistant's information.
    """
    try:
        # Fetch the assistant by ID with teams eagerly loaded
        statement = (
            select(Assistant)
            .select_from(Assistant)
            .options(selectinload(Assistant.teams).selectinload(Team.members))
            .where(
                Assistant.id == assistant_id,
                Assistant.user_id == x_user_id,
                Assistant.assistant_type == AssistantType.ADVANCED_ASSISTANT,
                Assistant.is_deleted.is_(False),
            )
        )
        result = await session.execute(statement)
        assistant = result.scalar_one_or_none()

        if not assistant:
            return ResponseWrapper.wrap(status=404, message="Assistant not found").to_response()  # Update the assistant table
        _update_assistant_basic_info(assistant, request)

        # Handle hierarchical team for MCPs and extensions
        hierarchical_team = None
        for team in assistant.teams:
            if team.workflow_type == WorkflowType.HIERARCHICAL:
                hierarchical_team = team
                break

        # Create or update hierarchical team based on MCP/extension IDs
        if request.mcp_ids or request.extension_ids:
            # If hierarchical team doesn't exist, create it
            if not hierarchical_team:
                hierarchical_team_id = str(uuid.uuid4())
                hierarchical_team_name = create_unique_key(id_=hierarchical_team_id, name="Hierarchical Unit")
                hierarchical_team = Team(
                    id=hierarchical_team_id,
                    name=hierarchical_team_name,
                    description="Execute user tasks based on integrated workers' tools.",
                    workflow_type=WorkflowType.HIERARCHICAL,
                    user_id=x_user_id,
                    assistant_id=assistant.id,
                )
                session.add(hierarchical_team)
                await session.flush()

                # Create root member for the hierarchical team
                root_member_id = str(uuid.uuid4())
                root_member_name = create_unique_key(id_=root_member_id, name="Leader")
                root_member = Member(
                    id=root_member_id,
                    name=root_member_name,
                    team_id=hierarchical_team.id,
                    backstory="Leader of the hierarchical team for advanced assistant.",
                    role="Gather inputs from your team and answer the question.",
                    type="root",
                    provider=request.provider or assistant.provider or env_settings.ANTHROPIC_PROVIDER,
                    model=request.model_name or assistant.model_name or env_settings.LLM_REASONING_MODEL,
                    temperature=env_settings.REASONING_MODEL_TEMPERATURE,
                    interrupt=False,
                    position_x=0.0,
                    position_y=0.0,
                )
                session.add(root_member)
                await session.flush()

            # Update mcp members of the hierarchical team
            await _aupdate_mcp_members(session, hierarchical_team, request, x_user_id)

            # Update extension members of the hierarchical team
            await _aupdate_extension_members(session, hierarchical_team, request, x_user_id)
        else:
            # If no MCPs or extensions, remove hierarchical team if it exists
            if hierarchical_team:
                # Delete hierarchical team and all its members
                member_statement = select(Member.id).where(Member.team_id == hierarchical_team.id)
                member_result = await session.execute(member_statement)
                member_ids = member_result.scalars().all()

                if member_ids:
                    # Delete skills and links
                    skills_statement = (
                        select(Skill.id)
                        .select_from(Skill)
                        .join(MemberSkillLink, Skill.id == MemberSkillLink.skill_id)
                        .where(MemberSkillLink.member_id.in_(member_ids))
                    )
                    skills_result = await session.execute(skills_statement)
                    skill_ids = skills_result.scalars().all()

                    await session.execute(delete(MemberSkillLink).where(MemberSkillLink.member_id.in_(member_ids)))
                    await session.execute(delete(MemberUploadLink).where(MemberUploadLink.member_id.in_(member_ids)))

                    if skill_ids:
                        await session.execute(delete(Skill).where(Skill.id.in_(skill_ids)))

                    await session.execute(delete(Member).where(Member.id.in_(member_ids)))

                await session.execute(delete(Team).where(Team.id == hierarchical_team.id))

        # Update support units
        await _aupdate_support_units(session, assistant, request, x_user_id)

        # Commit the transaction
        await session.commit()

        # Format and return the response
        response = _format_update_response(assistant, request)

        return ResponseWrapper.wrap(status=200, data=response).to_response()
    except Exception as e:
        logger.error(f"Error updating assistant: {e}", exc_info=True)
        await session.rollback()
        return ResponseWrapper.wrap(status=500, message="Internal Server Error").to_response()


@router.delete(
    "/{user_id}/{assistant_id}/hard-delete-advanced-assistant",
    summary="Delete an advanced asssistant, cannot recover",
    response_model=ResponseWrapper[MessageResponse],
)
async def ahard_delete_advanced_assistant(
    session: SessionDep,
    assistant_id: str,
    x_user_id: str = Header(None),
):
    """
    Delete an advanced assistant and all related entities using helper functions.

    This function:
    1. Validates the assistant exists and belongs to the user
    2. Uses the delete_assistant_cascade helper to delete all related entities
    3. Commits the transaction

    Args:
        session: Database session
        assistant_id: ID of the assistant to delete
        x_user_id: User ID from request

    Returns:
        Response indicating success or failure
    """
    try:
        # Verify the assistant exists and belongs to the user
        statement = select(Assistant).where(
            Assistant.id == assistant_id,
            Assistant.user_id == x_user_id,
            Assistant.assistant_type == AssistantType.ADVANCED_ASSISTANT,
            Assistant.is_deleted.is_(False),
        )
        result = await session.execute(statement)
        assistant = result.scalar_one_or_none()

        if not assistant:
            return ResponseWrapper.wrap(status=404, message="Assistant not found").to_response()

        # Use helper function to delete assistant and all related entities
        await _ahard_delete_assistant_cascade(session, assistant_id)  # Commit the transaction
        await session.commit()

        message = MessageResponse(message="Assistant deleted successfully")
        return ResponseWrapper.wrap(status=200, data=message).to_response()

    except Exception as e:
        logger.error(f"Error deleting assistant: {e}")
        await session.rollback()
        return ResponseWrapper.wrap(status=500, message="Internal Server Error").to_response()


@router.delete("/{assistant_id}/soft-delete-advanced-assistant", summary="Soft delete an advanced assistant.")
async def asoft_delete_advanced_assistant(
    session: SessionDep,
    assistant_id: str,
    x_user_id: str = Header(None),
):
    """
    Soft delete an advanced assistant and all related entities by setting is_deleted=True.

    This function:
    1. Validates the assistant exists and belongs to the user
    2. Uses the soft delete assistant cascade helper to mark all related entities as deleted
    3. Commits the transaction

    Args:
        session: Database session
        assistant_id: ID of the assistant to soft delete
        x_user_id: User ID from request

    Returns:
        Response indicating success or failure
    """
    try:
        # Verify the assistant exists and belongs to the user
        statement = select(Assistant).where(
            Assistant.id == assistant_id,
            Assistant.user_id == x_user_id,
            Assistant.assistant_type == AssistantType.ADVANCED_ASSISTANT,
            Assistant.is_deleted.is_(False),
        )
        result = await session.execute(statement)
        assistant = result.scalar_one_or_none()

        if not assistant:
            return ResponseWrapper.wrap(status=404, message="Assistant not found").to_response()

        # Use helper function to soft delete assistant and all related entities
        await _asoft_delete_assistant_cascade(session, assistant_id)

        # Commit the transaction
        await session.commit()

        message = MessageResponse(message="Assistant soft deleted successfully")
        return ResponseWrapper.wrap(status=200, data=message).to_response()

    except Exception as e:
        logger.error(f"Error soft deleting assistant: {e}")
        await session.rollback()
        return ResponseWrapper.wrap(status=500, message="Internal Server Error").to_response()


@router.patch("/{assistant_id}/update-config", description="Update advanced assistant configuration.", response_model=ResponseWrapper)
async def aupdate_assistant_config(
    session: SessionDep,
    assistant_id: str,
    request: UpdateAssistantConfigRequest,
    x_user_id: str = Header(None),
):
    """Update the configuration of an assistant.

    This function updates only the configuration fields of an assistant and its members
    without affecting the connected services (MCP and extensions). Unlike advanced assistant
    updates, this only modifies configuration settings and updates existing member configs.

    Args:
        session: Database session
        assistant_id: ID of the assistant to update
        request: Request data containing configuration updates
        x_user_id: User ID from header

    Returns:
        Response indicating success or failure
    """
    try:
        # Fetch the assistant by ID with teams eagerly loaded
        statement = (
            select(Assistant)
            .select_from(Assistant)
            .options(selectinload(Assistant.teams).selectinload(Team.members))
            .where(
                Assistant.id == assistant_id,
                Assistant.user_id == x_user_id,
                Assistant.is_deleted.is_(False),
            )
        )
        result = await session.execute(statement)
        assistant = result.scalar_one_or_none()

        if not assistant:
            return ResponseWrapper.wrap(status=404, message="Assistant not found").to_response()

        # Update the assistant configuration fields
        _update_assistant_config_info(assistant, request)
        await session.flush()  # Ensure changes are applied before proceeding

        # Get main team for advanced assistants and update member configurations
        if assistant.assistant_type == AssistantType.ADVANCED_ASSISTANT:
            main_team = await _aget_main_team_for_assistant(session, assistant_id, x_user_id)

            if not main_team:
                return ResponseWrapper.wrap(status=404, message="Main team not found").to_response()

            # Update configuration of existing members without deleting them
            await _aupdate_member_configurations(session, main_team, assistant, request)

            # Update configuration for all support teams (including hierarchical teams)
            for team in assistant.teams:
                if team.workflow_type != WorkflowType.CHATBOT:  # Skip main chatbot team
                    await _aupdate_member_configurations(session, team, assistant, request)

        # Commit the transaction
        await session.commit()

        message = MessageResponse(message="Assistant configuration updated successfully")
        return ResponseWrapper.wrap(status=200, data=message).to_response()

    except Exception as e:
        logger.error(f"Error updating assistant configuration: {e}")
        await session.rollback()
        return ResponseWrapper.wrap(status=500, message="Internal Server Error").to_response()