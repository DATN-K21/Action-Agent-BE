# Public Suggestion API

This documentation provides detailed information about the Suggestion API endpoints available in the AI Service. The Suggestion API provides intelligent code suggestions and chat-based interactions similar to GitHub Copilot's functionality.

## Overview

The Suggestion API enables you to:

- Generate inline code suggestions at cursor position (similar to GitHub Copilot's tab completion)
- Generate text responses for chat-based interactions (similar to GitHub Copilot's Ctrl+I feature)
- Submit feedback on suggestion quality to improve future recommendations
- Monitor service health

The API provides intelligent suggestions for prompts, tools, and arguments based on current context and cursor position, powered by machine learning models that analyze code patterns and user behavior.

## Base Models

### InlineSuggestionRequest

Request model for generating inline suggestions at cursor position:

| Field | Type | Description |
|-------|------|-------------|
| `context` | string | Current code context around cursor position |
| `cursor_position` | integer | Position of cursor in the text |
| `file_type` | string (optional) | Type of file (e.g., "python", "javascript") |
| `recent_code` | string (optional) | Recently written code for better context |
| `project_context` | object (optional) | Information about the current project |

### InlineSuggestionResponse

Response containing inline suggestions:

| Field | Type | Description |
|-------|------|-------------|
| `suggestions` | array[string] | List of suggested code completions |
| `context_id` | string | Unique identifier for this suggestion context |
| `confidence` | float | Confidence score (0-1) for the suggestions |
| `metadata` | object | Additional metadata about the suggestions |

### ChatGenerationRequest

Request model for generating chat responses:

| Field | Type | Description |
|-------|------|-------------|
| `prompt` | string | User's input prompt or question |
| `context` | string (optional) | Current code or text context |
| `conversation_history` | array (optional) | Previous messages in the conversation |
| `file_type` | string (optional) | Type of file being worked on |
| `project_info` | object (optional) | Information about the current project |

### ChatGenerationResponse

Response containing generated chat text:

| Field | Type | Description |
|-------|------|-------------|
| `response` | string | Generated text response |
| `context_id` | string | Unique identifier for this conversation context |
| `confidence` | float | Confidence score (0-1) for the response |
| `metadata` | object | Additional metadata about the response |

### SuggestionFeedbackRequest

Request model for submitting feedback on suggestions:

| Field | Type | Description |
|-------|------|-------------|
| `context_id` | string | ID of the suggestion context receiving feedback |
| `feedback_type` | string | Type of feedback ("accepted", "rejected", "modified") |
| `rating` | integer (optional) | Optional rating score (1-5) |
| `comments` | string (optional) | Optional feedback comments |

### MessageResponse

Simple response containing a message:

| Field | Type | Description |
|-------|------|-------------|
| `message` | string | Response message |

### ResponseWrapper

Standard wrapper for all API responses:

| Field | Type | Description |
|-------|------|-------------|
| `status` | integer | HTTP status code |
| `message` | string | Response message |
| `data` | object | Response data (varies by endpoint) |

## Endpoints

### Generate Inline Suggestions

Generates inline code suggestions at cursor position, similar to GitHub Copilot's tab completion feature.

**Endpoint:** `POST /suggestions/inline`

**Request Body:**
```json
{
  "context": "def calculate_average(numbers):\n    total = sum(numbers)\n    ",
  "cursor_position": 45,
  "file_type": "python",
  "recent_code": "# Working on math utility functions",
  "project_context": {
    "language": "python",
    "framework": "none"
  }
}
```

**Response:**

```json
{
  "status": 200,
  "message": "Suggestions generated successfully",
  "data": {
    "suggestions": [
      "return total / len(numbers)",
      "return total / len(numbers) if numbers else 0",
      "count = len(numbers)\n    return total / count"
    ],
    "context_id": "ctx_abc123",
    "confidence": 0.92,
    "metadata": {
      "suggestion_type": "code_completion",
      "language": "python",
      "function_context": "calculate_average"
    }
  }
}
```

### Generate Chat Response

Generates text responses for chat-based interactions, similar to GitHub Copilot's Ctrl+I feature.

**Endpoint:** `POST /suggestions/chat`

**Request Body:**
```json
{
  "prompt": "How can I optimize this function for better performance?",
  "context": "def calculate_average(numbers):\n    total = sum(numbers)\n    return total / len(numbers)",
  "conversation_history": [
    {
      "role": "user",
      "content": "I need help with this math function"
    }
  ],
  "file_type": "python",
  "project_info": {
    "name": "math_utils",
    "type": "library"
  }
}
```

**Response:**

```json
{
  "status": 200,
  "message": "Response generated successfully",
  "data": {
    "response": "Here are several ways to optimize your `calculate_average` function:\n\n1. **Add input validation**: Check if the list is empty to avoid division by zero\n2. **Use statistics module**: Python's built-in `statistics.mean()` is optimized\n3. **Consider numpy**: For large datasets, numpy arrays are much faster\n\nHere's an optimized version:\n\n```python\ndef calculate_average(numbers):\n    if not numbers:\n        return 0\n    return sum(numbers) / len(numbers)\n```\n\nFor very large datasets, consider:\n\n```python\nimport numpy as np\n\ndef calculate_average_fast(numbers):\n    return np.mean(numbers)\n```",
    "context_id": "ctx_def456",
    "confidence": 0.89,
    "metadata": {
      "response_type": "optimization_advice",
      "suggestions_count": 3,
      "code_examples": 2
    }
  }
}
```

### Submit Suggestion Feedback

Submits feedback on suggestion quality to improve future recommendations.

**Endpoint:** `POST /suggestions/feedback`

**Request Body:**
```json
{
  "context_id": "ctx_abc123",
  "feedback_type": "accepted",
  "rating": 5,
  "comments": "Perfect suggestion, exactly what I needed!"
}
```

**Response:**

```json
{
  "status": 200,
  "message": "Feedback submitted successfully",
  "data": {
    "message": "Thank you for your feedback!"
  }
}
```

### Health Check

Checks if the suggestion service is healthy and running properly.

**Endpoint:** `GET /suggestions/health`

**Response:**

```json
{
  "status": 200,
  "message": "Suggestion service is healthy",
  "data": {
    "message": "Service is running properly"
  }
}
```

## Error Handling

All endpoints use standard HTTP status codes and return consistent error responses:

| Status Code | Description |
|-------------|-------------|
| 200 | Success |
| 400 | Bad Request (invalid parameters or malformed JSON) |
| 404 | Not Found (suggestion context not found) |
| 500 | Internal Server Error |

**Error Response Format:**

```json
{
  "status": 400,
  "message": "Invalid request: Missing required parameter 'context'",
  "data": null
}
```

**Common Error Scenarios:**

1. **Missing Required Parameter:**
```json
{
  "status": 400,
  "message": "Missing required field: context"
}
```

2. **Invalid Context ID:**
```json
{
  "status": 404,
  "message": "Suggestion context not found"
}
```

3. **Service Unavailable:**
```json
{
  "status": 500,
  "message": "Failed to generate suggestions: Service temporarily unavailable"
}
```

## Feedback Types

The feedback system supports the following feedback types:

| Type | Description |
|------|-------------|
| `accepted` | User accepted and used the suggestion |
| `rejected` | User dismissed the suggestion without using it |
| `modified` | User accepted the suggestion but made modifications |
| `partially_used` | User used only part of the suggestion |

## Implementation Details

### Inline Suggestion Generation

The inline suggestion system works similarly to GitHub Copilot:

1. **Context Analysis**: Analyzes the code context around the cursor position
2. **Pattern Recognition**: Identifies coding patterns and intentions
3. **Suggestion Generation**: Generates multiple completion options
4. **Ranking**: Ranks suggestions by relevance and confidence
5. **Filtering**: Filters out inappropriate or low-confidence suggestions

### Chat Response Generation

The chat system provides conversational assistance:

1. **Prompt Analysis**: Understands the user's question or request
2. **Context Integration**: Incorporates code context and conversation history
3. **Response Generation**: Generates helpful and relevant responses
4. **Code Example Integration**: Includes code examples when appropriate
5. **Formatting**: Applies proper markdown formatting for readability

### Feedback Processing

User feedback helps improve the system:

1. **Collection**: Tracks user interactions with suggestions
2. **Analysis**: Analyzes which suggestions are most helpful
3. **Model Training**: Uses feedback to improve suggestion quality
4. **Performance Monitoring**: Monitors suggestion acceptance rates

## Examples

### Getting Inline Code Completions

**Request:**

```bash
curl -X POST "https://your-api-domain/suggestions/inline" \
  -H "Content-Type: application/json" \
  -d '{
    "context": "def fibonacci(n):\n    if n <= 1:\n        return n\n    ",
    "cursor_position": 55,
    "file_type": "python"
  }'
```

**Response:**

```json
{
  "status": 200,
  "message": "Suggestions generated successfully",
  "data": {
    "suggestions": [
      "return fibonacci(n-1) + fibonacci(n-2)",
      "else:\n        return fibonacci(n-1) + fibonacci(n-2)",
      "return fibonacci(n-1) + fibonacci(n-2)\n\n# Example usage:\n# print(fibonacci(10))"
    ],
    "context_id": "ctx_fib123",
    "confidence": 0.94,
    "metadata": {
      "suggestion_type": "function_completion",
      "language": "python",
      "algorithm": "recursion"
    }
  }
}
```

### Getting Chat-based Help

**Request:**

```bash
curl -X POST "https://your-api-domain/suggestions/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "How can I make this function more efficient?",
    "context": "def fibonacci(n):\n    if n <= 1:\n        return n\n    return fibonacci(n-1) + fibonacci(n-2)",
    "file_type": "python"
  }'
```

**Response:**

```json
{
  "status": 200,
  "message": "Response generated successfully",
  "data": {
    "response": "Your current fibonacci function uses simple recursion, which has exponential time complexity O(2^n). Here are more efficient approaches:\n\n## 1. Dynamic Programming (Memoization)\n```python\ndef fibonacci_memo(n, memo={}):\n    if n in memo:\n        return memo[n]\n    if n <= 1:\n        return n\n    memo[n] = fibonacci_memo(n-1, memo) + fibonacci_memo(n-2, memo)\n    return memo[n]\n```\n\n## 2. Iterative Approach (Most Efficient)\n```python\ndef fibonacci_iterative(n):\n    if n <= 1:\n        return n\n    a, b = 0, 1\n    for _ in range(2, n + 1):\n        a, b = b, a + b\n    return b\n```\n\nThe iterative approach is the most efficient with O(n) time and O(1) space complexity.",
    "context_id": "ctx_chat456",
    "confidence": 0.96,
    "metadata": {
      "response_type": "optimization_advice",
      "algorithms_suggested": ["memoization", "iteration"],
      "code_examples": 2
    }
  }
}
```

### Submitting Feedback

**Request:**

```bash
curl -X POST "https://your-api-domain/suggestions/feedback" \
  -H "Content-Type: application/json" \
  -d '{
    "context_id": "ctx_fib123",
    "feedback_type": "accepted",
    "rating": 4,
    "comments": "Good suggestion, but could be more efficient"
  }'
```

**Response:**

```json
{
  "status": 200,
  "message": "Feedback submitted successfully",
  "data": {
    "message": "Thank you for your feedback!"
  }
}
```

## Best Practices

1. **Provide Rich Context**: Include as much relevant context as possible (current code, file type, project information) to get better suggestions.

2. **Implement Feedback Loop**: Always submit feedback to help improve suggestion quality over time.

3. **Handle Context IDs**: Store context IDs when receiving suggestions to provide proper feedback later.

4. **Use Appropriate Confidence Thresholds**: Consider confidence scores when deciding whether to show suggestions to users.

5. **Implement Caching**: Cache suggestion contexts locally to reduce API calls for feedback submission.

6. **Error Handling**: Implement robust error handling for network issues and API errors.

## Integration Examples

### JavaScript Integration Example

```javascript
class SuggestionClient {
  constructor(baseUrl, apiKey) {
    this.baseUrl = baseUrl;
    this.headers = {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${apiKey}`
    };
  }

  async getInlineSuggestions(context, cursorPosition, fileType = null) {
    try {
      const response = await fetch(`${this.baseUrl}/suggestions/inline`, {
        method: 'POST',
        headers: this.headers,
        body: JSON.stringify({
          context,
          cursor_position: cursorPosition,
          file_type: fileType
        })
      });

      const data = await response.json();
      
      if (data.status === 200) {
        return data.data;
      } else {
        console.error(`Error: ${data.message}`);
        return null;
      }
    } catch (error) {
      console.error('Failed to fetch inline suggestions:', error);
      return null;
    }
  }

  async getChatResponse(prompt, context = null, conversationHistory = []) {
    try {
      const response = await fetch(`${this.baseUrl}/suggestions/chat`, {
        method: 'POST',
        headers: this.headers,
        body: JSON.stringify({
          prompt,
          context,
          conversation_history: conversationHistory
        })
      });

      const data = await response.json();
      
      if (data.status === 200) {
        return data.data;
      } else {
        console.error(`Error: ${data.message}`);
        return null;
      }
    } catch (error) {
      console.error('Failed to fetch chat response:', error);
      return null;
    }
  }

  async submitFeedback(contextId, feedbackType, rating = null, comments = null) {
    try {
      const response = await fetch(`${this.baseUrl}/suggestions/feedback`, {
        method: 'POST',
        headers: this.headers,
        body: JSON.stringify({
          context_id: contextId,
          feedback_type: feedbackType,
          rating,
          comments
        })
      });

      const data = await response.json();
      return data.status === 200;
    } catch (error) {
      console.error('Failed to submit feedback:', error);
      return false;
    }
  }

  async checkHealth() {
    try {
      const response = await fetch(`${this.baseUrl}/suggestions/health`);
      const data = await response.json();
      return data.status === 200;
    } catch (error) {
      console.error('Health check failed:', error);
      return false;
    }
  }
}

// Example usage
const client = new SuggestionClient('https://your-api-domain', 'YOUR_API_KEY');

// Get inline suggestions for code completion
async function showCodeCompletions(editor) {
  const context = editor.getTextUpToCursor();
  const cursorPos = editor.getCursorPosition();
  const fileType = editor.getFileExtension();
  
  const result = await client.getInlineSuggestions(context, cursorPos, fileType);
  
  if (result && result.suggestions.length > 0) {
    editor.showSuggestions(result.suggestions);
    
    // Handle suggestion selection
    editor.onSuggestionAccepted((suggestion) => {
      client.submitFeedback(result.context_id, 'accepted', 5);
    });
    
    editor.onSuggestionRejected(() => {
      client.submitFeedback(result.context_id, 'rejected');
    });
  }
}

// Get chat response for help
async function askForHelp(prompt, codeContext) {
  const result = await client.getChatResponse(prompt, codeContext);
  
  if (result) {
    console.log('AI Response:', result.response);
    
    // Submit positive feedback for helpful responses
    setTimeout(() => {
      client.submitFeedback(result.context_id, 'accepted', 4, 'Helpful explanation');
    }, 5000);
  }
}
```

### Python Integration Example

```python
import requests
import json
from typing import List, Optional, Dict, Any

class SuggestionClient:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {api_key}'
        }
    
    def get_inline_suggestions(
        self, 
        context: str, 
        cursor_position: int, 
        file_type: Optional[str] = None,
        recent_code: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Get inline code suggestions."""
        payload = {
            'context': context,
            'cursor_position': cursor_position
        }
        
        if file_type:
            payload['file_type'] = file_type
        if recent_code:
            payload['recent_code'] = recent_code
            
        try:
            response = requests.post(
                f"{self.base_url}/suggestions/inline",
                headers=self.headers,
                json=payload
            )
            
            data = response.json()
            
            if data['status'] == 200:
                return data['data']
            else:
                print(f"Error: {data['message']}")
                return None
        except Exception as e:
            print(f"Failed to fetch inline suggestions: {e}")
            return None
    
    def get_chat_response(
        self,
        prompt: str,
        context: Optional[str] = None,
        conversation_history: Optional[List[Dict]] = None,
        file_type: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Get chat response for assistance."""
        payload = {'prompt': prompt}
        
        if context:
            payload['context'] = context
        if conversation_history:
            payload['conversation_history'] = conversation_history
        if file_type:
            payload['file_type'] = file_type
            
        try:
            response = requests.post(
                f"{self.base_url}/suggestions/chat",
                headers=self.headers,
                json=payload
            )
            
            data = response.json()
            
            if data['status'] == 200:
                return data['data']
            else:
                print(f"Error: {data['message']}")
                return None
        except Exception as e:
            print(f"Failed to fetch chat response: {e}")
            return None
    
    def submit_feedback(
        self,
        context_id: str,
        feedback_type: str,
        rating: Optional[int] = None,
        comments: Optional[str] = None
    ) -> bool:
        """Submit feedback for suggestions."""
        payload = {
            'context_id': context_id,
            'feedback_type': feedback_type
        }
        
        if rating:
            payload['rating'] = rating
        if comments:
            payload['comments'] = comments
            
        try:
            response = requests.post(
                f"{self.base_url}/suggestions/feedback",
                headers=self.headers,
                json=payload
            )
            
            data = response.json()
            return data['status'] == 200
        except Exception as e:
            print(f"Failed to submit feedback: {e}")
            return False
    
    def check_health(self) -> bool:
        """Check service health."""
        try:
            response = requests.get(f"{self.base_url}/suggestions/health")
            data = response.json()
            return data['status'] == 200
        except Exception as e:
            print(f"Health check failed: {e}")
            return False

# Example usage
def example_usage():
    client = SuggestionClient("https://your-api-domain", "YOUR_API_KEY")
    
    # Check service health
    if not client.check_health():
        print("Service is not healthy")
        return
    
    # Get inline suggestions
    code_context = "def calculate_average(numbers):\n    total = sum(numbers)\n    "
    cursor_pos = len(code_context)
    
    suggestions = client.get_inline_suggestions(
        context=code_context,
        cursor_position=cursor_pos,
        file_type="python"
    )
    
    if suggestions:
        print("Suggestions:")
        for i, suggestion in enumerate(suggestions['suggestions']):
            print(f"{i+1}. {suggestion}")
        
        # Simulate user accepting first suggestion
        client.submit_feedback(
            suggestions['context_id'],
            'accepted',
            5,
            'Perfect completion!'
        )
    
    # Get chat help
    chat_response = client.get_chat_response(
        prompt="How can I optimize this function?",
        context=code_context,
        file_type="python"
    )
    
    if chat_response:
        print(f"\nAI Help:\n{chat_response['response']}")
        
        # Submit feedback
        client.submit_feedback(
            chat_response['context_id'],
            'accepted',
            4,
            'Very helpful explanation'
        )

if __name__ == "__main__":
    example_usage()
```

## Performance Considerations

1. **Response Time**: Inline suggestion endpoints are optimized to respond within 100-200ms for real-time code completion.

2. **Context Size Limits**: Keep context size reasonable (typically < 10KB) to maintain fast response times.

3. **Caching Strategy**: Implement client-side caching for frequently used suggestions and context data.

4. **Rate Limiting**: Be mindful of API rate limits when implementing real-time features.

5. **Background Processing**: Consider using background processing for non-critical feedback submission.

## Security Notes

1. **Data Privacy**: All code context is processed securely and not stored permanently.

2. **API Key Protection**: Keep API keys secure and rotate them regularly.

3. **Input Validation**: All inputs are validated to prevent injection attacks.

4. **Rate Limiting**: API endpoints implement rate limiting to prevent abuse.

5. **Secure Transmission**: All data is transmitted over HTTPS.

## Use Cases

### 1. Code Editor Integration
- Real-time code completion as users type
- Context-aware suggestions based on current file and project
- Smart auto-completion for functions, variables, and imports

### 2. AI-Powered Chat Assistant
- Interactive help for coding problems
- Code review and optimization suggestions
- Learning assistance with explanations and examples

### 3. Developer Productivity Tools
- Intelligent code generation
- Best practice recommendations
- Performance optimization suggestions

### 4. Educational Platforms
- Interactive coding tutorials
- Personalized learning suggestions
- Code quality feedback

This comprehensive API documentation provides developers with all the information needed to effectively integrate and leverage the Suggestion API endpoints in their applications, similar to GitHub Copilot's functionality.
