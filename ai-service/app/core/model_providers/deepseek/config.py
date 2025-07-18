from functools import lru_cache

from crewai import LLM
from langchain_deepseek import ChatDeepSeek
from pydantic import SecretStr

from app.core.enums import ModelCategory
from app.core.settings import env_settings

DEEPSEEK_API_KEY = env_settings.DEEPSEEK_API_KEY
DEEPSEEK_API_BASE_URL = env_settings.DEEPSEEK_API_BASE_URL

PROVIDER_CONFIG = {
    "provider_name": "deepseek",
    "base_url": DEEPSEEK_API_BASE_URL,
    "api_key": DEEPSEEK_API_KEY,
    "icon": "deepseek_icon",
    "description": "DeepSeek AI model",
}

SUPPORTED_MODELS = [
    {
        "name": "deepseek-chat",
        "categories": [ModelCategory.LLM, ModelCategory.CHAT],
        "capabilities": [],
    },
    {
        "name": "deepseek-coder",
        "categories": [ModelCategory.LLM, ModelCategory.CHAT],
        "capabilities": [],
    },
    {
        "name": "deepseek-reasoner",
        "categories": [ModelCategory.LLM, ModelCategory.CHAT],
        "capabilities": [],
    },
    {
        "name": "deepseek-v2-chat",
        "categories": [ModelCategory.LLM, ModelCategory.CHAT],
        "capabilities": [],
    },
    {
        "name": "deepseek-v2-coder",
        "categories": [ModelCategory.LLM, ModelCategory.CHAT],
        "capabilities": [],
    },
    {
        "name": "deepseek-v2.5",
        "categories": [ModelCategory.LLM, ModelCategory.CHAT],
        "capabilities": [],
    },
]


@lru_cache(maxsize=32)
def init_model(model: str, temperature: float, api_key: str, base_url: str, **kwargs):
    model_info = next((m for m in SUPPORTED_MODELS if m["name"] == model), None)
    if model_info and ModelCategory.CHAT in model_info["categories"]:
        return ChatDeepSeek(
            model=model,
            temperature=temperature,
            api_key=SecretStr(api_key),
            base_url=base_url,
            disable_streaming=False,
            streaming=True,
            **kwargs,
        )
    else:
        raise ValueError(f"Model {model} is not supported as a chat model.")


@lru_cache(maxsize=32)
def init_crewai_model(model: str, api_key: str, base_url: str, **kwargs):
    model_info = next((m for m in SUPPORTED_MODELS if m["name"] == model), None)
    if model_info and ModelCategory.CHAT in model_info["categories"]:
        return LLM(
            model=f"deepseek/{model}",  # CrewAI 格式：provider/model
            base_url=base_url,
            api_key=api_key,
            **kwargs,
        )
    else:
        raise ValueError(f"Model {model} is not supported as a chat model.")
