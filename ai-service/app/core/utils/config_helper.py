from typing import Any, Dict, Optional

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


def get_runnable_config(
    thread_id: Optional[str],
    timezone: Optional[str],
    recursion_limit: Optional[int],
) -> RunnableConfig:
    """
    Get the runnable config for the agent.
    """
    configurable: Dict[str, Any] = {}

    if thread_id is not None and thread_id != "":
        configurable["thread_id"] = thread_id

    if timezone is not None and timezone != "":
        configurable["timezone"] = timezone

    if recursion_limit is not None and recursion_limit > 0:
        return RunnableConfig(
            recursion_limit=recursion_limit,
            configurable=configurable,
        )

    return RunnableConfig(configurable=configurable)
