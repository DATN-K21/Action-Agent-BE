from enum import StrEnum

from langchain_openai import ChatOpenAI, AzureChatOpenAI
from pydantic import SecretStr

from app.core.settings import env_settings

MAX_TOKENS = 10000


class AIModelProviderEnum(StrEnum):
    LANGCHAIN_OPENAI = "langchain_openai"
    LANGCHAIN_AZURE_OPENAI = "langchain_azure_openai"


def convert_provider_str_to_enum(provider: str = env_settings.DEFAULT_PROVIDER) -> AIModelProviderEnum:
    """Convert a string to an AIModelProviderEnum."""
    if provider == "openai":
        return AIModelProviderEnum.LANGCHAIN_OPENAI
    elif provider == "azure-openai":
        return AIModelProviderEnum.LANGCHAIN_AZURE_OPENAI
    else:
        raise ValueError(f"Invalid AI model provider: {provider}")


class AIModelService:
    """Service class for retrieving AI models from various providers."""

    @classmethod
    def _get_langchain_openai_model(
            cls,
            model: str = env_settings.DEFAULT_MODEL,
            temperature: float = 0,
            streaming: bool = True
    ):
        """Get an OpenAI language model."""
        api_key = SecretStr(env_settings.OPENAI_API_KEY)
        return ChatOpenAI(temperature=temperature, streaming=streaming, model_name=model, openai_api_key=api_key)

    @classmethod
    def _get_langchain_azure_openai_model(
            cls,
            model: str = env_settings.DEFAULT_MODEL,
            temperature: float = 0,
            streaming: bool = True
    ):
        """Get an Azure OpenAI language model."""
        api_key = SecretStr(env_settings.AZURE_OPENAI_API_KEY)
        api_base = env_settings.AZURE_OPENAI_API_BASE
        api_version = env_settings.AZURE_OPENAI_API_VERSION
        return AzureChatOpenAI(
            openai_api_key=api_key,
            azure_endpoint=api_base,
            openai_api_version=api_version,
            temperature=temperature,
            streaming=streaming,
            model_name=model
        )

    @classmethod
    def get_ai_model(
            cls,
            provider: AIModelProviderEnum = convert_provider_str_to_enum(),
            model: str = env_settings.DEFAULT_MODEL,
            temperature: float = 0,
            streaming: bool = True,
    ):
        """Get an AI model from the specified provider."""
        if provider == AIModelProviderEnum.LANGCHAIN_OPENAI:
            return cls._get_langchain_openai_model(model=model, temperature=temperature, streaming=streaming)
        elif provider == AIModelProviderEnum.LANGCHAIN_AZURE_OPENAI:
            return cls._get_langchain_azure_openai_model()
        else:
            raise ValueError(f"Invalid provider: {provider}")
