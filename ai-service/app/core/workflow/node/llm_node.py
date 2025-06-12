from collections.abc import Sequence
from typing import Any

from langchain_core.messages import AnyMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableConfig, RunnableSerializable
from langchain_core.tools import BaseTool

from app.core.model_providers.model_provider_manager import model_provider_manager
from app.core.state import (
    ReturnWorkflowTeamState,
    WorkflowTeamState,
    format_messages,
    parse_variables,
    update_node_outputs,
)
from app.core.tools.tool_args_sanitizer import sanitize_tool_calls_list
from app.core.workflow.utils.db_utils import get_model_info


class LLMBaseNode:
    def __init__(
        self,
        node_id: str,
        model_name: str,
        tools: Sequence[BaseTool],
        temperature: float,
        system_prompt: str,
        agent_name: str,
    ):
        self.node_id = node_id
        self.system_prompt = system_prompt
        self.agent_name = agent_name
        self.model_info = get_model_info(model_name)
        try:
            self.model = model_provider_manager.init_model(
                provider_name=self.model_info["provider_name"],
                model=self.model_info["ai_model_name"],
                temperature=temperature,
                api_key=self.model_info["api_key"],
                base_url=self.model_info["base_url"],
            )

            if len(tools) >= 1 and hasattr(self.model, "bind_tools"):
                self.model = self.model.bind_tools(tools)

        except ValueError:
            raise ValueError(f"Model {model_name} is not supported as a chat model.")


class LLMNode(LLMBaseNode):
    """Perform LLM Node actions"""

    async def work(
        self, state: WorkflowTeamState, config: RunnableConfig
    ) -> ReturnWorkflowTeamState:

        if "node_outputs" not in state:
            state["node_outputs"] = {}

        if self.system_prompt:
            # First parse variables, then escape any remaining curly braces
            parsed_system_prompt = (
                parse_variables(self.system_prompt, state["node_outputs"])
                .replace("{", "{{")
                .replace("}", "}}")
            )

            llm_node_prompts = ChatPromptTemplate.from_messages(
                [
                    (
                        "system",
                        "Perform the task given to you.\n"
                        "If you are unable to perform the task, that's OK, you can ask human for help, or just say that you are unable to perform the task."
                        "Execute what you can to make progress. "
                        "And your role is:" + parsed_system_prompt + "\n"
                        "And your name is:"
                        + self.agent_name
                        + "\n"
                        + "please remember your name\n"
                        "Stay true to your role and use your tools if necessary.\n\n",
                    ),
                    (
                        "human",
                        "Here is the previous conversation: \n\n {history_string} \n\n Provide your response.",
                    ),
                    MessagesPlaceholder(variable_name="messages"),
                ]
            )

        else:
            llm_node_prompts = ChatPromptTemplate.from_messages(
                [
                    (
                        "system",
                        (
                            "Perform the task given to you.\n"
                            "If you are unable to perform the task, that's OK, you can ask human for help, or just say that you are unable to perform the task."
                            "Execute what you can to make progress. "
                            "Stay true to your role and use your tools if necessary.\n\n"
                        ),
                    ),
                    (
                        "human",
                        "Here is the previous conversation: \n\n {history_string} \n\n Provide your response.",
                    ),
                    MessagesPlaceholder(variable_name="messages"),
                ]
            )
        history = state.get("history", [])
        messages = state.get("messages", [])
        all_messages = state.get("all_messages", [])
        prompt = llm_node_prompts.partial(history_string=format_messages(history))
        chain: RunnableSerializable[dict[str, Any], AnyMessage] = prompt | self.model

        # Check if message contains images
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
            from langchain_core.messages import HumanMessage  # Create new temporary state for handling image messages

            temp_state = [HumanMessage(content=all_messages[-1].content, name="user")]
            result: AnyMessage = await self.model.ainvoke(temp_state, config)
        else:
            # Normal messages maintain the original processing method
            # Convert WorkflowTeamState to dict before passing to ainvoke
            result: AnyMessage = await chain.ainvoke({"messages": state.get("messages", [])}, config)

        # Sanitize tool calls if present to fix common LLM issues like string "null" values
        from langchain_core.messages import AIMessage

        if isinstance(result, AIMessage) and hasattr(result, "tool_calls") and result.tool_calls:
            result.tool_calls = sanitize_tool_calls_list(result.tool_calls)

        # 更新 node_outputs
        new_output = {self.node_id: {"response": result.content}}
        state["node_outputs"] = update_node_outputs(state["node_outputs"], new_output)

        return_state: ReturnWorkflowTeamState = {
            "history": history + [result],
            "messages": [result] if hasattr(result, "tool_calls") else [],
            "all_messages": messages + [result],
            "node_outputs": state["node_outputs"],
        }
        return return_state