from typing import Optional, Dict, Any

from langchain_core.runnables import RunnableConfig


def get_invocation_config(
        thread_id: Optional[str] = None,
        timezone: Optional[str] = None,
        recursion_limit: Optional[int] = None,
) -> RunnableConfig:
    configurable: Dict[str, Any] = {}

    if thread_id is not None:
        configurable["thread_id"] = thread_id
        configurable["search_kwargs"] = {"filter": {"namespace": {"$in": [thread_id]}}}

    if timezone is not None:
        configurable["timezone"] = timezone

    if recursion_limit is not None:
        return RunnableConfig(
            recursion_limit=recursion_limit,
            configurable=configurable,
        )
    
    return RunnableConfig(configurable=configurable)
