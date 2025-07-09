# Public LangManus API

This documentation provides comprehensive details about the LangManus API endpoints available in the AI Service. The LangManus API enables intelligent conversational AI capabilities, content generation, text-to-speech conversion, and integration with various AI tools and services.

## Overview

The LangManus API enables you to:

- Conduct intelligent conversations with streaming responses
- Ask questions with customizable research parameters
- Convert text to speech using advanced TTS technology
- Generate podcasts from written content
- Create PowerPoint presentations automatically
- Generate prose content with customizable options
- Integrate with Model Context Protocol (MCP) servers
- Access RAG (Retrieval-Augmented Generation) resources
- Configure and manage AI workflows

LangManus represents a comprehensive AI assistant platform that combines multiple AI capabilities through a unified API interface.

## Base Models

### ChatMessage

Represents a single message in a conversation:

| Field | Type | Description |
|-------|------|-------------|
| `role` | string | The role of the message sender ("user" or "assistant") |
| `content` | string or ContentItem[] | The message content, either plain text or structured content items |

### ContentItem

Represents structured content within a message:

| Field | Type | Description |
|-------|------|-------------|
| `type` | string | The type of content ("text", "image", etc.) |
| `text` | string (optional) | The text content if type is "text" |
| `image_url` | string (optional) | The image URL if type is "image" |

### Resource

Represents a knowledge resource for RAG:

| Field | Type | Description |
|-------|------|-------------|
| `uri` | string | The URI of the resource |
| `title` | string | The title of the resource |
| `description` | string (optional) | The description of the resource |

## Endpoints

### Ask Question

Processes a single question with customizable research parameters and returns a complete response.

**Endpoint:** `POST /langmanus/ask`

**Request Body:**

```json
{
  "question": "What are the latest trends in artificial intelligence?",
  "debug": false,
  "max_plan_iterations": 1,
  "max_step_num": 3,
  "enable_background_investigation": true
}
```

**Request Fields:**
- `question` (required): The question to ask the AI assistant
- `debug` (optional): Enable debug logging (default: false)
- `max_plan_iterations` (optional): Maximum number of plan iterations (default: 1)
- `max_step_num` (optional): Maximum number of steps in a plan (default: 3)
- `enable_background_investigation` (optional): Enable background research (default: true)

**Response:**

```json
{
  "status": "success",
  "response": "Based on my research, the latest trends in artificial intelligence include..."
}
```

### Chat Stream

Initiates a streaming conversation with the AI assistant, providing real-time responses and supporting interruptions.

**Endpoint:** `POST /langmanus/chat/stream`

**Request Body:**

```json
{
  "messages": [
    {
      "role": "user",
      "content": "Tell me about machine learning algorithms"
    }
  ],
  "thread_id": "conversation_123",
  "resources": [
    {
      "uri": "https://example.com/ml-guide",
      "title": "Machine Learning Guide",
      "description": "Comprehensive guide to ML algorithms"
    }
  ],
  "max_plan_iterations": 2,
  "max_step_num": 5,
  "max_search_results": 10,
  "auto_accepted_plan": false,
  "interrupt_feedback": "",
  "mcp_settings": {},
  "enable_background_investigation": true
}
```

**Request Fields:**
- `messages` (optional): History of conversation messages (default: [])
- `thread_id` (optional): Conversation identifier (default: "__default__")
- `resources` (optional): RAG resources to use (default: [])
- `max_plan_iterations` (optional): Maximum plan iterations (default: 1)
- `max_step_num` (optional): Maximum steps per plan (default: 3)
- `max_search_results` (optional): Maximum search results (default: 3)
- `auto_accepted_plan` (optional): Auto-accept research plans (default: false)
- `interrupt_feedback` (optional): User feedback on interrupted plans
- `mcp_settings` (optional): MCP server configuration
- `enable_background_investigation` (optional): Enable background research (default: true)

**Response:** Server-Sent Events (SSE) stream

**Event Types:**
- `message_chunk`: Partial message content
- `tool_calls`: AI tool invocations
- `tool_call_chunks`: Partial tool call data
- `tool_call_result`: Results from tool execution
- `interrupt`: Plan interruption requiring user input

**Example Stream Events:**

```
event: message_chunk
data: {"thread_id": "conversation_123", "agent": "researcher", "id": "msg_001", "role": "assistant", "content": "I'll research machine learning algorithms for you."}

event: tool_calls
data: {"thread_id": "conversation_123", "agent": "researcher", "id": "msg_002", "role": "assistant", "tool_calls": [{"id": "call_123", "type": "function", "function": {"name": "search", "arguments": "{\"query\": \"machine learning algorithms 2025\"}"}}]}

event: interrupt
data: {"thread_id": "conversation_123", "id": "interrupt_001", "role": "assistant", "content": "I've created a research plan. Would you like me to proceed?", "finish_reason": "interrupt", "options": [{"text": "Edit plan", "value": "edit_plan"}, {"text": "Start research", "value": "accepted"}]}
```

### Text-to-Speech

Converts text to speech using Volcengine TTS API with customizable voice parameters.

**Endpoint:** `POST /langmanus/tts`

**Request Body:**

```json
{
  "text": "Hello, welcome to our AI service!",
  "voice_type": "BV700_V2_streaming",
  "encoding": "mp3",
  "speed_ratio": 1.0,
  "volume_ratio": 1.0,
  "pitch_ratio": 1.0,
  "text_type": "plain",
  "with_frontend": 1,
  "frontend_type": "unitTson"
}
```

**Request Fields:**
- `text` (required): Text to convert to speech (max 1024 characters)
- `voice_type` (optional): Voice type (default: "BV700_V2_streaming")
- `encoding` (optional): Audio format (default: "mp3")
- `speed_ratio` (optional): Speech speed multiplier (default: 1.0)
- `volume_ratio` (optional): Volume multiplier (default: 1.0)
- `pitch_ratio` (optional): Pitch multiplier (default: 1.0)
- `text_type` (optional): Text type "plain" or "ssml" (default: "plain")
- `with_frontend` (optional): Enable frontend processing (default: 1)
- `frontend_type` (optional): Frontend type (default: "unitTson")

**Response:** Binary audio file

**Headers:**
- `Content-Type`: audio/mp3 (or specified encoding)
- `Content-Disposition`: attachment; filename=tts_output.mp3

### Generate Podcast

Converts written content into a podcast-style audio presentation.

**Endpoint:** `POST /langmanus/podcast/generate`

**Request Body:**

```json
{
  "content": "Today we'll discuss the fascinating world of artificial intelligence and its impact on modern society..."
}
```

**Request Fields:**
- `content` (required): The written content to convert into podcast format

**Response:** Binary MP3 audio file

**Headers:**
- `Content-Type`: audio/mp3
- `Content-Disposition`: attachment; filename=podcast.mp3

### Generate PowerPoint Presentation

Creates a PowerPoint presentation from written content using Marp.

**Endpoint:** `POST /langmanus/ppt/generate`

**Request Body:**

```json
{
  "content": "# AI Revolution\n\n## Introduction\nArtificial Intelligence is transforming industries...\n\n## Key Technologies\n- Machine Learning\n- Natural Language Processing\n- Computer Vision"
}
```

**Request Fields:**
- `content` (required): Markdown-formatted content for the presentation

**Response:** Binary PowerPoint file (.pptx)

**Headers:**
- `Content-Type`: application/vnd.openxmlformats-officedocument.presentationml.presentation
- `Content-Disposition`: attachment; filename=presentation_[session_id].pptx

### Generate Prose

Generates prose content with streaming responses and customizable writing options.

**Endpoint:** `POST /langmanus/prose/generate`

**Request Body:**

```json
{
  "prompt": "Write a compelling introduction about sustainable technology",
  "option": "creative",
  "command": "Focus on environmental benefits and innovation"
}
```

**Request Fields:**
- `prompt` (required): The writing prompt or topic
- `option` (required): Writing style option (e.g., "creative", "formal", "technical")
- `command` (optional): Additional custom instructions for the writer

**Response:** Server-Sent Events (SSE) stream

**Example Stream:**

```
data: Sustainable technology represents a paradigm shift...

data: in how we approach environmental challenges...

data: combining innovation with ecological responsibility.
```

### Get MCP Server Metadata

Retrieves metadata and available tools from a Model Context Protocol server.

**Endpoint:** `POST /langmanus/mcp/server/metadata`

**Request Body:**

```json
{
  "transport": "stdio",
  "command": "python",
  "args": ["-m", "my_mcp_server"],
  "env": {
    "API_KEY": "your_api_key"
  },
  "timeout_seconds": 300
}
```

**Request Fields:**
- `transport` (required): Connection type ("stdio" or "sse")
- `command` (optional): Command to execute (for stdio type)
- `args` (optional): Command arguments (for stdio type)
- `url` (optional): SSE server URL (for sse type)
- `env` (optional): Environment variables
- `timeout_seconds` (optional): Operation timeout (default: 300)

**Response:**

```json
{
  "transport": "stdio",
  "command": "python",
  "args": ["-m", "my_mcp_server"],
  "url": null,
  "env": {
    "API_KEY": "your_api_key"
  },
  "tools": [
    {
      "name": "search_web",
      "description": "Search the web for information",
      "parameters": {
        "type": "object",
        "properties": {
          "query": {
            "type": "string",
            "description": "Search query"
          }
        },
        "required": ["query"]
      }
    }
  ]
}
```

### Get RAG Configuration

Retrieves the current RAG (Retrieval-Augmented Generation) provider configuration.

**Endpoint:** `GET /langmanus/rag/config`

**Response:**

```json
{
  "provider": "ragflow"
}
```

### List RAG Resources

Retrieves available RAG resources with optional search filtering.

**Endpoint:** `GET /langmanus/rag/resources`

**Query Parameters:**
- `query` (optional): Search query to filter resources

**Example Request:**

```bash
GET /langmanus/rag/resources?query=machine%20learning
```

**Response:**

```json
{
  "resources": [
    {
      "uri": "https://example.com/ml-guide",
      "title": "Machine Learning Guide",
      "description": "Comprehensive guide to ML algorithms and techniques"
    },
    {
      "uri": "https://example.com/ai-trends",
      "title": "AI Trends 2025",
      "description": "Latest trends and developments in artificial intelligence"
    }
  ]
}
```

## Error Handling

All endpoints use standard HTTP status codes and return consistent error responses:

| Status Code | Description |
|-------------|-------------|
| 200 | Success |
| 400 | Bad Request (invalid parameters) |
| 500 | Internal Server Error |

**Error Response Format:**

```json
{
  "detail": "Error description"
}
```

## Examples

### Complete Conversation Flow

**1. Start a new conversation:**

```bash
curl -X POST "https://your-api-domain/langmanus/chat/stream" \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {
        "role": "user",
        "content": "I need help understanding quantum computing"
      }
    ],
    "thread_id": "quantum_conversation_001",
    "max_plan_iterations": 2,
    "enable_background_investigation": true
  }'
```

**2. Handle interruption and provide feedback:**

```bash
curl -X POST "https://your-api-domain/langmanus/chat/stream" \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {
        "role": "user",
        "content": "Focus more on practical applications"
      }
    ],
    "thread_id": "quantum_conversation_001",
    "interrupt_feedback": "accepted",
    "auto_accepted_plan": true
  }'
```

### Ask a Simple Question

```bash
curl -X POST "https://your-api-domain/langmanus/ask" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What are the main differences between supervised and unsupervised learning?",
    "max_step_num": 2,
    "enable_background_investigation": false
  }'
```

### Generate Content with TTS

**1. Create text content:**

```bash
curl -X POST "https://your-api-domain/langmanus/prose/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Explain the importance of renewable energy",
    "option": "educational",
    "command": "Keep it concise and engaging"
  }'
```

**2. Convert to speech:**

```bash
curl -X POST "https://your-api-domain/langmanus/tts" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Renewable energy is crucial for sustainable future...",
    "speed_ratio": 0.9,
    "volume_ratio": 1.1
  }' \
  --output speech.mp3
```

### Create a Complete Presentation

**1. Generate presentation content:**

```bash
curl -X POST "https://your-api-domain/langmanus/ask" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Create a presentation outline about climate change solutions",
    "max_step_num": 3
  }'
```

**2. Generate PowerPoint file:**

```bash
curl -X POST "https://your-api-domain/langmanus/ppt/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "# Climate Change Solutions\n\n## Renewable Energy\n- Solar power\n- Wind energy\n\n## Conservation\n- Energy efficiency\n- Sustainable practices"
  }' \
  --output climate_presentation.pptx
```

### Work with RAG Resources

**1. Check available resources:**

```bash
curl -X GET "https://your-api-domain/langmanus/rag/resources?query=artificial%20intelligence"
```

**2. Use resources in conversation:**

```bash
curl -X POST "https://your-api-domain/langmanus/chat/stream" \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {
        "role": "user",
        "content": "Summarize the latest AI research findings"
      }
    ],
    "resources": [
      {
        "uri": "https://example.com/ai-research-2025",
        "title": "AI Research 2025",
        "description": "Latest artificial intelligence research papers"
      }
    ]
  }'
```

### Integrate MCP Server

**1. Get server metadata:**

```bash
curl -X POST "https://your-api-domain/langmanus/mcp/server/metadata" \
  -H "Content-Type: application/json" \
  -d '{
    "transport": "stdio",
    "command": "python",
    "args": ["-m", "weather_mcp_server"],
    "env": {
      "WEATHER_API_KEY": "your_weather_api_key"
    }
  }'
```

**2. Use MCP tools in conversation:**

```bash
curl -X POST "https://your-api-domain/langmanus/chat/stream" \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {
        "role": "user",
        "content": "What is the weather like in New York today?"
      }
    ],
    "mcp_settings": {
      "weather_server": {
        "transport": "stdio",
        "command": "python",
        "args": ["-m", "weather_mcp_server"]
      }
    }
  }'
```

## Advanced Features

### Streaming Response Handling

When working with streaming endpoints, implement proper SSE handling:

```javascript
const eventSource = new EventSource('/langmanus/chat/stream', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    messages: [{
      role: 'user',
      content: 'Hello, how can you help me today?'
    }]
  })
});

eventSource.onmessage = function(event) {
  const data = JSON.parse(event.data);
  console.log('Received:', data);
};

eventSource.addEventListener('interrupt', function(event) {
  const data = JSON.parse(event.data);
  // Handle user interaction for plan approval
  handlePlanInterrupt(data);
});
```

### Plan Interruption Handling

The chat stream may interrupt for plan approval:

```javascript
function handlePlanInterrupt(interruptData) {
  // Show options to user
  const userChoice = confirm(`Plan: ${interruptData.content}\nProceed?`);
  
  // Continue with user feedback
  fetch('/langmanus/chat/stream', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      thread_id: interruptData.thread_id,
      interrupt_feedback: userChoice ? 'accepted' : 'edit_plan',
      auto_accepted_plan: userChoice
    })
  });
}
```

### Resource Management

Efficiently manage RAG resources:

```javascript
// Get available resources
async function getResources(query) {
  const response = await fetch(`/langmanus/rag/resources?query=${encodeURIComponent(query)}`);
  return await response.json();
}

// Use resources in conversation
async function chatWithResources(message, resources) {
  return fetch('/langmanus/chat/stream', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      messages: [{ role: 'user', content: message }],
      resources: resources
    })
  });
}
```

## Performance Considerations

1. **Streaming Responses**: Use streaming for long-running conversations to provide real-time feedback
2. **Resource Caching**: Cache RAG resources to avoid repeated API calls
3. **MCP Connection Pooling**: Reuse MCP server connections when possible
4. **File Size Limits**: Large content generation (PPT, podcast) may take significant time
5. **Timeout Management**: Set appropriate timeouts for MCP server operations

## Security Notes

1. **API Authentication**: Ensure proper authentication mechanisms are in place
2. **Content Validation**: Validate all input content for security threats
3. **Resource Access**: Verify RAG resource permissions before use
4. **MCP Security**: Validate MCP server commands and environment variables
5. **File Handling**: Securely handle generated files and temporary storage
6. **Rate Limiting**: Implement rate limiting for resource-intensive operations

## Integration Patterns

### Conversational AI Assistant

```python
import asyncio
import json
from typing import AsyncGenerator

class LangManusClient:
    def __init__(self, base_url: str):
        self.base_url = base_url
    
    async def chat_stream(self, messages: list, **kwargs) -> AsyncGenerator[dict, None]:
        # Implementation for streaming chat
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/langmanus/chat/stream",
                json={"messages": messages, **kwargs}
            ) as response:
                async for line in response.content:
                    if line.startswith(b"data: "):
                        yield json.loads(line[6:].decode())
```

### Content Generation Pipeline

```python
class ContentPipeline:
    def __init__(self, client: LangManusClient):
        self.client = client
    
    async def generate_complete_content(self, topic: str):
        # 1. Generate written content
        prose_content = await self.generate_prose(topic)
        
        # 2. Create presentation
        ppt_file = await self.generate_presentation(prose_content)
        
        # 3. Generate podcast
        audio_file = await self.generate_podcast(prose_content)
        
        return {
            "text": prose_content,
            "presentation": ppt_file,
            "audio": audio_file
        }
```

## Troubleshooting

### Common Issues

1. **Streaming Connection Lost**: Implement reconnection logic for SSE streams
2. **Large File Generation**: Increase timeout for PPT and podcast generation
3. **MCP Server Timeout**: Adjust timeout_seconds for slow MCP servers
4. **Resource Not Found**: Verify RAG resource URIs are accessible
5. **TTS Service Unavailable**: Check Volcengine API credentials

### Debug Mode

Enable debug mode for detailed logging:

```json
{
  "question": "Debug this issue",
  "debug": true,
  "max_step_num": 1
}
```

### Monitoring and Logging

- Monitor streaming connection health
- Log MCP server interaction failures
- Track resource usage and performance metrics
- Monitor file generation success rates

This comprehensive API documentation should provide developers with all the information needed to effectively integrate and use the LangManus AI service in their applications.
