# Team Stream API Documentation

## Overview

The Team Stream API provides real-time streaming responses for AI team interactions. This API supports sending prompts to AI teams and handling interrupt messages for human-in-the-loop workflows, particularly for hierarchical workflow interrupts.

## Base URL

```
POST /api/v1/team/{team_id}/stream/{thread_id}
```

## Authentication

This endpoint requires authentication through HTTP headers:

| Header | Type | Required | Description |
|--------|------|----------|-------------|
| `x-user-id` | `string` | **Yes** | User ID for authentication |
| `x-user-role` | `string` | **Yes** | User role (e.g., "user", "admin", "super admin") |

## Request Format

### URL Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `team_id` | `string` | **Yes** | Unique identifier of the team |
| `thread_id` | `string` | **Yes** | Unique identifier of the conversation thread |

### Request Body

The request body should be a JSON object with the following structure:

```typescript
interface ChatTeamRequest {
  messages: ChatMessage[];     // Required: Array of chat messages
  interrupt?: Interrupt;       // Optional: Interrupt configuration for human-in-the-loop
}
```

#### ChatMessage Schema

```typescript
interface ChatMessage {
  type: "human" | "ai";       // Required: Message type
  content: string;            // Required: Message content
  imgdata?: string;           // Optional: Base64 encoded image data
}
```

#### Interrupt Schema (For Hierarchical Workflow)

```typescript
interface Interrupt {
  interaction_type?: "tool_review" | "output_review" | "context_input";  // Optional: Type of interaction
  decision: "approved" | "rejected" | "replied" | "update" | "feedback" | "review" | "edit" | "continue";  // Required: User decision
  tool_message?: string;      // Optional: Additional message from user
}
```

## Response Format

The API returns Server-Sent Events (SSE) with `Content-Type: text/event-stream`. Each event contains JSON data in the following format:

```typescript
interface StreamResponse {
  type: "message" | "interrupt" | "error";  // Response type
  content?: string;                          // Message content (for regular messages)
  name?: string;                            // Source name (team member, tool, etc.)
  tool_calls?: ToolCall[];                  // Tool calls (when interrupt type)
  id: string;                               // Unique response ID
}
```

### Response Types

#### 1. Regular Message Response
```json
{
  "type": "message",
  "content": "Here is the response from the AI team...",
  "name": "team_leader",
  "id": "uuid-string"
}
```

#### 2. Interrupt Response (Human-in-the-loop)
```json
{
  "type": "interrupt",
  "name": "tool_review",
  "tool_calls": [
    {
      "id": "call_123",
      "name": "search_web",
      "args": {
        "query": "latest AI developments"
      }
    }
  ],
  "id": "uuid-string"
}
```

#### 3. Error Response
```json
{
  "type": "error",
  "content": "Error message description",
  "name": "error",
  "id": "uuid-string"
}
```

## Use Cases

### 1. Sending a Regular Prompt

Send a user message to the AI team for processing:

```json
{
  "messages": [
    {
      "type": "human",
      "content": "Please analyze the latest market trends in AI technology"
    }
  ]
}
```

### 2. Handling Tool Review Interrupts (Hierarchical Workflow)

When the AI team requests to use a tool, you can approve, reject, or modify the request:

#### Approve Tool Usage
```json
{
  "messages": [],
  "interrupt": {
    "interaction_type": "tool_review",
    "decision": "approved"
  }
}
```

#### Reject Tool Usage
```json
{
  "messages": [],
  "interrupt": {
    "interaction_type": "tool_review",
    "decision": "rejected",
    "tool_message": "Please try a different approach without using external tools"
  }
}
```

#### Update Tool Parameters
```json
{
  "messages": [],
  "interrupt": {
    "interaction_type": "tool_review",
    "decision": "update",
    "tool_message": "{\"query\": \"AI trends 2024\", \"max_results\": 5}"
  }
}
```

### 3. Handling Output Review Interrupts

Review and approve or request changes to AI output:

#### Approve Output
```json
{
  "messages": [],
  "interrupt": {
    "interaction_type": "output_review",
    "decision": "approved"
  }
}
```

#### Request Output Revision
```json
{
  "messages": [],
  "interrupt": {
    "interaction_type": "output_review",
    "decision": "review",
    "tool_message": "Please provide more specific examples and data sources"
  }
}
```

### 4. Providing Additional Context

Provide additional information when requested:

```json
{
  "messages": [],
  "interrupt": {
    "interaction_type": "context_input",
    "decision": "continue",
    "tool_message": "Focus on enterprise AI solutions and include market size data"
  }
}
```

## Error Handling

### HTTP Status Codes

| Status Code | Description |
|-------------|-------------|
| `200` | Success - Stream established |
| `400` | Bad Request - Invalid thread association or malformed request |
| `403` | Forbidden - Insufficient permissions |
| `404` | Not Found - Team or thread not found |
| `500` | Internal Server Error |

### Common Error Scenarios

1. **Team Not Found**
   ```json
   {
     "status": 404,
     "message": "Team not found"
   }
   ```

2. **Thread Not Found**
   ```json
   {
     "status": 404,
     "message": "Thread not found"
   }
   ```

3. **Thread Mismatch**
   ```json
   {
     "status": 400,
     "message": "Thread does not belong to this assistant"
   }
   ```

4. **Permission Denied**
   ```json
   {
     "status": 403,
     "message": "Not enough permissions"
   }
   ```

## Workflow Types Supported

### 1. Hierarchical Workflow
- **Features**: Multi-agent coordination with leader delegation
- **Interrupts**: Full support for all interrupt types
- **Use Case**: Complex tasks requiring multiple specialized agents

### 2. Sequential Workflow  
- **Features**: Step-by-step processing through team members
- **Interrupts**: Limited interrupt support
- **Use Case**: Linear workflows with defined steps

### 3. Chatbot Workflow
- **Features**: Single-agent conversational interface
- **Interrupts**: Basic interrupt support
- **Use Case**: Simple Q&A and conversational tasks

### 4. RAGBot Workflow
- **Features**: Retrieval-augmented generation with knowledge bases
- **Interrupts**: Tool-specific interrupts
- **Use Case**: Knowledge-intensive tasks

### 5. SearchBot Workflow
- **Features**: Web search and information retrieval
- **Interrupts**: Search-specific interrupts  
- **Use Case**: Research and information gathering

### 6. Custom Workflow
- **Features**: User-defined workflow graphs
- **Interrupts**: Configurable interrupt points
- **Use Case**: Custom business logic and specialized workflows

## Best Practices

### 1. Connection Management
- Always handle connection errors and reconnect if necessary
- Implement proper timeout handling for long-running requests
- Use appropriate buffer sizes for streaming data

### 2. Interrupt Handling
- Process interrupts promptly to avoid workflow timeouts
- Validate interrupt data before sending
- Provide clear feedback to users during interrupt flows

### 3. Error Recovery
- Implement retry logic for transient failures
- Log errors for debugging and monitoring
- Provide meaningful error messages to users

### 4. Performance Optimization
- Use streaming responses for real-time user experience
- Implement client-side caching where appropriate
- Monitor response times and optimize team configurations

## Rate Limiting

- **Concurrent Streams**: Maximum 10 concurrent streams per user
- **Message Rate**: Maximum 100 messages per minute per team
- **Request Size**: Maximum 10MB per request (including image data)

## Security Considerations

1. **Authentication**: Always validate user permissions before processing
2. **Input Validation**: Sanitize all user inputs and file uploads
3. **Rate Limiting**: Implement appropriate rate limits to prevent abuse
4. **Data Privacy**: Ensure sensitive data is handled according to privacy policies
5. **Audit Logging**: Log all team interactions for security monitoring

## Example Integration Patterns

### Real-time Chat Interface
```javascript
// Establish SSE connection
const eventSource = new EventSource('/api/v1/team/123/stream/456');

eventSource.onmessage = function(event) {
  const response = JSON.parse(event.data);
  
  if (response.type === 'interrupt') {
    // Handle interrupt - show approval UI
    showInterruptDialog(response);
  } else if (response.type === 'message') {
    // Display regular message
    displayMessage(response.content);
  }
};
```

### Batch Processing with Interrupts
```javascript
async function processWithInterrupts(teamId, threadId, message) {
  const response = await fetch(`/api/v1/team/${teamId}/stream/${threadId}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'x-user-id': userId,
      'x-user-role': userRole
    },
    body: JSON.stringify({
      messages: [{ type: 'human', content: message }]
    })
  });

  // Handle streaming response
  const reader = response.body.getReader();
  // ... process streaming data
}
```

This documentation provides comprehensive coverage of the Team Stream API, with special attention to hierarchical workflow interrupts as requested.
