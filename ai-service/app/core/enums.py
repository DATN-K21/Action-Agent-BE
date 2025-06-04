from enum import Enum


class UploadStatus(str, Enum):
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"
    FAILED = "Failed"


class ThreadType(str, Enum):
    MCPS_ASSISTANT = "Mcp Assistant"
    EXTENSIONS_ASSISTANT = "Extensions Assistant"
    MCP_AGENT = "Mcp Agent"
    EXTENSION_AGENT = "Extension Agent"
    DEFAULT = "Default"


class ChatMessageType(str, Enum):
    human = "human"
    ai = "ai"


class InterruptType(str, Enum):
    TOOL_REVIEW = "tool_review"
    OUTPUT_REVIEW = "output_review"
    CONTEXT_INPUT = "context_input"


class InterruptDecision(str, Enum):
    APPROVED = "approved"
    REJECTED = "rejected"
    REPLIED = "replied"
    UPDATE = "update"
    FEEDBACK = "feedback"
    REVIEW = "review"
    EDIT = "edit"
    CONTINUE = "continue"


class ModelCategory(str, Enum):
    LLM = "llm"
    CHAT = "chat"
    TEXT_EMBEDDING = "text-embedding"
    RERANK = "rerank"
    SPEECH_TO_TEXT = "speech-to-text"
    TEXT_TO_SPEECH = "text-to-speech"


class ModelCapability(str, Enum):
    VISION = "vision"


class LlmProvider(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    MISTRAL = "mistral"
    COHERE = "cohere"
    LOCAL = "local"

    @classmethod
    def supported_values(cls) -> list[str]:
        return [member for member in cls]


class StorageStrategy(str, Enum):
    PERSONAL_TOOL_CACHE = "personal_tool_cache"
    GLOBAL_TOOLS = "global_tools"
    DEFINITION = "definition"


class ConnectedServiceType(str, Enum):
    MCP = "mcp"
    EXTENSION = "extension"
    NONE = "None"


class ConnectionStatus(str, Enum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"