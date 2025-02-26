from typing import Optional, Dict, Any

from langchain_core.runnables import RunnableConfig


def get_invoking_config(
        thread_id: Optional[str] = None,
        user_id: Optional[str] = None,
        connected_account_id: Optional[str] = None,
        recursion_limit: int = 10,
) -> RunnableConfig:
    configurable: Dict[str, Any] = {}

    if thread_id is not None:
        configurable["thread_id"] = thread_id
        configurable["search_kwargs"] = {"filter": {"namespace": {"$in": [thread_id]}}}

    if user_id is not None:
        configurable["user_id"] = user_id

    if connected_account_id is not None:
        configurable["connected_account_id"] = connected_account_id

    return RunnableConfig(
        recursion_limit=recursion_limit,
        configurable=configurable,
    )