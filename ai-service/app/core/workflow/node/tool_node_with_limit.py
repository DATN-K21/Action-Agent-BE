"""
Custom ToolNode with output length limiting for context window management.

This module provides a ToolNode implementation that inherits from LangGraph's ToolNode
and adds intelligent output truncation to prevent context window overflow while
preserving maximum useful content.
"""

import json
import re
from typing import Any, Dict, List, Optional, Sequence

from langchain_core.messages import AnyMessage, ToolMessage
from langchain_core.messages.utils import count_tokens_approximately
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import BaseTool
from langgraph.prebuilt import ToolNode

from app.core import logging
from app.core.settings import env_settings
from app.core.utils.context_manager import ContextManager

logger = logging.get_logger(__name__)


class ToolNodeWithOutputLimit(ToolNode):
    """
    Enhanced ToolNode that limits tool output length to prevent context window overflow.

    This class inherits from LangGraph's ToolNode and adds intelligent output truncation
    that removes binary content and preserves maximum useful information within token limits.
    """

    def __init__(
        self,
        tools: Sequence[BaseTool],
        *,
        name: str = "tools",
        tags: Optional[list[str]] = None,
        max_output_tokens: Optional[int] = None,
        truncate_strategy: str = "smart",
        preserve_prefix_tokens: int = 2000,
        preserve_suffix_tokens: int = 1000,
        remove_binary_content: bool = True,
    ):
        """
        Initialize ToolNodeWithOutputLimit.

        Args:
            tools: Sequence of tools to use
            name: Name of the node
            tags: Tags for the node
            max_output_tokens: Maximum tokens allowed for tool output (defaults to conservative limit)
            truncate_strategy: Strategy for truncation ("smart", "prefix", "suffix", "middle")
            preserve_prefix_tokens: Tokens to preserve at the beginning when truncating
            preserve_suffix_tokens: Tokens to preserve at the end when truncating
            remove_binary_content: Whether to remove binary content before truncation
        """
        super().__init__(tools, name=name, tags=tags)

        # Set default max output tokens to a conservative value
        self.max_output_tokens = max_output_tokens or getattr(env_settings, "MAX_TOOL_OUTPUT_TOKENS", 40000)
        self.truncate_strategy = truncate_strategy
        self.preserve_prefix_tokens = preserve_prefix_tokens
        self.preserve_suffix_tokens = preserve_suffix_tokens
        self.remove_binary_content = remove_binary_content

        # Create context manager for token estimation
        self.context_manager = ContextManager()

        # Binary content patterns for detection and removal
        self.binary_patterns = [
            # Base64 encoded content (common in email attachments)
            r'[A-Za-z0-9+/]{100,}={0,2}',
            # Binary file headers and content
            r'(?i)content-type:\s*application/[^\s]+.*?(?=\n\n|\r\n\r\n|$)',
            r'(?i)content-transfer-encoding:\s*base64.*?(?=\n\n|\r\n\r\n|$)',
            # Common binary file signatures
            r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F-\xFF]{20,}',
            # Large attachment indicators
            r'(?i)attachment[;\s]*filename.*?(?=\n|\r\n)',
        ]

        logger.info(
            f"Initialized ToolNodeWithOutputLimit with max_output_tokens={self.max_output_tokens}, "
            f"strategy={self.truncate_strategy}, remove_binary={self.remove_binary_content}"
        )

    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count for text."""
        return count_tokens_approximately(text)

    def _detect_content_type(self, content: str, tool_name: str) -> str:
        """
        Detect the type of content for context-aware processing.
        
        Args:
            content: Content to analyze
            tool_name: Name of the tool that produced this content
            
        Returns:
            Content type (email, json, html, text, etc.)
        """
        content_lower = content.lower()
        tool_lower = tool_name.lower()
        
        # Email-related tools
        if 'gmail' in tool_lower or 'email' in tool_lower or 'mail' in tool_lower:
            return 'email'
        
        # Try to parse as JSON
        try:
            json.loads(content.strip())
            return 'json'
        except (json.JSONDecodeError, ValueError):
            pass
        
        # HTML content
        if '<html' in content_lower or '<!doctype html' in content_lower:
            return 'html'
        
        # Check for common structured patterns
        if re.search(r'\{[\s\S]*\}', content):
            return 'structured'
        
        return 'text'

    def _remove_binary_content(self, content: str, content_type: str = 'text') -> str:
        """
        Remove binary content and attachments from the content based on content type.

        Args:
            content: Original content
            content_type: Type of content for smarter filtering

        Returns:
            Content with binary parts removed
        """
        if not self.remove_binary_content:
            return content

        cleaned_content = content
        original_length = len(content)

        # Content-type specific cleaning
        if content_type == 'email':
            # For email content, be more careful about what we remove
            # Remove large base64 encoded blocks (likely attachments) but preserve email structure
            cleaned_content = re.sub(r'[A-Za-z0-9+/]{500,}={0,2}', '[LARGE_ATTACHMENT_REMOVED]', cleaned_content)
            
            # Remove binary MIME parts but keep text parts
            cleaned_content = re.sub(
                r'(?i)content-type:\s*(?:application|image|audio|video)/[^\r\n]*.*?(?=--[\w-]+|content-type:|$)',
                '[BINARY_MIME_PART_REMOVED]',
                cleaned_content,
                flags=re.DOTALL
            )
        
        elif content_type == 'html':
            # For HTML, remove style blocks and scripts but keep structure
            cleaned_content = re.sub(r'<style[^>]*>[\s\S]*?</style>', '[STYLE_BLOCK_REMOVED]', cleaned_content, flags=re.IGNORECASE)
            cleaned_content = re.sub(r'<script[^>]*>[\s\S]*?</script>', '[SCRIPT_BLOCK_REMOVED]', cleaned_content, flags=re.IGNORECASE)
            
            # Remove very long style attributes
            cleaned_content = re.sub(r'style="[^"]{200,}"', 'style="[LONG_STYLE_REMOVED]"', cleaned_content)
        
        else:
            # General binary content removal
            cleaned_content = re.sub(r'[A-Za-z0-9+/]{200,}={0,2}', '[BINARY_ATTACHMENT_REMOVED]', cleaned_content)

        # Common binary content patterns for all types
        cleaned_content = re.sub(
            r'(?i)content-transfer-encoding:\s*base64.*?(?=--|\r\n\r\n|\n\n|$)',
            '[BASE64_CONTENT_REMOVED]',
            cleaned_content,
            flags=re.DOTALL
        )

        # Remove sequences of non-printable characters (binary data)
        cleaned_content = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F-\xFF]{10,}', '[BINARY_DATA_REMOVED]', cleaned_content)

        # Clean up multiple consecutive removal markers
        cleaned_content = re.sub(r'(\[(?:BINARY_|BASE64_|LARGE_)[A-Z_]+REMOVED\]\s*){2,}', '[MULTIPLE_BINARY_ITEMS_REMOVED]\n', cleaned_content)

        # Remove excessive whitespace
        cleaned_content = re.sub(r'\n{4,}', '\n\n\n', cleaned_content)

        removed_size = original_length - len(cleaned_content)
        if removed_size > 1000:  # Only log if significant content was removed
            logger.info(f"Removed {removed_size} characters of binary content from {content_type} content")

        return cleaned_content

    def _extract_important_sections(self, content: str, content_type: str = 'text') -> Dict[str, str]:
        """
        Extract important sections from content for preservation based on content type.

        Args:
            content: Content to analyze
            content_type: Type of content for targeted extraction

        Returns:
            Dictionary with important sections
        """
        sections = {}

        if content_type == 'email':
            # Extract email metadata and key information
            # Email headers
            header_patterns = [
                r'(?i)^(from|to|subject|date|message-id|reply-to|cc|bcc):\s*[^\r\n]+',
                r'(?i)(sender|reply-to|return-path):\s*[^\r\n]+',
            ]
            
            headers = []
            for pattern in header_patterns:
                matches = re.findall(pattern, content, re.MULTILINE)
                headers.extend(matches)
            
            if headers:
                sections['email_headers'] = '\n'.join(headers[:10])  # Keep first 10 headers

            # Extract email body content (avoid CSS and markup)
            body_patterns = [
                r'(?i)(?:^|\n)([^<\n]+(?:@[^\s]+\.[^\s]+)[^<\n]*)',  # Lines with email addresses
                r'(?i)(?:^|\n)([^\n<]{20,}[.!?]\s*$)',  # Sentences
                r'(?i)^([^<\n]*(?:dear|hello|hi|regards|sincerely|best)[^<\n]*)',  # Greeting/closing
            ]
            
            body_content = []
            for pattern in body_patterns:
                matches = re.findall(pattern, content, re.MULTILINE)
                body_content.extend([match.strip() for match in matches if len(match.strip()) > 10])
            
            if body_content:
                sections['email_body'] = '\n'.join(body_content[:20])  # Keep first 20 meaningful lines

        elif content_type == 'json':
            # Extract JSON structures
            try:
                # Try to parse and extract key information
                parsed = json.loads(content)
                if isinstance(parsed, dict):
                    # Extract key-value pairs
                    important_keys = ['id', 'name', 'title', 'subject', 'from', 'to', 'date', 'status', 'error', 'message']
                    key_info = {}
                    for key in important_keys:
                        if key in parsed:
                            key_info[key] = parsed[key]
                    
                    if key_info:
                        sections['json_key_data'] = json.dumps(key_info, indent=2)
                        
                elif isinstance(parsed, list) and len(parsed) > 0:
                    # For lists, show first few items
                    sections['json_list_sample'] = json.dumps(parsed[:3], indent=2)
                    
            except (json.JSONDecodeError, ValueError):
                # Fallback to regex extraction
                json_matches = re.findall(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', content)
                if json_matches:
                    sections['json_data'] = '\n'.join(json_matches[:3])
        
        elif content_type == 'html':
            # Extract meaningful HTML content
            # Title
            title_match = re.search(r'<title[^>]*>([^<]+)</title>', content, re.IGNORECASE)
            if title_match:
                sections['html_title'] = title_match.group(1).strip()
            
            # Text content (remove HTML tags)
            text_content = re.sub(r'<[^>]+>', '', content)
            text_content = re.sub(r'\s+', ' ', text_content).strip()
            if len(text_content) > 100:
                sections['html_text'] = text_content[:2000]  # First 2000 chars of text

        # Common patterns for all content types
        # Extract structured data (tables, lists)
        list_matches = re.findall(r'^[\s]*[-*•]\s+.+(?:\n[\s]*[-*•]\s+.+)*', content, re.MULTILINE)
        if list_matches:
            sections['lists'] = '\n'.join(list_matches[:2])

        # Extract code blocks
        code_matches = re.findall(r'```[\s\S]*?```|`[^`]+`', content)
        if code_matches:
            sections['code'] = '\n'.join(code_matches[:3])

        # Extract error messages or important status information
        error_patterns = [
            r'(?i)(error|exception|failed|failure)[^\n]*',
            r'(?i)(success|completed|finished)[^\n]*',
            r'(?i)(warning|caution|alert)[^\n]*',
        ]
        
        status_messages = []
        for pattern in error_patterns:
            matches = re.findall(pattern, content)
            status_messages.extend(matches)
        
        if status_messages:
            sections['status_messages'] = '\n'.join(status_messages[:5])

        return sections

    def _truncate_output_smart(self, content: str, tool_name: str = '') -> str:
        """
        Smart truncation that preserves important parts of the output and maximizes useful content.

        Args:
            content: Original content to truncate
            tool_name: Name of the tool for context

        Returns:
            Truncated content with important parts preserved and maximum useful information
        """
        # Detect content type for context-aware processing
        content_type = self._detect_content_type(content, tool_name)
        
        # First, remove binary content
        cleaned_content = self._remove_binary_content(content, content_type)
        
        tokens = self._estimate_tokens(cleaned_content)

        if tokens <= self.max_output_tokens:
            return cleaned_content

        logger.info(f"Truncating {content_type} tool output '{tool_name}': {tokens} tokens > {self.max_output_tokens} limit")

        # Extract important sections first
        important_sections = self._extract_important_sections(cleaned_content, content_type)
        
        if self.truncate_strategy == "prefix":
            # Keep only the beginning
            target_chars = int(len(cleaned_content) * (self.max_output_tokens / tokens))
            truncated = cleaned_content[:target_chars]
            return truncated + f"\n\n[... TRUNCATED: Removed {tokens - self.max_output_tokens} tokens to prevent context overflow]"

        elif self.truncate_strategy == "suffix":
            # Keep only the end
            target_chars = int(len(cleaned_content) * (self.max_output_tokens / tokens))
            truncated = cleaned_content[-target_chars:]
            return f"[TRUNCATED: Removed {tokens - self.max_output_tokens} tokens from beginning...]\n\n" + truncated

        elif self.truncate_strategy == "middle":
            # Keep beginning and end, truncate middle
            prefix_chars = int(len(cleaned_content) * (self.preserve_prefix_tokens / tokens))
            suffix_chars = int(len(cleaned_content) * (self.preserve_suffix_tokens / tokens))

            prefix = cleaned_content[:prefix_chars]
            suffix = cleaned_content[-suffix_chars:]

            truncated_tokens = tokens - self.preserve_prefix_tokens - self.preserve_suffix_tokens
            return f"{prefix}\n\n[... TRUNCATED: Removed {truncated_tokens} tokens from middle to fit context limit ...]\n\n{suffix}"

        else:  # "smart" strategy - preserve maximum useful information
            # Start with important sections
            result_parts = []
            used_tokens = 0

            # Add important sections first if they exist and fit
            for section_name, section_content in important_sections.items():
                section_tokens = self._estimate_tokens(section_content)
                # Use more generous allocation for important sections based on content type
                max_section_ratio = 0.6 if content_type == 'email' else 0.4
                if used_tokens + section_tokens < self.max_output_tokens * max_section_ratio:
                    result_parts.append(f"[{section_name.upper()}]\n{section_content}\n")
                    used_tokens += section_tokens

            # Calculate remaining token budget
            remaining_tokens = self.max_output_tokens - used_tokens - 200  # Reserve 200 tokens for truncation message

            if remaining_tokens > 1000:  # If we have reasonable space left
                # Split remaining content intelligently based on content type
                if content_type == 'email':
                    # For emails, prioritize meaningful text content
                    lines = cleaned_content.split('\n')
                    
                    # Filter out lines that are already in important sections
                    important_text = '\n'.join(important_sections.values())
                    unique_lines = [line for line in lines if line.strip() and line not in important_text]

                    # Prioritize email-specific content
                    scored_lines = []
                    for line in unique_lines:
                        score = 0
                        line_lower = line.lower()
                        line_stripped = line.strip()
                        
                        # Skip CSS, HTML markup, and other noise
                        if (line_stripped.startswith(('<', '{', '}')) or 
                            'style=' in line_lower or 
                            'class=' in line_lower or
                            len(line_stripped) < 10):
                            continue
                        
                        # Score based on email content relevance
                        if any(keyword in line_lower for keyword in ['from:', 'to:', 'subject:', 'date:', 'reply-to:']):
                            score += 15
                        if re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', line):  # Email addresses
                            score += 10
                        if any(keyword in line_lower for keyword in ['dear', 'hello', 'hi', 'regards', 'sincerely', 'best']):
                            score += 8
                        if re.search(r'\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{4}', line):  # Dates
                            score += 5
                        if len(line_stripped) > 50 and '.' in line_stripped:  # Substantial sentences
                            score += 4
                        if any(keyword in line_lower for keyword in ['meeting', 'schedule', 'appointment', 'urgent', 'important']):
                            score += 3

                        if score > 0:  # Only include lines with some relevance
                            scored_lines.append((score, line))

                else:
                    # For other content types, use general scoring
                    lines = cleaned_content.split('\n')
                    important_text = '\n'.join(important_sections.values())
                    unique_lines = [line for line in lines if line.strip() and line not in important_text]

                    scored_lines = []
                    for line in unique_lines:
                        score = 0
                        line_lower = line.lower()
                        
                        # General content scoring
                        if any(keyword in line_lower for keyword in ['error', 'warning', 'success', 'failed', 'completed']):
                            score += 10
                        if len(line.strip()) > 50:  # Substantial content
                            score += 2
                        if line.strip().startswith(('>', '|', '-', '*', '•')):  # Structured content
                            score += 1

                        scored_lines.append((score, line))

                # Sort by score and include as many high-value lines as possible
                scored_lines.sort(reverse=True, key=lambda x: x[0])
                
                additional_content = []
                current_tokens = used_tokens
                
                for score, line in scored_lines:
                    line_tokens = self._estimate_tokens(line + '\n')
                    if current_tokens + line_tokens <= remaining_tokens:
                        additional_content.append(line)
                        current_tokens += line_tokens
                    else:
                        break

                if additional_content:
                    result_parts.append(f"[ADDITIONAL_{content_type.upper()}_CONTENT]\n" + '\n'.join(additional_content))

            # Add truncation summary
            final_tokens = self._estimate_tokens('\n'.join(result_parts))
            truncated_tokens = tokens - final_tokens
            
            result_parts.append(
                f"\n[TRUNCATION_SUMMARY: {content_type.upper()} content optimized. "
                f"Removed {truncated_tokens} tokens ({truncated_tokens/tokens*100:.1f}%) to fit {self.max_output_tokens} token limit. "
                f"Preserved key {content_type} information and removed noise/binary content.]"
            )

            return '\n'.join(result_parts)

    def _process_tool_messages(self, messages: List[AnyMessage]) -> List[AnyMessage]:
        """
        Process tool messages to apply output limiting.

        Args:
            messages: List of messages to process

        Returns:
            Processed messages with limited tool outputs
        """
        processed_messages = []

        for message in messages:
            if isinstance(message, ToolMessage):
                original_content = str(message.content)
                original_tokens = self._estimate_tokens(original_content)

                if original_tokens > self.max_output_tokens:
                    # Apply truncation with tool context
                    tool_name = getattr(message, 'name', 'unknown_tool')
                    truncated_content = self._truncate_output_smart(original_content, tool_name)

                    # Create new ToolMessage with truncated content
                    truncated_message = ToolMessage(
                        content=truncated_content,
                        name=message.name,
                        tool_call_id=message.tool_call_id,
                        artifact=getattr(message, "artifact", None),
                        additional_kwargs=getattr(message, "additional_kwargs", {}),
                    )

                    final_tokens = self._estimate_tokens(truncated_content)
                    logger.info(
                        f"Tool '{tool_name}' output optimized: {original_tokens} -> {final_tokens} tokens "
                        f"({final_tokens/original_tokens*100:.1f}% preserved, {len(original_content)} -> {len(truncated_content)} chars)"
                    )

                    processed_messages.append(truncated_message)
                else:
                    # Still apply binary content removal even if under token limit
                    if self.remove_binary_content:
                        tool_name = getattr(message, 'name', 'unknown_tool')
                        content_type = self._detect_content_type(original_content, tool_name)
                        cleaned_content = self._remove_binary_content(original_content, content_type)
                        if len(cleaned_content) != len(original_content):
                            cleaned_message = ToolMessage(
                                content=cleaned_content,
                                name=message.name,
                                tool_call_id=message.tool_call_id,
                                artifact=getattr(message, "artifact", None),
                                additional_kwargs=getattr(message, "additional_kwargs", {}),
                            )
                            processed_messages.append(cleaned_message)
                        else:
                            processed_messages.append(message)
                    else:
                        processed_messages.append(message)
            else:
                processed_messages.append(message)

        return processed_messages

    def invoke(self, input: Dict[str, Any], config: Optional[RunnableConfig] = None) -> Dict[str, Any]:
        """
        Override invoke method to add output limiting.

        Args:
            input: Input dictionary containing messages
            config: Optional configuration

        Returns:
            Output dictionary with limited tool outputs
        """
        # Call parent invoke method
        result = super().invoke(input, config)

        # Process the result to apply output limiting
        if "messages" in result:
            result["messages"] = self._process_tool_messages(result["messages"])

        return result

    async def ainvoke(self, input: Dict[str, Any], config: Optional[RunnableConfig] = None) -> Dict[str, Any]:
        """
        Override async invoke method to add output limiting.

        Args:
            input: Input dictionary containing messages
            config: Optional configuration

        Returns:
            Output dictionary with limited tool outputs
        """
        # Call parent ainvoke method
        result = await super().ainvoke(input, config)

        # Process the result to apply output limiting
        if "messages" in result:
            result["messages"] = self._process_tool_messages(result["messages"])

        return result


def create_tool_node_with_limit(
    tools: Sequence[BaseTool],
    *,
    name: str = "tools",
    max_output_tokens: Optional[int] = None,
    truncate_strategy: str = "smart",
    remove_binary_content: bool = True,
) -> ToolNodeWithOutputLimit:
    """
    Factory function to create a ToolNodeWithOutputLimit instance.

    Args:
        tools: Sequence of tools to use
        name: Name of the node
        max_output_tokens: Maximum tokens allowed for tool output
        truncate_strategy: Strategy for truncation
        remove_binary_content: Whether to remove binary content

    Returns:
        ToolNodeWithOutputLimit instance
    """
    return ToolNodeWithOutputLimit(
        tools=tools,
        name=name,
        max_output_tokens=max_output_tokens,
        truncate_strategy=truncate_strategy,
        remove_binary_content=remove_binary_content,
    )
