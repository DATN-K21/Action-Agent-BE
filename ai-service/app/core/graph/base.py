import functools
import inspect
from typing import Annotated, Any, Optional, Sequence, TypedDict, Literal, Union, Callable, TypeVar, Type, cast

from langchain_core.language_models import LanguageModelInput, LanguageModelLike, BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, SystemMessage, ToolMessage
from langchain_core.runnables import Runnable, RunnableBinding, RunnableConfig
from langchain_core.stores import BaseStore
from langchain_core.tools import BaseTool
from langgraph.errors import create_error_message, ErrorCode
from langgraph.graph import END, StateGraph
from langgraph.graph import add_messages
from langgraph.graph.graph import CompiledGraph
from langgraph.managed import IsLastStep, RemainingSteps
from langgraph.prebuilt import ToolNode, ToolExecutor
from langgraph.types import Checkpointer, interrupt, Send
from langgraph.utils.runnable import RunnableCallable
from pydantic import BaseModel, TypeAdapter

from app.core import logging
from app.core.enums import MessageName
from app.core.utils.messages import trimmer
from app.prompts.prompt_templates import get_human_in_loop_evaluation_prompt_template, \
    get_regenerate_tool_calls_prompt_template

logger = logging.get_logger(__name__)

StructuredResponse = Union[dict, BaseModel]
StructuredResponseSchema = Union[dict, type[BaseModel]]
F = TypeVar("F", bound=Callable[..., Any])


class ToolCall(BaseModel):
    name: str
    args: dict
    id: Optional[str] = None
    type: Optional[str] = None


class GraphState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    is_last_step: IsLastStep
    remaining_steps: RemainingSteps
    structured_response: StructuredResponse
    tool_calls: list[ToolCall]
    tool_messages: list[AIMessage]
    question: str
    next: str
    interrupted: bool


StateSchema = TypeVar("StateSchema", bound=GraphState)
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


class BinaryScore(TypedDict):
    score: Literal["yes", "no"]


class StreamData(BaseModel):
    node_name: str
    name: MessageName
    output: str


class HumanEditingData(BaseModel):
    execute: bool
    tool_calls: Optional[list[ToolCall]] = None


def _advanced_trimmer(messages: Sequence[BaseMessage]) -> Sequence[BaseMessage]:
    """Trims the messages to fit within the token limit."""
    try:
        messages = trimmer.invoke(messages)
        _validate_chat_history(messages)
        while len(messages) > 0 and not _check_chat_history(messages):
            messages = messages[:-1]

        return messages
    except Exception as e:
        logger.error(f"Error trimming messages: {e}")
        raise


def _get_prompt_runnable(prompt: Optional[Prompt]) -> Runnable:
    prompt_runnable: Runnable
    if prompt is None:
        prompt_runnable = RunnableCallable(
            lambda state: _advanced_trimmer(state["messages"]), name=PROMPT_RUNNABLE_NAME
        )
    elif isinstance(prompt, str):
        _system_message: BaseMessage = SystemMessage(content=prompt)
        prompt_runnable = RunnableCallable(
            lambda state: _advanced_trimmer([_system_message] + state["messages"]),
            name=PROMPT_RUNNABLE_NAME,
        )
    elif isinstance(prompt, SystemMessage):
        prompt_runnable = RunnableCallable(
            lambda state: _advanced_trimmer([prompt] + state["messages"]),
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

        def prompt(state: GraphState) -> Sequence[BaseMessage]:
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


# noinspection PyMethodMayBeStatic
class GraphBuilder:
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

    async def acall_model(self, state: GraphState, config: RunnableConfig):
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
        # We return a list, because this will get added to the existing list
        return {"messages": [response]}

    async def agenerate_structured_response(
            self, state: GraphState, config: RunnableConfig
    ):
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
        return {"structured_response": response}

    def should_continue(self, state: GraphState) -> Union[str, list]:
        messages = state["messages"]
        last_message = messages[-1]
        # If there is no function call, then we finish
        if not isinstance(last_message, AIMessage) or not last_message.tool_calls:
            return END if self.response_format is None else "generate_structured_response"
        # Otherwise if there is, we continue
        else:
            if self.version == "v1":
                return "tools"
            elif self.version == "v2":
                tool_calls = [
                    tool_node.inject_tool_args(call, state, store)  # type: ignore[arg-type]
                    for call in last_message.tool_calls
                ]
                return [Send("tools", [tool_call]) for tool_call in tool_calls]

    async def evaluate_human_loop(self, state: GraphState):
        messages = state["messages"]
        last_message = messages[-1]
        str_message = last_message.model_dump_json()

        prompt = get_human_in_loop_evaluation_prompt_template()
        chain = prompt | _get_model(self.model).with_structured_output(BinaryScore)

        response = await chain.ainvoke({"tool_calls": str_message})

        if response["score"] == "yes":
            return {"next": "human_editing", "interrupted": True}
        else:
            return {"next": "tools", "interrupted": False}

    async def human_editing(self, state: GraphState):
        messages = state["messages"]
        last_message = messages[-1]
        str_tool_message = last_message.model_dump_json()

        prompt = get_regenerate_tool_calls_prompt_template()
        chain = prompt | self.model
        await chain.ainvoke(input={"tool_calls": str_tool_message})

        data = interrupt(
            {
                "tool_calls": last_message.tool_calls,
            }
        )

        adapter = TypeAdapter(HumanEditingData)
        data = adapter.validate_python(data)

        # Approve the tool call and continue
        if data.execute:
            human_tool_calls = data.tool_calls
            if human_tool_calls is not None:
                tool_calls = last_message.tool_calls
                for human_tool_call in human_tool_calls:
                    index = next((i for i, item in enumerate(tool_calls)
                                  if item.name == human_tool_call.name
                                  ), -1)
                    tool_calls[index].args = human_tool_call.args

                last_message.tool_calls = tool_calls
                state["messages"][-1] = last_message

            return {"next": "tools"}

        # Reject the tool call and generate a response
        return {"next": END}

    def route_tool_responses(self, state: GraphState) -> Literal["agent", "__end__"]:
        for m in reversed(state["messages"]):
            if not isinstance(m, ToolMessage):
                break
            if m.name in self.should_return_direct:
                return END
        return "agent"

    def build_graph(self) -> CompiledGraph:
        if not self.tool_calling_enabled:
            # Define a new graph
            workflow = StateGraph(self.state_schema or GraphState)
            workflow.add_node("agent", self.acall_model)
            workflow.set_entry_point("agent")
            if self.response_format is not None:
                workflow.add_node(
                    "generate_structured_response",
                    self.agenerate_structured_response
                )
                workflow.add_edge("agent", "generate_structured_response")

            return workflow.compile(
                checkpointer=self.checkpointer,
                store=self.store,
                interrupt_before=self.interrupt_before,
                interrupt_after=self.interrupt_after,
                debug=self.debug,
                name=self.name,
            )

        # Define a new graph
        workflow = StateGraph(self.state_schema or GraphState)

        # Define the two nodes we will cycle between
        workflow.add_node("agent", self.acall_model)
        workflow.add_node("tools", self.tool_node)

        # Set the entrypoint as `agent`
        # This means that this node is the first one called
        workflow.set_entry_point("agent")

        # Add a structured output node if response_format is provided
        if self.response_format is not None:
            workflow.add_node(
                "generate_structured_response",
                self.agenerate_structured_response
            )
            workflow.add_edge("generate_structured_response", END)
            should_continue_destinations = ["tools", "generate_structured_response"]
        else:
            should_continue_destinations = ["tools", END]

        # We now add a conditional edge
        workflow.add_conditional_edges(
            # First, we define the start node. We use `agent`.
            # This means these are the edges taken after the `agent` node is called.
            "agent",
            # Next, we pass in the function that will determine which node is called next.
            self.should_continue,
            path_map=should_continue_destinations,
        )

        if self.should_return_direct:
            workflow.add_conditional_edges("tools", self.route_tool_responses)
        else:
            workflow.add_edge("tools", "agent")

        # Finally, we compile it!
        # This compiles it into a LangChain Runnable,
        # meaning you can use it as you would any other runnable
        return workflow.compile(
            checkpointer=self.checkpointer,
            store=self.store,
            interrupt_before=self.interrupt_before,
            interrupt_after=self.interrupt_after,
            debug=self.debug,
            name=self.name,
        )
