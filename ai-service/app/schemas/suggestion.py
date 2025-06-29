from typing import Any, Dict, List, Optional

from pydantic import Field

from app.schemas.base import BaseRequest, BaseResponse


class SuggestionContext(BaseRequest):
    """Context information for generating suggestions"""

    current_text: str = Field(..., description="Current text content")
    cursor_position: int = Field(..., description="Current cursor position in the text")
    context_type: str = Field(..., description="Type of context (prompt, tool_call, argument, etc.)")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional context metadata")


class InlineSuggestionRequest(BaseRequest):
    """Request for inline suggestions at cursor position"""

    context: SuggestionContext = Field(..., description="Context for generating suggestions")
    max_suggestions: int = Field(3, ge=1, le=10, description="Maximum number of suggestions to return")
    suggestion_type: str = Field("auto", description="Type of suggestion: auto, prompt, tool, argument")


class SuggestionItem(BaseResponse):
    """Individual suggestion item"""

    text: str = Field(..., description="Suggested text")
    completion_text: str = Field(..., description="Text to be inserted at cursor")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score of the suggestion")
    suggestion_type: str = Field(..., description="Type of suggestion")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional suggestion metadata")


class InlineSuggestionResponse(BaseResponse):
    """Response containing inline suggestions"""

    suggestions: List[SuggestionItem] = Field(..., description="List of suggestions")
    context_id: str = Field(..., description="Unique identifier for this suggestion context")


class ChatGenerationRequest(BaseRequest):
    """Request for chat-based text generation"""

    prompt: str = Field(..., description="User prompt for text generation")
    context: Optional[SuggestionContext] = Field(None, description="Optional context information")
    generation_type: str = Field("general", description="Type of generation: general, prompt, tool_usage, etc.")
    max_length: int = Field(500, ge=1, le=2000, description="Maximum length of generated text")
    temperature: float = Field(0.7, ge=0.0, le=2.0, description="Generation temperature")


class ChatGenerationResponse(BaseResponse):
    """Response containing generated text"""

    generated_text: str = Field(..., description="Generated text content")
    generation_type: str = Field(..., description="Type of generation performed")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional generation metadata")


class SuggestionFeedbackRequest(BaseRequest):
    """Request to provide feedback on suggestions"""

    context_id: str = Field(..., description="Context identifier from the suggestion")
    selected_suggestion: Optional[int] = Field(None, description="Index of selected suggestion (if any)")
    feedback_type: str = Field(..., description="Type of feedback: accepted, rejected, modified")
    user_action: str = Field(..., description="User action taken: tab_completion, manual_edit, ignored")
