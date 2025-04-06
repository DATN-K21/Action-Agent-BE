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