import importlib
import os
from collections.abc import Callable
from typing import Any

from app.core.settings import env_settings


class ModelProviderManager:
    def __init__(self):
        self.providers: dict[str, dict[str, Any]] = {}
        self.models: dict[str, list[dict[str, Any]]] = {}
        self.init_functions: dict[str, Callable] = {}
        self.init_crewai_functions: dict[str, Callable] = {}
        self.load_providers()

    def load_providers(self):
        providers_dir = os.path.dirname(os.path.abspath(__file__))
        for item in os.listdir(providers_dir):
            if os.path.isdir(os.path.join(providers_dir, item)) and not item.startswith(
                "__"
            ):
                try:
                    module = importlib.import_module(
                        f".{item}.config", package="app.core.model_providers"
                    )
                    provider_config = getattr(module, "PROVIDER_CONFIG", None)
                    supported_models = getattr(module, "SUPPORTED_MODELS", [])
                    init_function = getattr(module, "init_model", None)
                    init_crewai_function = getattr(module, "init_crewai_model", None)

                    if provider_config and init_function:
                        self.providers[item] = provider_config
                        self.models[item] = supported_models  # type: ignore
                        self.init_functions[item] = init_function
                        if init_crewai_function:
                            self.init_crewai_functions[item] = init_crewai_function
                except ImportError as e:
                    print(f"Failed to load provider config for {item}: {e}")

    def get_provider_config(self, provider_name: str) -> dict[str, Any]:
        return self.providers.get(provider_name, {})

    def get_supported_models(self, provider_name: str) -> list[dict[str, Any]]:
        return self.models.get(provider_name, [])

    def get_all_providers(self) -> dict[str, dict[str, Any]]:
        return self.providers

    def get_all_models(self) -> dict[str, list[dict[str, Any]]]:
        return self.models

    def get_model_info(self, model_name: str | None) -> dict[str, Any]:
        for key, value in self.models.items():
            for model in value:
                if model["name"] == model_name:
                    return {
                        "provider": key,
                        "model_name": model["name"],
                        "base_url": self.providers[key]["base_url"],
                        "api_key": self.providers[key]["api_key"],
                    }

        # If model not found, return an default configuration
        return {
            "provider": env_settings.OPENAI_PROVIDER,
            "model_name": env_settings.LLM_BASIC_MODEL,
            "base_url": env_settings.OPENAI_API_BASE_URL,
            "api_key": env_settings.OPENAI_API_KEY,
        }

    def init_model(
        self,
        provider_name: str,
        model: str,
        temperature: float,
        api_key: str,
        base_url: str,
        **kwargs,
    ):
        init_function = self.init_functions.get(provider_name)
        if init_function:

            return init_function(model, temperature, api_key, base_url, **kwargs)
        else:
            raise ValueError(
                f"No initialization function found for provider: {provider_name}"
            )

    def init_crewai_model(
        self,
        provider_name: str,
        model: str,
        api_key: str,
        base_url: str,
        **kwargs,
    ):
        init_function = self.init_crewai_functions.get(provider_name)
        if init_function:
            return init_function(model, api_key, base_url, **kwargs)
        else:
            raise ValueError(
                f"No crewai initialization function found for provider: {provider_name}"
            )


model_provider_manager = ModelProviderManager()
