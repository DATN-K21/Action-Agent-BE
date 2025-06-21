from collections.abc import Mapping
from typing import Annotated, Any

from langchain_core.messages import AIMessage, AnyMessage
from langchain_core.output_parsers.openai_tools import JsonOutputKeyToolsParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import (
    RunnableConfig,
    RunnableLambda,
    RunnableSerializable,
)
from langchain_core.tools import BaseTool
from langchain_openai import ChatOpenAI
from langgraph.graph import add_messages
from typing_extensions import NotRequired, TypedDict

from app.core.model_providers.model_provider_manager import model_provider_manager
from app.core.settings import env_settings
from app.core.state import (
    GraphLeader,
    GraphMember,
    GraphTeam,
    add_or_replace_messages,
)
from app.core.tools.tool_args_sanitizer import sanitize_tool_calls_list


class GraphTeamState(TypedDict):
    all_messages: Annotated[
        list[AnyMessage], add_messages
    ]  # Stores all messages in this thread
    messages: Annotated[list[AnyMessage], add_or_replace_messages]
    history: Annotated[list[AnyMessage], add_messages]
    team: GraphTeam
    next: str
    main_task: list[AnyMessage]
    task: list[
        AnyMessage
    ]  # This is the current task to be performed by a team member. It's a list because Worker's MessagesPlaceholder only accepts list of messages.


# When returning teamstate, is it possible to exclude fields that you don't want to update
class ReturnGraphTeamState(TypedDict):
    all_messages: NotRequired[list[AnyMessage]]
    messages: NotRequired[list[AnyMessage]]
    history: NotRequired[list[AnyMessage]]
    team: NotRequired[GraphTeam]
    next: NotRequired[str | None]  # Returning None is valid for sequential graphs only
    task: NotRequired[list[AnyMessage]]


class BaseNode:
    def __init__(
        self,
        provider: str | None,
        model: str | None,
        temperature: float | None,
    ):
        try:
            if provider is None or model is None:
                provider = env_settings.OPENAI_PROVIDER
                model = env_settings.LLM_BASIC_MODEL

            if temperature is None:
                temperature = env_settings.BASIC_MODEL_TEMPERATURE

            self.model_info = model_provider_manager.get_model_info(model)
            self.model = model_provider_manager.init_model(
                provider_name=provider,
                model=model,
                temperature=temperature,
                api_key=self.model_info["api_key"],
                base_url=self.model_info["base_url"],
            )  # Use temperature = 0 when initializing final_answer_model
            self.final_answer_model = model_provider_manager.init_model(
                provider_name=provider,
                model=model,
                temperature=0,
                api_key=self.model_info["api_key"],
                base_url=self.model_info["base_url"],
            )

        except ValueError:
            raise ValueError(f"Model {model} is not supported as a chat model.")

    def tag_with_name(self, ai_message: AIMessage, name: str) -> AIMessage:
        """Tag a name to the AI message"""
        ai_message.name = name
        return ai_message

    def get_team_members_name(
            self, team_members: Mapping[str, GraphMember | GraphLeader]
    ) -> str:
        """Get the names of all team members as a string"""
        return ",".join(list(team_members))

    async def _handle_messages(
        self,
        state: dict[str, Any] | GraphTeamState,
        config: RunnableConfig,
        chain: RunnableSerializable[Any, Any],
    ) -> AIMessage:
        """Handle both regular messages and image messages in a unified way"""
        all_messages = state.get("all_messages", [])

        if (
                all_messages
                and isinstance(all_messages[-1].content, list)
                and any(
            isinstance(item, dict)
            and "type" in item
            and item["type"] in ["text", "image_url"]
            for item in all_messages[-1].content
        )
        ):
            from langchain_core.messages import HumanMessage

            temp_state = [HumanMessage(content=all_messages[-1].content, name="user")]
            result = await self.model.ainvoke(temp_state, config)
        else:
            result = await chain.ainvoke(state, config)

        # Sanitize tool calls if present
        if hasattr(result, "tool_calls") and result.tool_calls:
            result.tool_calls = sanitize_tool_calls_list(result.tool_calls)

        return result

    def get_optimized_context_string(self, messages: list[AnyMessage]) -> str:
        """
        Get optimized context string for the current model.
        This method applies context optimization based on the model's capabilities and limits.

        Args:
            messages: List of messages to format

        Returns:
            Optimized formatted message string
        """
        from app.core.state import format_messages_with_model_context

        # Extract model name from model_info if available
        model_name = None
        provider = None

        if hasattr(self, "model_info") and self.model_info:
            model_name = self.model_info.get("model_name")
            provider = self.model_info.get("provider")

        # If we don't have model info, try to get it from the model object
        if not model_name and hasattr(self, "model"):
            try:
                # Try to get model name from the model object
                if hasattr(self.model, "model_name"):
                    model_name = self.model.model_name
                elif hasattr(self.model, "model"):
                    model_name = self.model.model
            except Exception:
                pass  # Fallback to default optimization

        return format_messages_with_model_context(messages, model_name, provider)


class WorkerNode(BaseNode):
    worker_prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                (
                    "You are a team member of {team_name} and you are one of the following team members: {team_members_name}.\n"
                    "Your team members (and other teams) will collaborate with you with their own set of skills. "
                    "You are chosen by one of your team member to perform this task. Try your best to perform it using your skills. "
                    "Stay true to your persona and role:\n{persona}\n"
                ),
            ),
            (
                "human",
                "Here is the task: \n\n {task_string} \n\n Here is the previous conversation: \n\n {history_string} \n\n Provide your response.",
            ),
            MessagesPlaceholder(variable_name="messages"),
        ]
    )

    def convert_output_to_ai_message(self, agent_output: dict[str, str]) -> AIMessage:
        """Convert agent executor output to ai message"""
        output = agent_output["output"]
        return AIMessage(content=output)

    async def work(
            self, state: GraphTeamState, config: RunnableConfig
    ) -> ReturnGraphTeamState:
        name = state["next"]
        member = state["team"].members[name]
        assert isinstance(member, GraphMember), "member is unexpectedly not a Member"
        team_members_name = self.get_team_members_name(state["team"].members)
        prompt = self.worker_prompt.partial(
            team_name=state["team"].name,
            team_members_name=team_members_name,
            persona=member.persona,
            history_string=self.get_optimized_context_string(state["history"]),
            task_string=self.get_optimized_context_string(state["task"]),
        )
        # If member has no tools, then use a regular model instead of an agent
        if len(member.tools) >= 1:
            tools: list[BaseTool] = []
            for tool in member.tools:
                tool_instance = await tool.aget_tool()
                tools.append(tool_instance)
            chain = prompt | self.model.bind_tools(tools)
        else:
            chain: RunnableSerializable[dict[str, Any], AnyMessage] = (  # type: ignore[no-redef]
                    prompt | self.model
            )
        work_chain: RunnableSerializable[dict[str, Any], Any] = chain | RunnableLambda(
            self.tag_with_name  # type: ignore[arg-type]
        ).bind(name=member.name)

        result: AIMessage = await self._handle_messages(state, config, work_chain)

        if result.tool_calls:
            return {"messages": [result]}
        else:
            return {
                "history": [result],
                "messages": [],
                "all_messages": state["messages"] + [result],
            }


class SequentialWorkerNode(WorkerNode):
    """Perform Sequential Worker actions"""

    worker_prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                (
                    "Perform the task given to you.\n"
                    "If you are unable to perform the task, that's OK, another member with different tools "
                    "will help where you left off. Do not attempt to communicate with other members. "
                    "Execute what you can to make progress. "
                    "Stay true to your persona and role:\n{persona}\n\n"
                ),
            ),
            (
                "human",
                "Here is the previous conversation: \n\n {history_string} \n\n Provide your response.",
            ),
            MessagesPlaceholder(variable_name="messages"),
        ]
    )

    def get_next_member_in_sequence(
            self, members: Mapping[str, GraphMember | GraphLeader], current_name: str
    ) -> str | None:
        member_names = list(members.keys())
        next_index = member_names.index(current_name) + 1
        if next_index < len(members):
            return member_names[member_names.index(current_name) + 1]
        else:
            return None

    async def work(
            self, state: GraphTeamState, config: RunnableConfig
    ) -> ReturnGraphTeamState:
        team = state["team"]  # This is actually the first member masked as a team.
        name = state["next"]
        member = team.members[name]
        assert isinstance(member, GraphMember), "member is unexpectedly not a Member"
        prompt = self.worker_prompt.partial(persona=member.persona, history_string=self.get_optimized_context_string(state["history"]))
        # If member has no tools, then use a regular model instead of an agent
        if len(member.tools) >= 1:
            tools: list[BaseTool] = []
            for tool in member.tools:
                tool_instance = await tool.aget_tool()
                tools.append(tool_instance)
            chain = prompt | self.model.bind_tools(tools)
        else:
            chain: RunnableSerializable[dict[str, Any], AnyMessage] = (  # type: ignore[no-redef]
                    prompt | self.model
            )
        work_chain: RunnableSerializable[dict[str, Any], Any] = chain | RunnableLambda(
            self.tag_with_name  # type: ignore[arg-type]
        ).bind(name=member.name)

        result: AIMessage = await self._handle_messages(state, config, work_chain)

        next: str | None
        if result.tool_calls:
            next = name
            return {"messages": [result], "next": next}
        else:
            next = self.get_next_member_in_sequence(team.members, name)
            return {
                "history": [result],
                "messages": [],
                "next": next,
                "all_messages": state["messages"] + [result],
            }


class LeaderNode(BaseNode):
    leader_prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                (
                    "You are the team leader of {team_name} and this is your role and you have the following team members: {team_members_name}.\n"
                    "Your team is given a task and you have to delegate the work among your team members based on their skills.\n"
                    "Team member info:"
                    "\n\n{team_members_info}\n\n"
                    "Stay true to your persona:"
                    "\n\n{persona}\n\n"
                    "Given the conversation, decide who should act next. Or should we FINISH? Select one of: {options}."
                ),
            ),
            (
                "human",
                (
                    "Here is the team's task: \n\n {team_task} \n\n Here is the previous conversation: \n\n {history_string} \n\n"
                    "Given the conversation, decide who should act next. Or should we FINISH? Select one of: {options}."
                ),
            ),
        ]
    )

    def get_team_members_info(
            self, team_members: Mapping[str, GraphMember | GraphLeader]
    ) -> str:
        """Create a string containing team members name and role."""
        result = ""
        for member in team_members.values():
            result += f"name: {member.name}\nrole: {member.role}\n\n"
        return result

    def get_tool_definition(self, options: list[str]) -> dict[str, Any]:
        """Return the tool definition to choose next team member and provide the task."""
        return {
            "type": "function",
            "function": {
                "name": "route",
                "description": (
                    "Provide both a task and the next most appropriate team member to perform it."
                    "\n'next' - The team member you should call."
                    "\n'task' - The task given to the team member."
                    "\nYou must provide both 'task' and 'next'."
                    "\n\nExample:"
                    "\nQn: How to cook food?"
                    '\n{"task": "Provide cooking instructions", "next": "CookingExpert"}'
                    "\n\nQn: How do you play soccer?"
                    '\n{"task": "Provide advice to play soccer", "next": "SoccerTeam"}'
                    "\n\nQn: How to make a dog happy?"
                    "\nAns: Pat its head and rub its belly"
                    '\n{"task": "No further tasks", "next": "FINISH"}'
                ),
                "parameters": {
                    "title": "routeSchema",
                    "type": "object",
                    "properties": {
                        "task": {
                            "title": "task",
                            "description": "Provide the next task only if answer is still incomplete. Else say no further task.",
                        },
                        "next": {
                            "title": "next",
                            "description": "Choose the next most appropriate team member if answer is still incomplete. Else choose FINISH.",
                            "anyOf": [
                                {"enum": options},
                            ],
                        },
                    },
                    "required": ["next", "task"],
                },
            },
        }

    async def delegate(
            self, state: GraphTeamState, config: RunnableConfig
    ) -> ReturnGraphTeamState:
        team = state["team"]  # This is the current node
        team_members_name = self.get_team_members_name(team.members)
        team_members_info = self.get_team_members_info(team.members)
        options = list(team.members) + ["FINISH"]
        tools = [self.get_tool_definition(options)]

        # Disable default parallel tool calls from ChatOpenAI
        if isinstance(self.model, ChatOpenAI):
            bind_tool = self.model.bind_tools(tools=tools, parallel_tool_calls=False)
        else:
            bind_tool = self.model.bind_tools(tools=tools)

        delegate_chain: RunnableSerializable[Any, Any] = (
            self.leader_prompt.partial(
                team_name=team.name,
                team_members_name=team_members_name,
                team_members_info=team_members_info,
                persona=team.persona,
                team_task=state["main_task"][0].content,
                history_string=self.get_optimized_context_string(state["history"]),
                options=str(options),
            )
            | bind_tool
            | JsonOutputKeyToolsParser(key_name="route", first_tool_only=True)
        )

        # Use the chain directly since it ends with JsonOutputKeyToolsParser
        # which should return a dict, not an AIMessage
        try:
            result = await delegate_chain.ainvoke(state, config)
        except Exception:
            # If the chain fails, return a finish state
            return {
                "next": "FINISH",
                "task": [AIMessage(content="Task completed due to error.", name=team.name)],
            }

        # Result should already be a dict from JsonOutputKeyToolsParser
        if not isinstance(result, dict):
            # Fallback: if it's not a dict, try to convert it
            if result is not None and hasattr(result, "model_dump"):
                result = result.model_dump()
            else:
                result = None

        if not result or result.get("next") is None or result["next"] == "FINISH":
            return {
                "next": "FINISH",
                "task": [AIMessage(content="Task completed.", name=team.name)],
            }
        else:
            task_content: str = str(result.get("task", state["main_task"][0].content))
            tasks = [AIMessage(content=task_content, name=team.name)]
            return {"next": result["next"], "task": tasks, "all_messages": tasks}  # type: ignore

    async def work(
            self, state: GraphTeamState, config: RunnableConfig
    ) -> ReturnGraphTeamState:
        # This method should contain the logic of the delegate method.
        return await self.delegate(state, config)


class SummariserNode(BaseNode):
    summariser_prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                (
                    "You are a team member of {team_name} and you have the following team members: {team_members_name}. "
                    "Your team was given a task and your team members have performed their roles and returned their responses to the team leader.\n\n"
                    "Your role is to interpret the team's conversation and provide the final answer to the team's task.\n"
                ),
            ),
            (
                "human",
                "Here is the team's task: \n\n {team_task} \n\n Here is the team's conversation: \n\n {history_string} \n\n Provide your response.",
            ),
        ]
    )

    async def summarise(
            self, state: GraphTeamState, config: RunnableConfig
    ) -> dict[str, list[AnyMessage]]:
        team = state["team"]
        team_members_name = self.get_team_members_name(team.members)
        # Retrieve the current task if available otherwise fall back to the main task
        tasks = state.get("task") or state.get("main_task", [])
        team_task = tasks[0].content if tasks else ""

        summarise_chain: RunnableSerializable[Any, Any] = (
            self.summariser_prompt.partial(
                team_name=team.name,
                team_members_name=team_members_name,
                team_task=team_task,
                history_string=self.get_optimized_context_string(state["history"]),
            )
            | self.final_answer_model
            | RunnableLambda(self.tag_with_name).bind(name=f"{team.name}_answer")  # type: ignore[arg-type]
        )
        result = await summarise_chain.ainvoke(state, config)
        return {"history": [result], "all_messages": [result]}


class ChatBotNode(BaseNode):
    worker_prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                (
                    "Execute what you can to make progress. "
                    "Stay true to your persona and role:\n{persona}\n\n"
                ),
            ),
            (
                "human",
                "Here is the previous conversation: \n\n {history_string} \n\n Provide your response.",
            ),
            MessagesPlaceholder(variable_name="messages"),
        ]
    )

    def convert_output_to_ai_message(self, agent_output: dict[str, str]) -> AIMessage:
        """Convert agent executor output to ai message"""
        output = agent_output["output"]
        return AIMessage(content=output)

    async def work(
            self, state: GraphTeamState, config: RunnableConfig
    ) -> ReturnGraphTeamState:
        name = state["next"]
        member = state["team"].members[name]
        assert isinstance(member, GraphMember), "member is unexpectedly not a Member"

        prompt = self.worker_prompt.partial(persona=member.persona, history_string=self.get_optimized_context_string(state["history"]))
        # If member has no tools, then use a regular model instead of an agent
        if len(member.tools) >= 1:
            tools: list[BaseTool] = []
            for tool in member.tools:
                tool_instance = await tool.aget_tool()
                tools.append(tool_instance)
            chain = prompt | self.model.bind_tools(tools)
        else:
            chain: RunnableSerializable[dict[str, Any], AnyMessage] = (  # type: ignore[no-redef]
                    prompt | self.model
            )
        work_chain: RunnableSerializable[dict[str, Any], Any] = chain | RunnableLambda(
            self.tag_with_name  # type: ignore[arg-type]
        ).bind(name=member.name)

        result: AIMessage = await self._handle_messages(state, config, work_chain)

        if result.tool_calls:
            return {"messages": [result]}
        else:
            return {
                "history": [result],
                "messages": [],
                "all_messages": state["messages"] + [result],
            }


class RAGBotNode(BaseNode):
    worker_prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                (
                    "You are an assistant for question-answering tasks. "
                    "Use the following pieces of retrieved context to answer "
                    "the question. If you don't know the answer, say that you "
                    "don't know. Use three sentences maximum and keep the answer concise."
                    "Stay true to your persona and role:\n{persona}\n\n"
                ),
            ),
            (
                "human",
                "Here is the previous conversation: \n\n {history_string} \n\n Provide your response.",
            ),
            MessagesPlaceholder(variable_name="messages"),
        ]
    )

    def convert_output_to_ai_message(self, agent_output: dict[str, str]) -> AIMessage:
        """Convert agent executor output to ai message"""
        output = agent_output["output"]
        return AIMessage(content=output)

    async def work(
            self, state: GraphTeamState, config: RunnableConfig
    ) -> ReturnGraphTeamState:
        name = state["next"]
        member = state["team"].members[name]
        assert isinstance(member, GraphMember), "member is unexpectedly not a Member"

        prompt = self.worker_prompt.partial(persona=member.persona, history_string=self.get_optimized_context_string(state["history"]))
        # If member has no tools, then use a regular model instead of an agent
        if len(member.tools) >= 1:
            tools: list[BaseTool] = []
            for tool in member.tools:
                tool_instance = await tool.aget_tool()
                tools.append(tool_instance)
            chain = prompt | self.model.bind_tools(tools)
        else:
            chain: RunnableSerializable[dict[str, Any], AnyMessage] = (  # type: ignore[no-redef]
                    prompt | self.model
            )
        work_chain: RunnableSerializable[dict[str, Any], Any] = chain | RunnableLambda(
            self.tag_with_name  # type: ignore[arg-type]
        ).bind(name=member.name)

        result: AIMessage = await self._handle_messages(state, config, work_chain)

        if result.tool_calls:
            return {"messages": [result]}
        else:
            return {
                "history": [result],
                "messages": [],
                "all_messages": state["messages"] + [result],
            }
