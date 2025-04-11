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