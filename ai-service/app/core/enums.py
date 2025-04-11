from enum import IntEnum, StrEnum


class HumanAction(StrEnum):
    CONTINUE = "continue"
    REFUSE = "refuse"


class MessageName(StrEnum):
    AI = "AI"
    HUMAN = "HUMAN"
    TOOL = "TOOL"
    ASSISTANT = "ASSISTANT"


class LlmProvider(StrEnum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    MISTRAL = "mistral"
    COHERE = "cohere"
    LOCAL = "local"

    def __str__(self):
        return self.value

    @classmethod
    def supported_values(cls):
        return [provider.value for provider in cls]


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