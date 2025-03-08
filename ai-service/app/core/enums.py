from enum import Enum


class HumanAction(str, Enum):
    CONTINUE = "continue"
    REFUSE = "refuse"


class MessageName(str, Enum):
    AI = "AI"
    HUMAN = "HUMAN"
    TOOL = "TOOL"
    ASSISTANT = "ASSISTANT"
