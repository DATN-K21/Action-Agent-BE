# Public Team API

This documentation provides detailed information about the Team API endpoints available in the AI Service. The Team API enables users to create and manage teams of AI assistants for collaborative problem-solving and task completion.

## Overview

The Team API enables you to:

- Create new teams with different workflow types
- Retrieve individual teams or lists of teams
- Update team information and configurations
- Delete teams when they are no longer needed
- Stream interactions with teams for real-time collaboration
- Stop active streaming sessions

Teams provide a framework for organizing multiple AI agents (members) to work together, with different workflow types supporting various collaboration patterns like hierarchical, sequential, chatbot, and more.

## Base Models

### TeamBase

Core team information structure:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Name of the team, must be 1-64 characters long and can only contain alphanumeric characters, underscores, and hyphens |
| `description` | string | No | Description of the team |
| `icon` | string | No | Icon of the team |
| `workflow_type` | string | Yes | Workflow type associated with the team (hierarchical, sequential, chatbot, ragbot, searchbot, workflow) |

### CreateTeamRequest

Request structure for creating a new team - inherits all fields from TeamBase.

### UpdateTeamRequest

Request structure for updating a team:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | No | Updated name of the team |
| `description` | string | No | Updated description of the team |
| `icon` | string | No | Updated icon of the team |
| `workflow_type` | string | No | Updated workflow type associated with the team |

### ChatTeamRequest

Request structure for team chat interactions:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `messages` | array[ChatMessage] | Yes | List of chat messages in the team chat |
| `interrupt` | Interrupt | No | Interrupt associated with the team |

### TeamResponse

Response structure for team information:

| Field | Type | Description |
|-------|------|-------------|
| `id` | integer | Unique identifier for the team |
| `name` | string | Name of the team |
| `description` | string | Description of the team |
| `icon` | string | Icon of the team |
| `workflow_type` | string | Workflow type associated with the team |
| `user_id` | integer | ID of the user who owns the team |

### TeamsResponse

Response structure for listing multiple teams:

| Field | Type | Description |
|-------|------|-------------|
| `teams` | array[TeamResponse] | List of teams |
| `count` | integer | Total count of teams |

## Endpoints

### Get All Teams

Retrieves a list of all teams accessible to the current user.

**Endpoint:** `GET /team/`

**Query Parameters:**
- `skip` (optional): Number of items to skip (default: 0)
- `limit` (optional): Maximum number of items to return (default: 100)

**Headers:**
- `x-user-id`: Current user's ID
- `x-user-role`: Current user's role

**Response:**

```json
{
  "status": 200,
  "message": "Success",
  "data": {
    "teams": [
      {
        "id": 1,
        "name": "Research Team",
        "description": "Team focused on academic research",
        "icon": "research_icon",
        "workflow_type": "hierarchical",
        "user_id": 123
      },
      {
        "id": 2,
        "name": "Customer Support",
        "description": "AI team for customer service",
        "icon": "support_icon",
        "workflow_type": "sequential",
        "user_id": 123
      }
    ],
    "count": 2
  }
}
```

### Get Team by ID

Retrieves a specific team by its ID.

**Endpoint:** `GET /team/{team_id}`

**Path Parameters:**
- `team_id`: ID of the team to retrieve

**Headers:**
- `x-user-id`: Current user's ID
- `x-user-role`: Current user's role

**Response:**

```json
{
  "status": 200,
  "message": "Success",
  "data": {
    "id": 1,
    "name": "Research Team",
    "description": "Team focused on academic research",
    "icon": "research_icon",
    "workflow_type": "hierarchical",
    "user_id": 123
  }
}
```

### Create Team

Creates a new team with the specified configuration.

**Endpoint:** `POST /team/`

**Headers:**
- `x-user-id`: Current user's ID

**Request Body:**
```json
{
  "name": "Product Development",
  "description": "Team for developing new products",
  "icon": "product_icon",
  "workflow_type": "hierarchical"
}
```

**Response:**

```json
{
  "status": 200,
  "message": "Success",
  "data": {
    "id": 3,
    "name": "Product Development",
    "description": "Team for developing new products",
    "icon": "product_icon",
    "workflow_type": "hierarchical",
    "user_id": 123
  }
}
```

### Update Team

Updates an existing team's information.

**Endpoint:** `PUT /team/{team_id}`

**Path Parameters:**
- `team_id`: ID of the team to update

**Headers:**
- `x-user-id`: Current user's ID
- `x-user-role`: Current user's role

**Request Body:**
```json
{
  "name": "Product Innovation",
  "description": "Team focused on innovation and new products",
  "icon": "innovation_icon"
}
```

**Response:**

```json
{
  "status": 200,
  "message": "Success",
  "data": {
    "id": 3,
    "name": "Product Innovation",
    "description": "Team focused on innovation and new products",
    "icon": "innovation_icon",
    "workflow_type": "hierarchical",
    "user_id": 123
  }
}
```

### Delete Team

Deletes a team.

**Endpoint:** `DELETE /team/{team_id}`

**Path Parameters:**
- `team_id`: ID of the team to delete

**Headers:**
- `x-user-id`: Current user's ID
- `x-user-role`: Current user's role

**Response:**

```json
{
  "status": 200,
  "message": "Success",
  "data": {
    "message": "Team deleted successfully"
  }
}
```

### Stream Team Chat

Streams a response from the team based on user input.

**Endpoint:** `POST /team/{team_id}/stream/{thread_id}`

**Path Parameters:**
- `team_id`: ID of the team to interact with
- `thread_id`: ID of the thread to continue

**Headers:**
- `x-user-id`: Current user's ID
- `x-user-role`: Current user's role

**Request Body:**
```json
{
  "messages": [
    {
      "role": "user",
      "content": "How can we improve our product's user experience?"
    }
  ],
  "interrupt": null
}
```

**Response:**

This endpoint returns a streaming response with the media type `text/event-stream`. Each chunk of the response will be a fragment of the complete response from the team.

### Stop Team Chat Stream

Stops an active streaming session for a specific team and thread.

**Endpoint:** `POST /team/{team_id}/stream/{thread_id}/stop`

**Path Parameters:**
- `team_id`: ID of the team with the active stream
- `thread_id`: ID of the thread with the active stream

**Headers:**
- `x-user-id`: Current user's ID
- `x-user-role`: Current user's role

**Response:**

```json
{
  "status": 200,
  "message": "Success",
  "data": {
    "message": "Stream stop request sent successfully"
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
  "message": "Team not found",
  "data": null
}
```

**Common Error Scenarios:**

1. **Team Not Found:**
```json
{
  "status": 404,
  "message": "Team not found"
}
```

2. **Insufficient Permissions:**
```json
{
  "status": 403,
  "message": "Not enough permissions"
}
```

3. **Invalid Team Name:**
```json
{
  "status": 400,
  "message": "Team name already exists"
}
```

4. **Invalid Workflow Type:**
```json
{
  "status": 400,
  "message": "Invalid workflow type. Supported types: hierarchical, sequential, chatbot, ragbot, workflow."
}
```

## Workflow Types

The Team API supports several workflow types that determine how members collaborate:

1. **Hierarchical**: Organized team structure with a leader and workers, suitable for complex problem-solving with delegation
2. **Sequential**: Step-by-step processing where each member performs a specific task in sequence
3. **Chatbot**: Single conversational agent optimized for direct user interactions
4. **RAGBot**: Retrieval-Augmented Generation bot that utilizes knowledge bases to provide informed responses
5. **SearchBot**: Specialized bot focused on search capabilities
6. **Workflow**: Custom workflow configuration for specialized use cases

When creating a team, the selected workflow type automatically initializes appropriate member structures.

## Integration Examples

### JavaScript Integration Example

```javascript
// Function to get all teams
async function getTeams(skip = 0, limit = 100) {
  try {
    const response = await fetch(`https://your-api-domain/team/?skip=${skip}&limit=${limit}`, {
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
    console.error('Failed to fetch teams:', error);
    return null;
  }
}

// Function to create a new team
async function createTeam(teamData) {
  try {
    const response = await fetch('https://your-api-domain/team/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-user-id': 'your-user-id'
      },
      body: JSON.stringify(teamData)
    });
    
    const data = await response.json();
    
    if (data.status === 200) {
      console.log('Team created successfully');
      return data.data;
    } else {
      console.error(`Error: ${data.message}`);
      return null;
    }
  } catch (error) {
    console.error('Failed to create team:', error);
    return null;
  }
}

// Function to chat with a team with streaming response
async function streamTeamChat(teamId, threadId, messages) {
  try {
    const response = await fetch(`https://your-api-domain/team/${teamId}/stream/${threadId}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-user-id': 'your-user-id',
        'x-user-role': 'your-user-role'
      },
      body: JSON.stringify({
        messages: messages,
        interrupt: null
      })
    });
    
    // Process the streaming response
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';
    
    const processStream = async () => {
      const { value, done } = await reader.read();
      if (done) return;
      
      buffer += decoder.decode(value, { stream: true });
      
      // Process buffer to handle SSE format
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';
      
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.substring(6);
          if (data === '[DONE]') {
            console.log('Stream complete');
          } else {
            try {
              const parsedData = JSON.parse(data);
              console.log('Received chunk:', parsedData);
              // Process the chunk here (e.g., append to UI)
            } catch (e) {
              console.error('Error parsing stream data:', e);
            }
          }
        }
      }
      
      return processStream();
    };
    
    return processStream();
  } catch (error) {
    console.error('Stream error:', error);
  }
}

// Function to stop a team chat stream
async function stopTeamChatStream(teamId, threadId) {
  try {
    const response = await fetch(`https://your-api-domain/team/${teamId}/stream/${threadId}/stop`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-user-id': 'your-user-id',
        'x-user-role': 'your-user-role'
      }
    });
    
    const data = await response.json();
    
    if (data.status === 200) {
      console.log('Stream stopped successfully');
      return true;
    } else {
      console.error(`Error: ${data.message}`);
      return false;
    }
  } catch (error) {
    console.error('Failed to stop stream:', error);
    return false;
  }
}

// Example usage
async function exampleTeamWorkflow() {
  // Create a new team
  const newTeam = await createTeam({
    name: "ProjectAlpha",
    description: "Team for Project Alpha development",
    icon: "alpha_icon",
    workflow_type: "hierarchical"
  });
  
  if (newTeam) {
    console.log(`Created team with ID: ${newTeam.id}`);
    
    // Get all teams to verify
    const teams = await getTeams();
    console.log(`Found ${teams.count} teams`);
    
    // Start a conversation with the team
    const messages = [
      {
        role: "user",
        content: "How should we approach the development of Project Alpha?"
      }
    ];
    
    // Assuming we have a thread ID from creating a thread elsewhere
    const threadId = "example-thread-id";
    
    // Start streaming chat
    await streamTeamChat(newTeam.id, threadId, messages);
    
    // After some time, stop the stream
    setTimeout(() => {
      stopTeamChatStream(newTeam.id, threadId);
    }, 10000);
  }
}
```

### Python Integration Example

```python
import requests
import json
import time
import sseclient

class TeamApiClient:
    def __init__(self, api_base_url, user_id, user_role):
        self.api_base_url = api_base_url
        self.headers = {
            'Content-Type': 'application/json',
            'x-user-id': user_id,
            'x-user-role': user_role
        }
    
    def get_teams(self, skip=0, limit=100):
        """Get all teams accessible to the current user."""
        try:
            response = requests.get(
                f"{self.api_base_url}/team/",
                headers=self.headers,
                params={'skip': skip, 'limit': limit}
            )
            response_data = response.json()
            
            if response_data["status"] == 200:
                return response_data["data"]
            else:
                print(f"Error: {response_data['message']}")
                return None
        except Exception as e:
            print(f"Failed to fetch teams: {e}")
            return None
    
    def get_team(self, team_id):
        """Get a specific team by ID."""
        try:
            response = requests.get(
                f"{self.api_base_url}/team/{team_id}",
                headers=self.headers
            )
            response_data = response.json()
            
            if response_data["status"] == 200:
                return response_data["data"]
            else:
                print(f"Error: {response_data['message']}")
                return None
        except Exception as e:
            print(f"Failed to fetch team: {e}")
            return None
    
    def create_team(self, name, description=None, icon=None, workflow_type="hierarchical"):
        """Create a new team."""
        payload = {
            "name": name,
            "workflow_type": workflow_type
        }
        
        if description:
            payload["description"] = description
            
        if icon:
            payload["icon"] = icon
            
        try:
            response = requests.post(
                f"{self.api_base_url}/team/",
                headers=self.headers,
                json=payload
            )
            response_data = response.json()
            
            if response_data["status"] == 200:
                print("Team created successfully")
                return response_data["data"]
            else:
                print(f"Error: {response_data['message']}")
                return None
        except Exception as e:
            print(f"Failed to create team: {e}")
            return None
    
    def update_team(self, team_id, name=None, description=None, icon=None, workflow_type=None):
        """Update an existing team."""
        payload = {}
        
        if name is not None:
            payload["name"] = name
            
        if description is not None:
            payload["description"] = description
            
        if icon is not None:
            payload["icon"] = icon
            
        if workflow_type is not None:
            payload["workflow_type"] = workflow_type
            
        try:
            response = requests.put(
                f"{self.api_base_url}/team/{team_id}",
                headers=self.headers,
                json=payload
            )
            response_data = response.json()
            
            if response_data["status"] == 200:
                print("Team updated successfully")
                return response_data["data"]
            else:
                print(f"Error: {response_data['message']}")
                return None
        except Exception as e:
            print(f"Failed to update team: {e}")
            return None
    
    def delete_team(self, team_id):
        """Delete a team."""
        try:
            response = requests.delete(
                f"{self.api_base_url}/team/{team_id}",
                headers=self.headers
            )
            response_data = response.json()
            
            if response_data["status"] == 200:
                print("Team deleted successfully")
                return True
            else:
                print(f"Error: {response_data['message']}")
                return False
        except Exception as e:
            print(f"Failed to delete team: {e}")
            return False
    
    def stream_chat(self, team_id, thread_id, messages, callback):
        """Stream a chat with a team."""
        payload = {
            "messages": messages,
            "interrupt": None
        }
            
        try:
            response = requests.post(
                f"{self.api_base_url}/team/{team_id}/stream/{thread_id}",
                headers=self.headers,
                json=payload,
                stream=True
            )
            
            client = sseclient.SSEClient(response)
            for event in client.events():
                if event.data == "[DONE]":
                    print("Stream complete")
                    break
                
                try:
                    data = json.loads(event.data)
                    callback(data)
                except Exception as e:
                    print(f"Error parsing stream data: {e}")
            
            return True
        except Exception as e:
            print(f"Stream error: {e}")
            return False
    
    def stop_stream(self, team_id, thread_id):
        """Stop an active stream."""
        try:
            response = requests.post(
                f"{self.api_base_url}/team/{team_id}/stream/{thread_id}/stop",
                headers=self.headers
            )
            response_data = response.json()
            
            if response_data["status"] == 200:
                print("Stream stopped successfully")
                return True
            else:
                print(f"Error: {response_data['message']}")
                return False
        except Exception as e:
            print(f"Failed to stop stream: {e}")
            return False


# Example usage
def example_team_workflow():
    # Initialize client
    client = TeamApiClient("https://your-api-domain", "your-user-id", "your-user-role")
    
    # Create a new team
    new_team = client.create_team(
        name="ResearchTeam",
        description="AI research and development team",
        workflow_type="hierarchical"
    )
    
    if new_team:
        team_id = new_team["id"]
        print(f"Created team with ID: {team_id}")
        
        # Get all teams to verify
        teams = client.get_teams()
        if teams:
            print(f"Found {teams['count']} teams")
        
        # Start a conversation with the team
        messages = [
            {
                "role": "user",
                "content": "What are the latest trends in AI research?"
            }
        ]
        
        # Assuming we have a thread ID from creating a thread elsewhere
        thread_id = "example-thread-id"
        
        # Define callback for processing stream chunks
        def process_chunk(data):
            print(f"Received: {data}")
        
        # Start streaming chat in a separate thread
        import threading
        stream_thread = threading.Thread(
            target=client.stream_chat,
            args=(team_id, thread_id, messages, process_chunk)
        )
        stream_thread.start()
        
        # Wait a bit and then stop the stream
        time.sleep(10)
        client.stop_stream(team_id, thread_id)
        
        # Wait for stream thread to complete
        stream_thread.join()

if __name__ == "__main__":
    example_team_workflow()
```

## Best Practices

1. **Team Naming**: Use descriptive, unique names for teams to easily identify their purpose.

2. **Workflow Selection**: Choose the appropriate workflow type based on the team's intended function:
   - Use hierarchical for complex problem-solving with delegation
   - Use sequential for step-by-step processing
   - Use chatbot for simple conversational interfaces
   - Use RAGBot when knowledge base integration is needed

3. **Error Handling**: Implement robust error handling for all API calls, particularly for streaming operations which may be interrupted.

4. **Streaming Management**: Always provide users with the ability to stop ongoing streams to prevent resource waste.

5. **Permission Control**: Respect the permission model - only team owners and administrators can modify teams.

## Performance Considerations

1. **Stream Timeouts**: Be prepared to handle timeouts in streaming connections, which may occur after periods of inactivity.

2. **Rate Limiting**: The API implements rate limiting to prevent abuse; consider implementing retry logic with exponential backoff.

3. **Large Team Management**: For teams with many members, consider pagination when retrieving member lists to improve performance.

4. **Resource Cleanup**: Always stop streams when they are no longer needed to free up server resources.

This comprehensive API documentation provides developers with all the information needed to effectively integrate and leverage the Team API endpoints in their applications.
