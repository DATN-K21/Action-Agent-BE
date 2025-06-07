from fastapi import APIRouter, Depends, Header
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.api.deps import SessionDep
from app.core import logging
from app.core.enums import AssistantType, WorkflowType
from app.db_models.assistant import Assistant
from app.db_models.connected_mcp import ConnectedMcp
from app.db_models.member import Member
from app.db_models.team import Team
from app.db_models.team_assistant_link import TeamAssistantLink
from app.schemas.assistant import CreateAdvancedAssistantRequest, CreateAdvancedAssistantResponse, GetAssistantResponse, GetAssistantsResponse
from app.schemas.base import PagingRequest, ResponseWrapper

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
                    .where(Assistant.is_deleted == False)
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
                temperature=0.0,  # TODO: Not support for custom temperature, let's update it later
                main_unit=WorkflowType.HIERARCHICAL if str(assistant.assistant_type) == AssistantType.ADVANCED_ASSISTANT else WorkflowType.CHATBOT,
                support_units=extract_support_units(assistant),
                teams=[{"id": team.id, "name": team.name} for team in assistant.teams],
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
            user_id=x_user_id,
            name=request.name,
            description=request.description,
            system_prompt=request.system_prompt,
            assistant_type=AssistantType.ADVANCED_ASSISTANT,  # Default type
        )

        session.add(new_assistant)
        await session.commit()
        await session.refresh(new_assistant)

        # Create main unit (main team)
        main_team = Team(
            name="Hierarchical Unit",
            description="Main unit for advanced assistant, which integrates with mcps and extensions.",
            workflow_type=WorkflowType.HIERARCHICAL,
            user_id=x_user_id,
        )

        session.add(main_team)
        await session.commit()
        await session.refresh(main_team)

        # Link the assistant with the main team
        new_assistant.teams.append(main_team)
        await session.commit()

        # Create root member for the main team
        root_member = Member(
            name=f"{request.name} Leader",
            team_id=main_team.id,
            backstory="Leader of the main team for advanced assistant.",
            user_id=x_user_id,
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
        await session.commit()
        await session.refresh(root_member)

        # Load members of the main team
        if request.mcp_ids:
            for mcp_id in request.mcp_ids:
                # Load mcp
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
                        name=str(connected_mcp.mcp_name),
                        team_id=main_team.id,
                        backstory=str(connected_mcp.description) if connected_mcp.description is not None else None,
                        user_id=x_user_id,
                        role="Execute actions based on provided tasks using binding tools and return the results",
                        type="worker",
                        source=root_member.id,
                        provider=request.provider,
                        model=request.model_name,
                        temperature=request.temperature,
                        interrupt=True,
                        position_x=0.0,  # Placeholder for UI positioning
                        position_y=0.0,  # Placeholder for UI positioning
                    )

                    session.add(member)
                    await session.commit()
                    await session.refresh(member)

        # Load extensions of the main team
        if request.extension_ids:
            for extension_id in request.extension_ids:
                # Load extension
                statement = (
                    select(ConnectedMcp)
                    .select_from(ConnectedMcp)
                    .where(ConnectedMcp.id == extension_id, ConnectedMcp.user_id == x_user_id, ConnectedMcp.is_deleted.is_(False))
                )
                result = await session.execute(statement)
                connected_extension = result.scalar_one_or_none()
                if connected_extension:
                    # Create a member for the main team
                    member = Member(
                        name=str(connected_extension.mcp_name),
                        team_id=main_team.id,
                        backstory=str(connected_extension.description) if connected_extension.description is not None else None,
                        user_id=x_user_id,
                        role="Execute actions based on provided tasks using binding tools and return the results",
                        type="worker",
                        source=root_member.id,
                        provider=request.provider,
                        model=request.model_name,
                        temperature=request.temperature,
                        interrupt=True,
                        position_x=0.0,  # Placeholder for UI positioning
                        position_y=0.0,  # Placeholder for UI positioning
                    )

                    session.add(member)
                    await session.commit()
                    await session.refresh(member)

        # For loop to create support units
        if request.support_units:
            for unit in request.support_units:
                # Create a support team for each unit
                support_team = Team(
                    name=f"Support Unit - {unit}",
                    description=f"Support unit for {unit} in advanced assistant.",
                    workflow_type=unit,
                    user_id=x_user_id,
                )

                session.add(support_team)
                await session.commit()
                await session.refresh(support_team)

                # Link the support team with the assistant
                new_assistant.teams.append(support_team)
                await session.commit()

                # Create freelancer head for the support team
                support_root_member = Member(
                    name=f"{unit}",
                    team_id=support_team.id,
                    backstory=f"Unit for advanced assistant: {unit}.",
                    user_id=x_user_id,
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
                await session.commit()
                await session.refresh(support_root_member)

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


@router.get("/{user_id}/{assistant_id}/get-detail", summary="Get assistant details.", response_model=ResponseWrapper[GetFullInfoAssistantResponse])
async def get_full_info_assistant_by_id(
    user_id: str,
    assistant_id: str,
    assistant_service: AssistantService = Depends(get_assistant_service),
    extension_assistant_service: ExtensionAssistantService = Depends(get_extension_assistant_service),
    mcp_assistant_service: McpAssistantService = Depends(get_mcp_assistant_service),
    _: bool = Depends(ensure_user_id),
):
    pass


@router.patch(
    "/{user_id}/{assistant_id}/update", summary="Update assistant information.", response_model=ResponseWrapper[UpdateFullInfoAssistantResponse]
)
async def update_assistant(
    user_id: str,
    assistant_id: str,
    request: UpdateFullInfoAssistantRequest,
    assistant_service: AssistantService = Depends(get_assistant_service),
    extension_assistant_service: ExtensionAssistantService = Depends(get_extension_assistant_service),
    mcp_assistant_service: McpAssistantService = Depends(get_mcp_assistant_service),
    connected_mcp_service: ConnectedMcpService = Depends(get_connected_mcp_service),
    connected_extension_service: ConnectedExtensionService = Depends(get_connected_extension_service),
    _: bool = Depends(ensure_user_id),
):
    pass


@router.delete("/{user_id}/{assistant_id}/delete", summary="Delete a thread.", response_model=ResponseWrapper[DeleteThreadResponse])
async def delete_assistant(
    user_id: str,
    assistant_id: str,
    assistant_service: AssistantService = Depends(get_assistant_service),
    extension_assistant_service: ExtensionAssistantService = Depends(get_extension_assistant_service),
    mcp_assistant_service: McpAssistantService = Depends(get_mcp_assistant_service),
    _: bool = Depends(ensure_user_id),
):
    pass
