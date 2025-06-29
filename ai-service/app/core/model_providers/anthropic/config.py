from crewai import LLM
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from pydantic import SecretStr

from app.core.enums import ModelCapability, ModelCategory
from app.core.settings import env_settings

ANTHROPIC_API_KEY = env_settings.ANTHROPIC_API_KEY
ANTHROPIC_API_BASE_URL = env_settings.ANTHROPIC_API_BASE_URL

PROVIDER_CONFIG = {
    "provider_name": "anthropic",
    "base_url": ANTHROPIC_API_BASE_URL,
    "api_key": ANTHROPIC_API_KEY,
    "icon": "anthropic_icon",
    "description": "Claude models provided by Anthropic",
}

SUPPORTED_MODELS = [
    {
        "name": "claude-3-5-sonnet-20241022",
        "categories": [ModelCategory.LLM, ModelCategory.CHAT],
        "capabilities": [ModelCapability.VISION],
    },
    {
        "name": "claude-3-5-sonnet-20240620",
        "categories": [ModelCategory.LLM, ModelCategory.CHAT],
        "capabilities": [ModelCapability.VISION],
    },
    {
        "name": "claude-3-5-haiku-20241022",
        "categories": [ModelCategory.LLM, ModelCategory.CHAT],
        "capabilities": [ModelCapability.VISION],
    },
    {
        "name": "claude-3-opus-20240229",
        "categories": [ModelCategory.LLM, ModelCategory.CHAT],
        "capabilities": [ModelCapability.VISION],
    },
    {
        "name": "claude-3-sonnet-20240229",
        "categories": [ModelCategory.LLM, ModelCategory.CHAT],
        "capabilities": [ModelCapability.VISION],
    },
    {
        "name": "claude-3-haiku-20240307",
        "categories": [ModelCategory.LLM, ModelCategory.CHAT],
        "capabilities": [ModelCapability.VISION],
    },
]


def init_model(model: str, temperature: float, api_key: str, base_url: str, **kwargs):
    """Initialize a ChatAnthropic model for LangChain."""
    model_info = next((m for m in SUPPORTED_MODELS if m["name"] == model), None)
    if model_info and ModelCategory.CHAT in model_info["categories"]:
        return ChatAnthropic(
            model_name=model,
            temperature=temperature,
            api_key=SecretStr(api_key),
            base_url=base_url,
            **kwargs,
        ).with_fallbacks(
            [
                ChatOpenAI(
                    model="gpt-4o-mini",  # Fallback to OpenAI's gpt-4o-mini
                    temperature=temperature,
                    api_key=SecretStr(env_settings.OPENAI_API_KEY),
                    base_url=env_settings.OPENAI_API_BASE_URL,
                    **kwargs,
                )
            ]
        )
    else:
        raise ValueError(f"Model {model} is not supported as a chat model.")


def init_crewai_model(model: str, api_key: str, base_url: str, **kwargs):
    """Initialize an Anthropic model for CrewAI."""
    model_info = next((m for m in SUPPORTED_MODELS if m["name"] == model), None)
    if model_info and ModelCategory.CHAT in model_info["categories"]:
        return LLM(
            model=f"anthropic/{model}",  # CrewAI format: provider/model
            base_url=base_url,
            api_key=api_key,
            **kwargs,
        )
    else:
        raise ValueError(f"Model {model} is not supported as a chat model.")
