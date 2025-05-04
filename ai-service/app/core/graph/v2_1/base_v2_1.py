import asyncio
import functools
import inspect
from typing import Annotated, Any, Literal, Optional, Sequence, TypedDict, Union, Callable, TypeVar, Type, cast

from langchain_core.language_models import LanguageModelInput, LanguageModelLike, BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, SystemMessage, ToolMessage
from langchain_core.runnables import Runnable, RunnableConfig, RunnableBinding
from langchain_core.stores import BaseStore
from langchain_core.tools import BaseTool
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.errors import create_error_message, ErrorCode
from langgraph.graph import END, START, StateGraph, add_messages
from langgraph.graph.state import CompiledStateGraph
from langgraph.managed import IsLastStep, RemainingSteps
from langgraph.prebuilt import ToolExecutor, ToolNode
from langgraph.types import interrupt, Checkpointer
from langgraph.utils.runnable import RunnableCallable
from pydantic import BaseModel, TypeAdapter

from app.core import logging
from app.core.enums import MessageName
from app.core.monkey_patches.composio_schema_helper import patch_substitute_file_downloads_recursively
from app.core.tools.tools import get_search_tools, get_rag_tools
from app.core.utils.messages import trimmer
from app.prompts.prompt_templates import (
    get_human_in_loop_evaluation_prompt_template,
    get_regenerate_tool_calls_prompt_template,
)
from app.services.llm_service import get_llm_chat_model

logger = logging.get_logger(__name__)

StructuredResponse = Union[dict, BaseModel]
StructuredResponseSchema = Union[dict, type[BaseModel]]
F = TypeVar("F", bound=Callable[..., Any])


class ToolCallV2(BaseModel):
    name: str
    args: dict
    id: Optional[str] = None
    type: Optional[str] = None


class ReActAgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    is_last_step: IsLastStep
    remaining_steps: RemainingSteps
    structured_response: StructuredResponse
    tool_calls: list[ToolCallV2]
    tool_messages: list[AIMessage]
    question: str
    next: str
    interrupted: bool


StateSchema = TypeVar("StateSchema", bound=ReActAgentState)
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


class BinaryScoreV2(TypedDict):
    score: Literal["yes", "no"]


class StreamDataV2(BaseModel):
    node_name: str
    name: MessageName
    output: str


class HumanEditingDataV2(BaseModel):
    execute: bool
    tool_calls: Optional[list[ToolCallV2]] = None


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

        def prompt(state: ReActAgentState) -> Sequence[BaseMessage]:
            return messages_modifier(state["messages"])

        return prompt
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


# noinspection PyMethodMayBeStatic
class GraphBuilderV2:
    def __init__(
            self,
            model: Union[str, LanguageModelLike],
            tools: Union[ToolExecutor, Sequence[BaseTool], ToolNode],
            *,
            state_schema: Optional[StateSchemaType] = None,
            prompt: Optional[Prompt] = None,
            response_format: Optional[
                Union[StructuredResponseSchema, tuple[str, StructuredResponseSchema]]
            ] = None,
            checkpointer: Optional[Checkpointer] = None,
            store: Optional[BaseStore] = None,
            interrupt_before: Optional[list[str]] = None,
            interrupt_after: Optional[list[str]] = None,
            debug: bool = False,
            version: Literal["v1", "v2"] = "v1",
            name: Optional[str] = None,
    ):
        # Declare the attributes
        self.model = model
        self.tools = tools
        self.state_schema = state_schema
        self.prompt = prompt
        self.response_format = response_format
        self.checkpointer = checkpointer
        self.store = store
        self.interrupt_before = interrupt_before
        self.interrupt_after = interrupt_after
        self.debug = debug
        self.version = version
        self.name = name

        # Initialize the object and validate the attributes
        if self.version not in ("v1", "v2"):
            raise ValueError(
                f"Invalid version {self.version}. Supported versions are 'v1' and 'v2'."
            )

        if self.state_schema is not None:
            self.required_keys = {"messages", "remaining_steps"}
            if self.response_format is not None:
                self.required_keys.add("structured_response")

            if missing_keys := self.required_keys - set(self.state_schema.__annotations__):
                raise ValueError(f"Missing required key(s) {missing_keys} in state_schema")

        if isinstance(self.tools, ToolExecutor):
            self.tool_classes: Sequence[BaseTool] = self.tools.tools
            self.tool_node = ToolNode(self.tool_classes)
        elif isinstance(self.tools, ToolNode):
            self.tool_classes = list(self.tools.tools_by_name.values())
            self.tool_node = self.tools
        else:
            self.tool_node = ToolNode(self.tools)
            # get the tool functions wrapped in a tool class from the ToolNode
            self.tool_classes = list(self.tool_node.tools_by_name.values())

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

        self.tool_calling_enabled = len(self.tool_classes) > 0

        if _should_bind_tools(self.model, self.tool_classes) and self.tool_calling_enabled:
            self.model = cast(BaseChatModel, self.model).bind_tools(self.tool_classes)

        self.model_runnable = _get_prompt_runnable(self.prompt) | self.model

        # If any of the tools are configured to return_directly after running,
        # our graph needs to check if these were called
        self.should_return_direct = {t.name for t in self.tool_classes if t.return_direct}

    async def _acall_model(self, state: ReActAgentState, config: RunnableConfig):
        logger.info("---CALL MODEL---")

        _validate_chat_history(state["messages"])

        response = cast(AIMessage, await self.model_runnable.ainvoke(state, config))
        # add agent name to the AIMessage
        response.name = self.name
        has_tool_calls = isinstance(response, AIMessage) and response.tool_calls
        all_tools_return_direct = (
            all(call["name"] in self.should_return_direct for call in response.tool_calls)
            if isinstance(response, AIMessage)
            else False
        )
        if (
                (
                        "remaining_steps" not in state
                        and state.get("is_last_step", False)
                        and has_tool_calls
                )
                or (
                "remaining_steps" in state
                and state["remaining_steps"] < 1
                and all_tools_return_direct
        )
                or (
                "remaining_steps" in state
                and state["remaining_steps"] < 2
                and has_tool_calls
        )
        ):
            return {
                "messages": [
                    AIMessage(
                        id=response.id,
                        content="Sorry, need more steps to process this request.",
                    )
                ]
            }

        if has_tool_calls:
            tool_calls = []
            for tool_call in response.tool_calls:
                data = ToolCallV2.model_validate(tool_call)
                tool_calls.append(data)
            return {"tool_calls": tool_calls, "next": "evaluate_human_in_loop"}
        else:
            if self.response_format is not None:
                return {"messages": [response], "next": "generate_structured_response"}

            return {"messages": [response], "next": END}

    async def _aevaluate_human_in_loop(self, state: ReActAgentState):
        logger.info("---EVALUATE HUMAN IN LOOP---")
        tool_calls = state.get("tool_calls")
        str_tool_calls = _convert_models_to_str(tool_calls)

        prompt = get_human_in_loop_evaluation_prompt_template()
        model = _get_model(self.model)
        chain = prompt | model.with_structured_output(BinaryScoreV2)
        response = await chain.ainvoke({"tool_calls": str_tool_calls})

        if response["score"] == "yes":
            return {"next": "edit_parameters", "interrupted": True}
        else:
            return {"next": "execute_tools", "interrupted": False}

    async def _aedit_parameters(self, state: ReActAgentState):
        logger.info("---EDIT PARAMETERS---")

        # Make a stream by using LLM (for socketio stream)
        str_tool_calls = _convert_models_to_str(state.get("tool_calls"))
        model = get_llm_chat_model(temperature=0)
        prompt = get_regenerate_tool_calls_prompt_template()
        chain = prompt | self.model

        await chain.ainvoke(input={"tool_calls": str_tool_calls})

        data = interrupt(
            {
                "tool_calls": state.get("tool_calls")
            }
        )

        adapter = TypeAdapter(HumanEditingDataV2)
        data = adapter.validate_python(data)

        # Approve the tool call and continue
        if data.execute:
            human_tool_calls = data.tool_calls
            if human_tool_calls is not None:
                tool_calls = state.get("tool_calls")
                for human_tool_call in human_tool_calls:
                    index = next((i for i, item in enumerate(tool_calls)
                                  if item.name == human_tool_call.name
                                  ), -1)
                    tool_calls[index].args = human_tool_call.args

                state["tool_calls"] = tool_calls
                str_tool_calls = _convert_models_to_str(tool_calls)

            return {"next": "execute_tools ", "messages": [AIMessage(content=str_tool_calls, name=MessageName.TOOL)]}

        # Reject the tool call and generate a response
        return {"next": END}

    async def _aexecute_tools(self, state: ReActAgentState, config: RunnableConfig):
        logger.info("---EXECUTE TOOLS---")

        # Fix composio library
        patch_substitute_file_downloads_recursively()

        tool_calls = state.get("tool_calls", [])
        tasks = []

        for tool_call in tool_calls:
            selected_tool = next((tool for tool in self.tools if tool.name == tool_call.name), None)  # type: ignore
            if not selected_tool:
                continue

            async def run_tool_call(tool, args):
                data = await tool.ainvoke(args, config)
                if data is not None:
                    return AIMessage(content=str(data), name=MessageName.TOOL)
                return None

            tasks.append(asyncio.create_task(run_tool_call(selected_tool, tool_call.args)))

        # Collect messages as they complete
        messages = []
        for task in asyncio.as_completed(tasks):
            result = await task
            if result is not None:
                messages.append(result)

        for m in messages:
            if m.name in self.should_return_direct:
                return {"messages": [AIMessage(content=m.content, name=MessageName.AI)], "next": END}
        return {"tool_messages": messages, "next": "agent", "messages": messages}

    async def _agenerate_structured_response(
            self, state: ReActAgentState, config: RunnableConfig
    ):
        logger.info("---GENERATE STRUCTURED RESPONSE---")
        # NOTE: we exclude the last message because there is enough information
        # for the LLM to generate the structured response
        messages = state["messages"][:-1]
        structured_response_schema = self.response_format
        if isinstance(self.response_format, tuple):
            system_prompt, structured_response_schema = self.response_format
            messages = [SystemMessage(content=system_prompt)] + list(messages)

        model_with_structured_output = _get_model(self.model).with_structured_output(
            cast(StructuredResponseSchema, structured_response_schema)
        )
        response = await model_with_structured_output.ainvoke(messages, config)
        return {"structured_response": response, "next": END}

    def build_graph(self) -> CompiledStateGraph:
        # Define a new graph
        workflow = StateGraph(ReActAgentState)

        # Define the nodes
        workflow.add_node("agent", self._acall_model)
        workflow.add_node("evaluate_human_in_loop", self._aevaluate_human_in_loop)
        workflow.add_node("edit_parameters", self._aedit_parameters)
        workflow.add_node("execute_tools", self._aexecute_tools)
        workflow.add_node("generate_structured_response", self._agenerate_structured_response)

        workflow.add_edge(START, "agent")
        workflow.add_conditional_edges("agent", lambda state: state.get("next"))
        workflow.add_conditional_edges("evaluate_human_in_loop", lambda state: state.get("next"))
        workflow.add_conditional_edges("edit_parameters", lambda state: state.get("next"))
        workflow.add_conditional_edges("execute_tools", lambda state: state.get("next"))
        workflow.add_edge("generate_structured_response", END)

        return workflow.compile(checkpointer=self.checkpointer)


def get_builtin_agent(name: str, checkpointer: AsyncPostgresSaver) -> CompiledStateGraph:
    """Get the built-in agent graph."""
    if name == "chat-agent":
        graph = GraphBuilderV2(
            model=get_llm_chat_model(),
            tools=[],
            checkpointer=checkpointer
        ).build_graph()

        return graph

    if name == "search-agent":
        graph = GraphBuilderV2(
            model=get_llm_chat_model(),
            tools=get_search_tools(),
            checkpointer=checkpointer
        ).build_graph()

        return graph

    if name == "rag-agent":
        graph = GraphBuilderV2(
            model=get_llm_chat_model(),
            tools=get_rag_tools(),
            checkpointer=checkpointer
        ).build_graph()

        return graph

    raise ValueError(f"Unknown agent name: {name}")
