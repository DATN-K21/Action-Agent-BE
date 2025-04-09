from langchain_openai import ChatOpenAI
from pydantic import SecretStr

from app.core.settings import env_settings


def get_openai_model(
    model: str = env_settings.DEFAULT_MODEL,
    temperature: float = 0,
    streaming: bool = False,
    api_key: str = env_settings.OPENAI_API_KEY,
):
    """
    Get an OpenAI language model.
    """
    return ChatOpenAI(temperature=temperature, streaming=streaming, model=model, api_key=SecretStr(api_key))
