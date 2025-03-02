from langchain_openai import ChatOpenAI
from pydantic import SecretStr

from app.core.settings import env_settings

MAX_TOKENS = 10000


def get_openai_model(model: str = "gpt-3.5-turbo", temperature=0, streaming=True):
    """Get an OpenAI language model."""
    api_key = SecretStr(env_settings.OPENAI_API_KEY)
    return ChatOpenAI(temperature=temperature, streaming=streaming, model_name=model, openai_api_key=api_key)
