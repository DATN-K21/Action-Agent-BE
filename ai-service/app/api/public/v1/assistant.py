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
from app.core.tools.tool_manager import create_unique_key, global_tools, tool_manager
from app.core.utils.convert_type import convert_base_tool_to_tool_info
from app.core.utils.general_assistant_helpers import GeneralAssistantHelpers
from app.db_models.assistant import Assistant
from app.db_models.connected_extension import ConnectedExtension
from app.db_models.connected_mcp import ConnectedMcp
from app.db_models.member import Member
from app.db_models.member_skill_link import MemberSkillLink
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
    if assistant.assistant_type == AssistantType.ADVANCED_ASSISTANT:
        main_unit = WorkflowType.HIERARCHICAL
    elif assistant.assistant_type == AssistantType.GENERAL_ASSISTANT:
        main_unit = WorkflowType.CHATBOT
    else:
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
    """
    # Import here to avoid circular imports
    from app.core.settings import env_settings

    if assistant.assistant_type == AssistantType.GENERAL_ASSISTANT:
        return GetGeneralAssistantResponse(
            id=assistant.id,
            user_id=assistant.user_id,
            name=assistant.name,
            assistant_type=assistant.assistant_type,
            description=assistant.description,
            system_prompt=assistant.system_prompt,
            provider=assistant.provider or env_settings.LLM_DEFAULT_PROVIDER,
            model_name=assistant.model_name,
            temperature=assistant.temperature,
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
            provider=assistant.provider,
            model_name=assistant.model_name,
            temperature=assistant.temperature,
            main_unit=WorkflowType.HIERARCHICAL,
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
            provider=assistant.provider or env_settings.LLM_DEFAULT_PROVIDER,
            model_name=assistant.model_name,
            temperature=assistant.temperature,
            main_unit=WorkflowType.CHATBOT,
            support_units=_extract_support_units(assistant),
            teams=teams_data,
            created_at=assistant.created_at,
        )


async def _acreate_main_team(
    session: AsyncSession, assistant: Assistant, request: CreateAdvancedAssistantRequest, user_id: str
) -> Tuple[Team, Member]:
    """
    Create the main hierarchical team for an advanced assistant.

    Args:
        session: Database session
        assistant: The assistant object
        request: Request data
        user_id: User ID

    Returns:
        Created team object
    """
    # Create main team
    main_team_id = str(uuid.uuid4())
    main_team_name = create_unique_key(id_=main_team_id, name="Hierarchical Unit")
    main_team = Team(
        id=main_team_id,
        name=main_team_name,
        description="Main unit for advanced assistant, which integrates with mcps and extensions.",
        workflow_type=WorkflowType.HIERARCHICAL,
        user_id=user_id,
        assistant_id=assistant.id,
    )
    session.add(main_team)
    await session.flush()

    # Create root member for the main team
    root_member_id = str(uuid.uuid4())
    root_member_name = create_unique_key(id_=root_member_id, name="Leader")
    root_member = Member(
        id=root_member_id,
        name=root_member_name,
        team_id=main_team.id,
        backstory="Leader of the main team for advanced assistant.",
        role="Gather inputs from your team and answer the question.",
        type="root",
        provider=request.provider,
        model=request.model_name,
        temperature=request.temperature,
        interrupt=False,
        position_x=0.0,
        position_y=0.0,
    )
    session.add(root_member)
    await session.flush()

    return main_team, root_member


async def _acreate_chatbot_member(
    session: AsyncSession,
    team_id: str,
    root_member_id: str,
    request: CreateAdvancedAssistantRequest,
    user_id: str,
) -> Member:
    """
    Create a chatbot member for the main team.

    Args:
        session: Database session
        team_id: Team ID to add member to
        root_member_id: Root member ID for source reference
        request: Request data containing provider/model info

    Returns:
        Created Member object
    """
    chatbot_member_id = str(uuid.uuid4())
    chatbot_member_name = create_unique_key(id_=chatbot_member_id, name="Chatbot Assistant")
    chatbot_member = Member(
        id=chatbot_member_id,
        name=chatbot_member_name,
        team_id=team_id,
        backstory="A friendly chatbot assistant designed to handle general conversations, provide greetings, engage in small talk, and help users with their questions using available tools.",
        role="Handle greetings, small talk, and general questions. Use search and knowledge base tools when needed. Politely decline inappropriate requests and ask for clarification when context is insufficient.",
        type="worker",
        source=root_member_id,
        provider=request.provider,
        model=request.model_name,
        temperature=request.temperature,
        interrupt=False,
        position_x=0.0,
        position_y=0.0,
        created_by=SYSTEM,
    )
    session.add(chatbot_member)
    await session.flush()

    await _acreate_search_skills(session, chatbot_member.id, user_id)

    return chatbot_member


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
    """  # Create member
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
        provider=request.provider,
        model=request.model_name,
        temperature=request.temperature,
        interrupt=True,
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
        tool_manager.add_personal_tool(
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
        provider=request.provider,
        model=request.model_name,
        temperature=request.temperature,
        interrupt=True,
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
        tool_manager.add_personal_tool(
            user_id=connected_extension.user_id,
            tool_key=skill_name,
            tool_info=tool_info,
        )


async def _acreate_support_team(
    session: AsyncSession, assistant: Assistant, workflow_type: WorkflowType, request: CreateAdvancedAssistantRequest, user_id: str
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
    support_team_name = create_unique_key(id_=support_team_id, name=f"{workflow_type} Support Unit")
    support_team = Team(
        id=support_team_id,
        name=support_team_name,
        description=f"Support unit for {workflow_type} in advanced assistant.",
        workflow_type=workflow_type,
        user_id=user_id,
        assistant_id=assistant.id,
    )
    session.add(support_team)
    await session.flush()

    # Create root member for the support team
    support_root_member_id = str(uuid.uuid4())
    support_root_member_name = create_unique_key(id_=support_root_member_id, name=f"{workflow_type} Support Root")
    support_root_member = Member(
        id=support_root_member_id,
        name=support_root_member_name,
        team_id=support_team.id,
        backstory=f"Unit for advanced assistant: {workflow_type}.",
        role="Answer the user's question.",
        type=f"{workflow_type}",
        provider=request.provider,
        model=request.model_name,
        temperature=request.temperature,
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
        skill_ids = skills_result.scalars().all()

        # Delete member skill links
        await session.execute(delete(MemberSkillLink).where(MemberSkillLink.member_id.in_(member_ids_to_delete)))

        # Delete skills associated with these members
        if skill_ids:
            await session.execute(delete(Skill).where(Skill.id.in_(skill_ids)))

        # Delete members
        await session.execute(delete(Member).where(Member.id.in_(member_ids_to_delete)))


async def _adelete_assistant_cascade(session: AsyncSession, assistant_id: str) -> None:
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
            skill_ids = skills_result.scalars().all()

            # Delete member skill links
            await session.execute(delete(MemberSkillLink).where(MemberSkillLink.member_id.in_(member_ids)))

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
    Get the main hierarchical team for an assistant.

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
            Team.workflow_type == WorkflowType.HIERARCHICAL,
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


async def _aupdate_mcp_members(
    session: AsyncSession,
    main_team: Team,
    request: UpdateAdvancedAssistantRequest,
    user_id: str,
) -> None:
    """
    Update MCP members for the main team by deleting existing ones and creating new ones.

    Args:
        session: Database session
        main_team: Main team to update members for
        request: Update request containing new MCP IDs
        user_id: User ID
    """
    # Only delete existing MCP members if new ones are provided
    if request.mcp_ids is not None:
        await _adelete_members_with_service_type(session, main_team, ConnectedServiceType.MCP)

        # If empty list provided, just return after deletion (remove all)
        if len(request.mcp_ids) == 0:
            return

        # Get root member ID for linking new MCP members
        root_member_id = None
        for member in main_team.members:
            if member.type == "root":
                root_member_id = member.id
                break

        if not root_member_id:
            raise ValueError("Root member not found in main team")

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
                    team_id=main_team.id,
                    backstory=connected_mcp.description if connected_mcp.description is not None else None,
                    role="Execute actions based on provided tasks using binding tools and return the results",
                    type="worker",
                    source=root_member_id,
                    provider=request.provider,
                    model=request.model_name,
                    temperature=request.temperature,
                    interrupt=True,
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
                    tool_manager.add_personal_tool(
                        user_id=user_id,
                        tool_key=skill_name,
                        tool_info=tool_info,
                    )


async def _aupdate_extension_members(
    session: AsyncSession,
    main_team: Team,
    request: UpdateAdvancedAssistantRequest,
    user_id: str,
) -> None:
    """
    Update extension members for the main team by deleting existing ones and creating new ones.

    Args:
        session: Database session
        main_team: Main team to update members for
        request: Update request containing new extension IDs
        user_id: User ID
    """
    # Only delete existing extension members if new ones are provided
    if request.extension_ids is not None:
        await _adelete_members_with_service_type(session, main_team, ConnectedServiceType.EXTENSION)

        # If empty list provided, just return after deletion (remove all)
        if len(request.extension_ids) == 0:
            return

        # Get root member ID for linking new extension members
        root_member_id = None
        for member in main_team.members:
            if member.type == "root":
                root_member_id = member.id
                break

        if not root_member_id:
            raise ValueError("Root member not found in main team")

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
                    team_id=main_team.id,
                    backstory="",
                    role="Execute actions based on provided tasks using binding tools and return the results",
                    type="worker",
                    source=root_member_id,
                    provider=request.provider,
                    model=request.model_name,
                    temperature=request.temperature,
                    interrupt=True,
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
                    tool_manager.add_personal_tool(
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
    """
    # Only update support units if they are provided in the request
    if request.support_units is not None:
        # Delete all support teams (non-hierarchical teams)
        all_teams_statement = select(Team).select_from(Team).where(Team.assistant_id == assistant.id)
        all_teams_result = await session.execute(all_teams_statement)
        all_teams = all_teams_result.scalars().all()

        # Find teams to delete (all except the hierarchical/main team)
        teams_to_delete = [team.id for team in all_teams if team.workflow_type != WorkflowType.HIERARCHICAL]

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
                skill_ids = skills_result.scalars().all()

                # Delete member skill links
                await session.execute(delete(MemberSkillLink).where(MemberSkillLink.member_id.in_(member_ids)))

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
                    provider=request.provider,
                    model=request.model_name,
                    temperature=request.temperature,
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
        request: Original update request

    Returns:
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
        main_unit=WorkflowType.HIERARCHICAL,
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
            assistant_teams = _format_team_data(assistant.teams)

            # For advanced assistants, extract MCP and extension IDs from hierarchical team
            mcp_ids = None
            extension_ids = None
            if assistant.assistant_type == AssistantType.ADVANCED_ASSISTANT:
                # Find the hierarchical team (main team for advanced assistants)
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
    2. A main hierarchical team with root member
    3. MCP members and their skills (if specified)
    4. Extension members and their skills (if specified)
    5. Support teams for different workflow types (if specified)

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
            provider=request.provider,
            model_name=request.model_name,
            temperature=request.temperature,
        )
        session.add(new_assistant)
        await session.flush()  # Ensure assistant exists before creating teams

        # Create the main hierarchical team using helper function
        main_team, root_member = await _acreate_main_team(session, new_assistant, request, x_user_id)

        # Get the root member ID for linking MCP/extension members
        root_member_id = None

        if root_member.type == "root":
            root_member_id = root_member.id

        if not root_member_id:
            raise ValueError("Root member not found in main team")

        # Create chatbot member for the main team
        await _acreate_chatbot_member(session, main_team.id, root_member_id, request, x_user_id)

        # Create MCP members and their skills using helper function
        if request.mcp_ids:
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
                        main_team.id,
                        root_member_id,
                        request,
                    )

        # Create extension members and their skills using helper function
        if request.extension_ids:
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
                        main_team.id,
                        root_member_id,
                        request,
                    )

        # Create support teams for each workflow type using helper function
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
        created_assistant = assistant_result.scalar_one()

        # Format teams data for response using helper function
        teams_data = _format_team_data(created_assistant.teams)  # Create response using helper function
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
            main_unit=WorkflowType.HIERARCHICAL,
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


@router.patch("{assistant_id}/update", summary="Update assistant information.", response_model=ResponseWrapper[UpdateAdvancedAssistantResponse])
async def aupdate_assistant(
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
            .where(Assistant.id == assistant_id, Assistant.user_id == x_user_id, Assistant.is_deleted.is_(False))
        )
        result = await session.execute(statement)
        assistant = result.scalar_one_or_none()

        if not assistant:
            return ResponseWrapper.wrap(status=404, message="Assistant not found").to_response()

        # Update the assistant table
        _update_assistant_basic_info(assistant, request)

        # Get main team (main unit)
        main_team = await _aget_main_team_for_assistant(session, assistant_id, x_user_id)

        if not main_team:
            return ResponseWrapper.wrap(status=404, message="Main team not found").to_response()

        # Update mcp members of the main team (main unit)
        await _aupdate_mcp_members(session, main_team, request, x_user_id)

        # Update extension members of the main team (main unit)
        await _aupdate_extension_members(session, main_team, request, x_user_id)

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


@router.delete("/{user_id}/{assistant_id}/delete", summary="Delete a thread.", response_model=ResponseWrapper[MessageResponse])
async def delete_assistant(session: SessionDep, assistant_id: str, x_user_id: str):
    """
    Delete an assistant and all related entities using helper functions.

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
        statement = select(Assistant).where(Assistant.id == assistant_id, Assistant.user_id == x_user_id, Assistant.is_deleted.is_(False))
        result = await session.execute(statement)
        assistant = result.scalar_one_or_none()

        if not assistant:
            return ResponseWrapper.wrap(status=404, message="Assistant not found").to_response()

        # Use helper function to delete assistant and all related entities
        await _adelete_assistant_cascade(session, assistant_id)

        # Commit the transaction
        await session.commit()

        message = MessageResponse(message="Assistant deleted successfully")
        return ResponseWrapper.wrap(status=200, data=message).to_response()

    except Exception as e:
        logger.error(f"Error deleting assistant: {e}")
        await session.rollback()
        return ResponseWrapper.wrap(status=500, message="Internal Server Error").to_response()
