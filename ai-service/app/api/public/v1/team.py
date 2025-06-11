from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.api.deps import SessionDep
from app.core import logging
from app.core.enums import WorkflowType
from app.core.graph.build import generator
from app.db_models import Member, Team, Thread
from app.schemas.base import MessageResponse, ResponseWrapper
from app.schemas.team import ChatTeamRequest, CreateTeamRequest, TeamResponse, TeamsResponse, UpdateTeamRequest

router = APIRouter(prefix="/team", tags=["Team"])

logger = logging.get_logger(__name__)


async def async_validate_name_on_create(session: SessionDep, team_in: CreateTeamRequest) -> None:
    """Validate that team name is unique"""
    statement = select(Team).where(Team.name == team_in.name, Team.is_deleted.is_(False))
    result = await session.execute(statement)
    team = result.scalar_one_or_none()
    if team:
        raise HTTPException(status_code=400, detail="Team name already exists")


async def async_validate_name_on_update(session: SessionDep, team_in: UpdateTeamRequest, id_team: int) -> None:
    """Validate that team name is unique"""
    statement = select(Team).where(Team.name == team_in.name, Team.id != id_team, Team.is_deleted.is_(False))
    result = await session.execute(statement)
    team = result.scalar_one_or_none()
    if team:
        raise HTTPException(status_code=400, detail="Team name already exists")


@router.get("/", response_model=ResponseWrapper[TeamsResponse])
async def aread_teams(
    session: SessionDep,
    skip: int = 0,
    limit: int = 100,
    x_user_id=Header(None),
    x_user_role=Header(None),
) -> Any:
    """
    Retrieve teams
    """

    try:
        if x_user_role in ["admin", "super admin"]:
            count_statement = select(func.count()).select_from(Team).where(Team.is_deleted.is_(False))
            count_result = await session.execute(count_statement)
            count = count_result.scalar_one()

            statement = select(Team).where(Team.is_deleted.is_(False)).offset(skip).limit(limit).order_by(Team.id.desc())
            result = await session.execute(statement)
            teams = result.scalars().all()
        else:
            count_statement = select(func.count()).select_from(Team).where(Team.user_id == x_user_id, Team.is_deleted.is_(False))
            count_result = await session.execute(count_statement)
            count = count_result.scalar_one()

            statement = select(Team).where(Team.user_id == x_user_id, Team.is_deleted.is_(False)).offset(skip).limit(limit).order_by(Team.id.desc())
            result = await session.execute(statement)
            teams = result.scalars().all()

        converted_teams = [
            TeamResponse.model_validate(team)
            for team in teams
        ]
        return ResponseWrapper(status=200, data=TeamsResponse(teams=converted_teams, count=count)).to_response()

    except Exception as e:
        logger.error(f"Error retrieving teams: {e}", exc_info=True)
        return ResponseWrapper(status=500, message="Internal server error").to_response()


@router.get("/{team_id}", response_model=ResponseWrapper[TeamResponse])
async def aread_team(session: SessionDep, team_id: str, x_user_id=Header(None), x_user_role=Header(None)) -> Any:
    """
    Get team by ID.
    """
    try:
        statement = select(Team).where(Team.id == team_id, Team.is_deleted.is_(False))

        result = await session.execute(statement)
        team = result.scalar_one_or_none()

        if not team:
            return ResponseWrapper(status=404, message="Team not found").to_response()
        if x_user_role not in ["admin", "super admin"] and (team.user_id != x_user_id):
            return ResponseWrapper(status=403, message="Not enough permissions").to_response()

        data = TeamResponse.model_validate(team)
        return ResponseWrapper(status=200, data=data).to_response()
    except Exception as e:
        logger.error(f"Error retrieving team: {e}", exc_info=True)
        return ResponseWrapper(status=500, message="Internal server error").to_response()


@router.post("/", response_model=ResponseWrapper[TeamResponse])
async def acreate_team(
    *,
    session: SessionDep,
    team_in: CreateTeamRequest,
    x_user_id=Header(None),
    _: bool = Depends(async_validate_name_on_create),
) -> Any:
    """
    Create new team and it's team leader
    """
    try:
        team_dict = team_in.model_dump(exclude_unset=True)
        team_dict["user_id"] = x_user_id

        if team_dict.get("workflow_type") not in [
            "hierarchical",
            "sequential",
            "chatbot",
            "ragbot",
            "searchbot",
            "workflow",
        ]:
            return ResponseWrapper(
                status=400, message="Invalid workflow type. Supported types: hierarchical, sequential, chatbot, ragbot, workflow."
            ).to_response()

        team = Team(**team_dict)
        session.add(team)
        await session.commit()

        if team.workflow_type == WorkflowType.HIERARCHICAL:
            # Create team leader
            member = Member(
                # The leader name will be used as the team's name in the graph, so it has to be specific
                name=f"{team.name}Leader",
                type="root",
                role="Gather inputs from your team and answer the question.",
                position_x=0,
                position_y=0,
                team_id=team.id,
            )
        elif team.workflow_type == WorkflowType.SEQUENTIAL:
            # Create a freelancer head
            member = Member(
                name="Worker0",
                type="freelancer_root",
                role="Answer the user's question.",
                position_x=0,
                position_y=0,
                team_id=team.id,
            )
        elif team.workflow_type == WorkflowType.CHATBOT:
            # Create a freelancer head
            member = Member(
                name="ChatBot",
                type="chatbot",
                role="Answer the user's question.",
                position_x=0,
                position_y=0,
                team_id=team.id,
            )
        elif team.workflow_type == WorkflowType.RAGBOT:
            # Create a freelancer head
            member = Member(
                name="RagBot",
                type="ragbot",
                role="Answer the user's question use knowledge base.",
                position_x=0,
                position_y=0,
                team_id=team.id,
            )
        elif team.workflow_type == WorkflowType.SEARCHBOT:
            # Create a freelancer head
            member = Member(
                name="Workflow",
                type="workflow",
                role="Answer the user's question.",
                position_x=0,
                position_y=0,
                team_id=team.id,
            )
        else:
            return ResponseWrapper(
                status=400, message="Invalid workflow type. Supported types: hierarchical, sequential, chatbot, ragbot, workflow."
            ).to_response()
        session.add(member)
        await session.commit()

        data = TeamResponse.model_validate(team)
        return ResponseWrapper(status=200, data=data).to_response()
    except Exception as e:
        logger.error(f"Error creating team: {e}", exc_info=True)
        await session.rollback()
        return ResponseWrapper(status=500, message="Internal server error").to_response()


@router.put("/{team_id}", response_model=ResponseWrapper[TeamResponse])
async def aupdate_team(
    *,
    session: SessionDep,
    team_id: str,
    team_in: UpdateTeamRequest,
    x_user_id=Header(None),
    x_user_role=Header(None),
    _: bool = Depends(async_validate_name_on_update),
) -> Any:
    """
    Update a team.
    """
    try:
        statement = select(Team).where(Team.id == team_id, Team.is_deleted.is_(False))

        result = await session.execute(statement)
        team = result.scalar_one_or_none()

        if not team:
            return ResponseWrapper(status=404, message="Team not found").to_response()
        if x_user_role not in ["admin", "super admin"] and (team.user_id != x_user_id):
            return ResponseWrapper(status=403, message="Not enough permissions").to_response()

        update_dict = team_in.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            setattr(team, key, value)
        session.add(team)
        await session.commit()
        await session.refresh(team)

        data = TeamResponse.model_validate(team)
        return ResponseWrapper(status=200, data=data).to_response()
    except Exception as e:
        logger.error(f"Error updating team: {e}", exc_info=True)
        await session.rollback()
        return ResponseWrapper(status=500, message="Internal server error").to_response()


@router.delete("/{team_id}")
async def adelete_team(
    session: SessionDep,
    team_id: str,
    x_user_id=Header(None),
    x_user_role=Header(None),
) -> Any:
    """
    Delete a team.
    """
    try:
        statement = select(Team).where(Team.id == team_id, Team.is_deleted.is_(False))

        result = await session.execute(statement)
        team = result.scalar_one_or_none()

        if not team:
            return ResponseWrapper(status=404, message="Team not found").to_response()
        if x_user_role not in ["admin", "super admin"] and (team.user_id != x_user_id):
            return ResponseWrapper(status=403, message="Not enough permissions").to_response()

        await session.delete(team)
        await session.commit()

        data = MessageResponse(message="Team deleted successfully")
        return ResponseWrapper(status=200, data=data).to_response()

    except Exception as e:
        logger.error(f"Error deleting team: {e}", exc_info=True)
        await session.rollback()
        return ResponseWrapper(status=500, message="Internal server error").to_response()


@router.post("/{team_id}/stream/{thread_id}")
async def astream(
    session: SessionDep,
    team_id: str,
    thread_id: str,
    team_chat: ChatTeamRequest,
    x_user_id=Header(None),
    x_user_role=Header(None),
) -> Any:
    """
    Stream a response to a user's input.
    """
    try:
        # Get team and join members and skills
        statement = (
            select(Team)
            .options(selectinload(Team.assistant), selectinload(Team.graphs), selectinload(Team.subgraphs), selectinload(Team.members))
            .where(Team.id == team_id, Team.is_deleted.is_(False))
        )

        result = await session.execute(statement)
        team = result.scalar_one_or_none()

        if not team:
            return ResponseWrapper(status=404, message="Team not found").to_response()
        if x_user_role not in ["admin", "super admin"] and (team.user_id != x_user_id):
            return ResponseWrapper(
                status=403, message="Not enough permissions"
            ).to_response()

        # Check if thread belongs to the team
        statement = select(Thread).where(Thread.id == thread_id, Thread.is_deleted.is_(False))
        result = await session.execute(statement)
        thread = result.scalar_one_or_none()

        if not thread:
            return ResponseWrapper(status=404, message="Thread not found").to_response()

        # Ensure the thread is associated with the requested assistant
        if thread.assistant_id != team.assistant.id:
            return ResponseWrapper(status=400, message="Thread does not belong to this assistant").to_response()

        # Populate the skills and accessible uploads for each member
        # Load members for this team
        statement = (
            select(Member)
            .options(selectinload(Member.skills), selectinload(Member.uploads), selectinload(Member.team))
            .where(Member.team_id == team.id, Member.is_deleted.is_(False))
        )
        result = await session.execute(statement)
        members = result.scalars().all()
        for member in members:
            member.skills = member.skills
            member.uploads = member.uploads
        graphs = team.graphs
        for graph in graphs:
            graph.config = graph.config

        return StreamingResponse(
            generator(team, list(members), team_chat.messages, thread_id, team_chat.interrupt),
            media_type="text/event-stream",
        )
    except Exception as e:
        logger.error(f"Error streaming response: {e}", exc_info=True)
        return ResponseWrapper(status=500, message="Internal server error").to_response()
