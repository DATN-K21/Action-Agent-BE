from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage, trim_messages
from tiktoken import encoding_for_model

from app.services.model_service import get_openai_model

MAX_TOKENS = 10000


trimmer = trim_messages(
    max_tokens=MAX_TOKENS,
    strategy="last",
    token_counter=get_openai_model(),
    include_system=True,
    allow_partial=True,
)

def get_tokens(text: str, model: str) -> list[int]:
    """
    Get the tokens for a given text using the specified model.
    This function uses the tiktoken library to encode the text into tokens.
    """
    return encoding_for_model(model).encode(text)


def truncate_text(text: str, max_tokens: int = MAX_TOKENS, model: str = "gpt-3.5-turbo") -> str:
    """
    Truncate text if the token count exceeds the limit.
    """
    encoding = encoding_for_model(model)
    tokens = encoding.encode(text)

    if len(tokens) <= max_tokens:
        return text  # No truncation needed

    truncated_tokens = tokens[:max_tokens]
    return encoding.decode(truncated_tokens) + "..."  # Indicate truncation


def get_message_prefix(msg):
    """
    Get the prefix of a message based on its type.
    """
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
