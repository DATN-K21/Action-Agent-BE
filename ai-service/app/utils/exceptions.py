from typing import Optional


class ExecutingException(Exception):
    """An exception raised during execution."""

    status: int
    user_id: Optional[str] = None
    thread_id: Optional[str] = None
    output: str
    detail: str

    def __init__(
        self,
        status: int,
        user_id: Optional[str] = None,
        thread_id: Optional[str] = None,
        output: str = "",
        detail: str = "",
    ):
        self.status = status
        self.user_id = user_id
        self.thread_id = thread_id
        self.output = output
        self.detail = detail


class UnknownException(Exception):
    status: int
    output: str
    detail: str

    def __init__(
        self,
        status: int,
        output: str = "",
        detail: str = "",
    ):
        self.status = status
        self.output = output
        self.detail = detail
