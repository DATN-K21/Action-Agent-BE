import uuid
from typing import List

from fastapi import APIRouter, HTTPException, status
from langchain_core.messages import HumanMessage, SystemMessage

from app.core import logging
from app.core.enums import SuggestionContextType
from app.core.settings import env_settings
from app.schemas.base import MessageResponse, ResponseWrapper
from app.schemas.suggestion import (
    ChatGenerationRequest,
    ChatGenerationResponse,
    InlineSuggestionRequest,
    InlineSuggestionResponse,
    SuggestionItem,
)
from app.services.llm_service import get_llm_chat_model

logger = logging.get_logger(__name__)

router = APIRouter(prefix="/suggestion", tags=["Suggestion"])


class SuggestionService:
    """Service for handling suggestion generation using OpenAI GPT-4.1-mini"""

    def __init__(self):
        self._llm_model = None

    def _get_llm_model(self):
        """Get the LLM model for suggestion generation"""
        if self._llm_model is None:
            self._llm_model = get_llm_chat_model(
                provider=env_settings.SUGGESTION_LLM_PROVIDER,
                model=env_settings.LLM_SUGGESTION_MODEL,
                api_key=env_settings.SUGGESTION_MODEL_API_KEY,
                base_url=env_settings.SUGGESTION_MODEL_API_BASE_URL,
                temperature=env_settings.SUGGESTION_MODEL_TEMPERATURE,
                max_tokens=env_settings.SUGGESTION_MODEL_MAX_TOKENS,
            )
        return self._llm_model

    async def generate_inline_suggestions(self, request: InlineSuggestionRequest) -> InlineSuggestionResponse:
        """Generate inline suggestions based on context"""
        context = request.context
        context_id = str(uuid.uuid4())

        suggestions = []

        try:
            # Generate suggestions based on context type
            if context.context_type == SuggestionContextType.PROMPT:
                suggestions = await self._generate_prompt_suggestions(context, request.max_suggestions)
            elif context.context_type == SuggestionContextType.TOOL_CALL:
                suggestions = await self._generate_tool_suggestions(context, request.max_suggestions)
            elif context.context_type == SuggestionContextType.ARGUMENT:
                suggestions = await self._generate_argument_suggestions(context, request.max_suggestions)
            else:
                suggestions = await self._generate_general_suggestions(context, request.max_suggestions)

        except Exception as e:
            logger.error(f"Error generating suggestions: {str(e)}")
            # Return empty suggestions on error
            suggestions = []

        return InlineSuggestionResponse(suggestions=suggestions, context_id=context_id)

    async def generate_chat_response(self, request: ChatGenerationRequest) -> ChatGenerationResponse:
        """Generate text response for chat-based interaction"""
        try:
            if request.generation_type == "prompt":
                generated_text = await self._generate_prompt_assistance(request)
            elif request.generation_type == "tool_usage":
                generated_text = await self._generate_tool_usage_assistance(request)
            else:
                generated_text = await self._generate_general_assistance(request)

            return ChatGenerationResponse(
                generated_text=generated_text,
                generation_type=request.generation_type,
                metadata={
                    "prompt_length": len(request.prompt),
                    "has_context": request.context is not None,
                    "context_length": len(request.context) if request.context else 0,
                },
            )

        except Exception as e:
            logger.error(f"Error generating chat response: {str(e)}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to generate response: {str(e)}")

    async def _generate_prompt_suggestions(self, context, max_suggestions: int) -> List[SuggestionItem]:
        """Generate suggestions for prompt completion using GPT-4.1-mini"""
        current_text = context.current_text
        cursor_pos = context.cursor_position

        # Extract text before cursor
        text_before = current_text[:cursor_pos]
        text_after = current_text[cursor_pos:]

        # Create prompt for GPT-4.1-mini
        system_prompt = """You are an AI assistant that helps users write better prompts for action execution and tool usage. 
        Given the current text and cursor position, suggest ONLY the completion text that should be added after the cursor.
        Focus on:
        - Clear action instructions
        - Proper tool usage syntax
        - Parameter specifications
        - Context clarity
        
        IMPORTANT: 
        1. Respond in the same language as the user's input. If the user writes in Vietnamese, respond in Vietnamese. If in English, respond in English.
        2. Return ONLY the text that should be added after the cursor position, NOT the full sentence.
        3. Do NOT repeat the text before cursor in your suggestions.
        4. One suggestion per line, without explanations."""

        user_prompt = f"""Current text: "{current_text}"
        Cursor position: {cursor_pos}
        Text before cursor: "{text_before}"
        Text after cursor: "{text_after}"
        
        Please suggest {max_suggestions} completion texts that should be added RIGHT AFTER the cursor position to improve this prompt.
        Do NOT include the text before cursor in your suggestions - only provide the continuation text."""

        try:
            llm = self._get_llm_model()
            messages = [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]

            response = await llm.ainvoke(messages)
            suggestions_text = response.content
            if isinstance(suggestions_text, list):
                suggestions_text = "\n".join(str(item) for item in suggestions_text)
            suggestions_text = suggestions_text.strip()

            # Parse the response into suggestions
            suggestion_lines = [line.strip() for line in suggestions_text.split("\n") if line.strip()]

            suggestions = []
            for i, suggestion_text in enumerate(suggestion_lines[:max_suggestions]):
                confidence = 0.9 - (i * 0.1)  # Decreasing confidence

                # Ensure proper spacing between text_before and suggestion_text
                if text_before and not text_before.endswith(" ") and not suggestion_text.startswith(" "):
                    full_text = f"{text_before} {suggestion_text}"
                    completion_text = f" {suggestion_text}"
                else:
                    full_text = f"{text_before}{suggestion_text}"
                    completion_text = suggestion_text

                suggestions.append(
                    SuggestionItem(
                        text=full_text,
                        completion_text=completion_text,
                        confidence=confidence,
                        suggestion_type="prompt",
                        metadata={"generated_by": "gpt-4.1-mini", "context_type": "prompt_completion"},
                    )
                )

            return suggestions

        except Exception as e:
            logger.error(f"Error generating prompt suggestions with GPT-4.1-mini: {str(e)}")
            # Fallback to template-based suggestions
            return await self._generate_fallback_prompt_suggestions(context, max_suggestions)

    async def _generate_fallback_prompt_suggestions(self, context, max_suggestions: int) -> List[SuggestionItem]:
        """Fallback method for prompt suggestions when GPT-4.1-mini fails"""
        current_text = context.current_text
        cursor_pos = context.cursor_position
        text_before = current_text[:cursor_pos]

        # Choose templates based on detected language
        prompt_templates = [
            "Please help me to",
            "Can you assist with",
            "I need guidance on",
            "Show me how to",
            "Explain the process of",
        ]

        suggestions = []
        for i, template in enumerate(prompt_templates[:max_suggestions]):
            confidence = 0.7 - (i * 0.1)  # Lower confidence for fallback

            # Ensure proper spacing between text_before and template
            if text_before and not text_before.endswith(" ") and not template.startswith(" "):
                full_text = f"{text_before} {template}"
                completion_text = f" {template}"
            else:
                full_text = f"{text_before}{template}"
                completion_text = template

            suggestions.append(
                SuggestionItem(
                    text=full_text,
                    completion_text=completion_text,
                    confidence=confidence,
                    suggestion_type="prompt",
                    metadata={"template": template, "fallback": True},
                )
            )

        return suggestions

    async def _generate_tool_suggestions(self, context, max_suggestions: int) -> List[SuggestionItem]:
        """Generate suggestions for tool usage using GPT-4.1-mini"""
        current_text = context.current_text
        cursor_pos = context.cursor_position

        system_prompt = """You are an AI assistant that helps users select and use appropriate tools for their tasks.
        Given the current context, suggest ONLY the completion text that should be added after the cursor.
        Focus on:
        - Appropriate tool selection
        - Proper tool invocation syntax
        - Common tool usage patterns
        - Tool parameter suggestions
        
        IMPORTANT: 
        1. Respond in the same language as the user's input. If the user writes in Vietnamese, respond in Vietnamese. If in English, respond in English.
        2. Return ONLY the text that should be added after the cursor position.
        3. One suggestion per line, without explanations."""

        user_prompt = f"""Current text: "{current_text}"
        Cursor position: {cursor_pos}
        Context type: tool_call
        
        Please suggest {max_suggestions} completion texts that should be added RIGHT AFTER the cursor position for tool usage.
        Do NOT include the existing text in your suggestions - only provide the continuation text."""

        try:
            llm = self._get_llm_model()
            messages = [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]

            response = await llm.ainvoke(messages)
            suggestions_text = response.content
            if isinstance(suggestions_text, list):
                suggestions_text = "\n".join(str(item) for item in suggestions_text)
            suggestions_text = suggestions_text.strip()

            suggestion_lines = [line.strip() for line in suggestions_text.split("\n") if line.strip()]

            suggestions = []
            for i, suggestion_text in enumerate(suggestion_lines[:max_suggestions]):
                confidence = 0.85 - (i * 0.1)

                text_before = current_text[:cursor_pos]
                # Ensure proper spacing
                if text_before and not text_before.endswith(" ") and not suggestion_text.startswith(" "):
                    full_text = f"{text_before} {suggestion_text}"
                    completion_text = f" {suggestion_text}"
                else:
                    full_text = f"{text_before}{suggestion_text}"
                    completion_text = suggestion_text

                suggestions.append(
                    SuggestionItem(
                        text=full_text,
                        completion_text=completion_text,
                        confidence=confidence,
                        suggestion_type="tool_call",
                        metadata={"generated_by": "gpt-4.1-mini", "context_type": "tool_usage"},
                    )
                )

            return suggestions

        except Exception as e:
            logger.error(f"Error generating tool suggestions with GPT-4.1-mini: {str(e)}")
            return await self._generate_fallback_tool_suggestions(context, max_suggestions)

    async def _generate_fallback_tool_suggestions(self, context, max_suggestions: int) -> List[SuggestionItem]:
        """Fallback method for tool suggestions"""
        # Choose suggestions based on detected language
        tool_suggestions = [
            "use the search tool to",
            "call the file manager to",
            "execute the data processor with",
            "invoke the calculator function",
            "run the text analyzer on",
        ]

        suggestions = []
        for i, suggestion in enumerate(tool_suggestions[:max_suggestions]):
            confidence = 0.7 - (i * 0.1)  # Lower confidence for fallback

            text_before = context.current_text[: context.cursor_position]
            # Ensure proper spacing
            if text_before and not text_before.endswith(" ") and not suggestion.startswith(" "):
                full_text = f"{text_before} {suggestion}"
                completion_text = f" {suggestion}"
            else:
                full_text = f"{text_before}{suggestion}"
                completion_text = suggestion

            suggestions.append(
                SuggestionItem(
                    text=full_text,
                    completion_text=completion_text,
                    confidence=confidence,
                    suggestion_type="tool_call",
                    metadata={"tool_category": "general", "fallback": True},
                )
            )

        return suggestions

    async def _generate_argument_suggestions(self, context, max_suggestions: int) -> List[SuggestionItem]:
        """Generate suggestions for tool arguments using GPT-4.1-mini"""
        current_text = context.current_text
        cursor_pos = context.cursor_position

        system_prompt = """You are an AI assistant that helps users provide appropriate arguments for tool calls.
        Given the current context, suggest argument values that would be most appropriate.
        Focus on:
        - Proper data types and formats
        - Common argument patterns
        - Valid parameter values
        - JSON structure when needed
        
        IMPORTANT: 
        1. Respond in the same language as the user's input. If the user writes in Vietnamese, respond in Vietnamese. If in English, respond in English.
        2. Return ONLY the argument values that should be added after the cursor position.
        3. One suggestion per line, without explanations."""

        user_prompt = f"""Current text: "{current_text}"
        Cursor position: {cursor_pos}
        Context type: argument
        
        Please suggest {max_suggestions} argument values that should be added RIGHT AFTER the cursor position.
        Do NOT include the existing text in your suggestions - only provide the argument values."""

        try:
            llm = self._get_llm_model()
            messages = [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]

            response = await llm.ainvoke(messages)
            suggestions_text = response.content
            if isinstance(suggestions_text, list):
                suggestions_text = "\n".join(str(item) for item in suggestions_text)
            suggestions_text = suggestions_text.strip()

            suggestion_lines = [line.strip() for line in suggestions_text.split("\n") if line.strip()]

            suggestions = []
            for i, suggestion_text in enumerate(suggestion_lines[:max_suggestions]):
                confidence = 0.8 - (i * 0.1)

                text_before = current_text[:cursor_pos]
                # For arguments, usually no space is needed (e.g., function(arg) or "key":value)
                # But check if space is needed based on context
                if text_before and not text_before.endswith((" ", "(", ":", "[", "{")) and not suggestion_text.startswith((" ", ")", ":", "]", "}")):
                    full_text = f"{text_before} {suggestion_text}"
                    completion_text = f" {suggestion_text}"
                else:
                    full_text = f"{text_before}{suggestion_text}"
                    completion_text = suggestion_text

                suggestions.append(
                    SuggestionItem(
                        text=full_text,
                        completion_text=completion_text,
                        confidence=confidence,
                        suggestion_type="argument",
                        metadata={"generated_by": "gpt-4.1-mini", "context_type": "argument_value"},
                    )
                )

            return suggestions

        except Exception as e:
            logger.error(f"Error generating argument suggestions with GPT-4.1-mini: {str(e)}")
            return await self._generate_fallback_argument_suggestions(context, max_suggestions)

    async def _generate_fallback_argument_suggestions(self, context, max_suggestions: int) -> List[SuggestionItem]:
        """Fallback method for argument suggestions"""
        arg_suggestions = [
            '"example_value"',
            '{"key": "value"}',
            '["item1", "item2"]',
            "true",
            "42",
        ]

        suggestions = []
        for i, suggestion in enumerate(arg_suggestions[:max_suggestions]):
            confidence = 0.6 - (i * 0.1)  # Lower confidence for fallback

            text_before = context.current_text[: context.cursor_position]
            # For arguments, check if we need spacing
            if text_before and not text_before.endswith((" ", "(", ":", "[", "{")) and not suggestion.startswith((" ", ")", ":", "]", "}")):
                full_text = f"{text_before} {suggestion}"
                completion_text = f" {suggestion}"
            else:
                full_text = f"{text_before}{suggestion}"
                completion_text = suggestion

            suggestions.append(
                SuggestionItem(
                    text=full_text,
                    completion_text=completion_text,
                    confidence=confidence,
                    suggestion_type="argument",
                    metadata={"argument_type": "auto_detected", "fallback": True},
                )
            )

        return suggestions

    async def _generate_general_suggestions(self, context, max_suggestions: int) -> List[SuggestionItem]:
        """Generate general suggestions using GPT-4.1-mini"""
        current_text = context.current_text
        cursor_pos = context.cursor_position

        system_prompt = """You are an AI assistant that provides helpful suggestions for general text completion.
        Given the current context, suggest completions that would be most helpful to the user.
        Focus on:
        - Natural text flow
        - Context-appropriate completions
        - Actionable suggestions
        - Clear and concise text
        
        IMPORTANT: 
        1. Respond in the same language as the user's input. If the user writes in Vietnamese, respond in Vietnamese. If in English, respond in English.
        2. Return ONLY the text that should be added after the cursor position.
        3. One suggestion per line, without explanations."""

        user_prompt = f"""Current text: "{current_text}"
        Cursor position: {cursor_pos}
        Context type: general
        
        Please suggest {max_suggestions} completion texts that should be added RIGHT AFTER the cursor position.
        Do NOT include the existing text in your suggestions - only provide the continuation text."""

        try:
            llm = self._get_llm_model()
            messages = [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]

            response = await llm.ainvoke(messages)
            suggestions_text = response.content
            if isinstance(suggestions_text, list):
                suggestions_text = "\n".join(str(item) for item in suggestions_text)
            suggestions_text = suggestions_text.strip()

            suggestion_lines = [line.strip() for line in suggestions_text.split("\n") if line.strip()]

            suggestions = []
            for i, suggestion_text in enumerate(suggestion_lines[:max_suggestions]):
                confidence = 0.7 - (i * 0.1)

                text_before = current_text[:cursor_pos]
                # Ensure proper spacing
                if text_before and not text_before.endswith(" ") and not suggestion_text.startswith(" "):
                    full_text = f"{text_before} {suggestion_text}"
                    completion_text = f" {suggestion_text}"
                else:
                    full_text = f"{text_before}{suggestion_text}"
                    completion_text = suggestion_text

                suggestions.append(
                    SuggestionItem(
                        text=full_text,
                        completion_text=completion_text,
                        confidence=confidence,
                        suggestion_type="general",
                        metadata={"generated_by": "gpt-4.1-mini", "context_type": "general_completion"},
                    )
                )

            return suggestions

        except Exception as e:
            logger.error(f"Error generating general suggestions with GPT-4.1-mini: {str(e)}")
            return await self._generate_fallback_general_suggestions(context, max_suggestions)

    async def _generate_fallback_general_suggestions(self, context, max_suggestions: int) -> List[SuggestionItem]:
        """Fallback method for general suggestions"""
        general_suggestions = [
            "continue with the next step",
            "provide more details about",
            "explain how this works",
            "show an example of",
            "help me understand",
        ]

        suggestions = []
        for i, suggestion in enumerate(general_suggestions[:max_suggestions]):
            confidence = 0.5 - (i * 0.1)  # Lower confidence for fallback

            text_before = context.current_text[: context.cursor_position]
            # Ensure proper spacing
            if text_before and not text_before.endswith(" ") and not suggestion.startswith(" "):
                full_text = f"{text_before} {suggestion}"
                completion_text = f" {suggestion}"
            else:
                full_text = f"{text_before}{suggestion}"
                completion_text = suggestion

            suggestions.append(
                SuggestionItem(
                    text=full_text,
                    completion_text=completion_text,
                    confidence=confidence,
                    suggestion_type="general",
                    metadata={"fallback": True},
                )
            )

        return suggestions

    async def _generate_prompt_assistance(self, request: ChatGenerationRequest) -> str:
        """Generate assistance for prompt creation using GPT-4.1-mini"""
        system_prompt = """You are an AI assistant specialized in helping users create effective prompts for action execution.
        Provide detailed, actionable advice on how to improve prompts for better results.
        Focus on:
        - Clarity and specificity
        - Proper action instructions
        - Context provision
        - Expected outcome specification
        - Tool integration suggestions
        
        IMPORTANT: Always respond in the same language as the user's input. If the user writes in Vietnamese, respond in Vietnamese. If in English, respond in English. Match the user's language exactly.
        Be concise but comprehensive in your response."""

        # Build user prompt with context if provided
        user_prompt = f"""User's current prompt: "{request.prompt}" """
        if request.context:
            user_prompt += f"""
        Additional context: "{request.context}" """

        user_prompt += """
        Please provide specific suggestions on how to improve this prompt for better action execution and tool usage."""

        try:
            llm = self._get_llm_model()
            messages = [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]

            response = await llm.ainvoke(messages)
            generated_text = response.content
            if isinstance(generated_text, list):
                generated_text = "\n".join(str(item) for item in generated_text)

            return generated_text.strip()

        except Exception as e:
            logger.error(f"Error generating prompt assistance with GPT-4.1-mini: {str(e)}")
            return "Here are some suggestions for your prompt: Consider being more specific about the action you want to perform, include relevant context, and specify the expected outcome."

    async def _generate_tool_usage_assistance(self, request: ChatGenerationRequest) -> str:
        """Generate help for tool usage using GPT-4.1-mini"""
        system_prompt = """You are an AI assistant specialized in helping users with tool selection and usage.
        Provide practical guidance on choosing the right tools and using them effectively.
        Focus on:
        - Tool selection criteria
        - Proper tool invocation
        - Parameter configuration
        - Error handling
        - Best practices
        
        IMPORTANT: Always respond in the same language as the user's input. If the user writes in Vietnamese, respond in Vietnamese. If in English, respond in English. Match the user's language exactly.
        Be specific and actionable in your advice."""

        # Build user prompt with context if provided
        user_prompt = f"""User's request: "{request.prompt}" """
        if request.context:
            user_prompt += f"""
        Additional context: "{request.context}" """

        user_prompt += """
        Please provide guidance on tool selection and usage for this specific request."""

        try:
            llm = self._get_llm_model()
            messages = [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]

            response = await llm.ainvoke(messages)
            generated_text = response.content
            if isinstance(generated_text, list):
                generated_text = "\n".join(str(item) for item in generated_text)

            return generated_text.strip()

        except Exception as e:
            logger.error(f"Error generating tool usage help with GPT-4.1-mini: {str(e)}")
            return "For tool usage, consider: 1) Identify the right tool for your task, 2) Prepare the required parameters, 3) Handle the tool response appropriately."

    async def _generate_general_assistance(self, request: ChatGenerationRequest) -> str:
        """Generate general assistance using GPT-4.1-mini"""
        system_prompt = """You are an AI assistant that provides helpful guidance for various tasks.
        Analyze the user's request and provide relevant, actionable assistance.
        Focus on:
        - Understanding the user's intent
        - Providing step-by-step guidance
        - Suggesting best practices
        - Offering practical solutions
        
        IMPORTANT: Always respond in the same language as the user's input. If the user writes in Vietnamese, respond in Vietnamese. If in English, respond in English. Match the user's language exactly.
        Be helpful, clear, and concise in your response."""

        # Build user prompt with context if provided
        user_prompt = f"""User's request: "{request.prompt}" """
        if request.context:
            user_prompt += f"""
        Additional context: "{request.context}" """

        user_prompt += """
        Please provide helpful assistance for this request."""

        try:
            llm = self._get_llm_model()
            messages = [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]

            response = await llm.ainvoke(messages)
            generated_text = response.content
            if isinstance(generated_text, list):
                generated_text = "\n".join(str(item) for item in generated_text)

            return generated_text.strip()

        except Exception as e:
            logger.error(f"Error generating general assistance with GPT-4.1-mini: {str(e)}")
            return "I can help you with: prompt creation, tool selection, parameter configuration, and action execution guidance. What specific area would you like assistance with?"


# Initialize the service
suggestion_service = SuggestionService()


@router.post(
    "/inline",
    response_model=ResponseWrapper[InlineSuggestionResponse],
    summary="Get inline suggestions",
    description="Generate inline suggestions at cursor position for prompts, tools, and arguments",
)
async def get_inline_suggestions(request: InlineSuggestionRequest) -> ResponseWrapper[InlineSuggestionResponse]:
    """
    Generate inline suggestions based on the current context and cursor position.
    Similar to GitHub Copilot's tab completion feature.
    """
    try:
        result = await suggestion_service.generate_inline_suggestions(request)
        return ResponseWrapper(status=200, message="Suggestions generated successfully", data=result)
    except Exception as e:
        logger.error(f"Error in get_inline_suggestions: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to generate suggestions: {str(e)}")


@router.post(
    "/chat",
    response_model=ResponseWrapper[ChatGenerationResponse],
    summary="Generate chat response",
    description="Generate text response for chat-based interaction (similar to Ctrl+I)",
)
async def generate_chat_response(request: ChatGenerationRequest) -> ResponseWrapper[ChatGenerationResponse]:
    """
    Generate a text response based on user prompt and context.
    Similar to GitHub Copilot's chat feature (Ctrl+I).
    """
    try:
        result = await suggestion_service.generate_chat_response(request)
        return ResponseWrapper(status=200, message="Response generated successfully", data=result)
    except Exception as e:
        logger.error(f"Error in generate_chat_response: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to generate response: {str(e)}")


@router.get(
    "/health", response_model=ResponseWrapper[MessageResponse], summary="Health check", description="Check if the suggestion service is healthy"
)
async def health_check() -> ResponseWrapper[MessageResponse]:
    """Health check endpoint for the suggestion service"""
    return ResponseWrapper(status=200, message="Suggestion service is healthy", data=MessageResponse(message="Service is running properly"))
