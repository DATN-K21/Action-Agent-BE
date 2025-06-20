# Copyright (c) 2025 Bytedance Ltd. and/or its affiliates
# SPDX-License-Identifier: MIT

import os
from pathlib import Path
from typing import Any, Dict, Union

from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI

from app.core.langmanus.config import load_yaml_config
from app.core.langmanus.config.agents import LLMType

# Cache for LLM instances
_llm_cache: dict[LLMType, Union[ChatOpenAI, ChatAnthropic]] = {}


def _get_env_llm_conf(llm_type: str) -> Dict[str, Any]:
    """
    Get LLM configuration from environment variables.
    Environment variables should follow the format: {LLM_TYPE}__{KEY}
    e.g., BASIC_MODEL__api_key, BASIC_MODEL__base_url
    """
    prefix = f"{llm_type.upper()}_MODEL__"
    conf = {}
    for key, value in os.environ.items():
        if key.startswith(prefix):
            conf_key = key[len(prefix) :].lower()
            conf[conf_key] = value
    return conf


def _create_llm_use_conf(llm_type: LLMType, conf: Dict[str, Any]) -> Union[ChatOpenAI, ChatAnthropic]:
    llm_type_map = {
        "reasoning": conf.get("REASONING_MODEL", {}),
        "basic": conf.get("BASIC_MODEL", {}),
        "vision": conf.get("VISION_MODEL", {}),
    }
    llm_conf = llm_type_map.get(llm_type)
    if not isinstance(llm_conf, dict):
        raise ValueError(f"Invalid LLM Conf: {llm_type}")
    # Get configuration from environment variables
    env_conf = _get_env_llm_conf(llm_type)

    # Merge configurations, with environment variables taking precedence
    merged_conf = {**llm_conf, **env_conf}

    if not merged_conf:
        raise ValueError(f"Unknown LLM Conf: {llm_type}")

    # Determine provider and create appropriate LLM instance
    provider = merged_conf.get("provider", "openai").lower()

    if provider == "anthropic":
        # Convert OpenAI-style parameters to Anthropic equivalents
        anthropic_conf = {}
        if "api_key" in merged_conf:
            anthropic_conf["api_key"] = merged_conf["api_key"]
        if "model_name" in merged_conf:
            anthropic_conf["model"] = merged_conf["model_name"]
        elif "model" in merged_conf:
            anthropic_conf["model"] = merged_conf["model"]
        if "temperature" in merged_conf:
            anthropic_conf["temperature"] = merged_conf["temperature"]
        if "max_tokens" in merged_conf:
            anthropic_conf["max_tokens"] = merged_conf["max_tokens"]

        return ChatAnthropic(**anthropic_conf)
    else:
        # Default to OpenAI
        return ChatOpenAI(**merged_conf)


def get_llm_by_type(
    llm_type: LLMType,
) -> Union[ChatOpenAI, ChatAnthropic]:
    """
    Get LLM instance by type. Returns cached instance if available.
    """
    if llm_type in _llm_cache:
        return _llm_cache[llm_type]

    conf = load_yaml_config(
        os.getenv(
            "FLOCK_CONFIG_PATH",
            str(Path(__file__).resolve().parents[4] / "conf.yaml"),
        )
    )

    llm = _create_llm_use_conf(llm_type, conf)
    _llm_cache[llm_type] = llm
    return llm


# In the future, we will use reasoning_llm and vl_llm for different purposes
# reasoning_llm = get_llm_by_type("reasoning")
# vl_llm = get_llm_by_type("vision")


if __name__ == "__main__":
    # Initialize LLMs for different purposes - now these will be cached
    basic_llm = get_llm_by_type("basic")
    print(basic_llm.invoke("Hello"))
