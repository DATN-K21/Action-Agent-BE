from crewai import LLM
from langchain_openai import ChatOpenAI
from pydantic import SecretStr

from app.core.enums import ModelCategory

PROVIDER_CONFIG = {
    "provider_name": "siliconflow",
    "base_url": "https://api.siliconflow.cn/v1",
    "api_key": "",
    "icon": "siliconflow_icon",
    "description": "The model provided by SiliconFlow",
}

SUPPORTED_MODELS = [
    {
        "name": "Qwen/Qwen2.5-7B-Instruct",
        "categories": [ModelCategory.LLM, ModelCategory.CHAT],
        "capabilities": [],
    },
    {
        "name": "meta-llama/Meta-Llama-3.1-8B-Instruct",
        "categories": [ModelCategory.LLM, ModelCategory.CHAT],
        "capabilities": [],
    },
    {
        "name": "THUDM/glm-4-9b-chat",
        "categories": [ModelCategory.LLM, ModelCategory.CHAT],
        "capabilities": [],
    },
    {
        "name": "01-ai/Yi-1.5-9B-Chat-16K",
        "categories": [ModelCategory.LLM, ModelCategory.CHAT],
        "capabilities": [],
    },
    {
        "name": "google/gemma-2-9b-it",
        "categories": [ModelCategory.LLM, ModelCategory.CHAT],
        "capabilities": [],
    },
    {
        "name": "BAAI/bge-large-zh-v1.5",
        "categories": [ModelCategory.TEXT_EMBEDDING],
        "capabilities": [],
        "dimension": 1024,
    },
    {
        "name": "BAAI/bge-large-en-v1.5",
        "categories": [ModelCategory.TEXT_EMBEDDING],
        "capabilities": [],
        "dimension": 1024,
    },
    {
        "name": "BAAI/bge-m3",
        "categories": [ModelCategory.TEXT_EMBEDDING],
        "capabilities": [],
        "dimension": 1024,
    },
    {
        "name": "netease-youdao/bce-embedding-base_v1",
        "categories": [ModelCategory.TEXT_EMBEDDING],
        "capabilities": [],
        "dimension": 768,
    },
    {
        "name": "deepseek-ai/DeepSeek-R1-Distill-Llama-8B",
        "categories": [ModelCategory.LLM, ModelCategory.CHAT],
        "capabilities": [],
    },
    {
        "name": "deepseek-ai/DeepSeek-R1-Distill-Qwen-7B",
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
            model=f"openai/{model}",
            base_url=base_url,
            api_key=api_key,
            **kwargs,
        )
    else:
        raise ValueError(f"Model {model} is not supported as a chat model.")
