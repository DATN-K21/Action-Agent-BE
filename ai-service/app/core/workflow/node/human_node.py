import json
from typing import Any, List
from uuid import uuid4

from langchain_core.messages import AIMessage, AnyMessage, HumanMessage, ToolMessage
from langchain_core.runnables import RunnableConfig
from langgraph.types import Command, interrupt

from app.core.enums import InterruptDecision, InterruptType
from app.core.state import ReturnWorkflowTeamState, WorkflowTeamState
from app.core.tools.tool_args_sanitizer import sanitize_tool_args


class HumanNode:
    """Human-machine interaction node, supporting three interaction modes: tool call review, output review, and context input"""

    def __init__(
            self,
            node_id: str,
            routes: dict[str, str],  # Route Configuration
            title: str | None = None,  # Custom Title
            interaction_type: InterruptType = InterruptType.TOOL_REVIEW,  # Interaction Types
    ):
        self.node_id = node_id
        self.routes = routes
        self.title = title
        self.interaction_type = interaction_type
        self.history = None
        self.messages = None
        self.all_messages = None
        self.last_message = None

    async def work(
            self, state: WorkflowTeamState, config: RunnableConfig
    ) -> ReturnWorkflowTeamState | Command[str]:
        self.history = state.get("history", [])
        self.messages = state.get("messages", [])
        self.all_messages = state.get("all_messages", [])

        # Get the last message
        self.last_message = state["messages"][-1]

        # Build interrupt data based on different interaction types
        interrupt_data = {
            "title": self.title,
            "interaction_type": self.interaction_type,
        }

        if self.interaction_type == InterruptType.TOOL_REVIEW:
            if not isinstance(self.last_message, AIMessage) or not hasattr(self.last_message, "tool_calls") or not self.last_message.tool_calls:
                return {
                    "all_messages": state["all_messages"],
                    "history": state["history"],
                    "messages": state["messages"],
                    "team": state["team"],
                    "next": state["next"],
                    "task": state["task"],
                    "node_outputs": state["node_outputs"],
                }

            tool_call = self.last_message.tool_calls
            interrupt_data.update(
                {
                    "question": "Please review this tool call:",
                    "tool_call": tool_call,
                }
            )
        elif self.interaction_type == InterruptType.OUTPUT_REVIEW:
            interrupt_data.update(
                {
                    "question": "Please review this output:",
                    "content": self.last_message.content,
                }
            )
        elif self.interaction_type == InterruptType.CONTEXT_INPUT:
            interrupt_data.update(
                {
                    "question": "Please provide more information:",
                }
            )

        # Execute interrupt
        human_review = interrupt(interrupt_data)

        # Get action and data from interrupt response
        action = human_review["action"]
        review_data = human_review.get("data")

        # Handle response based on different interaction types
        if self.interaction_type == InterruptType.TOOL_REVIEW:
            return self._handle_tool_review(action, review_data)
        elif self.interaction_type == InterruptType.OUTPUT_REVIEW:
            return self._handle_output_review(action, review_data)
        elif self.interaction_type == InterruptType.CONTEXT_INPUT:
            return self._handle_context_input(action, review_data)
        else:
            raise ValueError(f"Unknown interaction type: {self.interaction_type}")

    def _handle_tool_review(self, action: str, review_data: Any) -> Command[str]:
        # Use safety checks to ensure last_message is an AIMessage with tool_calls
        if not isinstance(self.last_message, AIMessage) or not hasattr(self.last_message, "tool_calls") or not self.last_message.tool_calls:
            raise ValueError("Last message does not contain valid tool calls for review")

        tool_call = self.last_message.tool_calls[-1]
        match action:
            case InterruptDecision.APPROVED:
                # Approve tool call, execute directly
                next_node = self.routes.get("approved", "run_tool")
                return Command(goto=next_node)

            case InterruptDecision.REJECTED:
                # Reject tool call, add rejection message
                result: List[AnyMessage] = [
                    ToolMessage(
                        tool_call_id=tool_call["id"],
                        content="Rejected by user. Continue assisting.",
                    )
                ]
                if review_data:
                    result.append(
                        HumanMessage(content=review_data, name="user", id=str(uuid4())),
                    )
                result.append(
                    AIMessage(content="I understand your concern. Let's try again.")
                )

                return_state: ReturnWorkflowTeamState = {
                    "history": (self.history or []) + result,
                    "messages": result,
                    "all_messages": (self.all_messages or []) + result,
                }
                next_node = self.routes.get("rejected", "call_llm")
                return Command(goto=next_node, update=return_state)

            case InterruptDecision.UPDATE:
                # Update tool call parameters
                # Ensure review_data is dictionary type
                args = (
                    review_data
                    if isinstance(review_data, dict)
                    else json.loads(review_data)
                )

                # Sanitize tool arguments to fix common LLM issues like string "null" values
                sanitized_args = sanitize_tool_args(args)

                updated_message = AIMessage(
                    content=self.last_message.content,
                    tool_calls=[
                        {
                            "id": tool_call["id"],
                            "name": tool_call["name"],
                            "args": sanitized_args,  # Use sanitized arguments
                        }
                    ],
                    id=self.last_message.id,
                )

                return_state: ReturnWorkflowTeamState = {
                    "history": (self.history or []) + [updated_message],
                    "messages": [updated_message],
                    "all_messages": (self.all_messages or []) + [updated_message],
                }
                next_node = self.routes.get("update", "run_tool")
                return Command(goto=next_node, update=return_state)

            case _:
                raise ValueError(f"Unknown action for tool review: {action}")

    def _handle_output_review(self, action: str, review_data: Any) -> Command[str]:
        match action:
            case InterruptDecision.APPROVED:
                next_node = self.routes.get("approved", "")
                return Command(goto=next_node)

            case InterruptDecision.REVIEW:
                result = HumanMessage(content=review_data, name="user", id=str(uuid4()))
                next_node = self.routes.get("review", "call_llm")
                return_state: ReturnWorkflowTeamState = {
                    "history": (self.history or []) + [result],
                    "messages": [result],
                    "all_messages": (self.all_messages or []) + [result],
                }
                return Command(goto=next_node, update=return_state)

            case _:
                raise ValueError(f"Unknown action for output review: {action}")

    def _handle_context_input(self, action: str, review_data: Any) -> Command[str]:
        if action == InterruptDecision.CONTINUE:
            if not isinstance(self.last_message, AIMessage) or not hasattr(self.last_message, "tool_calls") or not self.last_message.tool_calls:
                result = HumanMessage(content=review_data, name="user", id=str(uuid4()))
            else:
                # If the last message is an AIMessage with tool calls, we can append the context input
                result = ToolMessage(
                    tool_call_id=self.last_message.tool_calls[-1]["id"],
                    content=review_data,
                )

            next_node = self.routes.get("continue", "call_llm")
            return_state: ReturnWorkflowTeamState = {
                "history": (self.history or []) + [result],
                "messages": [result],
                "all_messages": (self.all_messages or []) + [result],
            }
            return Command(goto=next_node, update=return_state)
        else:
            raise ValueError(f"Unknown action for context input: {action}")
