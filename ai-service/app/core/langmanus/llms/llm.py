# Copyright (c) 2025 Bytedance Ltd. and/or its affiliates
# SPDX-License-Identifier: MIT

from typing import Union

from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from pydantic import SecretStr

from app.core.langmanus.config.agents import LLMType
from app.core.settings import env_settings

# Cache for LLM instances
_llm_cache: dict[LLMType, Union[ChatOpenAI, ChatAnthropic]] = {}


def _create_llm_from_settings(llm_type: LLMType) -> Union[ChatOpenAI, ChatAnthropic]:
    """
    Create LLM instance based on settings configuration for the given type.
    """
    # Map LLM types to their corresponding settings
    if llm_type == "basic":
        model_name = env_settings.LLM_BASIC_MODEL
        temperature = env_settings.BASIC_MODEL_TEMPERATURE
    elif llm_type == "reasoning":
        model_name = env_settings.LLM_REASONING_MODEL
        temperature = env_settings.REASONING_MODEL_TEMPERATURE
    elif llm_type == "vision":
        model_name = env_settings.LLM_VISION_MODEL
        temperature = env_settings.VISION_MODEL_TEMPERATURE
    else:
        raise ValueError(f"Unknown LLM type: {llm_type}")

    # Determine provider based on model name
    if model_name.startswith("claude") or model_name.startswith("anthropic"):
        # Anthropic model
        return ChatAnthropic(
            api_key=SecretStr(env_settings.ANTHROPIC_API_KEY),
            model_name=model_name,
            temperature=temperature,
            base_url=env_settings.ANTHROPIC_API_BASE_URL,
            timeout=60.0,  # Default timeout
            stop=None,  # Default stop sequences
        )
    else:
        # Default to OpenAI
        return ChatOpenAI(
            api_key=SecretStr(env_settings.OPENAI_API_KEY),
            model=model_name,
            temperature=temperature,
            base_url=env_settings.OPENAI_API_BASE_URL,
        )


def get_llm_by_type(
    llm_type: LLMType,
) -> Union[ChatOpenAI, ChatAnthropic]:
    """
    Get LLM instance by type. Returns cached instance if available.
    """
    if llm_type in _llm_cache:
        return _llm_cache[llm_type]

    llm = _create_llm_from_settings(llm_type)
    _llm_cache[llm_type] = llm
    return llm
