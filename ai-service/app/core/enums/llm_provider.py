from enum import IntEnum


class LLM_Provider(IntEnum):
    OPENAI = 1
    ANTHROPIC = 2
    GOOGLE = 3
    MISTRAL = 4
    COHERE = 5
    LOCAL = 6

    def __str__(self):
        return str(self.value)
