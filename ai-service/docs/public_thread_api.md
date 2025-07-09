# Public Thread API

This documentation provides detailed information about the Thread API endpoints available in the AI Service. The Thread API enables users to create and manage conversation threads for interactions with AI assistants.

## Overview

The Thread API enables you to:

- Create new threads associated with specific assistants
- Retrieve individual threads or lists of threads
- Update thread information
- Delete threads when they are no longer needed
- Generate thread titles based on conversation content
- Retrieve conversation history within a thread

Threads serve as containers for conversations with AI assistants, maintaining context and history across multiple interactions. Each thread is associated with a specific assistant and belongs to a user.

## Base Models

### ThreadBase

Core thread information structure:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `title` | string | Yes | Title of the thread, must be 3-50 characters long |
| `assistant_id` | string | Yes | ID of the assistant associated with the thread |

### CreateThreadRequest

Request structure for creating a new thread - inherits all fields from ThreadBase.

### UpdateThreadRequest

Request structure for updating a thread:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `title` | string | No | Updated title of the thread |
| `assistant_id` | string | No | Updated ID of the assistant associated with the thread |

### ThreadResponse

Response structure for thread information:

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique identifier for the thread |
| `user_id` | string | ID of the user who owns the thread |
| `title` | string | Title of the thread |
| `assistant_id` | string | ID of the assistant associated with the thread |
| `created_at` | datetime | Timestamp when the thread was created |
| `assistant` | object | Details of the assistant associated with the thread (optional) |

### ThreadsResponse

Response structure for listing multiple threads:

| Field | Type | Description |
|-------|------|-------------|
| `threads` | array[ThreadResponse] | List of threads |
| `cursor` | string | Current pagination cursor |
| `next_cursor` | string | Cursor for the next page of results |
| `prev_cursor` | string | Cursor for the previous page of results |

### GetHistoryResponse

Response structure for retrieving thread history:

| Field | Type | Description |
|-------|------|-------------|
| `user_id` | string | ID of the user who owns the thread |
| `thread_id` | string | ID of the thread |
| `assistant_id` | string | ID of the assistant associated with the thread |
| `messages` | array[ChatResponse] | List of messages in the thread |

## Endpoints

### Get All Threads

Retrieves a list of all threads accessible to the current user.

**Endpoint:** `GET /thread/get-all`

**Query Parameters:**
- `cursor` (optional): Pagination cursor
- `max_per_page` (optional): Maximum number of items to return

**Headers:**
- `x-user-id`: Current user's ID
- `x-user-role`: Current user's role

**Response:**

```json
{
  "status": 200,
  "message": "Success",
  "data": {
    "threads": [
      {
        "id": "thread-123",
        "user_id": "user-456",
        "title": "Project Discussion",
        "assistant_id": "assistant-789",
        "created_at": "2025-06-30T14:30:00Z",
        "assistant": {
          "id": "assistant-789",
          "name": "Project Manager",
          "description": "Helps with project management tasks",
          "system_prompt": "You are a helpful project management assistant.",
          "assistant_type": "chatbot",
          "provider": "openai",
          "model_name": "gpt-4o",
          "temperature": 0.7,
          "ask_human": false,
          "interrupt": false,
          "created_at": "2025-06-15T10:00:00Z"
        }
      },
      {
        "id": "thread-124",
        "user_id": "user-456",
        "title": "Coding Help",
        "assistant_id": "assistant-790",
        "created_at": "2025-06-29T09:45:00Z",
        "assistant": {
          "id": "assistant-790",
          "name": "Code Expert",
          "description": "Helps with coding problems",
          "system_prompt": "You are a coding expert who helps solve programming problems.",
          "assistant_type": "chatbot",
          "provider": "anthropic",
          "model_name": "claude-3-opus",
          "temperature": 0.5,
          "ask_human": false,
          "interrupt": true,
          "created_at": "2025-06-10T08:20:00Z"
        }
      }
    ],
    "cursor": null,
    "next_cursor": "2025-06-29T09:45:00Z",
    "prev_cursor": "2025-06-30T14:30:00Z"
  }
}
```

### Get Thread by ID

Retrieves a specific thread by its ID.

**Endpoint:** `GET /thread/{thread_id}/get-detail`

**Path Parameters:**
- `thread_id`: ID of the thread to retrieve

**Headers:**
- `x-user-id`: Current user's ID

**Response:**

```json
{
  "status": 200,
  "message": "Success",
  "data": {
    "id": "thread-123",
    "user_id": "user-456",
    "title": "Project Discussion",
    "assistant_id": "assistant-789",
    "created_at": "2025-06-30T14:30:00Z",
    "assistant": {
      "id": "assistant-789",
      "name": "Project Manager",
      "description": "Helps with project management tasks",
      "system_prompt": "You are a helpful project management assistant.",
      "assistant_type": "chatbot",
      "provider": "openai",
      "model_name": "gpt-4o",
      "temperature": 0.7,
      "ask_human": false,
      "interrupt": false,
      "created_at": "2025-06-15T10:00:00Z"
    }
  }
}
```

### Create Thread

Creates a new thread with the specified configuration.

**Endpoint:** `POST /thread/create`

**Headers:**
- `x-user-id`: Current user's ID
- `x-user-role`: Current user's role

**Request Body:**
```json
{
  "title": "New Research Project",
  "assistant_id": "assistant-789"
}
```

**Response:**

```json
{
  "status": 200,
  "message": "Success",
  "data": {
    "id": "thread-125",
    "user_id": "user-456",
    "title": "New Research Project",
    "assistant_id": "assistant-789",
    "created_at": "2025-07-01T09:15:00Z"
  }
}
```

### Update Thread

Updates an existing thread's information.

**Endpoint:** `PATCH /thread/{thread_id}/update`

**Path Parameters:**
- `thread_id`: ID of the thread to update

**Headers:**
- `x-user-id`: Current user's ID

**Request Body:**
```json
{
  "title": "Updated Research Project",
  "assistant_id": "assistant-791"
}
```

**Response:**

```json
{
  "status": 200,
  "message": "Success",
  "data": {
    "id": "thread-125",
    "user_id": "user-456",
    "title": "Updated Research Project",
    "assistant_id": "assistant-791",
    "created_at": "2025-07-01T09:15:00Z"
  }
}
```

### Delete Thread

Deletes a thread. This is a soft delete that marks the thread as deleted but retains the data.

**Endpoint:** `DELETE /thread/{thread_id}/delete`

**Path Parameters:**
- `thread_id`: ID of the thread to delete

**Headers:**
- `x-user-id`: Current user's ID

**Response:**

```json
{
  "status": 200,
  "message": "Success",
  "data": {
    "message": "Thread deleted successfully"
  }
}
```

### Generate Thread Title

Automatically generates a title for a thread based on its conversation content.

**Endpoint:** `POST /thread/{thread_id}/generate-title`

**Path Parameters:**
- `thread_id`: ID of the thread to generate a title for

**Headers:**
- `x-user-id`: Current user's ID

**Response:**

```json
{
  "status": 200,
  "message": "Success",
  "data": {
    "id": "thread-125",
    "user_id": "user-456",
    "title": "AI Research Methods Discussion",
    "assistant_id": "assistant-791",
    "created_at": "2025-07-01T09:15:00Z"
  }
}
```

### Get Thread History

Retrieves the conversation history within a thread.

**Endpoint:** `POST /thread/{thread_id}/get-history`

**Path Parameters:**
- `thread_id`: ID of the thread to retrieve history for

**Headers:**
- `x-user-id`: Current user's ID

**Response:**

```json
{
  "status": 200,
  "message": "Success",
  "data": {
    "user_id": "user-456",
    "thread_id": "thread-125",
    "assistant_id": "assistant-791",
    "messages": [
      {
        "id": "msg-1",
        "role": "user",
        "type": "user",
        "content": "What are the latest research methods in AI?",
        "created_at": "2025-07-01T09:20:00Z"
      },
      {
        "id": "msg-2",
        "role": "assistant",
        "type": "assistant",
        "content": "The latest research methods in AI include...",
        "created_at": "2025-07-01T09:20:15Z"
      },
      {
        "id": "msg-3",
        "role": "user",
        "type": "user",
        "content": "Can you elaborate on reinforcement learning from human feedback?",
        "created_at": "2025-07-01T09:22:00Z"
      },
      {
        "id": "msg-4",
        "role": "assistant",
        "type": "assistant",
        "content": "Reinforcement Learning from Human Feedback (RLHF) is...",
        "created_at": "2025-07-01T09:22:30Z"
      }
    ]
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
| 403 | Forbidden (insufficient permissions) |
| 404 | Not Found (resource not found) |
| 500 | Internal Server Error |

**Error Response Format:**

```json
{
  "status": 404,
  "message": "Thread not found",
  "data": null
}
```

**Common Error Scenarios:**

1. **Thread Not Found:**
```json
{
  "status": 404,
  "message": "Thread not found"
}
```

2. **Invalid Thread Parameters:**
```json
{
  "status": 400,
  "message": "Title must be between 3 and 50 characters"
}
```

3. **Assistant Not Found:**
```json
{
  "status": 404,
  "message": "Assistant not found"
}
```

## Integration Examples

### JavaScript Integration Example

```javascript
// Function to get all threads
async function getThreads(cursor = null, maxPerPage = 20) {
  try {
    let url = `https://your-api-domain/thread/get-all?max_per_page=${maxPerPage}`;
    if (cursor) {
      url += `&cursor=${encodeURIComponent(cursor)}`;
    }
    
    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'x-user-id': 'your-user-id',
        'x-user-role': 'your-user-role'
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
    console.error('Failed to fetch threads:', error);
    return null;
  }
}

// Function to create a new thread
async function createThread(title, assistantId) {
  try {
    const response = await fetch('https://your-api-domain/thread/create', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-user-id': 'your-user-id',
        'x-user-role': 'your-user-role'
      },
      body: JSON.stringify({
        title: title,
        assistant_id: assistantId
      })
    });
    
    const data = await response.json();
    
    if (data.status === 200) {
      console.log('Thread created successfully');
      return data.data;
    } else {
      console.error(`Error: ${data.message}`);
      return null;
    }
  } catch (error) {
    console.error('Failed to create thread:', error);
    return null;
  }
}

// Function to get thread history
async function getThreadHistory(threadId) {
  try {
    const response = await fetch(`https://your-api-domain/thread/${threadId}/get-history`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-user-id': 'your-user-id',
        'x-user-role': 'your-user-role'
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
    console.error('Failed to get thread history:', error);
    return null;
  }
}

// Function to generate a title for a thread
async function generateThreadTitle(threadId) {
  try {
    const response = await fetch(`https://your-api-domain/thread/${threadId}/generate-title`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-user-id': 'your-user-id',
        'x-user-role': 'your-user-role'
      }
    });
    
    const data = await response.json();
    
    if (data.status === 200) {
      console.log(`Title generated: ${data.data.title}`);
      return data.data;
    } else {
      console.error(`Error: ${data.message}`);
      return null;
    }
  } catch (error) {
    console.error('Failed to generate thread title:', error);
    return null;
  }
}

// Example usage
async function exampleThreadWorkflow() {
  // Create a new thread
  const newThread = await createThread("Initial Research Discussion", "assistant-789");
  
  if (newThread) {
    console.log(`Created thread with ID: ${newThread.id}`);
    
    // Get thread history (assuming messages have been added in another part of the application)
    const history = await getThreadHistory(newThread.id);
    if (history && history.messages.length > 0) {
      console.log(`Retrieved ${history.messages.length} messages from thread`);
      
      // Generate a title based on the conversation
      const updatedThread = await generateThreadTitle(newThread.id);
      console.log(`Thread title updated to: ${updatedThread.title}`);
    } else {
      console.log("No messages in the thread yet");
    }
    
    // Get all threads to verify
    const threads = await getThreads();
    if (threads) {
      console.log(`Found ${threads.threads.length} threads`);
      threads.threads.forEach(thread => {
        console.log(`- ${thread.title} (ID: ${thread.id})`);
      });
    }
  }
}

// Run the example workflow
exampleThreadWorkflow();
```

### Python Integration Example

```python
import requests
import json
from urllib.parse import quote

class ThreadApiClient:
    def __init__(self, api_base_url, user_id, user_role):
        self.api_base_url = api_base_url
        self.headers = {
            'Content-Type': 'application/json',
            'x-user-id': user_id,
            'x-user-role': user_role
        }
    
    def get_threads(self, cursor=None, max_per_page=20):
        """Get all threads accessible to the current user."""
        try:
            url = f"{self.api_base_url}/thread/get-all?max_per_page={max_per_page}"
            if cursor:
                url += f"&cursor={quote(cursor)}"
                
            response = requests.get(
                url,
                headers=self.headers
            )
            response_data = response.json()
            
            if response_data["status"] == 200:
                return response_data["data"]
            else:
                print(f"Error: {response_data['message']}")
                return None
        except Exception as e:
            print(f"Failed to fetch threads: {e}")
            return None
    
    def get_thread(self, thread_id):
        """Get a specific thread by ID."""
        try:
            response = requests.get(
                f"{self.api_base_url}/thread/{thread_id}/get-detail",
                headers=self.headers
            )
            response_data = response.json()
            
            if response_data["status"] == 200:
                return response_data["data"]
            else:
                print(f"Error: {response_data['message']}")
                return None
        except Exception as e:
            print(f"Failed to fetch thread: {e}")
            return None
    
    def create_thread(self, title, assistant_id):
        """Create a new thread."""
        payload = {
            "title": title,
            "assistant_id": assistant_id
        }
            
        try:
            response = requests.post(
                f"{self.api_base_url}/thread/create",
                headers=self.headers,
                json=payload
            )
            response_data = response.json()
            
            if response_data["status"] == 200:
                print("Thread created successfully")
                return response_data["data"]
            else:
                print(f"Error: {response_data['message']}")
                return None
        except Exception as e:
            print(f"Failed to create thread: {e}")
            return None
    
    def update_thread(self, thread_id, title=None, assistant_id=None):
        """Update an existing thread."""
        payload = {}
        
        if title is not None:
            payload["title"] = title
            
        if assistant_id is not None:
            payload["assistant_id"] = assistant_id
            
        try:
            response = requests.patch(
                f"{self.api_base_url}/thread/{thread_id}/update",
                headers=self.headers,
                json=payload
            )
            response_data = response.json()
            
            if response_data["status"] == 200:
                print("Thread updated successfully")
                return response_data["data"]
            else:
                print(f"Error: {response_data['message']}")
                return None
        except Exception as e:
            print(f"Failed to update thread: {e}")
            return None
    
    def delete_thread(self, thread_id):
        """Delete a thread."""
        try:
            response = requests.delete(
                f"{self.api_base_url}/thread/{thread_id}/delete",
                headers=self.headers
            )
            response_data = response.json()
            
            if response_data["status"] == 200:
                print("Thread deleted successfully")
                return True
            else:
                print(f"Error: {response_data['message']}")
                return False
        except Exception as e:
            print(f"Failed to delete thread: {e}")
            return False
    
    def generate_title(self, thread_id):
        """Generate a title for a thread based on its content."""
        try:
            response = requests.post(
                f"{self.api_base_url}/thread/{thread_id}/generate-title",
                headers=self.headers
            )
            response_data = response.json()
            
            if response_data["status"] == 200:
                print(f"Title generated: {response_data['data']['title']}")
                return response_data["data"]
            else:
                print(f"Error: {response_data['message']}")
                return None
        except Exception as e:
            print(f"Failed to generate thread title: {e}")
            return None
    
    def get_thread_history(self, thread_id):
        """Get the conversation history for a thread."""
        try:
            response = requests.post(
                f"{self.api_base_url}/thread/{thread_id}/get-history",
                headers=self.headers
            )
            response_data = response.json()
            
            if response_data["status"] == 200:
                return response_data["data"]
            else:
                print(f"Error: {response_data['message']}")
                return None
        except Exception as e:
            print(f"Failed to get thread history: {e}")
            return None


# Example usage
def example_thread_workflow():
    # Initialize client
    client = ThreadApiClient("https://your-api-domain", "your-user-id", "your-user-role")
    
    # Create a new thread
    new_thread = client.create_thread(
        title="AI Research Discussion",
        assistant_id="assistant-789"
    )
    
    if new_thread:
        thread_id = new_thread["id"]
        print(f"Created thread with ID: {thread_id}")
        
        # Update the thread title
        updated_thread = client.update_thread(
            thread_id=thread_id,
            title="Advanced AI Research Discussion"
        )
        if updated_thread:
            print(f"Updated thread title to: {updated_thread['title']}")
        
        # Get thread history (assuming messages have been added elsewhere)
        history = client.get_thread_history(thread_id)
        if history and history.get("messages"):
            print(f"Retrieved {len(history['messages'])} messages from thread")
            
            # Generate a title based on the conversation
            titled_thread = client.generate_title(thread_id)
            if titled_thread:
                print(f"Thread title auto-generated to: {titled_thread['title']}")
        else:
            print("No messages in the thread yet")
        
        # Get all threads to verify
        threads = client.get_threads()
        if threads and threads.get("threads"):
            print(f"Found {len(threads['threads'])} threads:")
            for thread in threads["threads"]:
                print(f"- {thread['title']} (ID: {thread['id']})")

if __name__ == "__main__":
    example_thread_workflow()
```

## Best Practices

1. **Thread Management**: Create separate threads for different topics or projects to keep conversations organized.

2. **Thread Titles**: Use descriptive thread titles to easily identify conversations, or leverage the auto-generation feature if the conversation already has messages.

3. **Thread Lifecycle**: Delete threads that are no longer needed to keep your interface clean and organized.

4. **Error Handling**: Implement robust error handling in your applications, especially for thread operations that require specific permissions.

5. **Pagination**: When retrieving multiple threads, use the cursor-based pagination to efficiently load threads as needed rather than all at once.

## Performance Considerations

1. **Thread History**: For threads with extensive conversation history, consider optimizing your client to display messages incrementally or paginate them.

2. **Title Generation**: The title generation feature processes the entire conversation history, so it may take longer for threads with many messages.

3. **Caching**: Consider caching thread information on the client side to reduce the number of API calls, especially for frequently accessed threads.

4. **Rate Limiting**: Be aware that the API may implement rate limiting for operations like creating or updating threads.

This comprehensive API documentation provides developers with all the information needed to effectively integrate and leverage the Thread API endpoints in their applications.
