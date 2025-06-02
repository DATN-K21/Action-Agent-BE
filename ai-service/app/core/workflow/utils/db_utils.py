from collections.abc import Callable
from typing import Any, TypeVar

from sqlalchemy.orm import Session

from app.core.db_session import get_db_session_sync

T = TypeVar("T")


def db_operation(operation: Callable[[Session], T]) -> T:
    """
    Execute a database operation synchronously.

    Args:
        operation: A callable that takes a Session and returns a result.

    Returns:
        The result of the operation.
    """
    with get_db_session_sync() as session:
        try:
            return operation(session)
        except Exception as e:
            session.rollback()
            raise e


# Example Usage
def get_all_models_helper():
    # from app.curd.models import get_all_models
    # return db_operation(get_all_models)

    raise NotImplementedError


def get_models_by_provider_helper(provider_id: int):
    # from app.curd.models import get_models_by_provider
    # return db_operation(lambda session: get_models_by_provider(session, provider_id))

    raise NotImplementedError


# More helper functions can be added as needed
def get_model_info(model_name: str) -> dict[str, str]:
    """
    Get model information from all available models.
    """
    # with get_db_session() as session:
    #     # 直接从数据库查询 Models 和关联的 ModelProvider
    #     model = session.exec(
    #         select(Models).join(ModelProvider).where(Models.ai_model_name == model_name)
    #     ).first()
    #
    #     if not model:
    #         raise ValueError(f"Model {model_name} not supported now.")
    #
    #     return {
    #         "ai_model_name": model.ai_model_name,
    #         "provider_name": model.provider.provider_name,
    #         "base_url": model.provider.base_url,
    #         "api_key": model.provider.decrypted_api_key,  # 现在可以使用decrypted_api_key
    #     }

    raise NotImplementedError


def get_subgraph_by_id(subgraph_id: int) -> dict[str, Any]:
    """
    Get subgraph config by ID.
    """
    # with get_db_session() as session:
    #     subgraph = session.get(Subgraph, subgraph_id)
    #     if not subgraph:
    #         raise ValueError(f"Subgraph {subgraph_id} not found")
    #     return subgraph.config, subgraph.name

    raise NotImplementedError
