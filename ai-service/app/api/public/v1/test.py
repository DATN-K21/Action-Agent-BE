from fastapi import APIRouter
from langchain.schema import AIMessage, HumanMessage
from langchain_core.runnables.config import RunnableConfig
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.deps import SessionDep
from app.core.enums import ChatMessageType
from app.core.graph.build import acreate_hierarchical_graph, convert_hierarchical_team_to_dict
from app.core.models import ChatMessage
from app.core.settings import env_settings
from app.db_models.member import Member
from app.db_models.team import Team
from app.db_models.thread import Thread
from app.memory.checkpoint import get_checkpointer
from app.schemas.base import ResponseWrapper

router = APIRouter(prefix="", tags=["Tests"], responses={})


@router.get("/ping", summary="Endpoint to check server.", response_model=dict)
async def check():
    return {"message": "pong"}


@router.get("/error", summary="Endpoint to check error handlers.", response_model=ResponseWrapper)
async def error():
    raise Exception("Test exception")


@router.post("/test-hierachical", summary="Endpont to test multi-agent")
async def test_hierarchical(
    session: SessionDep,
    team_id: str | None = None,
    x_user_id: str | None = None,
    thread_id: str | None = None,
    x_user_role: str | None = None,
):
    team_id = "e674125a-618f-4a1b-8a9c-13a61f656434" if team_id is None else team_id
    x_user_id = "d51ba2c3-5d84-41c2-9a87-0bf5b5d885b8" if x_user_id is None else x_user_id
    thread_id = "75dc0c73-6ba1-4878-b5d3-fe3947256ebc" if thread_id is None else thread_id
    x_user_role = "user" if x_user_role is None else x_user_role

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
        return ResponseWrapper(status=403, message="Not enough permissions").to_response()

    # Check if thread belongs to the team
    statement = select(Thread).where(Thread.id == thread_id, Thread.is_deleted.is_(False))
    result = await session.execute(statement)
    thread = result.scalar_one_or_none()

    if not thread:
        return ResponseWrapper(status=404, message="Thread not found").to_response()

    # Ensure the thread is associated with the requested assistant
    if thread.assistant_id != team.assistant.id:
        return ResponseWrapper(status=400, message="Thread does not belong to this assistant").to_response()

    # Populate the skills and accessible uploads for each member        # Load members for this team
    statement = (
        select(Member)
        .options(selectinload(Member.skills), selectinload(Member.uploads), selectinload(Member.team))
        .where(Member.team_id == team.id, Member.is_deleted.is_(False))
    )
    result = await session.execute(statement)
    members = list(result.scalars().all())
    for member in members:
        member.skills = member.skills
        member.uploads = member.uploads
    graphs = team.graphs
    for graph in graphs:
        graph.config = graph.config

    messages = [ChatMessage(type=ChatMessageType.human, content="Give me code of c++")]

    formatted_messages = [
        (
            HumanMessage(
                content=(
                    [
                        {"type": "text", "text": message.content},
                        {"type": "image_url", "image_url": {"url": message.imgdata}},
                    ]
                    if message.imgdata
                    else message.content
                ),
                name="user",
            )
            if message.type == "human"
            else AIMessage(content=message.content)
        )
        for message in messages
    ]

    teams = convert_hierarchical_team_to_dict(members)
    team_leader = list(teams.keys())[0]
    checkpointer = await get_checkpointer()
    root = await acreate_hierarchical_graph(teams, leader_name=team_leader, checkpointer=checkpointer)
    state = {
        "history": formatted_messages,
        "messages": [],
        "team": teams[team_leader],
        "main_task": formatted_messages,
        "all_messages": formatted_messages,
    }

    config: RunnableConfig = {
        "configurable": {"thread_id": thread_id},
        "recursion_limit": env_settings.RECURSION_LIMIT,
    }

    result = await root.ainvoke(state, config=config)
    if not result:
        return ResponseWrapper(status=500, message="Failed to create hierarchical graph").to_response()

    return result
