from enum import IntEnum, StrEnum


class HumanAction(StrEnum):
    CONTINUE = "continue"
    REFUSE = "refuse"


class MessageName(StrEnum):
    AI = "AI"
    HUMAN = "HUMAN"
    TOOL = "TOOL"
    ASSISTANT = "ASSISTANT"


class LlmProvider(IntEnum):
    OPENAI = 1
    ANTHROPIC = 2
    GOOGLE = 3
    MISTRAL = 4
    COHERE = 5
    LOCAL = 6


class MessageFormat(IntEnum):
    MARKDOWN = 1
    FILE = 2


class MessageRole(IntEnum):
    SYSTEM = 0
    HUMAN = 1
    AI = 2
    TOOL = 3


class ThreadFileStatus(IntEnum):
    FAILED = 0
    UPLOADED = 1
    VECTORIZING = 2
    VECTORIZED = 3