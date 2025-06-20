from typing import Any, Dict, List

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableConfig
from langgraph.prebuilt import create_react_agent

from app.core.model_providers.model_provider_manager import model_provider_manager
from app.core.state import (
    ReturnWorkflowTeamState,
    WorkflowTeamState,
    format_messages,
    parse_variables,
    update_node_outputs,
)
from app.core.tools.tool_args_sanitizer import sanitize_tool_calls_list
from app.core.workflow.utils.tools_utils import get_retrieval_tool, get_tool


class AgentNode:
    """Agent Node that combines LLM with tools and knowledge bases"""

    def __init__(
        self,
        node_id: str,
        model_name: str,
        temperature: float,
        system_message: str | None = None,
        user_message: str | None = None,
        tools: List[str] | None = None,
        retrieval_tools: List[Dict[str, Any]] | None = None,
        agent_name: str | None = None,
    ):
        self.node_id = node_id
        self.system_message = system_message
        self.user_message = user_message
        self.agent_name = agent_name or node_id
        self.model_info = model_provider_manager.get_model_info(model_name)
        self.system_prompt = system_message
        self.user_prompt = user_message
        # Prepare the list of tools
        self.tools_list = []

        # Add general tools
        if tools:
            for tool_name in tools:
                tool = get_tool(tool_name)
                if tool:
                    self.tools_list.append(tool)

        # Add knowledge base tools
        if retrieval_tools:
            for kb_tool in retrieval_tools:
                if isinstance(kb_tool, dict):
                    retrieval_tool = get_retrieval_tool(
                        kb_tool["name"],
                        kb_tool.get("description", ""),
                        kb_tool.get("usr_id", 0),
                        kb_tool.get("kb_id", 0),
                    )
                    if retrieval_tool:
                        self.tools_list.append(retrieval_tool)
                elif isinstance(kb_tool, str):
                    retrieval_tool = get_retrieval_tool(
                        kb_tool,
                        f"Search in knowledge base {kb_tool}",
                        0,
                        0,
                    )
                    if retrieval_tool:
                        self.tools_list.append(retrieval_tool)

        # Initialize the model
        try:
            # Create model configuration
            self.model_config = {
                "provider_name": self.model_info["provider_name"],
                "model": self.model_info["ai_model_name"],
                "temperature": temperature,
                "api_key": self.model_info["api_key"],
                "base_url": self.model_info["base_url"],
            }

            # Initialize the model
            self.llm = model_provider_manager.init_model(**self.model_config)

        except ValueError:
            raise ValueError(f"Model {model_name} is not supported as a chat model.")

    async def work(
            self, state: WorkflowTeamState, config: RunnableConfig
    ) -> ReturnWorkflowTeamState:
        """Execute the work of the Agent node"""

        if "node_outputs" not in state:
            state["node_outputs"] = {}

        history = state.get("history", [])
        messages = state.get("messages", [])
        all_messages = state.get("all_messages", [])

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

        # Prepare the input state for the Agent
        if self.user_prompt:
            parsed_user_prompt = (
                parse_variables(self.user_prompt, state["node_outputs"])
                .replace("{", "{{")
                .replace("}", "}}")
            )
            agent_input = {
                "messages": [{"role": "user", "content": parsed_user_prompt}]}
        else:
            agent_input = {
                "messages": [{"role": "user", "content": all_messages[-1].content}]}  # The last user-type message

        # Create React Agent
        self.agent = create_react_agent(
            model=self.llm,
            tools=self.tools_list,
            prompt=prompt,
        )

        # Invoke the Agent
        agent_result = await self.agent.ainvoke(agent_input)  # Get the final reply
        messages = agent_result["messages"]

        # Sanitize tool calls in all messages to fix common LLM issues like string "null" values
        from langchain_core.messages import AIMessage

        for msg in messages:
            if isinstance(msg, AIMessage) and hasattr(msg, "tool_calls") and msg.tool_calls:
                msg.tool_calls = sanitize_tool_calls_list(msg.tool_calls)

        # Find the first AI message from the end that does not contain a tool call
        for msg in reversed(messages):
            if msg.type == "ai" and not hasattr(msg, "tool_calls"):
                result = msg
                break
        else:
            # If no suitable AIMessage is found, use the last message
            result = messages[-1]

        # Update node_outputs
        new_output = {self.node_id: {"response": result.content}}
        state["node_outputs"] = update_node_outputs(state["node_outputs"], new_output)

        return_state: ReturnWorkflowTeamState = {
            "history": history + [result],
            "messages": [result] if hasattr(result, "tool_calls") and result.tool_calls else [],
            "all_messages": messages + [result],
            "node_outputs": state["node_outputs"],
        }

        return return_state
