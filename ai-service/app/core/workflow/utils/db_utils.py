from collections.abc import Callable
from typing import Any, TypeVar

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db_session import SyncSessionLocal
from app.core.settings import env_settings
from app.db_models import Model, ModelProvider, Subgraph

T = TypeVar("T")


def db_operation(operation: Callable[[Session], T]) -> T:
    """
    Execute a database operation synchronously.

    Args:
        operation: A callable that takes a Session and returns a result.

    Returns:
        The result of the operation.
    """
    with SyncSessionLocal() as session:
        try:
            result = operation(session)
            session.commit()
            return result
        except Exception:
            session.rollback()
            raise


# Example Usage
def get_all_models_helper():
    # from app.curd.models import get_all_models
    # return db_operation(get_all_models)
    def _get_all_models(session: Session):
        stmt = (
            select(Model, ModelProvider)
            .join(ModelProvider, Model.provider_id == ModelProvider.id)
            .where(
                Model.is_deleted.is_(False),
                ModelProvider.is_deleted.is_(False),
            )
        )
        result = session.execute(stmt)
        models: list[dict[str, Any]] = []
        for model, provider in result.all():
            models.append(
                {
                    "ai_model_name": model.ai_model_name,
                    "provider_name": provider.provider_name,
                    "base_url": provider.base_url,
                    "api_key": provider.decrypted_api_key,
                    "categories": model.categories,
                    "capabilities": model.capabilities,
                    "metadata": model.metadata_,
                }
            )
        return models

    return db_operation(_get_all_models)


def get_models_by_provider_helper(provider_id: str):
    # from app.curd.models import get_models_by_provider
    # return db_operation(lambda session: get_models_by_provider(session, provider_id))
    def _get_models(session: Session):
        stmt = select(Model).where(Model.provider_id == provider_id, Model.is_deleted.is_(False))
        result = session.execute(stmt)
        return result.scalars().all()

    return db_operation(_get_models)


# More helper functions can be added as needed
def get_model_info(model_name: str) -> dict[str, str]:
    """
    Get model information from all available models.
    """
    return {
        "model_name": env_settings.LLM_BASIC_MODEL,
        "provider": env_settings.LLM_DEFAULT_PROVIDER,
        "base_url": env_settings.OPENAI_API_KEY,
        "api_key": env_settings.OPENAI_API_BASE_URL,
    }

    # def _get_info(session: Session) -> dict[str, str]:
    #     stmt = (
    #         select(Model, ModelProvider)
    #         .join(ModelProvider, Model.provider_id == ModelProvider.id)
    #         .where(
    #             Model.ai_model_name == model_name,
    #             Model.is_deleted.is_(False),
    #             ModelProvider.is_deleted.is_(False),
    #         )
    #     )
    #     result = session.execute(stmt).first()
    #     if not result:
    #         raise ValueError(f"Model {model_name} not supported now.")

    #     model, provider = result
    #     return {
    #         "ai_model_name": model.ai_model_name,
    #         "provider_name": provider.provider_name,
    #         "base_url": provider.base_url,
    #         "api_key": provider.decrypted_api_key,
    #     }

    # return db_operation(_get_info)


def get_subgraph_by_id(subgraph_id: str) -> tuple[str, dict[str, Any]]:
    """
    Get subgraph config by ID.
    """
    def _get_subgraph(session: Session) -> tuple[str, dict[str, Any]]:
        subgraph = session.get(Subgraph, subgraph_id)
        if not subgraph:
            raise ValueError(f"Subgraph {subgraph_id} not found")
        return subgraph.name, subgraph.config  # type: ignore

    return db_operation(_get_subgraph)
