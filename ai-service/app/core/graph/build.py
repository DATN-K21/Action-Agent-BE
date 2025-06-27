import asyncio
from collections import defaultdict, deque
from collections.abc import AsyncGenerator, Hashable, Mapping
from functools import partial
from typing import Any
from uuid import uuid4

from langchain_core.messages import AIMessage, AnyMessage, HumanMessage, ToolMessage
from langchain_core.runnables import RunnableLambda
from langchain_core.runnables.config import RunnableConfig
from langchain_core.tools import BaseTool
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import END, StateGraph
from langgraph.graph.graph import CompiledGraph
from langgraph.prebuilt import ToolNode
from langgraph.types import Command

from app.core.enums import InterruptDecision, InterruptType, WorkflowType
from app.core.graph.members import (
    GraphLeader,
    GraphMember,
    GraphTeam,
    GraphTeamState,
    LeaderNode,
    SequentialWorkerNode,
    SummariserNode,
    WorkerNode,
)
from app.core.graph.messages import ChatResponse, event_to_response
from app.core.models import ChatMessage, Interrupt
from app.core.settings import env_settings
from app.core.state import GraphSkill, GraphUpload
from app.core.workflow.build_workflow import initialize_graph
from app.core.workflow.node.human_node import HumanNode
from app.db_models import Member, Team
from app.memory.checkpoint import get_checkpointer


def convert_hierarchical_team_to_dict(members: list[Member]
                                      ) -> dict[str, GraphTeam]:
    """
    Converts a team and its members into a dictionary representation.

    Args:
        members (list[Member]): A list of member models belonging to the team.

    Returns:
        dict: A dictionary containing the team's information, with member details.

    Raises:
        ValueError: If the root leader is not found in the team.

    Notes:
        This function assumes that each team has a single root leader.
    """
    teams: dict[str, GraphTeam] = {}

    in_counts: defaultdict[str, int] = defaultdict(int)
    out_counts: defaultdict[str, list[str]] = defaultdict(list[str])
    members_lookup: dict[str, Member] = {}

    for member in members:
        assert member.id is not None, "member.id is unexpectedly None"
        member_id = member.id
        if member.source is not None:
            source_id = member.source
            in_counts[member_id] += 1
            out_counts[source_id].append(member_id)
        else:
            in_counts[member_id] = 0
        members_lookup[member_id] = member

    queue: deque[str] = deque()

    for member_id in in_counts:
        if in_counts[member_id] == 0:
            queue.append(member_id)

    while queue:
        member_id = queue.popleft()
        member = members_lookup[member_id]
        if member.type == "root" or member.type == "leader":
            leader_name = member.name
            # Create the team definitions
            teams[leader_name] = GraphTeam(
                name=leader_name,
                role=member.role,
                backstory=member.backstory or "",
                members={},
                provider=member.provider,
                model=member.model,
                temperature=member.temperature,
            )
        # If member is not root team leader, add as a member
        if member.type != "root" and member.source is not None:
            member_name = member.name
            source_id = member.source
            leader = members_lookup[source_id]
            leader_name = leader.name
            if member.type == "worker":
                tools: list[GraphSkill | GraphUpload]
                tools = [
                    GraphSkill(
                        skill_id=skill.id,
                        member_id=member.id,
                        display_name=skill.display_name,
                        user_id=member.team.user_id,
                        name=skill.name,
                        strategy=skill.strategy,
                        definition=skill.tool_definition,
                    )
                    for skill in member.skills
                ]
                tools += [
                    GraphUpload(
                        name=upload.name,
                        description=upload.description,
                        user_id=upload.user_id,
                        upload_id=upload.id,
                    )
                    for upload in member.uploads
                    if upload.user_id is not None
                ]
                teams[leader_name].members[member_name] = GraphMember(
                    name=member_name,
                    backstory=member.backstory or "",
                    role=member.role,
                    tools=tools,
                    provider=member.provider,
                    model=member.model,
                    temperature=member.temperature,
                    interrupt=member.interrupt if member.interrupt else False,
                )
            elif member.type == "leader":
                teams[leader_name].members[member_name] = GraphLeader(
                    name=member_name,
                    backstory=member.backstory or "",
                    role=member.role,
                    provider=member.provider,
                    model=member.model,
                    temperature=member.temperature,
                )
        for nei_id in out_counts[member_id]:
            in_counts[nei_id] -= 1
            if in_counts[nei_id] == 0:
                queue.append(nei_id)

    return teams


def convert_sequential_team_to_dict(members: list[Member]) -> dict[str, GraphMember]:
    team_dict: dict[str, GraphMember] = {}

    in_counts: defaultdict[str, int] = defaultdict(int)
    out_counts: defaultdict[str, list[str]] = defaultdict(list[str])
    members_lookup: dict[str, Member] = {}
    for member in members:
        assert member.id is not None, "member.id is unexpectedly None"
        member_id = member.id
        if member.source is not None:
            source_id = member.source
            in_counts[member_id] += 1
            out_counts[source_id].append(member_id)
        else:
            in_counts[member_id] = 0
        members_lookup[member_id] = member

    queue: deque[str] = deque()

    for member_id in in_counts:
        if in_counts[member_id] == 0:
            queue.append(member_id)

    while queue:
        member_id = queue.popleft()
        member = members_lookup[member_id]
        tools: list[GraphSkill | GraphUpload]
        tools = [
            GraphSkill(
                skill_id=skill.id,
                member_id=member.id,
                display_name=skill.display_name,
                user_id=member.team.user_id,
                name=skill.name,
                strategy=skill.strategy,
                definition=skill.tool_definition,
            )
            for skill in member.skills
        ]
        tools += [
            GraphUpload(
                name=upload.name,
                description=upload.description,
                user_id=upload.user_id,
                upload_id=upload.id,
            )
            for upload in member.uploads
            if upload.user_id is not None
        ]
        graph_member = GraphMember(
            name=member.name,
            backstory=member.backstory or "",
            role=member.role,
            tools=tools,
            provider=member.provider,
            model=member.model,
            temperature=member.temperature,
            interrupt=member.interrupt if member.interrupt else False,
        )
        team_dict[graph_member.name] = graph_member
        for nei_id in out_counts[member_id]:
            in_counts[nei_id] -= 1
            if in_counts[nei_id] == 0:
                queue.append(nei_id)
    return team_dict


def convert_chatbot_ragbot_searchbot_team_to_dict(members: list[Member], workflow_type: WorkflowType) -> Mapping[str, GraphMember]:
    team_dict: dict[str, GraphMember] = {}

    if len(members) != 1:
        raise ValueError("Team must contain exactly one member.")

    member = members[0]
    assert member.id is not None, "member.id is unexpectedly None"
    tools: list[GraphSkill | GraphUpload]
    if workflow_type == WorkflowType.RAGBOT:
        tools = [
            GraphUpload(
                name=upload.name,
                description=upload.description,
                user_id=upload.user_id,
                upload_id=upload.id,
            )
            for upload in member.uploads
            if upload.user_id is not None
        ]
    elif workflow_type == WorkflowType.CHATBOT:
        tools = [
            GraphUpload(
                name=upload.name,
                description=upload.description,
                user_id=upload.user_id,
                upload_id=upload.id,
            )
            for upload in member.uploads
            if upload.user_id is not None
        ] + [
            GraphSkill(
                skill_id=skill.id,
                member_id=member.id,
                display_name=skill.display_name,
                user_id=member.team.user_id,
                name=skill.name,
                strategy=skill.strategy,
                definition=skill.tool_definition,
            )
            for skill in member.skills
        ]
    elif workflow_type == WorkflowType.SEARCHBOT:
        tools = [
            GraphSkill(
                skill_id=skill.id,
                member_id=member.id,
                display_name=skill.display_name,
                user_id=member.team.user_id,
                name=skill.name,
                strategy=skill.strategy,
                definition=skill.tool_definition,
            )
            for skill in member.skills
        ]

    else:
        raise ValueError("Invalid workflow_type. Expected 'ragbot', 'searchbot' or 'chatbot'.")

    graph_member = GraphMember(
        name=member.name,
        backstory=member.backstory or "",
        role=member.role,
        tools=tools,
        provider=member.provider,
        model=member.model,
        temperature=member.temperature,
        interrupt=member.interrupt if member.interrupt else False,
    )
    team_dict[graph_member.name] = graph_member

    return team_dict


def router(state: GraphTeamState) -> str:
    return state["next"]


def enter_chain(state: GraphTeamState, team: GraphTeam) -> dict[str, Any]:
    """
    Initialize the sub-graph state.
    This makes it so that the states of each graph don't get intermixed.
    """
    task = state["task"]
    results = {
        "main_task": task,
        "team": team,
        "team_members": team.members,
    }
    return results


def exit_chain(state: GraphTeamState) -> dict[str, list[AnyMessage]]:
    """
    Pass the final response back to the top-level graph's state.
    """
    answer = state["history"][-1]
    return {"history": [answer], "all_messages": state["all_messages"]}


def should_continue(state: GraphTeamState) -> str:
    """Determine if graph should go to tool node or not. For tool calling agents."""
    messages: list[AnyMessage] = state["messages"]
    if messages and isinstance(messages[-1], AIMessage) and messages[-1].tool_calls:
        # Prioritise asking a human if any tool call requests it
        if any(tc.get("name") == "ask-human" for tc in messages[-1].tool_calls):
            return "call_human"
        # Otherwise proceed with the tool calls
        return "call_tools"
    else:
        return "continue"


def create_tools_condition(
        current_member_name: str,
        next_member_name: str,
        tools: list[GraphSkill | GraphUpload],
) -> dict[Hashable, str]:
    """Creates the mapping for conditional edges
    The tool node must be in format: '{current_member_name}-tools'

    Args:
        current_member_name (str): The name of the member that is calling the tool
        next_member_name (str): The name of the next member after the current member processes the tool response. Can be END.
        tools: List of tools that the agent has.
    """
    mapping: dict[Hashable, str] = {
        # Else continue to the next node
        "continue": next_member_name,
    }

    for tool in tools:
        if tool.name == "ask-human":
            mapping["call_human"] = f"{current_member_name}-ask-human-tool"
        else:
            mapping["call_tools"] = f"{current_member_name}-tools"
    return mapping


def create_tools_condition_with_human_review(
    current_member_name: str,
    next_member_name: str,
    tools: list[GraphSkill | GraphUpload],
) -> dict[Hashable, str]:
    """Creates the mapping for conditional edges with human review capabilities
    The tool review node must be in format: '{current_member_name}-tool-review'
    The tool node must be in format: '{current_member_name}-tools'

    Args:
        current_member_name (str): The name of the member that is calling the tool
        next_member_name (str): The name of the next member after tool processing. Can be END.
        tools: List of tools that the agent has.
    """
    mapping: dict[Hashable, str] = {
        # Else continue to the next node
        "continue": next_member_name,
    }

    for tool in tools:
        if tool.name == "ask-human":
            mapping["call_human"] = f"{current_member_name}-ask-human-tool"
        else:
            # Route to human review node for tool approval
            mapping["call_tools"] = f"{current_member_name}-tool-review"
    return mapping


def ask_human_node(state: GraphTeamState) -> None:
    """Dummy node for ask human tool"""


def create_human_review_node(member_name: str, interaction_type: str, routes: dict) -> HumanNode:
    """Create a HumanNode for tool/output review with proper routing"""

    return HumanNode(
        node_id=f"{member_name}-human-review",
        routes=routes,
        title=f"Review for {member_name}",
        interaction_type=getattr(InterruptType, interaction_type.upper()),
    )


def create_human_tool_review_node(member_name: str) -> HumanNode:
    """Create a HumanNode specifically for tool call review"""
    routes = {
        "approved": f"{member_name}-tools",
        "rejected": member_name,
        "update": f"{member_name}-tools",
    }

    return create_human_review_node(member_name, "tool_review", routes)


def create_human_output_review_node(member_name: str) -> HumanNode:
    """Create a HumanNode specifically for output review"""
    routes = {
        "approved": member_name,  # Continue to member after approval
        "rejected": member_name,  # Go back to member after rejection with feedback
        "update": f"{member_name}-tools",  # Update tool parameters and execute
        "review": member_name,  # Go back to member for revision
        "continue": member_name,  # Continue with additional context
    }
    return create_human_review_node(member_name, "output_review", routes)


async def acreate_hierarchical_graph(
    teams: dict[str, GraphTeam],
    leader_name: str,
    checkpointer: BaseCheckpointSaver | None = None,
) -> CompiledGraph:
    """Create the team's graph with manual interrupt capabilities using HumanNode.

    This function creates a graph representation of the given teams with enhanced interrupt capabilities.
    Instead of using interrupt_before, it uses HumanNode to provide manual interrupts with full control
    including approved, rejected, update, review, and edit options.

    Args:
        teams (dict[str, dict[str, str | dict[str, Member | Leader]]]): A dictionary where each key is a team leader's name and the value is
            another dictionary containing the team's members.
        leader_name (str): The name of the root leader in the team.
        checkpointer (BaseCheckpointSaver | None): The checkpoint saver to use.

    Returns:
        dict: A dictionary representing the graph of teams.
    """
    build = StateGraph(GraphTeamState)

    # Add the start and end node
    build.add_node(
        leader_name,
        RunnableLambda(
            LeaderNode(
                provider=teams[leader_name].provider,
                model=teams[leader_name].model,
                temperature=teams[leader_name].temperature,
            ).delegate  # type: ignore[arg-type]
        ),
    )
    build.add_node(
        "final-answer",
        RunnableLambda(
            SummariserNode(
                provider=env_settings.OPENAI_PROVIDER,
                model=env_settings.LLM_BASIC_MODEL,
                temperature=env_settings.BASIC_MODEL_TEMPERATURE,
            ).summarise  # type: ignore[arg-type]
        ),
    )

    members = teams[leader_name].members
    for name, member in members.items():
        if isinstance(member, GraphMember):
            build.add_node(
                name,
                RunnableLambda(
                    WorkerNode(
                        provider=member.provider,
                        model=member.model,
                        temperature=member.temperature,
                    ).work
                ),
            )
            if member.tools:
                normal_tools: list[BaseTool] = []

                for tool in member.tools:
                    if tool.name == "ask-human":
                        # Handling Ask-Human tool with HumanNode for context input
                        human_context_node = create_human_review_node(name, "context_input", {"continue": name})
                        build.add_node(f"{name}-ask-human-tool", human_context_node.work)
                        build.add_edge(f"{name}-ask-human-tool", name)
                    else:
                        tool_object = await tool.aget_tool()
                        normal_tools.append(tool_object)

                if normal_tools:
                    # Add node for normal tools
                    build.add_node(f"{name}-tools", ToolNode(normal_tools))

                    # Add HumanNode for tool review if member.interrupt is True
                    if member.interrupt:
                        human_tool_review_node = create_human_tool_review_node(name)
                        build.add_node(f"{name}-tool-review", human_tool_review_node.work)
                        # Route: member -> tool-review -> tools -> member
                        build.add_edge(f"{name}-tool-review", f"{name}-tools")
                        build.add_edge(f"{name}-tools", name)
                    else:
                        # Direct connection without review
                        build.add_edge(f"{name}-tools", name)

        elif isinstance(member, GraphLeader):
            subgraph = await acreate_hierarchical_graph(teams, leader_name=name, checkpointer=checkpointer)
            enter = partial(enter_chain, team=teams[name])
            build.add_node(
                name,
                enter | subgraph | exit_chain,
            )
        else:
            continue

        # Create conditional edges with enhanced routing for HumanNode interrupts
        if isinstance(member, GraphMember) and member.tools:
            if member.interrupt:
                # Route to human review node first, then to tools
                build.add_conditional_edges(
                    name,
                    should_continue,
                    create_tools_condition_with_human_review(name, leader_name, member.tools),
                )
            else:
                # Direct routing without human review
                build.add_conditional_edges(
                    name,
                    should_continue,
                    create_tools_condition(name, leader_name, member.tools),
                )
        else:
            build.add_edge(name, leader_name)

    conditional_mapping: dict[Hashable, str] = {v: v for v in members}
    conditional_mapping["FINISH"] = "final-answer"
    build.add_conditional_edges(leader_name, router, conditional_mapping)

    build.set_entry_point(leader_name)
    build.set_finish_point("final-answer")
    # Note: No interrupt_before needed since we use HumanNode with interrupt() function
    graph = build.compile(checkpointer=checkpointer, debug=env_settings.DEBUG_AGENT)

    return graph


async def acreate_sequential_graph(team: Mapping[str, GraphMember], checkpointer: BaseCheckpointSaver) -> CompiledGraph:
    """
    Creates a sequential graph from a list of team members with manual interrupt capabilities.

    The graph will have a node for each team member, with edges connecting the nodes in the order the members are provided.
    Instead of using interrupt_before, it uses HumanNode to provide manual interrupts with full control
    including approved, rejected, update, review, and edit options.

    Args:
        team (List[Member]): A list of team members.
        checkpointer (BaseCheckpointSaver): A checkpointer object.

    Returns:
        CompiledGraph: The compiled graph representing the sequential workflow.
    """
    graph = StateGraph(GraphTeamState)
    members = list(team.values())

    for i, member in enumerate(members):
        graph.add_node(
            member.name,
            RunnableLambda(
                SequentialWorkerNode(
                    provider=member.provider,
                    model=member.model,
                    temperature=member.temperature,
                ).work
            ),
        )
        if member.tools:
            normal_tools: list[BaseTool] = []

            for tool in member.tools:
                if tool.name == "ask-human":
                    # Handling Ask-Human tool with HumanNode for context input
                    human_context_node = create_human_review_node(member.name, "context_input", {"continue": member.name})
                    graph.add_node(f"{member.name}-ask-human-tool", human_context_node.work)
                    graph.add_edge(f"{member.name}-ask-human-tool", member.name)
                else:
                    tool_object = await tool.aget_tool()
                    normal_tools.append(tool_object)

            if normal_tools:
                # Add node for normal tools
                graph.add_node(f"{member.name}-tools", ToolNode(normal_tools))

                # Add HumanNode for tool review if member.interrupt is True
                if member.interrupt:
                    human_tool_review_node = create_human_tool_review_node(member.name)
                    graph.add_node(f"{member.name}-tool-review", human_tool_review_node.work)
                    # Route: member -> tool-review -> tools -> member
                    graph.add_edge(f"{member.name}-tool-review", f"{member.name}-tools")
                    graph.add_edge(f"{member.name}-tools", member.name)
                else:
                    # Direct connection without review
                    graph.add_edge(f"{member.name}-tools", member.name)

        if i > 0:
            previous_member = members[i - 1]
            if previous_member.tools:
                if previous_member.interrupt:
                    # Route with human review
                    graph.add_conditional_edges(
                        previous_member.name,
                        should_continue,
                        create_tools_condition_with_human_review(previous_member.name, member.name, previous_member.tools),
                    )
                else:
                    # Direct routing without human review
                    graph.add_conditional_edges(
                        previous_member.name,
                        should_continue,
                        create_tools_condition(previous_member.name, member.name, previous_member.tools),
                    )
            else:
                graph.add_edge(previous_member.name, member.name)

    # Handle the final member's tools
    final_member = members[-1]
    if final_member.tools:
        if final_member.interrupt:
            # Route with human review
            graph.add_conditional_edges(
                final_member.name,
                should_continue,
                create_tools_condition_with_human_review(final_member.name, END, final_member.tools),
            )
        else:
            # Direct routing without human review
            graph.add_conditional_edges(
                final_member.name,
                should_continue,
                create_tools_condition(final_member.name, END, final_member.tools),
            )
    else:
        graph.add_edge(final_member.name, END)

    graph.set_entry_point(members[0].name)
    # Note: No interrupt_before needed since we use HumanNode with interrupt() function
    graph = graph.compile(
        checkpointer=checkpointer,
    )

    return graph


async def acreate_chatbot_ragbot_searhbot_graph(team: Mapping[str, GraphMember], checkpointer: BaseCheckpointSaver) -> CompiledGraph:
    """
    Creates a simple chatbot graph for a single team member with manual interrupt capabilities.

    Instead of using interrupt_before, it uses HumanNode to provide manual interrupts with full control
    including approved, rejected, update, review, and edit options.

    Args:
        team (Mapping[str, GraphMember]): A mapping of a single team member.
        checkpointer (BaseCheckpointSaver): A checkpointer object.
    Returns:
        CompiledGraph: The compiled graph representing the sequential workflow.
    """
    if len(team) > 1:
        raise ValueError("Team can only have one GraphMember.")

    member = next(iter(team.values()))
    graph = StateGraph(GraphTeamState)

    graph.add_node(
        member.name,
        RunnableLambda(
            SequentialWorkerNode(
                provider=member.provider,
                model=member.model,
                temperature=member.temperature,
            ).work
        ),
    )
    # if member can call tools, then add tool node
    if len(member.tools) >= 1:
        normal_tools: list[BaseTool] = []

        for tool in member.tools:
            if tool.name == "ask-human":
                # Handling Ask-Human tool with HumanNode for context input
                human_context_node = create_human_review_node(member.name, "context_input", {"continue": member.name})
                graph.add_node(f"{member.name}-ask-human-tool", human_context_node.work)
                graph.add_edge(f"{member.name}-ask-human-tool", member.name)
            else:
                tool_object = await tool.aget_tool()
                normal_tools.append(tool_object)

        if normal_tools:
            # Add node for normal tools
            graph.add_node(f"{member.name}-tools", ToolNode(normal_tools))

            # Add HumanNode for tool review if member.interrupt is True
            if member.interrupt:
                human_tool_review_node = create_human_tool_review_node(member.name)
                graph.add_node(f"{member.name}-tool-review", human_tool_review_node.work)
                # Route: member -> tool-review -> tools -> member
                graph.add_edge(f"{member.name}-tool-review", f"{member.name}-tools")
                graph.add_edge(f"{member.name}-tools", member.name)
            else:
                # Direct connection without review
                graph.add_edge(f"{member.name}-tools", member.name)

    if len(member.tools) >= 1:
        if member.interrupt:
            # Route with human review
            graph.add_conditional_edges(
                member.name,
                should_continue,
                create_tools_condition_with_human_review(member.name, END, member.tools),
            )
        else:
            # Direct routing without human review
            graph.add_conditional_edges(
                member.name,
                should_continue,
                create_tools_condition(member.name, END, member.tools),
            )
    else:
        graph.add_edge(member.name, END)

    graph.set_entry_point(member.name)
    # Note: No interrupt_before needed since we use HumanNode with interrupt() function
    return graph.compile(checkpointer=checkpointer)


def convert_messages_and_tasks_to_dict(data: Any) -> Any:
    if isinstance(data, dict):
        new_data = {}
        for key, value in data.items():
            if key == "messages" or key == "history" or key == "task":
                if isinstance(value, list):
                    new_data[key] = [message.dict() for message in value]
                else:
                    new_data[key] = value
            else:
                new_data[key] = convert_messages_and_tasks_to_dict(value)
        return new_data
    elif isinstance(data, list):
        return [convert_messages_and_tasks_to_dict(item) for item in data]
    else:
        return data


async def generator(
    team: Team,
    members: list[Member],
    messages: list[ChatMessage],
    thread_id: str,
    interrupt: Interrupt | None = None,
    user_id: str | None = None,
) -> AsyncGenerator[Any, Any]:
    """Create the graph and stream responses as JSON."""

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

    try:
        checkpointer = await get_checkpointer()
        state: Any = None
        graph_config: dict[str, Any] = {}
        response: Any = None
        interrupt_name = None
        if team.workflow_type == WorkflowType.HIERARCHICAL:
            teams = convert_hierarchical_team_to_dict(members)
            team_leader = list(teams.keys())[0]
            root = await acreate_hierarchical_graph(teams, leader_name=team_leader, checkpointer=checkpointer)
            state = {
                "history": formatted_messages,
                "messages": [],
                "team": teams[team_leader],
                "main_task": formatted_messages,
                "all_messages": formatted_messages,
            }

        elif team.workflow_type == WorkflowType.SEQUENTIAL:
            member_dict = convert_sequential_team_to_dict(members)
            root = await acreate_sequential_graph(member_dict, checkpointer)
            first_member = list(member_dict.values())[0]
            state = {
                "history": formatted_messages,
                "team": GraphTeam(
                    name=first_member.name,
                    role=first_member.role,
                    backstory=first_member.backstory,
                    members=member_dict,  # type: ignore[arg-type]
                    provider=first_member.provider,
                    model=first_member.model,
                    temperature=first_member.temperature,
                ),
                "messages": [],
                "next": first_member.name,
                "all_messages": formatted_messages,
            }

        elif team.workflow_type == WorkflowType.RAGBOT:
            member_dict = convert_chatbot_ragbot_searchbot_team_to_dict(members, workflow_type=team.workflow_type)
            root = await acreate_chatbot_ragbot_searhbot_graph(member_dict, checkpointer)
            first_member = list(member_dict.values())[0]
            state = {
                "history": formatted_messages,
                "team": GraphTeam(
                    name=first_member.name,
                    role=first_member.role,
                    backstory=first_member.backstory,
                    members=member_dict,  # type: ignore[arg-type]
                    provider=first_member.provider,
                    model=first_member.model,
                    temperature=first_member.temperature,
                ),
                "messages": [],
                "next": first_member.name,
                "all_messages": formatted_messages,
            }
        elif team.workflow_type == WorkflowType.CHATBOT:
            member_dict = convert_chatbot_ragbot_searchbot_team_to_dict(members, workflow_type=team.workflow_type)
            root = await acreate_chatbot_ragbot_searhbot_graph(member_dict, checkpointer)
            first_member = list(member_dict.values())[0]
            state = {
                "history": formatted_messages,
                "team": GraphTeam(
                    name=first_member.name,
                    role=first_member.role,
                    backstory=first_member.backstory,
                    members=member_dict,  # type: ignore[arg-type]
                    provider=first_member.provider,
                    model=first_member.model,
                    temperature=first_member.temperature,
                ),
                "messages": [],
                "next": first_member.name,
                "all_messages": formatted_messages,
            }
        elif team.workflow_type == WorkflowType.SEARCHBOT:
            member_dict = convert_chatbot_ragbot_searchbot_team_to_dict(members, workflow_type=team.workflow_type)
            root = await acreate_chatbot_ragbot_searhbot_graph(member_dict, checkpointer)
            first_member = list(member_dict.values())[0]
            state = {
                "history": formatted_messages,
                "team": GraphTeam(
                    name=first_member.name,
                    role=first_member.role,
                    backstory=first_member.backstory,
                    members=member_dict,  # type: ignore[arg-type]
                    provider=first_member.provider,
                    model=first_member.model,
                    temperature=first_member.temperature,
                ),
                "messages": [],
                "next": first_member.name,
                "all_messages": formatted_messages,
            }
        elif team.workflow_type == WorkflowType.WORKFLOW:

            graph_config = team.graphs[0].config

            root = initialize_graph(
                graph_config, checkpointer, save_graph_img=False
            )

            state = {
                "history": formatted_messages,
                "messages": [],
                "all_messages": formatted_messages,
            }
        else:
            raise ValueError("Unsupported graph type ")

        config: RunnableConfig = {
            "configurable": {"thread_id": thread_id},
            "recursion_limit": env_settings.RECURSION_LIMIT,
        }

        # Handle interrupt logic by overriding state
        if interrupt and interrupt.interaction_type is None:
            if interrupt.decision == InterruptDecision.APPROVED:
                state = None
            elif interrupt.decision == InterruptDecision.REJECTED:
                current_values = await root.aget_state(config)
                messages = current_values.values["messages"]
                if messages and isinstance(messages[-1], AIMessage):
                    tool_calls = messages[-1].tool_calls
                    state = {
                        "messages": [
                            ToolMessage(
                                tool_call_id=tool_call["id"],
                                content="Rejected by user. Continue assisting.",
                            )
                            for tool_call in tool_calls
                        ]
                    }
                    if interrupt.tool_message:
                        state["messages"].append(
                            HumanMessage(
                                content=interrupt.tool_message,
                                name="user",
                                id=str(uuid4()),
                            )
                        )
            elif interrupt.decision == InterruptDecision.REPLIED:
                current_values = await root.aget_state(config)
                messages = current_values.values["messages"]
                if (
                        messages
                        and isinstance(messages[-1], AIMessage)
                        and interrupt.tool_message
                ):
                    tool_calls = messages[-1].tool_calls
                    state = {
                        "messages": [
                            ToolMessage(
                                tool_call_id=tool_call["id"],
                                content=interrupt.tool_message,
                                name="ask-human",
                            )
                            for tool_call in tool_calls
                            if tool_call["name"] == "ask-human"
                        ]
                    }
        elif interrupt and interrupt.interaction_type is not None:
            # Enhanced interrupt handling for both custom workflows and traditional workflows with HumanNode
            if interrupt.interaction_type == "tool_review":
                if interrupt.decision == InterruptDecision.APPROVED:
                    # Tool call approved, continue execution
                    state = Command(resume={"action": "approved"})

                elif interrupt.decision == InterruptDecision.REJECTED:
                    # Tool call rejected, add rejection message
                    reject_message = (
                        interrupt.tool_message if interrupt.tool_message else None
                    )
                    state = Command(
                        resume={"action": "rejected", "data": reject_message}
                    )

                elif interrupt.decision == InterruptDecision.UPDATE:
                    # Update tool call parameters
                    state = Command(
                        resume={"action": "update", "data": interrupt.tool_message}
                    )

            elif interrupt.interaction_type == "output_review":
                # Handle output review
                if interrupt.decision == InterruptDecision.APPROVED:
                    # Output approved, continue execution
                    state = Command(resume={"action": "approved"})
                elif interrupt.decision == InterruptDecision.REVIEW:
                    # Output needs revision, add feedback
                    state = Command(
                        resume={"action": "review", "data": interrupt.tool_message}
                    )
                elif interrupt.decision == InterruptDecision.EDIT:
                    # Directly edit output content
                    state = Command(
                        resume={"action": "edit", "data": interrupt.tool_message}
                    )
                else:
                    raise ValueError(
                        f"Unsupported decision for output review: {interrupt.decision}"
                    )

            elif interrupt.interaction_type == "context_input":
                # Handle context input, add extra information provided by user
                if interrupt.decision == InterruptDecision.CONTINUE:
                    state = Command(
                        resume={
                            "action": "continue",
                            "data": interrupt.tool_message,
                        }
                    )
                else:
                    raise ValueError(
                        f"Unsupported decision for context input: {interrupt.decision}"
                    )

            else:
                raise ValueError(f"Unsupported interrupt type: {interrupt.interaction_type}")

        async for event in root.astream_events(state, version="v2", config=config):
            # Check if stop has been requested for this user and thread
            if user_id:
                from app.core.stream_control import ais_stop_requested

                is_stopped = await ais_stop_requested(user_id, thread_id)
                if is_stopped:
                    # Send a stop message and break the loop
                    response = ChatResponse(
                        type="stop",
                        content="Stream stopped by user request",
                        id=str(uuid4()),
                        name="system",
                    )
                    formatted_output = f"data: {response.model_dump_json()}\n\n"
                    yield formatted_output
                    break

            # If workflow type and graph_config exists, pass nodes parameter
            nodes = graph_config["nodes"] if team.workflow_type == WorkflowType.WORKFLOW and hasattr(graph_config, "nodes") else None
            response = event_to_response(event, nodes=nodes)
            if response:
                formatted_output = f"data: {response.model_dump_json()}\n\n"
                yield formatted_output

        snapshot = await root.aget_state(config)
        if snapshot.next:
            try:
                message = snapshot.values["messages"][-1]
            except Exception:
                message = snapshot.values["all_messages"][-1]

            # Determine if it should return default or ask-human interrupt based on whether AskHuman tool was called.
            if team.workflow_type != WorkflowType.WORKFLOW and team.workflow_type != WorkflowType.HIERARCHICAL:
                if not isinstance(message, AIMessage):
                    return
                for tool_call in message.tool_calls:
                    if tool_call["name"] == "ask-human":
                        response = ChatResponse(
                            type="interrupt",
                            name="human",
                            tool_calls=message.tool_calls,
                            id=str(uuid4()),
                        )
                        break
                    else:
                        response = ChatResponse(
                            type="interrupt",
                            name="interrupt",
                            tool_calls=message.tool_calls,
                            id=str(uuid4()),
                        )
            # Handle workflow type or hierarchical workflow type
            else:
                next_node = snapshot.next[0]
                interrupt_name = None

                if team.workflow_type == WorkflowType.WORKFLOW:
                    # For custom workflows, get interrupt_name from graph_config
                    for node in graph_config["nodes"]:
                        if node["id"] == next_node:
                            interrupt_name = node["data"]["interaction_type"]
                            break
                elif team.workflow_type == WorkflowType.HIERARCHICAL:
                    # For hierarchical workflows, determine interrupt_name from node name patterns
                    if next_node.endswith("-ask-human-tool"):
                        interrupt_name = "context_input"
                    elif next_node.endswith("-tool-review"):
                        interrupt_name = "tool_review"
                    # Note: Regular tool nodes ({member_name}-tools) don't have interrupts

                if interrupt_name == "context_input":
                    response = ChatResponse(
                        type="interrupt",
                        name=interrupt_name,
                        content=f"LLM output is as follows:\n\n{message.content}\n\nPlease enter your additional information.",
                        id=str(uuid4()),
                    )
                elif interrupt_name == "tool_review":
                    response = ChatResponse(
                        type="interrupt",
                        name=interrupt_name,
                        tool_calls=message.tool_calls,
                        id=str(uuid4()),
                    )
                elif interrupt_name == "output_review":
                    response = ChatResponse(
                        type="interrupt",
                        name=interrupt_name,
                        content=f"LLM output is as follows:\n\n{message.content}\n\nPlease approve, or enter your review comments.",
                        id=str(uuid4()),
                    )

            formatted_output = f"data: {response.model_dump_json()}\n\n"
            yield formatted_output
    except Exception as e:
        response = ChatResponse(
            type="error", content=str(e), id=str(uuid4()), name="error"
        )
        yield f"data: {response.model_dump_json()}\n\n"
        await asyncio.sleep(0.1)  # Add a small delay to ensure the message is sent
        raise e
