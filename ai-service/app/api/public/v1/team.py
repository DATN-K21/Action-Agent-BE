from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Header
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select

from app.api.deps import SessionDep
from app.core import logging
from app.core.graph.build import generator
from app.db_models import Team, Member, Thread
from app.schemas.base import ResponseWrapper, MessageResponse
from app.schemas.team import CreateTeamRequest, UpdateTeamRequest, TeamsResponse, TeamResponse, ChatTeamRequest

router = APIRouter()

logger = logging.get_logger(__name__)


async def validate_name_on_create(session: SessionDep, team_in: CreateTeamRequest) -> None:
    """Validate that team name is unique"""
    statement = select(Team).where(
        Team.name == team_in.name,
        Team.is_deleted.is_(False)
    )
    team = session.exec(statement).first()
    if team:
        raise HTTPException(status_code=400, detail="Team name already exists")


async def validate_name_on_update(
        session: SessionDep, team_in: UpdateTeamRequest, id_team: int
) -> None:
    """Validate that team name is unique"""
    statement = select(Team).where(
        Team.name == team_in.name,
        Team.id != id_team,
        Team.is_deleted.is_(False)
    )
    team = session.exec(statement).first()
    if team:
        raise HTTPException(status_code=400, detail="Team name already exists")


@router.get("/", response_model=ResponseWrapper[TeamsResponse])
def read_teams(
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
        if x_user_role == "admin":
            count_statement = select(func.count()).select_from(Team).where(Team.is_deleted.is_(False))
            count = session.exec(count_statement).one()
            statement = select(Team).where(Team.is_deleted.is_(False)).offset(skip).limit(limit).order_by(
                Team.id.desc())
            teams = session.exec(statement).all()
        else:
            count_statement = (
                select(func.count())
                .select_from(Team)
                .where(
                    Team.user_id == x_user_id,
                    Team.is_deleted.is_(False)
                )
            )
            count = session.exec(count_statement).one()
            statement = (
                select(Team)
                .where(
                    Team.user_id == x_user_id,
                    Team.is_deleted.is_(False)
                )
                .offset(skip)
                .limit(limit)
                .order_by(Team.id.desc())
            )
            teams = session.exec(statement).all()

        converted_teams = [
            TeamResponse.model_validate(team)
            for team in teams
        ]
        return ResponseWrapper(status=200, data=TeamsResponse(teams=converted_teams, count=count)).to_response()
    except Exception as e:
        logger.error(f"Error retrieving teams: {e}", exc_info=True)
        return ResponseWrapper(status=500, message="Internal server error").to_response()


@router.get("/{id}", response_model=ResponseWrapper[TeamResponse])
def read_team(
        session: SessionDep,
        team_id: str,
        x_user_id=Header(None),
        x_user_role=Header(None)
) -> Any:
    """
    Get team by ID.
    """
    try:
        team = session.get(Team, team_id)
        if not team:
            return ResponseWrapper(status=404, message="Team not found").to_response()
        if not x_user_role and (team.user_id != x_user_id):
            return ResponseWrapper(status=403, message="Not enough permissions").to_response()

        data = TeamResponse.model_validate(team)
        return ResponseWrapper(status=200, data=data).to_response()
    except Exception as e:
        logger.error(f"Error retrieving team: {e}", exc_info=True)
        return ResponseWrapper(status=500, message="Internal server error").to_response()


@router.post("/", response_model=ResponseWrapper[TeamResponse])
def create_team(
        *,
        session: SessionDep,
        team_in: CreateTeamRequest,
        x_user_id=Header(None),
        x_user_role=Header(None),
        _: bool = Depends(validate_name_on_create),
) -> Any:
    """
    Create new team and it's team leader
    """
    try:
        team_dict = team_in.model_dump(exclude_unset=True)
        team_dict["user_id"] = x_user_id

        if team_dict.get("workflow") not in [
            "hierarchical",
            "sequential",
            "chatbot",
            "ragbot",
            "workflow",
        ]:
            return ResponseWrapper(
                status=400,
                message="Invalid workflow type. Supported types: hierarchical, sequential, chatbot, ragbot, workflow."
            ).to_response()

        team = Team(**team_dict)
        session.add(team)
        session.commit()

        if team.workflow == "hierarchical":
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
        elif team.workflow == "sequential":
            # Create a freelancer head
            member = Member(
                name="Worker0",
                type="freelancer_root",
                role="Answer the user's question.",
                position_x=0,
                position_y=0,
                team_id=team.id,
            )
        elif team.workflow == "chatbot":
            # Create a freelancer head
            member = Member(
                name="ChatBot",
                type="chatbot",
                role="Answer the user's question.",
                position_x=0,
                position_y=0,
                team_id=team.id,
            )
        elif team.workflow == "ragbot":
            # Create a freelancer head
            member = Member(
                name="RagBot",
                type="ragbot",
                role="Answer the user's question use knowledge base.",
                position_x=0,
                position_y=0,
                team_id=team.id,
            )
        elif team.workflow == "workflow":
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
                status=400,
                message="Invalid workflow type. Supported types: hierarchical, sequential, chatbot, ragbot, workflow."
            ).to_response()
        session.add(member)
        session.commit()

        data = TeamResponse.model_validate(team)
        return ResponseWrapper(status=200, data=data).to_response()
    except Exception as e:
        logger.error(f"Error creating team: {e}", exc_info=True)
        return ResponseWrapper(status=500, message="Internal server error").to_response()


@router.put("/{id}", response_model=ResponseWrapper[TeamResponse])
def update_team(
        *,
        session: SessionDep,
        team_id: str,
        team_in: UpdateTeamRequest,
        x_user_id=Header(None),
        x_user_role=Header(None),
        _: bool = Depends(validate_name_on_update),
) -> Any:
    """
    Update a team.
    """
    try:
        team = session.get(Team, team_id)
        if not team:
            return ResponseWrapper(status=404, message="Team not found").to_response()
        if x_user_role != "admin" and (team.owner_id != x_user_id):
            return ResponseWrapper(
                status=403, message="Not enough permissions"
            ).to_response()

        update_dict = team_in.model_dump(exclude_unset=True)
        team.sqlmodel_update(update_dict)
        session.add(team)
        session.commit()
        session.refresh(team)

        data = TeamResponse.model_validate(team)
        return ResponseWrapper(status=200, data=data).to_response()
    except Exception as e:
        logger.error(f"Error updating team: {e}", exc_info=True)
        return ResponseWrapper(status=500, message="Internal server error").to_response()


@router.delete("/{id}")
def delete_team(
        session: SessionDep,
        team_id: str,
        x_user_id=Header(None),
        x_user_role=Header(None),
) -> Any:
    """
    Delete a team.
    """
    try:
        team = session.get(Team, team_id)
        if not team:
            return ResponseWrapper(status=404, message="Team not found").to_response()
        if x_user_role != "admin" and (team.user_id != x_user_id):
            return ResponseWrapper(
                status=403, message="Not enough permissions"
            ).to_response()
        session.delete(team)
        session.commit()

        data = MessageResponse(message="Team deleted successfully")
        return ResponseWrapper(status=200, data=data).to_response()
    except Exception as e:
        logger.error(f"Error deleting team: {e}", exc_info=True)
        return ResponseWrapper(status=500, message="Internal server error").to_response()


@router.post("/{id}/stream/{thread_id}")
async def stream(
        session: SessionDep,
        team_id: int,
        thread_id: str,
        team_chat: ChatTeamRequest,
        x_user_id=Header(None),
        x_user_role=Header(None),
) -> StreamingResponse | Any:
    """
    Stream a response to a user's input.
    """
    try:
        # Get team and join members and skills
        team = session.get(Team, team_id)
        if not team:
            return ResponseWrapper(status=404, message="Team not found").to_response()
        if x_user_role != "admin" and (team.user_id != x_user_id):
            return ResponseWrapper(
                status=403, message="Not enough permissions"
            ).to_response()

        # Check if thread belongs to the team
        thread = session.get(Thread, thread_id)
        if not thread:
            return ResponseWrapper(status=404, message="Thread not found").to_response()
        if thread.team_id != team_id:
            return ResponseWrapper(
                status=400, message="Thread does not belong to the team"
            ).to_response()

        # Populate the skills and accessible uploads for each member
        members = team.members
        for member in members:
            member.skills = member.skills
            member.uploads = member.uploads
        graphs = team.graphs
        for graph in graphs:
            graph.config = graph.config
        return StreamingResponse(
            generator(team, members, team_chat.messages, thread_id, team_chat.interrupt),
            media_type="text/event-stream",
        )
    except Exception as e:
        logger.error(f"Error streaming response: {e}", exc_info=True)
        return ResponseWrapper(status=500, message="Internal server error").to_response()
