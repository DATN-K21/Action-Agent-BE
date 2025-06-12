from crewai import LLM
from langchain_anthropic import ChatAnthropic
from pydantic import SecretStr

from app.core.enums import ModelCapability, ModelCategory

PROVIDER_CONFIG = {
    "provider_name": "anthropic",
    "base_url": "https://api.anthropic.com",
    "api_key": "",
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
            **kwargs,
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
