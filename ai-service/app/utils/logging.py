import inspect
from functools import lru_cache


@lru_cache(maxsize=None)  # Infinite caching for coroutine checks
def is_async(func):
    return inspect.iscoroutinefunction(func)

@lru_cache(maxsize=None)  # Infinite caching for method checks
def is_method(func):
    signature = inspect.signature(func)
    return "self" in signature.parameters or "cls" in signature.parameters
