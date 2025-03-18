from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage, trim_messages

from app.services.model_service import MAX_TOKENS, AIModelService, AIModelProviderEnum

trimmer = trim_messages(
    max_tokens=MAX_TOKENS,
    strategy="last",
    token_counter=AIModelService.get_ai_model(provider=AIModelProviderEnum.langchain_openai),
    include_system=True,
    allow_partial=True,
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
