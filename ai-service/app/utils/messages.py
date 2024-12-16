from langchain_core.messages import trim_messages
from app.services.models_service import get_openai_model, MAX_TOKENS
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage, AIMessage

trimmer = trim_messages(
    max_tokens=MAX_TOKENS,
    strategy="last",
    token_counter=get_openai_model(),
    # Usually, we want to keep the SystemMessage
    # if it's present in the original history.
    # The SystemMessage has special instructions for the model.
    include_system=True,
    # Most chat models expect that chat history starts with either:
    # (1) a HumanMessage or
    # (2) a SystemMessage followed by a HumanMessage
    # start_on="human" makes sure we produce a valid chat history
    start_on="human",
)

def get_message_prefix(msg):
    if isinstance(msg, AIMessage):
        return "AIMessage"
    elif isinstance(msg, HumanMessage):
        return "HumanMessage"
    elif isinstance(msg, SystemMessage):
        return "SystemMessage"
    elif isinstance(msg, ToolMessage):
        return "ToolMessage"
    else:
        return "UnknownMessage"