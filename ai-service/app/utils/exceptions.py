class ExecutingException(Exception):
    """An exception raised during execution."""
    status: int
    thread_id: str
    output: str
    detail: str
    def __init__(self, status: int, thread_id: str, output: str, detail: str):
        self.status = status
        self.thread_id = thread_id
        self.output = output
        self.detail = detail