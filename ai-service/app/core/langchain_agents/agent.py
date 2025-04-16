from langchain_core.tools import Tool
from langgraph.prebuilt import create_react_agent

from app.services.model_service import get_openai_model


def make_graph(tools: list[Tool]):
    agent = create_react_agent(model=get_openai_model(), tools=tools, debug=True)
    return agent
