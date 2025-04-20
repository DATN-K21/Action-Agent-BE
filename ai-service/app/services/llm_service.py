from langchain_core.language_models.chat_models import BaseChatModel
from langchain_openai import ChatOpenAI
from pydantic import SecretStr

from app.core.enums import LlmProvider
from app.core.settings import env_settings

MAX_TOKENS = 10000


def _get_openai_model(
    model: str,
    temperature: float,
    api_key: SecretStr,
    timeout: int = 60,
    max_retries: int = 3,
    **kwargs,
) -> ChatOpenAI:
    """
    Get an OpenAI language model.
    """
    return ChatOpenAI(
        temperature=temperature,
        stream_usage=kwargs.get("streaming", False),
        model=model,
        api_key=api_key,
        timeout=timeout,
        max_retries=max_retries,
        **kwargs,
    )


def get_llm_chat_model(
    *,
    provider: LlmProvider = env_settings.LLM_DEFAULT_PROVIDER,
    model: str = env_settings.LLM_DEFAULT_MODEL,
    api_key: str = env_settings.LLM_DEFAULT_API_KEY,
    temperature: float = 0,
    **kwargs,
) -> BaseChatModel:
    """
    Get a chat model based on the provider.
    """
    match provider:
        case LlmProvider.OPENAI:
            return _get_openai_model(
                model=model,
                temperature=temperature,
                api_key=SecretStr(api_key),
                **kwargs,
            )
        case _:
            raise ValueError(f"Unsupported provider: {provider}. Supported are: {LlmProvider.supported_values()}")

