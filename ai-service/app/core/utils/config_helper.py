from typing import Optional, Dict, Any

from langchain_core.runnables import RunnableConfig


def get_invocation_config(
        thread_id: Optional[str] = None,
        recursion_limit: int = 10,
) -> RunnableConfig:
    configurable: Dict[str, Any] = {}

    if thread_id is not None:
        configurable["thread_id"] = thread_id
        configurable["search_kwargs"] = {"filter": {"namespace": {"$in": [thread_id]}}}

    return RunnableConfig(
        recursion_limit=recursion_limit,
        configurable=configurable,
    )
