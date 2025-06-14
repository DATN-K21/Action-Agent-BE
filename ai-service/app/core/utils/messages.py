import tiktoken
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage, trim_messages

from app.core.settings import env_settings
from app.services.llm_service import MAX_TOKENS, get_llm_chat_model

trimmer = trim_messages(
    max_tokens=MAX_TOKENS,
    strategy="last",
    token_counter=get_llm_chat_model(),
    include_system=True,
    allow_partial=True,
)


def truncate_text(text: str, max_tokens: int = MAX_TOKENS, model: str = env_settings.LLM_DEFAULT_MODEL) -> str:
    """Truncate text if the token count exceeds the limit."""
    encoding = tiktoken.encoding_for_model(model)
    tokens = encoding.encode(text)

    if len(tokens) <= max_tokens:
        return text  # No truncation needed

    truncated_tokens = tokens[:max_tokens]
    truncated_text = encoding.decode(truncated_tokens)

    return truncated_text + "..."  # Indicate truncation


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
