# Public Suggestion API

This documentation provides detailed information about the Suggestion API endpoints available in the AI Service. The Suggestion API enables users to receive intelligent recommendations, autocompletions, and contextual guidance within the system.

## Overview

The Suggestion API enables you to:

- Receive contextual suggestions based on user activity and input
- Get real-time autocompletions for various text inputs
- Access personalized recommendations for assistants, tools, and actions
- Receive intelligent next-step guidance during user workflows
- Customize suggestion preferences and relevance

Suggestions provide an enhanced user experience by anticipating user needs, reducing manual input, and guiding users through complex tasks. These suggestions are powered by machine learning models that analyze usage patterns and content.

## Base Models

### SuggestionResponse

Base suggestion information for a single recommendation:

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique identifier for the suggestion |
| `type` | string | Type of suggestion (autocomplete, command, assistant, etc.) |
| `content` | string | Primary content of the suggestion |
| `description` | string | Optional description providing context about the suggestion |
| `confidence` | float | Confidence score (0-1) indicating relevance of suggestion |
| `metadata` | object | Additional metadata related to the suggestion |

### BaseListSuggestionResponse

Response containing a list of suggestions:

| Field | Type | Description |
|-------|------|-------------|
| `suggestions` | array[SuggestionResponse] | List of suggestion items |
| `request_id` | string | Unique identifier for the suggestion request |
| `context` | object | Context information used to generate suggestions |

### SuggestionContext

Context information to help generate more relevant suggestions:

| Field | Type | Description |
|-------|------|-------------|
| `input` | string | User input text that triggered the suggestion |
| `thread_id` | string (optional) | ID of the current thread if applicable |
| `assistant_id` | string (optional) | ID of the current assistant if applicable |
| `recent_messages` | array (optional) | Recent message history for context |
| `document_context` | object (optional) | Information about currently opened documents |

### SuggestionFeedbackRequest

Feedback on a suggestion for improving the suggestion system:

| Field | Type | Description |
|-------|------|-------------|
| `suggestion_id` | string | ID of the suggestion receiving feedback |
| `request_id` | string | ID of the original suggestion request |
| `was_accepted` | boolean | Whether the suggestion was accepted by the user |
| `rating` | integer (optional) | Optional rating score (1-5) |
| `feedback_text` | string (optional) | Optional feedback comments |

## Endpoints

### Get Text Autocomplete Suggestions

Retrieves autocomplete suggestions based on user input text.

**Endpoint:** `GET /suggestions/autocomplete`

**Query Parameters:**
- `input` (required): The text input to generate suggestions for
- `context` (optional): JSON string containing context information
- `max_results` (optional): Maximum number of suggestions to return (default: 5)
- `types` (optional): Comma-separated list of suggestion types to include
  
**Response:**

```json
{
  "status": 200,
  "message": "Success",
  "data": {
    "suggestions": [
      {
        "id": "sug_abc123",
        "type": "autocomplete",
        "content": "import numpy as np",
        "description": "Import NumPy library",
        "confidence": 0.95,
        "metadata": {
          "category": "library_import",
          "language": "python"
        }
      },
      {
        "id": "sug_def456",
        "type": "autocomplete",
        "content": "import pandas as pd",
        "description": "Import Pandas library",
        "confidence": 0.92,
        "metadata": {
          "category": "library_import",
          "language": "python"
        }
      },
      {
        "id": "sug_ghi789",
        "type": "autocomplete",
        "content": "import matplotlib.pyplot as plt",
        "description": "Import Matplotlib plotting library",
        "confidence": 0.89,
        "metadata": {
          "category": "library_import",
          "language": "python"
        }
      }
    ],
    "request_id": "req_xyz123",
    "context": {
      "input": "import ",
      "thread_id": null,
      "document_context": {
        "file_type": "python"
      }
    }
  }
}
```

### Get Command Suggestions

Retrieves contextual command suggestions based on the current user state and activity.

**Endpoint:** `GET /suggestions/commands`

**Query Parameters:**
- `context` (optional): JSON string containing context information
- `max_results` (optional): Maximum number of suggestions to return (default: 5)
  
**Response:**

```json
{
  "status": 200,
  "message": "Success",
  "data": {
    "suggestions": [
      {
        "id": "sug_cmd123",
        "type": "command",
        "content": "analyze_data",
        "description": "Analyze current dataset using statistical methods",
        "confidence": 0.88,
        "metadata": {
          "requires_input": false,
          "category": "data_analysis"
        }
      },
      {
        "id": "sug_cmd456",
        "type": "command",
        "content": "generate_visualization",
        "description": "Create visualization for the selected data",
        "confidence": 0.85,
        "metadata": {
          "requires_input": true,
          "category": "visualization",
          "input_description": "Visualization type (bar, line, scatter, etc.)"
        }
      },
      {
        "id": "sug_cmd789",
        "type": "command",
        "content": "export_results",
        "description": "Export current results to file",
        "confidence": 0.82,
        "metadata": {
          "requires_input": true,
          "category": "data_export",
          "input_description": "File format (csv, xlsx, json)"
        }
      }
    ],
    "request_id": "req_cmd123",
    "context": {
      "thread_id": "thread_abc123",
      "assistant_id": "asst_def456",
      "document_context": {
        "file_type": "data_analysis"
      }
    }
  }
}
```

### Get Assistant Suggestions

Retrieves assistant suggestions based on the current context and user history.

**Endpoint:** `GET /suggestions/assistants`

**Query Parameters:**
- `context` (optional): JSON string containing context information
- `max_results` (optional): Maximum number of suggestions to return (default: 3)
  
**Response:**

```json
{
  "status": 200,
  "message": "Success",
  "data": {
    "suggestions": [
      {
        "id": "sug_asst123",
        "type": "assistant",
        "content": "Code Review Assistant",
        "description": "Get feedback on your code quality and suggestions for improvements",
        "confidence": 0.94,
        "metadata": {
          "assistant_id": "asst_code123",
          "skills": ["code_review", "refactoring", "best_practices"],
          "usage_count": 156
        }
      },
      {
        "id": "sug_asst456",
        "type": "assistant",
        "content": "Data Analysis Assistant",
        "description": "Help with analyzing datasets and generating insights",
        "confidence": 0.91,
        "metadata": {
          "assistant_id": "asst_data456",
          "skills": ["data_analysis", "statistics", "visualization"],
          "usage_count": 142
        }
      },
      {
        "id": "sug_asst789",
        "type": "assistant",
        "content": "Learning Assistant",
        "description": "Get help learning new programming concepts and techniques",
        "confidence": 0.87,
        "metadata": {
          "assistant_id": "asst_learn789",
          "skills": ["explanation", "tutorials", "examples"],
          "usage_count": 124
        }
      }
    ],
    "request_id": "req_asst123",
    "context": {
      "thread_id": null,
      "document_context": {
        "file_type": "python"
      }
    }
  }
}
```

### Get Workflow Suggestions

Retrieves next-step suggestions for the current user workflow.

**Endpoint:** `GET /suggestions/workflow`

**Query Parameters:**
- `thread_id` (required): ID of the current thread
- `max_results` (optional): Maximum number of suggestions to return (default: 3)
  
**Response:**

```json
{
  "status": 200,
  "message": "Success",
  "data": {
    "suggestions": [
      {
        "id": "sug_wf123",
        "type": "workflow",
        "content": "Create unit tests",
        "description": "Generate unit tests for your newly implemented function",
        "confidence": 0.92,
        "metadata": {
          "category": "testing",
          "estimated_time": "10-15 minutes"
        }
      },
      {
        "id": "sug_wf456",
        "type": "workflow",
        "content": "Document function",
        "description": "Add documentation for your new implementation",
        "confidence": 0.89,
        "metadata": {
          "category": "documentation",
          "estimated_time": "5-10 minutes"
        }
      },
      {
        "id": "sug_wf789",
        "type": "workflow",
        "content": "Commit changes",
        "description": "Commit your changes to version control",
        "confidence": 0.85,
        "metadata": {
          "category": "version_control",
          "estimated_time": "1-2 minutes"
        }
      }
    ],
    "request_id": "req_wf123",
    "context": {
      "thread_id": "thread_xyz789",
      "assistant_id": "asst_dev123"
    }
  }
}
```

### Submit Suggestion Feedback

Submits user feedback for a suggestion to improve future suggestions.

**Endpoint:** `POST /suggestions/feedback`

**Request Body:**
```json
{
  "suggestion_id": "sug_abc123",
  "request_id": "req_xyz123",
  "was_accepted": true,
  "rating": 5,
  "feedback_text": "This suggestion was exactly what I needed!"
}
```

**Response:**

```json
{
  "status": 200,
  "message": "Feedback submitted successfully",
  "data": {
    "suggestion_id": "sug_abc123",
    "request_id": "req_xyz123"
  }
}
```

## Error Handling

All endpoints use standard HTTP status codes and return consistent error responses:

| Status Code | Description |
|-------------|-------------|
| 200 | Success |
| 400 | Bad Request (invalid parameters) |
| 401 | Unauthorized (authentication required) |
| 404 | Not Found (resource not found) |
| 500 | Internal Server Error |

**Error Response Format:**

```json
{
  "status": 400,
  "message": "Invalid request: Missing required parameter 'input'",
  "data": null
}
```

**Common Error Scenarios:**

1. **Missing Required Parameter:**
```json
{
  "status": 400,
  "message": "Missing required parameter: input"
}
```

2. **Invalid Context Format:**
```json
{
  "status": 400,
  "message": "Invalid context format: Unable to parse JSON"
}
```

3. **Resource Not Found:**
```json
{
  "status": 404,
  "message": "Thread not found with ID: thread_unknown"
}
```

## Implementation Details

### Suggestion Generation Algorithm

Suggestions are generated using a multi-step process:

1. **Context Collection**: Gather relevant context including user input, thread history, and document information
2. **Candidate Generation**: Generate potential suggestions using ML models and rules-based systems
3. **Relevance Scoring**: Score each suggestion based on relevance to current context
4. **Filtering and Ranking**: Apply filters and rank suggestions by confidence score
5. **Response Formation**: Format and return the top suggestions

### Feedback Processing

User feedback is collected and processed to improve the suggestion system:

1. **Immediate Feedback**: Track which suggestions are accepted vs. rejected
2. **Explicit Ratings**: Process user ratings and comments
3. **Model Updating**: Periodically update suggestion models based on collected feedback
4. **A/B Testing**: Compare different suggestion algorithms using feedback data

## Examples

### Getting Code Autocompletions

**Request:**

```bash
curl -X GET "https://your-api-domain/suggestions/autocomplete?input=def%20calculate_" \
  -H "Content-Type: application/json"
```

**Response:**

```json
{
  "status": 200,
  "message": "Success",
  "data": {
    "suggestions": [
      {
        "id": "sug_code1",
        "type": "autocomplete",
        "content": "def calculate_average(numbers):\n    return sum(numbers) / len(numbers)",
        "description": "Calculate average of a list of numbers",
        "confidence": 0.96,
        "metadata": {
          "language": "python",
          "function_type": "math"
        }
      },
      {
        "id": "sug_code2",
        "type": "autocomplete",
        "content": "def calculate_median(numbers):\n    sorted_numbers = sorted(numbers)\n    n = len(sorted_numbers)\n    if n % 2 == 0:\n        return (sorted_numbers[n//2 - 1] + sorted_numbers[n//2]) / 2\n    else:\n        return sorted_numbers[n//2]",
        "description": "Calculate median of a list of numbers",
        "confidence": 0.92,
        "metadata": {
          "language": "python",
          "function_type": "math"
        }
      },
      {
        "id": "sug_code3",
        "type": "autocomplete",
        "content": "def calculate_distance(point1, point2):\n    return math.sqrt((point2[0] - point1[0])**2 + (point2[1] - point1[1])**2)",
        "description": "Calculate Euclidean distance between two points",
        "confidence": 0.88,
        "metadata": {
          "language": "python",
          "function_type": "math"
        }
      }
    ],
    "request_id": "req_auto123",
    "context": {
      "input": "def calculate_",
      "document_context": {
        "file_type": "python",
        "file_name": "math_utils.py"
      }
    }
  }
}
```

### Getting Personalized Assistant Recommendations

**Request:**

```bash
curl -X GET "https://your-api-domain/suggestions/assistants" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

**Response:**

```json
{
  "status": 200,
  "message": "Success",
  "data": {
    "suggestions": [
      {
        "id": "sug_pa1",
        "type": "assistant",
        "content": "SQL Expert",
        "description": "Get help with database queries and optimizations",
        "confidence": 0.97,
        "metadata": {
          "assistant_id": "asst_sql123",
          "skills": ["sql", "database_optimization", "query_building"],
          "usage_count": 42,
          "personalized": true
        }
      },
      {
        "id": "sug_pa2",
        "type": "assistant",
        "content": "Frontend Developer",
        "description": "Assistance with HTML, CSS, and JavaScript",
        "confidence": 0.94,
        "metadata": {
          "assistant_id": "asst_front456",
          "skills": ["html", "css", "javascript", "react"],
          "usage_count": 37,
          "personalized": true
        }
      },
      {
        "id": "sug_pa3",
        "type": "assistant",
        "content": "DevOps Helper",
        "description": "Help with CI/CD pipelines and deployment",
        "confidence": 0.91,
        "metadata": {
          "assistant_id": "asst_devops789",
          "skills": ["ci_cd", "docker", "kubernetes", "deployment"],
          "usage_count": 28,
          "personalized": true
        }
      }
    ],
    "request_id": "req_pa123",
    "context": {
      "user_id": "user_abc123",
      "recent_activity": {
        "technologies": ["sql", "database", "react"]
      }
    }
  }
}
```

## Best Practices

1. **Provide Rich Context**: Always include as much context as possible when requesting suggestions to improve relevance.

2. **Implement Feedback Loop**: Encourage users to provide feedback on suggestions to improve the system over time.

3. **Use Appropriate Endpoints**: Choose the most specific suggestion endpoint for your needs.

4. **Handle Confidence Scores**: Consider using confidence scores to determine how prominently to display suggestions.

5. **Cache Common Suggestions**: For performance optimization, cache frequently used suggestions.

## Integration Examples

### JavaScript Integration Example

```javascript
// Function to fetch autocomplete suggestions
async function fetchAutocompleteSuggestions(inputText, contextInfo = {}) {
  try {
    const queryParams = new URLSearchParams({
      input: inputText
    });
    
    if (Object.keys(contextInfo).length > 0) {
      queryParams.append('context', JSON.stringify(contextInfo));
    }
    
    const response = await fetch(`https://your-api-domain/suggestions/autocomplete?${queryParams.toString()}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer YOUR_API_KEY'
      }
    });
    
    const data = await response.json();
    
    if (data.status === 200) {
      return data.data;
    } else {
      console.error(`Error: ${data.message}`);
      return null;
    }
  } catch (error) {
    console.error('Failed to fetch suggestions:', error);
    return null;
  }
}

// Function to submit feedback for a suggestion
async function submitSuggestionFeedback(suggestionId, requestId, wasAccepted, rating = null, feedbackText = null) {
  try {
    const response = await fetch('https://your-api-domain/suggestions/feedback', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer YOUR_API_KEY'
      },
      body: JSON.stringify({
        suggestion_id: suggestionId,
        request_id: requestId,
        was_accepted: wasAccepted,
        rating: rating,
        feedback_text: feedbackText
      })
    });
    
    const data = await response.json();
    
    if (data.status === 200) {
      console.log('Feedback submitted successfully');
      return true;
    } else {
      console.error(`Error: ${data.message}`);
      return false;
    }
  } catch (error) {
    console.error('Failed to submit feedback:', error);
    return false;
  }
}

// Example usage
async function showCodeCompletions(editor) {
  const currentText = editor.getCurrentLine();
  const cursorPosition = editor.getCursorPosition();
  const fileType = editor.getFileType();
  
  const contextInfo = {
    document_context: {
      file_type: fileType,
      file_name: editor.getFileName(),
      line_number: cursorPosition.line
    }
  };
  
  const suggestionsData = await fetchAutocompleteSuggestions(currentText, contextInfo);
  
  if (suggestionsData && suggestionsData.suggestions.length > 0) {
    // Display suggestions in editor
    editor.showSuggestions(suggestionsData.suggestions);
    
    // Set up feedback handler
    editor.onSuggestionSelected((suggestion) => {
      submitSuggestionFeedback(suggestion.id, suggestionsData.request_id, true);
    });
    
    editor.onSuggestionDismissed((suggestion) => {
      submitSuggestionFeedback(suggestion.id, suggestionsData.request_id, false);
    });
  }
}
```

### Python Integration Example

```python
import requests
import json

class SuggestionClient:
    def __init__(self, api_base_url, api_key):
        self.api_base_url = api_base_url
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {api_key}'
        }
    
    def get_autocomplete_suggestions(self, input_text, context=None, max_results=5):
        """Get autocomplete suggestions based on input text."""
        params = {
            'input': input_text,
            'max_results': max_results
        }
        
        if context:
            params['context'] = json.dumps(context)
            
        try:
            response = requests.get(
                f"{self.api_base_url}/suggestions/autocomplete",
                headers=self.headers,
                params=params
            )
            response_data = response.json()
            
            if response_data["status"] == 200:
                return response_data["data"]
            else:
                print(f"Error: {response_data['message']}")
                return None
        except Exception as e:
            print(f"Failed to fetch autocomplete suggestions: {e}")
            return None
    
    def get_assistant_suggestions(self, context=None, max_results=3):
        """Get assistant suggestions based on context."""
        params = {'max_results': max_results}
        
        if context:
            params['context'] = json.dumps(context)
            
        try:
            response = requests.get(
                f"{self.api_base_url}/suggestions/assistants",
                headers=self.headers,
                params=params
            )
            response_data = response.json()
            
            if response_data["status"] == 200:
                return response_data["data"]
            else:
                print(f"Error: {response_data['message']}")
                return None
        except Exception as e:
            print(f"Failed to fetch assistant suggestions: {e}")
            return None
    
    def get_workflow_suggestions(self, thread_id, max_results=3):
        """Get workflow suggestions for a thread."""
        params = {
            'thread_id': thread_id,
            'max_results': max_results
        }
            
        try:
            response = requests.get(
                f"{self.api_base_url}/suggestions/workflow",
                headers=self.headers,
                params=params
            )
            response_data = response.json()
            
            if response_data["status"] == 200:
                return response_data["data"]
            else:
                print(f"Error: {response_data['message']}")
                return None
        except Exception as e:
            print(f"Failed to fetch workflow suggestions: {e}")
            return None
    
    def submit_suggestion_feedback(self, suggestion_id, request_id, was_accepted, 
                                  rating=None, feedback_text=None):
        """Submit feedback for a suggestion."""
        payload = {
            'suggestion_id': suggestion_id,
            'request_id': request_id,
            'was_accepted': was_accepted
        }
        
        if rating is not None:
            payload['rating'] = rating
            
        if feedback_text:
            payload['feedback_text'] = feedback_text
            
        try:
            response = requests.post(
                f"{self.api_base_url}/suggestions/feedback",
                headers=self.headers,
                json=payload
            )
            response_data = response.json()
            
            if response_data["status"] == 200:
                print("Feedback submitted successfully")
                return True
            else:
                print(f"Error: {response_data['message']}")
                return False
        except Exception as e:
            print(f"Failed to submit feedback: {e}")
            return False


# Example usage
def example_usage():
    # Initialize client
    client = SuggestionClient("https://your-api-domain", "YOUR_API_KEY")
    
    # Get code autocomplete suggestions
    code_context = {
        "document_context": {
            "file_type": "python",
            "file_name": "data_processing.py"
        }
    }
    
    code_suggestions = client.get_autocomplete_suggestions("import ", code_context)
    if code_suggestions:
        print("Code Suggestions:")
        for suggestion in code_suggestions["suggestions"]:
            print(f"- {suggestion['content']} ({suggestion['confidence']})")
        
        # Submit feedback for the first suggestion
        if code_suggestions["suggestions"]:
            first_suggestion = code_suggestions["suggestions"][0]
            client.submit_suggestion_feedback(
                first_suggestion["id"],
                code_suggestions["request_id"],
                True,
                5,
                "Perfect suggestion!"
            )
    
    # Get assistant suggestions
    assistant_suggestions = client.get_assistant_suggestions()
    if assistant_suggestions:
        print("\nRecommended Assistants:")
        for assistant in assistant_suggestions["suggestions"]:
            print(f"- {assistant['content']}: {assistant['description']}")
```

## Performance Considerations

1. **Response Time Optimization**: Suggestion endpoints are designed to respond within 200ms to provide a responsive user experience.

2. **Caching Strategy**: Implement client-side caching for frequently used suggestion types to reduce API calls.

3. **Batch Processing**: When possible, use batch processing for suggestion feedback to minimize API calls.

4. **Context Size**: Limit the size of context information to essential data to improve performance.

## Security Notes

1. **Data Privacy**: All suggestions are generated using anonymized data and do not expose sensitive user information.

2. **Access Control**: Authentication is required for personalized suggestion endpoints.

3. **Rate Limiting**: API endpoints implement rate limiting to prevent abuse.

4. **Context Validation**: All context information is validated to prevent injection attacks.

This comprehensive API documentation provides developers with all the information needed to effectively integrate and leverage the Suggestion API endpoints in their applications.
