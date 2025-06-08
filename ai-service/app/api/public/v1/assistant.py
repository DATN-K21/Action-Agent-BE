import uuid

from fastapi import APIRouter, Depends, Header
from sqlalchemy import delete, func, select
from sqlalchemy.orm import selectinload

from app.api.deps import SessionDep
from app.core import logging
from app.core.enums import AssistantType, ConnectedServiceType, StorageStrategy, WorkflowType
from app.core.tools.tool_manager import create_unique_key, global_tools, tool_manager
from app.core.utils.convert_type import convert_base_tool_to_tool_info
from app.db_models.assistant import Assistant
from app.db_models.connected_extension import ConnectedExtension
from app.db_models.connected_mcp import ConnectedMcp
from app.db_models.member import Member
from app.db_models.member_skill_link import MemberSkillLink
from app.db_models.skill import Skill
from app.db_models.team import Team
from app.db_models.team_assistant_link import TeamAssistantLink
from app.schemas.assistant import (
    CreateAdvancedAssistantRequest,
    CreateAdvancedAssistantResponse,
    GetAdvancedAssistantResponse,
    GetAssistantResponse,
    GetAssistantsResponse,
    UpdateAdvancedAssistantRequest,
    UpdateAdvancedAssistantResponse,
)
from app.schemas.base import MessageResponse, PagingRequest, ResponseWrapper
from app.services.extensions import extension_service_manager
from app.services.mcps.mcp_service import McpService

logger = logging.get_logger(__name__)

router = APIRouter(prefix="/assistant", tags=["Assistant"])


def extract_support_units(assistant: Assistant) -> list[WorkflowType]:
    """
    Extract support units from the assistant object.
    This is a placeholder function, actual implementation may vary.
    """

    support_units = []
    main_unit = WorkflowType.HIERARCHICAL if str(assistant.assistant_type) == AssistantType.ADVANCED_ASSISTANT else WorkflowType.CHATBOT

    for team in assistant.teams:
        if team.workflow_type:
            if team.workflow_type != main_unit:
                support_units.append(team.workflow_type)

    return support_units


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
    """
    try:
        paging_number = paging.page_number if paging.page_number else 1
        max_per_page = paging.max_per_page if paging.max_per_page else 10

        if x_user_role in ["admin", "superuser"]:
            # Admins can see all assistants
            if assistant_type is None:
                count_statement = select(func.count(Assistant.id)).select_from(Assistant).where(Assistant.is_deleted.is_(False))
                statement = (
                    select(Assistant)
                    .options(selectinload(Assistant.teams))
                    .where(Assistant.is_deleted.is_(False))
                    .offset((paging_number - 1) * max_per_page)
                    .limit(max_per_page)
                    .order_by(Assistant.created_at.desc())
                )
            else:
                count_statement = (
                    select(func.count(Assistant.id))
                    .select_from(Assistant)
                    .where(Assistant.assistant_type == assistant_type, Assistant.is_deleted.is_(False))
                )
                statement = (
                    select(Assistant)
                    .options(selectinload(Assistant.teams))
                    .where(Assistant.assistant_type == assistant_type, Assistant.is_deleted.is_(False))
                    .offset((paging_number - 1) * max_per_page)
                    .limit(max_per_page)
                    .order_by(Assistant.created_at.desc())
                )
        else:
            # Regular users can only see their own assistants
            if assistant_type is None:
                count_statement = (
                    select(func.count(Assistant.id)).select_from(Assistant).where(Assistant.user_id == x_user_id, Assistant.is_deleted.is_(False))
                )
                statement = (
                    select(Assistant)
                    .options(selectinload(Assistant.teams))
                    .where(Assistant.user_id == x_user_id, Assistant.is_deleted.is_(False))
                    .offset((paging_number - 1) * max_per_page)
                    .limit(max_per_page)
                    .order_by(Assistant.created_at.desc())
                )
            else:
                count_statement = (
                    select(func.count(Assistant.id))
                    .select_from(Assistant)
                    .where(Assistant.user_id == x_user_id, Assistant.assistant_type == assistant_type, Assistant.is_deleted.is_(False))
                )
                statement = (
                    select(Assistant)
                    .options(selectinload(Assistant.teams))
                    .where(
                        Assistant.user_id == x_user_id,
                        Assistant.assistant_type == assistant_type,
                        Assistant.is_deleted.is_(False),
                    )
                    .offset((paging_number - 1) * max_per_page)
                    .limit(max_per_page)
                    .order_by(Assistant.created_at.desc())
                )

        count_result = await session.execute(count_statement)
        count = count_result.scalar_one()
        if count == 0:
            return ResponseWrapper.wrap(
                status=200,
                data=GetAssistantsResponse(assistants=[], page_number=paging_number, max_per_page=max_per_page, total_page=0),
            )

        total_pages = (count + max_per_page - 1) // max_per_page

        result = await session.execute(statement)
        assistants = result.scalars().all()

        wrapped_assistants = [
            GetAssistantResponse(
                id=str(assistant.id),
                user_id=str(assistant.user_id),
                name=str(assistant.name),
                assistant_type=assistant.assistant_type,  # type: ignore
                description=str(assistant.description),
                system_prompt=str(assistant.system_prompt),
                provider="",  # TODO: Not support for custom provider, let's update it later
                model_name="",  # TODO: Not support for custom model, let's update it later
                # TODO: Not support for custom temperature, let's update it later
                main_unit=WorkflowType.HIERARCHICAL if str(assistant.assistant_type) == AssistantType.ADVANCED_ASSISTANT else WorkflowType.CHATBOT,
                support_units=extract_support_units(assistant),
                teams=[
                    {
                        "id": team.id,
                        "name": team.name,
                        "description": team.description,
                        "workflow_type": team.workflow_type,
                        "members": [
                            {"id": member.id, "name": member.name, "type": member.type, "role": member.role}
                            for member in team.members
                            if hasattr(team, "members") and team.members
                        ],
                    }
                    for team in assistant.teams
                ],
                created_at=assistant.created_at,  # type: ignore
            )
            if str(assistant.assistant_type) == AssistantType.GENERAL_ASSISTANT
            else GetAdvancedAssistantResponse(
                id=str(assistant.id),
                user_id=str(assistant.user_id),
                name=str(assistant.name),
                assistant_type=assistant.assistant_type,  # type: ignore
                description=str(assistant.description),
                system_prompt=str(assistant.system_prompt),
                provider="",  # TODO: Not support for custom provider, let's update it later
                model_name="",  # TODO: Not support for custom model, let's update it later
                temperature=0.0,  # TODO: Not support for custom temperature, let's update it later
                main_unit=WorkflowType.HIERARCHICAL if str(assistant.assistant_type) == AssistantType.ADVANCED_ASSISTANT else WorkflowType.CHATBOT,
                support_units=extract_support_units(assistant),
                mcp_ids=None,  # TODO: Not support for MCPs yet
                # TODO: Not support for extensions yet
                teams=[
                    {
                        "id": team.id,
                        "name": team.name,
                        "description": team.description,
                        "workflow_type": team.workflow_type,
                        "members": [
                            {"id": member.id, "name": member.name, "type": member.type, "role": member.role}
                            for member in team.members
                            if hasattr(team, "members") and team.members
                        ],
                    }
                    for team in assistant.teams
                ],
                created_at=assistant.created_at,  # type: ignore
            )
            for assistant in assistants
        ]

        return ResponseWrapper.wrap(
            status=200,
            data=GetAssistantsResponse(assistants=wrapped_assistants, page_number=paging_number, max_per_page=max_per_page, total_page=total_pages),
        ).to_response()
    except Exception as e:
        logger.error(f"Error fetching assistants: {e}")
        return ResponseWrapper.wrap(status=500, message="Internal Server Error").to_response()


@router.post("/create", summary="Create an advanced assistant.", response_model=ResponseWrapper[CreateAdvancedAssistantResponse])
async def create_advanced_assistant(
    session: SessionDep,
    request: CreateAdvancedAssistantRequest,
    x_user_id: str = Header(None),
):
    try:
        # Create a new assistant instance
        new_assistant = Assistant(
            id=str(uuid.uuid4()),
            user_id=x_user_id,
            name=request.name,
            description=request.description,
            system_prompt=request.system_prompt,
            assistant_type=AssistantType.ADVANCED_ASSISTANT,  # Default type
        )
        session.add(new_assistant)

        # Create main unit (main team)
        main_team = Team(
            id=str(uuid.uuid4()),
            name="Hierarchical Unit",
            description="Main unit for advanced assistant, which integrates with mcps and extensions.",
            workflow_type=WorkflowType.HIERARCHICAL,
            user_id=x_user_id,
        )

        session.add(main_team)
        await session.flush()  # Flush to get the ID of the main team

        # Link the assistant with the main team
        team_assistant_link = TeamAssistantLink(
            team_id=main_team.id,
            assistant_id=new_assistant.id,
        )
        session.add(team_assistant_link)

        # Create root member for the main team
        root_member = Member(
            id=str(uuid.uuid4()),
            name=f"{request.name} Leader",
            team_id=main_team.id,
            backstory="Leader of the main team for advanced assistant.",
            role="Gather inputs from your team and answer the question.",
            type="root",
            provider=request.provider,
            model=request.model_name,
            temperature=request.temperature,
            interrupt=False,  # Default value
            position_x=0.0,
            position_y=0.0,
        )
        session.add(root_member)

        # Load members of the main team
        if request.mcp_ids:
            for mcp_id in request.mcp_ids:
                # Load connected_mcp
                statement = (
                    select(ConnectedMcp)
                    .select_from(ConnectedMcp)
                    .where(ConnectedMcp.id == mcp_id, ConnectedMcp.user_id == x_user_id, ConnectedMcp.is_deleted.is_(False))
                )
                result = await session.execute(statement)
                connected_mcp = result.scalar_one_or_none()
                if connected_mcp:
                    # Create a member for the main team
                    member = Member(
                        id=str(uuid.uuid4()),
                        name=str(connected_mcp.mcp_name),
                        team_id=main_team.id,
                        backstory=str(connected_mcp.description) if connected_mcp.description is not None else None,
                        role="Execute actions based on provided tasks using binding tools and return the results",
                        type="worker",
                        source=root_member.id,
                        provider=request.provider,
                        model=request.model_name,
                        temperature=request.temperature,
                        interrupt=True,
                        position_x=0.0,
                        position_y=0.0,
                    )
                    session.add(member)

                    # Load skills
                    connections = {}
                    connections[connected_mcp.mcp_name] = {
                        "url": connected_mcp.url,
                        "transport": connected_mcp.transport,
                    }

                    tool_infos = await McpService.aget_mcp_tool_info(connections=connections)
                    skills_to_cache = []  # Store info for later caching

                    # Create skills
                    for tool_info in tool_infos:
                        # Create skill
                        skill = Skill(
                            id=str(uuid.uuid4()),
                            user_id=str(connected_mcp.user_id),
                            name=tool_info.display_name,
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

                        # Add link to member
                        member_skill_link = MemberSkillLink(
                            member_id=member.id,
                            skill_id=skill.id,
                        )
                        session.add(member_skill_link)

                        # Store info for later caching
                        skills_to_cache.append((skill, tool_info))

                    await session.flush()

                    # Now add tools to cache
                    for skill, tool_info in skills_to_cache:
                        # Add tool to cache
                        tool_manager.add_personal_tool(
                            user_id=str(connected_mcp.user_id),
                            tool_key=create_unique_key(skill_id=str(skill.id), skill_name=str(skill.name)),
                            tool_info=tool_info,
                        )

        # Load extensions of the main team
        if request.extension_ids:
            for extension_id in request.extension_ids:
                # Load connected_extension
                statement = (
                    select(ConnectedExtension)
                    .select_from(ConnectedExtension)
                    .where(ConnectedExtension.id == extension_id, ConnectedExtension.user_id == x_user_id, ConnectedExtension.is_deleted.is_(False))
                )
                result = await session.execute(statement)
                connected_extension = result.scalar_one_or_none()
                if connected_extension:
                    # Create a member for the main team
                    member = Member(
                        id=str(uuid.uuid4()),
                        name=str(connected_extension.extension_name),
                        team_id=main_team.id,
                        backstory="",  # TODO: Let's get description of the extension later
                        role="Execute actions based on provided tasks using binding tools and return the results",
                        type="worker",
                        source=root_member.id,
                        provider=request.provider,
                        model=request.model_name,
                        temperature=request.temperature,
                        interrupt=True,
                        position_x=0.0,
                        position_y=0.0,
                    )
                    session.add(member)

                    # Load skills
                    extension_service_info = extension_service_manager.get_service_info(service_enum=str(connected_extension.extension_enum))

                    if not extension_service_info or not extension_service_info.service_object:
                        raise ValueError(f"Extension service info for {connected_extension.extension_enum} not found or service object is None.")

                    extension_service = extension_service_info.service_object
                    tools = extension_service.get_authed_tools(user_id=str(connected_extension.user_id))

                    tool_infos = [convert_base_tool_to_tool_info(tool) for tool in tools]
                    skills_to_cache = []  # Store info for later caching

                    for tool_info in tool_infos:
                        # Create skill
                        skill = Skill(
                            id=str(uuid.uuid4()),
                            user_id=str(connected_extension.user_id),
                            name=tool_info.display_name,
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

                        # Add link to member
                        member_skill_link = MemberSkillLink(
                            member_id=member.id,
                            skill_id=skill.id,
                        )
                        session.add(member_skill_link)

                        # Store info for later caching
                        skills_to_cache.append((skill, tool_info))

                    await session.flush()

                    # Now add tools to cache
                    for skill, tool_info in skills_to_cache:
                        # Add tool to cache
                        tool_manager.add_personal_tool(
                            user_id=str(connected_extension.user_id),
                            tool_key=create_unique_key(skill_id=str(skill.id), skill_name=str(skill.name)),
                            tool_info=tool_info,
                        )
        # For loop to create support units
        if request.support_units:
            for unit in request.support_units:
                # Create a support team for each unit
                support_team = Team(
                    id=str(uuid.uuid4()),
                    name=f"Support Unit - {unit}",
                    description=f"Support unit for {unit} in advanced assistant.",
                    workflow_type=unit,
                    user_id=x_user_id,
                )
                session.add(support_team)
                await session.flush()

                # Link the support team with the assistant
                support_team_assistant_link = TeamAssistantLink(
                    team_id=support_team.id,
                    assistant_id=new_assistant.id,
                )
                session.add(support_team_assistant_link)

                # Create freelancer head for the support team
                support_root_member = Member(
                    id=str(uuid.uuid4()),
                    name=f"{unit}",
                    team_id=support_team.id,
                    backstory=f"Unit for advanced assistant: {unit}.",
                    role="Answer the user's question.",
                    type=f"{unit}",
                    provider=request.provider,
                    model=request.model_name,
                    temperature=request.temperature,
                    interrupt=False,  # Default value
                    position_x=0.0,
                    position_y=0.0,
                )
                session.add(support_root_member)
                await session.flush()

                # Load skill for RAGBOT unit
                if unit == WorkflowType.RAGBOT:
                    rag_skill = Skill(
                        id=str(uuid.uuid4()),
                        user_id=x_user_id,  # This user_id is correct as it's for Skill model
                        name="KnowledgeBase",
                        description="Query documents for answers.",
                        icon="",
                        display_name="Knowledge Base",
                        strategy=StorageStrategy.PERSONAL_TOOL_CACHE,
                        input_parameters={},
                        reference_type=ConnectedServiceType.NONE,
                    )
                    session.add(rag_skill)
                    await session.flush()

                    # Add link to member
                    member_skill_link = MemberSkillLink(
                        member_id=support_root_member.id,
                        skill_id=rag_skill.id,
                    )
                    session.add(member_skill_link)

                # Load skill for SEARCHBOT unit
                if unit == WorkflowType.SEARCHBOT:
                    # DDG tool
                    ddg_tool_info = global_tools.get("duckduckgo-search")
                    if not ddg_tool_info:
                        raise ValueError("DuckDuckGo search tool not found in global tools.")

                    ddg_skill = Skill(
                        id=str(uuid.uuid4()),
                        user_id=x_user_id,  # This user_id is correct as it's for Skill model
                        name=ddg_tool_info.display_name,
                        description=ddg_tool_info.description,
                        icon="",
                        display_name=ddg_tool_info.display_name,
                        strategy=StorageStrategy.GLOBAL_TOOLS,
                        input_parameters=ddg_tool_info.input_parameters,
                        reference_type=ConnectedServiceType.NONE,
                    )
                    session.add(ddg_skill)
                    await session.flush()

                    # Add link to member
                    member_skill_link = MemberSkillLink(
                        member_id=support_root_member.id,
                        skill_id=ddg_skill.id,
                    )
                    session.add(member_skill_link)

                    # Wikipedia tool
                    wikipedia_tool_info = global_tools.get("wikipedia")
                    if not wikipedia_tool_info:
                        raise ValueError("Wikipedia tool not found in global tools.")
                    wikipedia_skill = Skill(
                        id=str(uuid.uuid4()),
                        user_id=x_user_id,  # This user_id is correct as it's for Skill model
                        name=wikipedia_tool_info.display_name,
                        description=wikipedia_tool_info.description,
                        icon="",
                        display_name=wikipedia_tool_info.display_name,
                        strategy=StorageStrategy.GLOBAL_TOOLS,
                        input_parameters=wikipedia_tool_info.input_parameters,
                        reference_type=ConnectedServiceType.NONE,
                    )
                    session.add(wikipedia_skill)
                    await session.flush()

                    # Add link to member
                    member_skill_link = MemberSkillLink(
                        member_id=support_root_member.id,
                        skill_id=wikipedia_skill.id,
                    )
                    session.add(member_skill_link)

        # Commit the session to save all changes
        await session.commit()

        # Get all teams associated with the new assistant
        statement = (
            select(Team)
            .select_from(Team)
            .options(selectinload(Team.members))
            .join(TeamAssistantLink, Team.id == TeamAssistantLink.team_id)
            .join(Assistant, TeamAssistantLink.assistant_id == Assistant.id)
            .where(TeamAssistantLink.assistant_id == new_assistant.id)
        )

        result = await session.execute(statement)
        teams = result.scalars().all()
        teams_data = []
        for team in teams:
            team_dict = {
                "id": team.id,
                "name": team.name,
                "description": team.description,
                "workflow_type": team.workflow_type,
                "members": [{"id": member.id, "name": member.name, "type": member.type, "role": member.role} for member in team.members],
            }
            teams_data.append(team_dict)

        # Prepare the response
        response = CreateAdvancedAssistantResponse(
            id=str(new_assistant.id),
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
            created_at=new_assistant.created_at,  # type: ignore
        )

        return ResponseWrapper.wrap(status=201, data=response).to_response()
    except Exception as e:
        logger.error(f"Error creating advanced assistant: {e}")
        await session.rollback()
        return ResponseWrapper.wrap(status=500, message="Internal Server Error").to_response()


@router.get(
    "/{assistant_id}/get-detail",
    summary="Get assistant details.",
    response_model=ResponseWrapper[GetAssistantResponse | GetAdvancedAssistantResponse],
)
async def get_assistant_by_id(session: SessionDep, assistant_id: str, x_user_id: str = Header(None), x_user_role: str = Header(None)):
    """
    Get details of an assistant by its ID.
    """
    try:
        # Fetch the assistant by ID
        if x_user_role in ["admin", "superuser"]:
            statement = (
                select(Assistant)
                .select_from(Assistant)
                .options(selectinload(Assistant.teams))
                .where(Assistant.id == assistant_id, Assistant.is_deleted.is_(False))
            )
        else:
            statement = (
                select(Assistant)
                .select_from(Assistant)
                .options(selectinload(Assistant.teams))
                .where(Assistant.user_id == x_user_id, Assistant.id == assistant_id, Assistant.is_deleted.is_(False))
            )

        result = await session.execute(statement)
        assistant = result.scalar_one_or_none()

        if not assistant:
            return ResponseWrapper.wrap(status=404, message="Assistant not found").to_response()

        # Prepare the response
        if str(assistant.assistant_type) == AssistantType.ADVANCED_ASSISTANT:
            response = GetAdvancedAssistantResponse(
                id=str(assistant.id),
                user_id=str(assistant.user_id),
                name=str(assistant.name),
                assistant_type=assistant.assistant_type,  # type: ignore
                description=str(assistant.description),
                system_prompt=str(assistant.system_prompt),
                provider="",  # TODO: Not support for custom provider, let's update it later
                model_name="",  # TODO: Not support for custom model, let's update it later
                temperature=0.0,  # TODO: Not support for custom temperature, let's update it later
                main_unit=WorkflowType.HIERARCHICAL if str(assistant.assistant_type) == AssistantType.ADVANCED_ASSISTANT else WorkflowType.CHATBOT,
                support_units=extract_support_units(assistant),
                mcp_ids=None,  # TODO: Not support for MCPs yet
                # TODO: Not support for extensions yet
                teams=[
                    {
                        "id": team.id,
                        "name": team.name,
                        "description": team.description,
                        "workflow_type": team.workflow_type,
                        "members": [
                            {"id": member.id, "name": member.name, "type": member.type, "role": member.role}
                            for member in team.members
                            if hasattr(team, "members") and team.members
                        ],
                    }
                    for team in assistant.teams
                ],
                created_at=assistant.created_at,  # type: ignore
            )

            return ResponseWrapper.wrap(status=200, data=response).to_response()
        else:
            response = GetAssistantResponse(
                id=str(assistant.id),
                user_id=str(assistant.user_id),
                name=str(assistant.name),
                assistant_type=assistant.assistant_type,  # type: ignore
                description=str(assistant.description),
                system_prompt=str(assistant.system_prompt),
                provider="",  # TODO: Not support for custom provider, let's update it later
                model_name="",  # TODO: Not support for custom model, let's update it later
                temperature=0.0,  # TODO: Not support for custom temperature, let's update it later
                main_unit=WorkflowType.CHATBOT,
                support_units=[],
                teams=[
                    {
                        "id": team.id,
                        "name": team.name,
                        "description": team.description,
                        "workflow_type": team.workflow_type,
                        "members": [
                            {"id": member.id, "name": member.name, "type": member.type, "role": member.role}
                            for member in team.members
                            if hasattr(team, "members") and team.members
                        ],
                    }
                    for team in assistant.teams
                ],
                created_at=assistant.created_at,  # type: ignore
            )
            return ResponseWrapper.wrap(status=200, data=response).to_response()

    except Exception as e:
        logger.error(f"Error fetching assistant details: {e}")
        return ResponseWrapper.wrap(status=500, message="Internal Server Error").to_response()


@router.patch("{assistant_id}/update", summary="Update assistant information.", response_model=ResponseWrapper[UpdateAdvancedAssistantResponse])
async def update_assistant(
    session: SessionDep,
    assistant_id: str,
    request: UpdateAdvancedAssistantRequest,
    x_user_id: str = Header(None),
):
    """
    Update an assistant's information.
    """
    try:
        # Fetch the assistant by ID
        statement = (
            select(Assistant)
            .select_from(Assistant)
            .where(Assistant.id == assistant_id, Assistant.user_id == x_user_id, Assistant.is_deleted.is_(False))
        )
        result = await session.execute(statement)
        assistant = result.scalar_one_or_none()

        if not assistant:
            return ResponseWrapper.wrap(status=404, message="Assistant not found").to_response()

        # Update the assistant table
        if request.name:
            setattr(assistant, "name", request.name)
        if request.description:
            setattr(assistant, "description", request.description)
        if request.system_prompt:
            setattr(assistant, "system_prompt", request.system_prompt)

        # Get main team (main unit)
        # Get main team (hierarchical unit)
        statement = (
            select(Team)
            .select_from(Team)
            .options(selectinload(Team.members))
            .join(TeamAssistantLink, Team.id == TeamAssistantLink.team_id)
            .where(
                Team.user_id == x_user_id,
                TeamAssistantLink.assistant_id == assistant.id,
                Team.workflow_type == WorkflowType.HIERARCHICAL
            )
        )
        
        result = await session.execute(statement)
        main_team = result.scalar_one_or_none()

        if not main_team:
            return ResponseWrapper.wrap(status=404, message="Main team not found").to_response()

        # Update mcp members of the main team (main unit)
        if request.mcp_ids and len(request.mcp_ids) > 0:
            # Delete all members that have at least on mcp skill
            # Find all members in the main team that have MCP skills
            mcp_member_ids = []

            for member in main_team.members:
                if member.type == "worker":  # Workers are the ones that have MCP/extension skills
                    # Check if this member has any MCP skills
                    statement = (
                        select(Skill)
                        .select_from(Skill)
                        .join(MemberSkillLink, Skill.id == MemberSkillLink.skill_id)
                        .where(
                            MemberSkillLink.member_id == member.id,
                            Skill.reference_type == ConnectedServiceType.MCP
                        )
                    )
                    
                    skill_result = await session.execute(statement)
                    mcp_skills = skill_result.scalars().all()
                    
                    if mcp_skills:
                        mcp_member_ids.append(member.id)

            # Delete the member skills first
            if mcp_member_ids:
                await session.execute(
                    delete(MemberSkillLink)
                    .where(MemberSkillLink.member_id.in_(mcp_member_ids))
                )
                
                # Then delete the members
                await session.execute(
                    delete(Member)
                    .where(Member.id.in_(mcp_member_ids))
                )
                
            
            # Now, add new members based on the provided MCP IDs
            for mcp_id in request.mcp_ids:
                # Load connected_mcp
                statement = (
                    select(ConnectedMcp)
                    .select_from(ConnectedMcp)
                    .where(ConnectedMcp.id == mcp_id, ConnectedMcp.user_id == x_user_id, ConnectedMcp.is_deleted.is_(False))
                )
                result = await session.execute(statement)
                connected_mcp = result.scalar_one_or_none()
                if connected_mcp:
                    # Create a member for the main team
                    member = Member(
                        id=str(uuid.uuid4()),
                        name=str(connected_mcp.mcp_name),
                        team_id=main_team.id,
                        backstory=str(connected_mcp.description) if connected_mcp.description is not None else None,
                        role="Execute actions based on provided tasks using binding tools and return the results",
                        type="worker",
                        source=None,  # No root member for MCPs
                        provider=request.provider,
                        model=request.model_name,
                        temperature=request.temperature,
                        interrupt=True,
                        position_x=0.0,  # Placeholder for UI positioning
                        position_y=0.0,  # Placeholder for UI positioning
                    )
                    session.add(member)

                    # Commit to ensure member exists before creating skill links
                    await session.commit()
                    await session.refresh(member)

                    # Load skills
                    connections = {}
                    connections[connected_mcp.mcp_name] = {
                        "url": connected_mcp.url,
                        "transport": connected_mcp.transport,
                    }

                    tool_infos = await McpService.aget_mcp_tool_info(connections=connections)

                    # Create skills
                    for tool_info in tool_infos:
                        # Create skill
                        skill = Skill(
                            id=str(uuid.uuid4()),
                            user_id=str(connected_mcp.user_id),
                            name=tool_info.display_name,
                            description=tool_info.description,
                            icon="",
                            display_name=tool_info.display_name,
                            strategy=StorageStrategy.PERSONAL_TOOL_CACHE,
                            input_parameters=tool_info.input_parameters,
                            reference_type=ConnectedServiceType.MCP,
                            mcp_id=connected_mcp.id,
                        )
                        session.add(skill)
                        await session.commit()  # Commit after creating skill
                        await session.refresh(skill)

                        # Add link to member
                        member_skill_link = MemberSkillLink(
                            member_id=member.id,
                            skill_id=skill.id,
                        )
                        session.add(member_skill_link)
                        await session.commit()  # Commit after creating link

        # Update extension members of the main team (main unit)
        if request.extension_ids and len(request.extension_ids) > 0:
            # Delete all members that have at least one extension skill
            # Find all members in the main team that have extension skills
            extension_member_ids = []

            for member in main_team.members:
                if member.type == "worker":  # Workers are the ones that have MCP/extension skills
                    # Check if this member has any extension skills
                    statement = (
                        select(Skill)
                        .select_from(Skill)
                        .join(MemberSkillLink, Skill.id == MemberSkillLink.skill_id)
                        .where(
                            MemberSkillLink.member_id == member.id,
                            Skill.reference_type == ConnectedServiceType.EXTENSION,
                            Skill.is_deleted.is_(False)
                        )
                    )
                    
                    skill_result = await session.execute(statement)
                    extension_skills = skill_result.scalars().all()
                    
                    if extension_skills:
                        extension_member_ids.append(member.id)

            # Delete the member skills first
            if extension_member_ids:
                await session.execute(
                    delete(MemberSkillLink)
                    .where(MemberSkillLink.member_id.in_(extension_member_ids))
                )
                
                # Then delete the members
                await session.execute(
                    delete(Member)
                    .where(Member.id.in_(extension_member_ids))
                )
                
            # Now, add new members based on the provided extension IDs
            for extension_id in request.extension_ids:
                # Load connected_extension
                statement = (
                    select(ConnectedExtension)
                    .select_from(ConnectedMcp)
                    .where(ConnectedMcp.id == extension_id, ConnectedMcp.user_id == x_user_id, ConnectedMcp.is_deleted.is_(False))
                )
                result = await session.execute(statement)
                connected_extension = result.scalar_one_or_none()
                if connected_extension:
                    # Create a member for the main team
                    member = Member(
                        id=str(uuid.uuid4()),
                        name=str(connected_extension.extension_name),
                        team_id=main_team.id,
                        backstory="",  # TODO: Let's get description of the extension later
                        role="Execute actions based on provided tasks using binding tools and return the results",
                        type="worker",
                        source=None,  # No root member for extensions
                        provider=request.provider,
                        model=request.model_name,
                        temperature=request.temperature,
                        interrupt=True,
                        position_x=0.0,  # Placeholder for UI positioning
                        position_y=0.0,  # Placeholder for UI positioning
                    )
                    session.add(member)

                    # Commit to ensure member exists before creating skill links
                    await session.commit()
                    await session.refresh(member)

                    # Load skills
                    extension_service_info = extension_service_manager.get_service_info(service_enum=str(connected_extension.extension_enum))

                    if not extension_service_info or not extension_service_info.service_object:
                        raise ValueError(f"Extension service info for {connected_extension.extension_enum} not found or service object is None.")

                    extension_service = extension_service_info.service_object
                    tools = extension_service.get_authed_tools(user_id=str(connected_extension.user_id))

                    tool_infos = [convert_base_tool_to_tool_info(tool) for tool in tools]

                    for tool_info in tool_infos:
                        # Create skill
                        skill = Skill(
                            id=str(uuid.uuid4()),
                            user_id=str(connected_extension.user_id),
                            name=tool_info.display_name,
                            description=tool_info.description,
                            icon="",
                            display_name=tool_info.display_name,
                            strategy=StorageStrategy.PERSONAL_TOOL_CACHE,
                            input_parameters=tool_info.input_parameters,
                            reference_type=ConnectedServiceType.EXTENSION,
                            extension_id=connected_extension.id,
                        )
                        session.add(skill)

                        # Add link to member
                        member_skill_link = MemberSkillLink(
                            member_id=member.id,
                            skill_id=skill.id,
                        )
                        session.add(member_skill_link)

        # Update support units
        if request.support_units and len(request.support_units) > 0:
            # Delete all support teams that are not in the request
            # Find all teams associated with this assistant
            all_teams_statement = (
                select(Team)
                .select_from(Team)
                .join(TeamAssistantLink, Team.id == TeamAssistantLink.team_id)
                .where(TeamAssistantLink.assistant_id == assistant.id)
            )
            all_teams_result = await session.execute(all_teams_statement)
            all_teams = all_teams_result.scalars().all()

            # Find teams to delete (all except the hierarchical/main team)
            teams_to_delete = [team.id for team in all_teams if str(team.workflow_type) != WorkflowType.HIERARCHICAL]

            if teams_to_delete:
                # Delete all member skill links for members in these teams
                member_statement = select(Member.id).where(Member.team_id.in_(teams_to_delete))
                member_result = await session.execute(member_statement)
                member_ids = member_result.scalars().all()

                if member_ids:
                    await session.execute(delete(MemberSkillLink).where(MemberSkillLink.member_id.in_(member_ids)))

                # Delete all members in these teams
                await session.execute(delete(Member).where(Member.team_id.in_(teams_to_delete)))

                # Delete team assistant links
                await session.execute(delete(TeamAssistantLink).where(TeamAssistantLink.team_id.in_(teams_to_delete)))

                # Delete the teams themselves
                await session.execute(delete(Team).where(Team.id.in_(teams_to_delete)))

            # Now create new support teams based on the request
            for unit in request.support_units:
                # Create a support team for each unit
                support_team = Team(
                    id=str(uuid.uuid4()),
                    name=f"Support Unit - {unit}",
                    description=f"Support unit for {unit} in advanced assistant.",
                    workflow_type=unit,
                    user_id=x_user_id,
                )

                session.add(support_team)

                # Link the support team with the assistant
                support_team_assistant_link = TeamAssistantLink(
                    team_id=support_team.id,
                    assistant_id=assistant.id,
                )
                session.add(support_team_assistant_link)

                # Create root member for the support team
                support_root_member = Member(
                    id=str(uuid.uuid4()),
                    name=f"{unit}",
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

                # Load skill for RAGBOT unit
                if unit == WorkflowType.RAGBOT:
                    rag_skill = Skill(
                        id=str(uuid.uuid4()),
                        user_id=str(x_user_id),
                        name="KnowledgeBase",
                        description="Query documents for answers.",
                        icon="",
                        display_name="Knowledge Base",
                        strategy=StorageStrategy.PERSONAL_TOOL_CACHE,
                        input_parameters={},
                        reference_type=ConnectedServiceType.NONE,
                    )
                    session.add(rag_skill)

                    # Add link to member
                    member_skill_link = MemberSkillLink(
                        member_id=support_root_member.id,
                        skill_id=rag_skill.id,
                    )
                    session.add(member_skill_link)

                # Load skill for SEARCHBOT unit
                if unit == WorkflowType.SEARCHBOT:
                    # DDG tool
                    ddg_tool_info = global_tools.get("duckduckgo-search")
                    if not ddg_tool_info:
                        raise ValueError("DuckDuckGo search tool not found in global tools.")

                    ddg_skill = Skill(
                        id=str(uuid.uuid4()),
                        user_id=str(x_user_id),
                        name=ddg_tool_info.display_name,
                        description=ddg_tool_info.description,
                        icon="",
                        display_name=ddg_tool_info.display_name,
                        strategy=StorageStrategy.GLOBAL_TOOLS,
                        input_parameters=ddg_tool_info.input_parameters,
                        reference_type=ConnectedServiceType.NONE,
                    )
                    session.add(ddg_skill)

                    # Add link to member
                    member_skill_link = MemberSkillLink(
                        member_id=support_root_member.id,
                        skill_id=ddg_skill.id,
                    )
                    session.add(member_skill_link)

                    # Wikipedia tool
                    wikipedia_tool_info = global_tools.get("wikipedia")
                    if not wikipedia_tool_info:
                        raise ValueError("Wikipedia tool not found in global tools.")
                    wikipedia_skill = Skill(
                        id=str(uuid.uuid4()),
                        user_id=str(x_user_id),
                        name=wikipedia_tool_info.display_name,
                        description=wikipedia_tool_info.description,
                        icon="",
                        display_name=wikipedia_tool_info.display_name,
                        strategy=StorageStrategy.GLOBAL_TOOLS,
                        input_parameters=wikipedia_tool_info.input_parameters,
                        reference_type=ConnectedServiceType.NONE,
                    )
                    session.add(wikipedia_skill)

                    # Add link to member
                    member_skill_link = MemberSkillLink(
                        member_id=support_root_member.id,
                        skill_id=wikipedia_skill.id,
                    )
                    session.add(member_skill_link)
        
        # Save all changes
        await session.commit()
        
        # Return value
        # Fetch the updated assistant with all teams
        statement = (
            select(Assistant)
            .select_from(Assistant)
            .options(selectinload(Assistant.teams).selectinload(Team.members))
            .where(Assistant.id == assistant_id)
        )

        result = await session.execute(statement)
        updated_assistant = result.scalar_one()

        # Format the response data
        teams_data = []
        for team in updated_assistant.teams:
            team_dict = {
                "id": team.id,
                "name": team.name,
                "description": team.description,
                "workflow_type": team.workflow_type,
                "members": [
                    {"id": member.id, "name": member.name, "type": member.type, "role": member.role}
                    for member in team.members
                ],
            }
            teams_data.append(team_dict)

        response = UpdateAdvancedAssistantResponse(
            id=str(updated_assistant.id),
            user_id=str(updated_assistant.user_id),
            name=str(updated_assistant.name),
            assistant_type=updated_assistant.assistant_type,  # type: ignore
            description=str(updated_assistant.description),
            system_prompt=str(updated_assistant.system_prompt),
            provider=request.provider,
            model_name=request.model_name,
            temperature=request.temperature,
            main_unit=WorkflowType.HIERARCHICAL,
            support_units=request.support_units or extract_support_units(updated_assistant),
            mcp_ids=request.mcp_ids,
            extension_ids=request.extension_ids,
            teams=teams_data,
            created_at=updated_assistant.created_at,  # type: ignore
        )

        return ResponseWrapper.wrap(status=200, data=response).to_response()
    except Exception as e:
        logger.error(f"Error updating assistant: {e}", exc_info=True)
        await session.rollback()
        return ResponseWrapper.wrap(status=500, message="Internal Server Error").to_response()


@router.delete("/{user_id}/{assistant_id}/delete", summary="Delete a thread.", response_model=ResponseWrapper[MessageResponse])
async def delete_assistant(session: SessionDep, assistant_id: str, x_user_id: str):
    """
    Delete an assistant by setting its is_deleted flag to True.
    """
    try:
        # Fetch the assistant by ID
        statement = (
            select(Assistant)
            .select_from(Assistant)
            .where(Assistant.id == assistant_id, Assistant.user_id == x_user_id, Assistant.is_deleted.is_(False))
        )
        result = await session.execute(statement)
        assistant = result.scalar_one_or_none()

        if not assistant:
            return ResponseWrapper.wrap(status=404, message="Assistant not found").to_response()

        # Remove assistant, its teams, teams's members, members's skills.
        # First, get all teams associated with the assistant
        teams_statement = (
            select(Team.id)
            .select_from(Team)
            .join(TeamAssistantLink, Team.id == TeamAssistantLink.team_id)
            .where(TeamAssistantLink.assistant_id == assistant_id)
        )
        teams_result = await session.execute(teams_statement)
        team_ids = teams_result.scalars().all()

        if team_ids:
            # Get all member IDs from these teams
            members_statement = select(Member.id).where(Member.team_id.in_(team_ids))
            members_result = await session.execute(members_statement)
            member_ids = members_result.scalars().all()

            if member_ids:
                # Delete member skill links
                await session.execute(delete(MemberSkillLink).where(MemberSkillLink.member_id.in_(member_ids)))

                # Delete skills associated with these members
                await session.execute(
                    delete(Skill).where(
                        Skill.id.in_(
                            select(Skill.id)
                            .select_from(Skill)
                            .join(MemberSkillLink, Skill.id == MemberSkillLink.skill_id)
                            .where(MemberSkillLink.member_id.in_(member_ids))
                        )
                    )
                )

                # Delete members
                await session.execute(delete(Member).where(Member.id.in_(member_ids)))

            # Delete team assistant links
            await session.execute(delete(TeamAssistantLink).where(TeamAssistantLink.assistant_id == assistant_id))

            # Delete teams
            await session.execute(delete(Team).where(Team.id.in_(team_ids)))

        # Finally, delete the assistant
        await session.execute(delete(Assistant).where(Assistant.id == assistant_id))

        await session.commit()

        message = MessageResponse(message="Assistant deleted successfully")

        return ResponseWrapper.wrap(status=200, data=message).to_response()

    except Exception as e:
        logger.error(f"Error deleting assistant: {e}")
        await session.rollback()
        return ResponseWrapper.wrap(status=500, message="Internal Server Error").to_response()
