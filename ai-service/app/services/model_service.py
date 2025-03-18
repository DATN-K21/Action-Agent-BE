from enum import StrEnum

from langchain_openai import ChatOpenAI
from pydantic import SecretStr

from app.core.g4f_chat_model import ChatG4F
from app.core.settings import env_settings

MAX_TOKENS = 10000


class AIModelProviderEnum(StrEnum):
    langchain_openai = "langchain_openai"
    gpt4free = "gpt4free"


class AIModelService:
    """Service class for retrieving AI models from various providers."""

    @classmethod
    def _get_langchain_openai_model(
            cls,
            model: str = "gpt-3.5-turbo",
            temperature: float = 0,
            streaming: bool = True
    ):
        """Get an OpenAI language model."""
        api_key = SecretStr(env_settings.OPENAI_API_KEY)
        return ChatOpenAI(temperature=temperature, streaming=streaming, model_name=model, openai_api_key=api_key)

    @classmethod
    def _get_gpt4free_llm(cls):
        """Get a GPT-4-free language model."""
        return ChatG4F(temperature=0, streaming=True, model_name="gpt-4")

    @classmethod
    def get_ai_model(
            cls,
            provider: AIModelProviderEnum = AIModelProviderEnum.langchain_openai,
            model: str = "gpt-3.5-turbo",
            temperature: float = 0,
            streaming: bool = True,
    ):
        """Get an AI model from the specified provider."""
        if provider == AIModelProviderEnum.langchain_openai:
            return cls._get_langchain_openai_model(model=model, temperature=temperature, streaming=streaming)
        elif provider == AIModelProviderEnum.gpt4free:
            return cls._get_gpt4free_llm()
        else:
            raise ValueError(f"Invalid provider: {provider}")
