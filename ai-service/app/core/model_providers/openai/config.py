from crewai import LLM
from langchain_openai import ChatOpenAI
from pydantic import SecretStr

from app.core.enums import ModelCategory
from app.core.settings import env_settings

OPENAI_API_KEY = env_settings.OPENAI_API_KEY
OPENAI_API_BASE_URL = env_settings.OPENAI_API_BASE_URL

PROVIDER_CONFIG = {
    "provider_name": "openai",
    "base_url": OPENAI_API_BASE_URL,
    "api_key": OPENAI_API_KEY,
    "icon": "openai_icon",
    "description": "OpenAI model",
}

SUPPORTED_MODELS = [
    {
        "name": "gpt-4",
        "categories": [ModelCategory.LLM, ModelCategory.CHAT],
        "capabilities": [],
    },
    {
        "name": "gpt-4-0314",
        "categories": [ModelCategory.LLM, ModelCategory.CHAT],
        "capabilities": [],
    },
    {
        "name": "gpt-4-32k",
        "categories": [ModelCategory.LLM, ModelCategory.CHAT],
        "capabilities": [],
    },
    {
        "name": "gpt-4-32k-0314",
        "categories": [ModelCategory.LLM, ModelCategory.CHAT],
        "capabilities": [],
    },
    {
        "name": "gpt-3.5-turbo",
        "categories": [ModelCategory.LLM, ModelCategory.CHAT],
        "capabilities": [],
    },
    {
        "name": "gpt-3.5-turbo-16k",
        "categories": [ModelCategory.LLM, ModelCategory.CHAT],
        "capabilities": [],
    },
    {
        "name": "gpt-4o-mini",
        "categories": [ModelCategory.LLM, ModelCategory.CHAT],
        "capabilities": [],
    },
]


def init_model(model: str, temperature: float, api_key: str, base_url: str, **kwargs):
    model_info = next((m for m in SUPPORTED_MODELS if m["name"] == model), None)
    if model_info and ModelCategory.CHAT in model_info["categories"]:
        return ChatOpenAI(
            model=model,
            temperature=temperature,
            api_key=SecretStr(api_key),
            base_url=base_url,
            **kwargs,
        )
    else:
        raise ValueError(f"Model {model} is not supported as a chat model.")


def init_crewai_model(model: str, api_key: str, base_url: str, **kwargs):
    model_info = next((m for m in SUPPORTED_MODELS if m["name"] == model), None)
    if model_info and ModelCategory.CHAT in model_info["categories"]:
        return LLM(
            model=f"openai/{model}",  # CrewAI 格式：provider/model
            base_url=base_url,
            api_key=api_key,
            **kwargs,
        )
    else:
        raise ValueError(f"Model {model} is not supported as a chat model.")