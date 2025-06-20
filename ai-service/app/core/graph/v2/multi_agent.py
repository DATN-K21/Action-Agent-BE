import functools
import inspect
from typing import Annotated, Any, Callable, Literal, Optional, Sequence, Type, TypedDict, TypeVar, Union, cast

from langchain_core.language_models import BaseChatModel, LanguageModelInput, LanguageModelLike
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.runnables import Runnable, RunnableBinding, RunnableConfig
from langchain_core.tools import BaseTool
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.errors import ErrorCode, create_error_message
from langgraph.graph import END, START, StateGraph, add_messages
from langgraph.graph.graph import CompiledGraph
from langgraph.managed import IsLastStep, RemainingSteps
from langgraph.prebuilt import create_react_agent
from langgraph.types import Checkpointer
from langgraph.utils.runnable import RunnableCallable
from openai import BaseModel

from app.core import logging
from app.core.settings import env_settings
from app.core.utils.messages import trimmer
from app.core.utils.standard_sring import standardize_string
from app.services.database.assistant_service import AssistantService
from app.services.database.extension_assistant_service import ExtensionAssistantService
from app.services.database.mcp_assistant_service import McpAssistantService
from app.services.extensions.extension_service_manager import ExtensionServiceManager
from app.services.llm_service import get_llm_chat_model
from app.services.mcps.mcp_service import McpService

logger = logging.get_logger(__name__)

StructuredResponse = Union[dict, BaseModel]
StructuredResponseSchema = Union[dict, type[BaseModel]]
F = TypeVar("F", bound=Callable[..., Any])


class MultiAgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    is_last_step: IsLastStep
    remaining_steps: RemainingSteps
    structured_response: StructuredResponse
    question: str
    next: str
    actions: list[dict]
    current_action_index: int


StateSchema = TypeVar("StateSchema", bound=MultiAgentState)
StateSchemaType = Type[StateSchema]

PROMPT_RUNNABLE_NAME = "Prompt"

MessagesModifier = Union[
    SystemMessage,
    str,
    Callable[[Sequence[BaseMessage]], LanguageModelInput],
    Runnable[Sequence[BaseMessage], LanguageModelInput],
]

Prompt = Union[
    SystemMessage,
    str,
    Callable[[StateSchema], LanguageModelInput],
    Runnable[StateSchema, LanguageModelInput],
]


class Worker(BaseModel):
    name: str
    description: Optional[str] = None


def _get_prompt_runnable(prompt: Optional[Prompt]) -> Runnable:
    prompt_runnable: Runnable
    if prompt is None:
        prompt_runnable = RunnableCallable(
            lambda state: trimmer.invoke(state["messages"]), name=PROMPT_RUNNABLE_NAME
        )
    elif isinstance(prompt, str):
        _system_message: BaseMessage = SystemMessage(content=prompt)
        prompt_runnable = RunnableCallable(
            lambda state: trimmer.invoke([_system_message] + state["messages"]),
            name=PROMPT_RUNNABLE_NAME,
        )
    elif isinstance(prompt, SystemMessage):
        prompt_runnable = RunnableCallable(
            lambda state: trimmer.invoke([prompt] + state["messages"]),
            name=PROMPT_RUNNABLE_NAME,
        )
    elif inspect.iscoroutinefunction(prompt):
        prompt_runnable = RunnableCallable(
            None,
            prompt,
            name=PROMPT_RUNNABLE_NAME,
        )
    elif callable(prompt):
        prompt_runnable = RunnableCallable(
            prompt,
            name=PROMPT_RUNNABLE_NAME,
        )
    elif isinstance(prompt, Runnable):
        prompt_runnable = prompt
    else:
        raise ValueError(f"Got unexpected type for `prompt`: {type(prompt)}")

    return prompt_runnable


def _convert_messages_modifier_to_prompt(
        messages_modifier: MessagesModifier,
) -> Prompt:
    prompt: Prompt
    if isinstance(messages_modifier, (str, SystemMessage)):
        return messages_modifier
    elif callable(messages_modifier):

        def messages_prompt(state: MultiAgentState) -> Sequence[BaseMessage]:
            result = messages_modifier(state["messages"])
            if isinstance(result, list) and all(isinstance(msg, BaseMessage) for msg in result):
                # Ensure all items are BaseMessage instances
                if isinstance(result, list) and all(isinstance(msg, BaseMessage) for msg in result):
                    # Convert any string to HumanMessage, filter out non-BaseMessage
                    return [
                        msg if isinstance(msg, BaseMessage) else HumanMessage(content=msg) for msg in result if isinstance(msg, (BaseMessage, str))
                    ]
                elif isinstance(result, BaseMessage):
                    return [result]
                elif isinstance(result, str):
                    return [HumanMessage(content=result)]
                else:
                    raise TypeError("messages_modifier must return a BaseMessage, a list of BaseMessage objects, or a string.")
            elif isinstance(result, BaseMessage):
                return [result]
            else:
                raise TypeError("messages_modifier must return a BaseMessage or a list of BaseMessage objects.")

        return messages_prompt
    elif isinstance(messages_modifier, Runnable):
        prompt = (lambda state: state["messages"]) | messages_modifier
        return prompt
    raise ValueError(
        f"Got unexpected type for `messages_modifier`: {type(messages_modifier)}"
    )


def _convert_modifier_to_prompt(func: F) -> F:
    """Decorator that converts state_modifier/messages_modifier kwargs to prompt kwarg."""

    # noinspection PyTypeChecker
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        prompt = kwargs.get("prompt")
        state_modifier = kwargs.pop("state_modifier", None)
        messages_modifier = kwargs.pop("messages_modifier", None)
        if sum(p is not None for p in (prompt, state_modifier, messages_modifier)) > 1:
            raise ValueError(
                "Expected only one of prompt, state_modifier, or messages_modifier, got multiple values"
            )

        if state_modifier is not None:
            prompt = state_modifier
        elif messages_modifier is not None:
            prompt = _convert_messages_modifier_to_prompt(messages_modifier)

        kwargs["prompt"] = prompt
        return func(*args, **kwargs)

    return cast(F, wrapper)


def _should_bind_tools(model: LanguageModelLike, tools: Sequence[BaseTool]) -> bool:
    if not isinstance(model, RunnableBinding):
        return True

    if "tools" not in model.kwargs:
        return True

    bound_tools = model.kwargs["tools"]
    if len(tools) != len(bound_tools):
        raise ValueError(
            "Number of tools in the model.bind_tools() and tools passed to create_react_agent must match"
        )

    tool_names = set(tool.name for tool in tools)
    bound_tool_names = set()
    for bound_tool in bound_tools:
        # OpenAI-style tool
        if bound_tool.get("type") == "function":
            bound_tool_name = bound_tool["function"]["name"]
        # Anthropic-style tool
        elif bound_tool.get("name"):
            bound_tool_name = bound_tool["name"]
        else:
            # unknown tool type so we'll ignore it
            continue

        bound_tool_names.add(bound_tool_name)

    if missing_tools := tool_names - bound_tool_names:
        raise ValueError(f"Missing tools '{missing_tools}' in the model.bind_tools()")

    return False


def _get_model(model: LanguageModelLike) -> BaseChatModel:
    """Get the underlying model from a RunnableBinding or return the model itself."""
    if isinstance(model, RunnableBinding):
        model = model.bound

    if not isinstance(model, BaseChatModel):
        raise TypeError(
            f"Expected `model` to be a ChatModel or RunnableBinding (e.g. model.bind_tools(...)), got {type(model)}"
        )

    return model


def _check_chat_history(
        messages: Sequence[BaseMessage],
) -> bool:
    all_tool_calls = [
        tool_call
        for message in messages
        if isinstance(message, AIMessage)
        for tool_call in message.tool_calls
    ]
    tool_call_ids_with_results = {
        message.tool_call_id for message in messages if isinstance(message, ToolMessage)
    }
    tool_calls_without_results = [
        tool_call
        for tool_call in all_tool_calls
        if tool_call["id"] not in tool_call_ids_with_results
    ]
    if not tool_calls_without_results:
        return True

    return False


def _validate_chat_history(
        messages: Sequence[BaseMessage],
) -> None:
    """Validate that all tool calls in AIMessages have a corresponding ToolMessage."""
    all_tool_calls = [
        tool_call
        for message in messages
        if isinstance(message, AIMessage)
        for tool_call in message.tool_calls
    ]
    tool_call_ids_with_results = {
        message.tool_call_id for message in messages if isinstance(message, ToolMessage)
    }
    tool_calls_without_results = [
        tool_call
        for tool_call in all_tool_calls
        if tool_call["id"] not in tool_call_ids_with_results
    ]
    if not tool_calls_without_results:
        return

    error_message = create_error_message(
        message="Found AIMessages with tool_calls that do not have a corresponding ToolMessage. "
                f"Here are the first few of those tool calls: {tool_calls_without_results[:3]}.\n\n"
                "Every tool call (LLM requesting to call a tool) in the message history MUST have a corresponding ToolMessage "
                "(result of a tool invocation to return to the LLM) - this is required by most LLM providers.",
        error_code=ErrorCode.INVALID_CHAT_HISTORY,
    )
    raise ValueError(error_message)


def _convert_models_to_str(models: list[BaseModel]) -> str:
    return str([model.model_dump_json() for model in models])


def _get_planner_system_prompt(workers: list[Worker]):
    members = [worker.name for worker in workers]
    metadata = "\n".join(
        f"## Description of {worker.name}: {worker.description}"
        for worker in workers
    )

    system_prompt = (
        "You are a planning assistant tasked with generating a structured plan to fulfill a user request.\n"
        "The plan must be a sequence of steps, each with:\n"
        "  - `task`: A clear description of the action to be performed (not the result or output)\n"
        "  - `next`: The tool (worker) responsible for the task; must be one of the following: "
        f"{', '.join(members)} or `FINISH`\n"
        "\n"
        "Guidelines:\n"
        "- Each step must use one of the listed tools.\n"
        "- Do not invent tools or use tools not listed.\n"
        "- The final step must always use `next: FINISH`.\n"
        "- The final step should summarize the overall plan outcome **based on the user request**, but `task` should describe the summary action (e.g., 'Summarize the search results and actions taken').\n"
        "- Do NOT include actual content, responses, or email messages in `task` fields.\n"
        "- Respond **only** with a list of steps in valid JSON format.\n"
        "\n"
        "# Details of the available tools (workers):\n"
        f"{metadata}"
    )

    return system_prompt


class MultiAgentGraphBuilder:
    """
    Multi Agent Graph Builder to build the multi-agent graph.
    """

    def __init__(
            self,
            model: Union[str, LanguageModelLike],
            *,
            response_format: Optional[
                Union[StructuredResponseSchema, tuple[str, StructuredResponseSchema]]
            ] = None,
            checkpointer: Optional[Checkpointer] = None,
            name: Optional[str] = None,
    ):
        # Declare the attributes
        self.model = model
        self.response_format = response_format
        self.checkpointer = checkpointer
        self.name = name

        # Initialize the object and validate the attributes
        if isinstance(self.model, str):
            try:
                from langchain.chat_models import (  # type: ignore[import-not-found]
                    init_chat_model,
                )
            except ImportError:
                raise ImportError(
                    "Please install langchain (`pip install langchain`) to use '<provider>:<model>' string syntax for `model` parameter."
                )

            self.model = cast(BaseChatModel, init_chat_model(self.model))

        self.model_runnable = _get_prompt_runnable(None) | self.model

        self.workflow = StateGraph(MultiAgentState)
        self.workers: list[Worker] = list()

    def add_subgraph(self, subgraph: CompiledGraph, node_name: str,
                     node_description: Optional[str] = None):
        """
        Add a subgraph to the workflow.
        """

        for worker in self.workers:
            if worker.name == node_name:
                raise ValueError(f"Worker with name '{node_name}' already exists.")

        self.workflow.add_node(node_name, subgraph)
        self.workflow.add_edge(node_name, "supervisor")
        self.workers.append(Worker(name=node_name, description=node_description))

    async def _aplan(self, state: MultiAgentState, config: RunnableConfig):
        logger.info("[NODE] PLAN")

        if isinstance(self.model, str):
            raise TypeError(
                "self.model must be a LanguageModelLike, not a str. Please initialize MultiAgentGraphBuilder with a valid model instance."
            )
        model = _get_model(self.model)

        options = ["FINISH"] + [worker.name for worker in self.workers]

        system_prompt = _get_planner_system_prompt(self.workers)
        messages = state.get("messages")
        messages = [SystemMessage(content=system_prompt)] + list(messages)
        messages = await trimmer.ainvoke(messages)
        question = messages[-1].content

        # noinspection PyPep8Naming
        class ActionStep(TypedDict):
            """
            Represents one step in a plan.
            - next: The tool to use in the next step (e.g., gmail, calendar).
            - task: The action to perform with the selected tool.
            """
            # noinspection PyTypeHints
            next: Literal[*options]  # type: ignore
            task: str

        class StepList(TypedDict):
            """
            A sequence of steps to be executed in order.
            - steps: List of ActionStep items.
            """
            steps: list[ActionStep]

        response = await model.with_structured_output(StepList).ainvoke(messages, config)

        logger.info(f"[Plan:] {response}")

        return {"actions": response.get("steps", []), "current_action_index": 0, "next": "supervisor", "question": question}  # type: ignore

    async def _acall_model(self, state: MultiAgentState, config: RunnableConfig):
        logger.info("[NODE] CALL MODEL")

        response = cast(AIMessage, await self.model_runnable.ainvoke(state, config))

        if self.response_format is not None:
            return {"messages": [response], "next": "generate_structured_response"}

        return {"messages": [response], "next": END}

    async def _agenerate_structured_response(
            self, state: MultiAgentState, config: RunnableConfig
    ):
        logger.info("[NODE] GENERATE STRUCTURED RESPONSE")
        # NOTE: we exclude the last message because there is enough information
        # for the LLM to generate the structured response
        messages = state["messages"][:-1]
        structured_response_schema = self.response_format
        if isinstance(self.response_format, tuple):
            system_prompt, structured_response_schema = self.response_format
            messages = [SystemMessage(content=system_prompt)] + list(messages)

        if isinstance(self.model, str):
            raise TypeError(
                "self.model must be a LanguageModelLike, not a str. Please initialize MultiAgentGraphBuilder with a valid model instance."
            )

        model_with_structured_output = _get_model(self.model).with_structured_output(
            cast(StructuredResponseSchema, structured_response_schema)
        )
        response = await model_with_structured_output.ainvoke(messages, config)
        return {"structured_response": response, "next": END}

    # noinspection PyMethodMayBeStatic
    async def _supervisor_node(self, state: MultiAgentState):
        logger.info("[NODE] SUPERVISOR NODE")

        current_action_index = state["current_action_index"]
        actions = state["actions"]
        action = None

        if actions is None or current_action_index >= len(actions):
            current_action_index = 0
            next_ = END
        else:
            action = actions[current_action_index]
            next_ = action["next"]
            current_action_index += 1

        if next_ == "FINISH":
            next_ = "agent"

        logger.info(f"[NODE] {next_} ")

        task_content = ""
        if action is not None:
            task_content = action.get("task") or ""
        return {"next": next_, "current_action_index": current_action_index, "messages": [HumanMessage(content=task_content)]}

    def build_graph(self) -> CompiledGraph:
        """
        Build the multi-agent graph.
        """
        # Add the supervisor node to the workflow
        self.workflow.add_node("plan", self._aplan)
        self.workflow.add_node("supervisor", self._supervisor_node)
        self.workflow.add_node("agent", self._acall_model)
        self.workflow.add_node("generate_structured_response", self._agenerate_structured_response)

        self.workflow.add_edge(START, "plan")
        self.workflow.add_edge("plan", "supervisor")
        self.workflow.add_conditional_edges("supervisor", lambda state: state["next"])
        self.workflow.add_conditional_edges("agent", lambda state: state["next"])
        self.workflow.add_edge("generate_structured_response", END)

        return self.workflow.compile(
            checkpointer=self.checkpointer,
            name=self.name,
        )


async def acreate_multi_agent(
        user_id: str,
        assistant_id: str,
        checkpointer: AsyncPostgresSaver,
        assistant_service: AssistantService,
        extension_assistant_service: ExtensionAssistantService,
        mcp_assistant_service: McpAssistantService,
        extension_service_manager: ExtensionServiceManager
) -> CompiledGraph | None:
    """
    Create a multi-agent graph.
    """

    result = await assistant_service.get_assistant_by_id(user_id=user_id, assistant_id=assistant_id)
    assistant = result.data

    if assistant is None:
        raise ValueError("Assistant not found")

    if assistant.type == "mcp":
        result = await mcp_assistant_service.list_mcps_of_assistant(assistant_id=assistant_id)
        if not result.data or not hasattr(result.data, "mcps"):
            raise ValueError("No MCP connections found for the assistant")
        mcp_connections = result.data.mcps

        builder = MultiAgentGraphBuilder(
            model=get_llm_chat_model(),
            checkpointer=checkpointer,
            name=assistant.name,
        )

        for mcp in mcp_connections:
            connections = {}
            connections[mcp.mcp_name] = {"url": mcp.url, "transport": mcp.connection_type}
            tools = await McpService.aget_tools(connections=connections)

            mcp_name = standardize_string(mcp.mcp_name)

            subgraph = create_react_agent(
                name=mcp_name,
                tools=tools,
                model=get_llm_chat_model(),
                checkpointer=checkpointer,
                debug=env_settings.DEBUG_AGENT,
            )

            builder.add_subgraph(subgraph, node_name=mcp_name)

        return builder.build_graph()

    if assistant.type == "extension":
        result = await extension_assistant_service.list_extensions_of_assistant(assistant_id=assistant_id)
        if not result.data or not hasattr(result.data, "extensions"):
            raise ValueError("No extensions found for the assistant")
        extensions = result.data.extensions

        # Build multi-agent graph
        builder = MultiAgentGraphBuilder(
            model=get_llm_chat_model(),
            checkpointer=checkpointer,
            name=assistant.name,
        )

        for extension in extensions:
            extension_service = extension_service_manager.get_extension_service(extension.extension_name)
            if extension_service is None:
                logger.warning(f"Extension service for '{extension.extension_name}' not found, skipping.")
                continue
            tools = extension_service.get_authed_tools(user_id=user_id)

            # Filter tools to only include BaseTool instances and standardize the extension name
            filtered_tools = [tool for tool in tools if isinstance(tool, BaseTool)]
            extension_name = standardize_string(extension.extension_name)

            subgraph = create_react_agent(
                name=extension_name,
                tools=filtered_tools,
                model=get_llm_chat_model(),
                checkpointer=checkpointer,
                debug=env_settings.DEBUG_AGENT,
            )

            builder.add_subgraph(subgraph, node_name=extension_name)

        return builder.build_graph()

    raise ValueError("Invalid assistant type")
