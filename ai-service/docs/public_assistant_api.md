# Public Assistant API

This documentation provides details about the Assistant API endpoints available in the AI Service. The Assistant API allows you to create, retrieve, update, and delete AI assistants with various capabilities and configurations.

## Overview

The Assistant API enables you to:

- Create custom AI assistants with specific configurations
- Retrieve existing assistants
- Update assistant properties and configurations
- Delete assistants

## Assistant Types

The system supports two main types of assistants:

1. **General Assistant** - A default assistant with predefined capabilities (CHATBOT as main unit with RAGBOT and SEARCHBOT as support units)
2. **Advanced Assistant** - A customizable assistant that can be configured with specific units, models, and settings

## Endpoints

### Get All Assistants

Retrieves all assistants available to the authenticated user.

**Endpoint:** `GET /assistant/get-all`

**Query Parameters:**
- `offset` (optional): Number of items to skip (default: 0)
- `limit` (optional): Maximum number of items to return (default: 10)

**Response:**

```json
{
  "status": 200,
  "message": "",
  "data": {
    "assistants": [
      {
        "id": "6f8d9e7c-5b3a-4a2f-8c1d-9e7f5b3a4a2f",
        "user_id": "1a2b3c4d-5e6f-7g8h-9i0j-1k2l3m4n5o6p",
        "name": "Research Assistant",
        "assistant_type": "ADVANCED",
        "description": "Helps with research tasks",
        "system_prompt": "You are a research assistant...",
        "provider": "openai",
        "model_name": "gpt-4",
        "temperature": 0.7,
        "ask_human": true,
        "interrupt": false,
        "main_unit": "CHATBOT",
        "support_units": ["RAGBOT", "SEARCHBOT"],
        "mcp_ids": ["mcp-1", "mcp-2"],
        "extension_ids": ["ext-1", "ext-2"],
        "teams": [
          {
            "id": "team-1",
            "name": "Research Team",
            "description": "Team for research tasks"
          }
        ],
        "created_at": "2025-06-28T14:30:00.000Z"
      }
    ],
    "total": 1,
    "offset": 0,
    "limit": 10
  }
}
```

### Get Assistant by ID

Retrieves a specific assistant by its ID.

**Endpoint:** `GET /assistant/{assistant_id}`

**Path Parameters:**
- `assistant_id`: The unique identifier of the assistant

**Response:**

```json
{
  "status": 200,
  "message": "",
  "data": {
    "id": "6f8d9e7c-5b3a-4a2f-8c1d-9e7f5b3a4a2f",
    "user_id": "1a2b3c4d-5e6f-7g8h-9i0j-1k2l3m4n5o6p",
    "name": "Research Assistant",
    "assistant_type": "ADVANCED",
    "description": "Helps with research tasks",
    "system_prompt": "You are a research assistant...",
    "provider": "openai",
    "model_name": "gpt-4",
    "temperature": 0.7,
    "ask_human": true,
    "interrupt": false,
    "main_unit": "CHATBOT",
    "support_units": ["RAGBOT", "SEARCHBOT"],
    "mcp_ids": ["mcp-1", "mcp-2"],
    "extension_ids": ["ext-1", "ext-2"],
    "teams": [
      {
        "id": "team-1",
        "name": "Research Team",
        "description": "Team for research tasks"
      }
    ],
    "created_at": "2025-06-28T14:30:00.000Z"
  }
}
```

### Create Advanced Assistant

Creates a new advanced assistant with customizable settings.

**Endpoint:** `POST /assistant/create`

**Request Body:**

```json
{
  "name": "Research Assistant",
  "description": "Helps with research tasks",
  "system_prompt": "You are a research assistant...",
  "provider": "openai",
  "model_name": "gpt-4",
  "temperature": 0.7,
  "ask_human": true,
  "interrupt": false,
  "support_units": ["RAGBOT", "SEARCHBOT"],
  "mcp_ids": ["mcp-1", "mcp-2"],
  "extension_ids": ["ext-1", "ext-2"]
}
```

**Request Parameters:**
- `name` (required): Name of the assistant (3-100 characters)
- `description` (optional): Description of the assistant (3-5000 characters)
- `system_prompt` (optional): Initial prompt for the assistant (3-5000 characters)
- `provider` (optional): Provider of the model (e.g., 'openai', 'anthropic')
- `model_name` (optional): Name of the model to use (e.g., 'gpt-4')
- `temperature` (optional): Controls randomness of output (0.0-2.0)
- `ask_human` (optional): Whether to ask for human confirmation before executing tasks
- `interrupt` (optional): Whether to allow interruption of current tasks
- `support_units` (optional): List of workflow types to support (e.g., ["RAGBOT", "SEARCHBOT"])
- `mcp_ids` (optional): List of MCP IDs to use
- `extension_ids` (optional): List of extension IDs to use

**Response:**

```json
{
  "status": 200,
  "message": "",
  "data": {
    "id": "6f8d9e7c-5b3a-4a2f-8c1d-9e7f5b3a4a2f",
    "user_id": "1a2b3c4d-5e6f-7g8h-9i0j-1k2l3m4n5o6p",
    "name": "Research Assistant",
    "assistant_type": "ADVANCED",
    "description": "Helps with research tasks",
    "system_prompt": "You are a research assistant...",
    "provider": "openai",
    "model_name": "gpt-4",
    "temperature": 0.7,
    "ask_human": true,
    "interrupt": false,
    "main_unit": "CHATBOT",
    "support_units": ["RAGBOT", "SEARCHBOT"],
    "mcp_ids": ["mcp-1", "mcp-2"],
    "extension_ids": ["ext-1", "ext-2"],
    "teams": [
      {
        "id": "team-1",
        "name": "Research Team",
        "description": "Team for research tasks"
      }
    ],
    "created_at": "2025-06-28T14:30:00.000Z"
  }
}
```

### Update Advanced Assistant

Updates an existing advanced assistant with new settings.

**Endpoint:** `PUT /assistant/{assistant_id}`

**Path Parameters:**
- `assistant_id`: The unique identifier of the assistant to update

**Request Body:**

```json
{
  "name": "Updated Research Assistant",
  "description": "Updated description for research tasks",
  "system_prompt": "You are an improved research assistant...",
  "provider": "anthropic",
  "model_name": "claude-3",
  "temperature": 0.5,
  "ask_human": false,
  "interrupt": true,
  "support_units": ["SEARCHBOT"],
  "mcp_ids": ["mcp-3"],
  "extension_ids": ["ext-3", "ext-4"]
}
```

**Request Parameters:**
- All parameters are optional, only the fields you want to update need to be included

**Response:**

```json
{
  "status": 200,
  "message": "",
  "data": {
    "id": "6f8d9e7c-5b3a-4a2f-8c1d-9e7f5b3a4a2f",
    "user_id": "1a2b3c4d-5e6f-7g8h-9i0j-1k2l3m4n5o6p",
    "name": "Updated Research Assistant",
    "assistant_type": "ADVANCED",
    "description": "Updated description for research tasks",
    "system_prompt": "You are an improved research assistant...",
    "provider": "anthropic",
    "model_name": "claude-3",
    "temperature": 0.5,
    "ask_human": false,
    "interrupt": true,
    "main_unit": "CHATBOT",
    "support_units": ["SEARCHBOT"],
    "mcp_ids": ["mcp-3"],
    "extension_ids": ["ext-3", "ext-4"],
    "teams": [
      {
        "id": "team-1",
        "name": "Research Team",
        "description": "Team for research tasks"
      }
    ],
    "created_at": "2025-06-28T14:30:00.000Z"
  }
}
```

### Update Assistant Configuration

Updates only the configuration settings of an assistant.

**Endpoint:** `PUT /assistant/{assistant_id}/config`

**Path Parameters:**
- `assistant_id`: The unique identifier of the assistant to update

**Request Body:**

```json
{
  "system_prompt": "You are an improved research assistant...",
  "provider": "anthropic",
  "model_name": "claude-3",
  "temperature": 0.5,
  "ask_human": false,
  "interrupt": true
}
```

**Response:**

```json
{
  "status": 200,
  "message": "Assistant configuration updated successfully",
  "data": null
}
```

### Delete Advanced Assistant

Deletes an advanced assistant permanently.

**Endpoint:** `DELETE /assistant/{assistant_id}`

**Path Parameters:**
- `assistant_id`: The unique identifier of the assistant to delete

**Response:**

```json
{
  "status": 200,
  "message": "Assistant deleted successfully",
  "data": null
}
```

### Soft Delete Advanced Assistant

Marks an advanced assistant as deleted without permanently removing it.

**Endpoint:** `DELETE /assistant/{assistant_id}/soft-delete-advanced-assistant`

**Path Parameters:**
- `assistant_id`: The unique identifier of the assistant to soft-delete

**Response:**

```json
{
  "status": 200,
  "message": "Assistant soft deleted successfully",
  "data": null
}
```

## Data Schemas

### Assistant Base

Common properties shared by all assistant types:

| Field | Type | Description |
|-------|------|-------------|
| name | string | Name of the assistant (3-100 characters) |
| description | string (optional) | Description of the assistant (3-5000 characters) |
| system_prompt | string (optional) | Initial prompt for the assistant (3-5000 characters) |

### CreateAdvancedAssistantRequest

| Field | Type | Description |
|-------|------|-------------|
| name | string | Name of the assistant (3-100 characters) |
| description | string (optional) | Description of the assistant (3-5000 characters) |
| system_prompt | string (optional) | Initial prompt for the assistant (3-5000 characters) |
| provider | string (optional) | Provider of the model (e.g., 'openai', 'anthropic') |
| model_name | string (optional) | Name of the model to use (e.g., 'gpt-4') |
| temperature | float (optional) | Controls randomness of output (0.0-2.0) |
| ask_human | boolean (optional) | Whether to ask for human confirmation before executing tasks |
| interrupt | boolean (optional) | Whether to allow interruption of current tasks |
| support_units | array (optional) | List of workflow types to support (e.g., ["RAGBOT", "SEARCHBOT"]) |
| mcp_ids | array (optional) | List of MCP IDs to use |
| extension_ids | array (optional) | List of extension IDs to use |

### UpdateAdvancedAssistantRequest

Same as CreateAdvancedAssistantRequest but all fields are optional.

### UpdateAssistantConfigRequest

| Field | Type | Description |
|-------|------|-------------|
| system_prompt | string (optional) | Initial prompt for the assistant (3-5000 characters) |
| provider | string (optional) | Provider of the model (e.g., 'openai', 'anthropic') |
| model_name | string (optional) | Name of the model to use (e.g., 'gpt-4') |
| temperature | float (optional) | Controls randomness of output (0.0-2.0) |
| ask_human | boolean (optional) | Whether to ask for human confirmation before executing tasks |
| interrupt | boolean (optional) | Whether to allow interruption of current tasks |

### Assistant Response Fields

| Field | Type | Description |
|-------|------|-------------|
| id | string | Unique identifier of the assistant |
| user_id | string | ID of the user who created the assistant |
| name | string | Name of the assistant |
| assistant_type | enum | Type of assistant (GENERAL or ADVANCED) |
| description | string (optional) | Description of the assistant |
| system_prompt | string (optional) | Initial prompt for the assistant |
| provider | string | Provider of the model |
| model_name | string (optional) | Name of the model being used |
| temperature | float (optional) | Controls randomness of output (0.0-2.0) |
| ask_human | boolean (optional) | Whether to ask for human confirmation before executing tasks |
| interrupt | boolean (optional) | Whether to allow interruption of current tasks |
| main_unit | enum | Main workflow type (e.g., CHATBOT) |
| support_units | array (optional) | List of supporting workflow types |
| mcp_ids | array (optional) | List of MCP IDs used by the assistant |
| extension_ids | array (optional) | List of extension IDs used by the assistant |
| teams | array (optional) | List of teams associated with the assistant |
| created_at | datetime (optional) | Creation timestamp of the assistant |

## Error Handling

The API uses standard HTTP status codes to indicate success or failure of requests:

| Status Code | Description |
|-------------|-------------|
| 200 | Success |
| 400 | Bad request (client error) |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Assistant not found |
| 500 | Internal server error |

For detailed error messages, refer to the `message` field in the response.

## Examples

### Creating a Simple Advanced Assistant

**Request:**

```bash
curl -X POST "https://your-api-domain/assistant/create" \
  -H "Authorization: Bearer YOUR_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Simple Helper",
    "description": "A basic assistant for everyday tasks",
    "system_prompt": "You are a helpful assistant...",
    "provider": "openai",
    "model_name": "gpt-4",
    "temperature": 0.7
  }'
```

**Response:**

```json
{
  "status": 200,
  "message": "",
  "data": {
    "id": "a1b2c3d4-e5f6-7g8h-9i0j-k1l2m3n4o5p6",
    "user_id": "u1v2w3x4-y5z6-7a8b-9c0d-e1f2g3h4i5j6",
    "name": "Simple Helper",
    "assistant_type": "ADVANCED",
    "description": "A basic assistant for everyday tasks",
    "system_prompt": "You are a helpful assistant...",
    "provider": "openai",
    "model_name": "gpt-4",
    "temperature": 0.7,
    "ask_human": null,
    "interrupt": null,
    "main_unit": "CHATBOT",
    "support_units": [],
    "mcp_ids": null,
    "extension_ids": null,
    "teams": [
      {
        "id": "team-chatbot-1",
        "name": "Simple Helper Team",
        "description": "Team for Simple Helper"
      }
    ],
    "created_at": "2025-07-01T10:15:00.000Z"
  }
}
```

### Creating an Advanced Assistant with Multiple Units

**Request:**

```bash
curl -X POST "https://your-api-domain/assistant/create" \
  -H "Authorization: Bearer YOUR_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Research Expert",
    "description": "Advanced assistant for research tasks",
    "system_prompt": "You are a specialized research assistant...",
    "provider": "anthropic",
    "model_name": "claude-3",
    "temperature": 0.5,
    "ask_human": true,
    "support_units": ["RAGBOT", "SEARCHBOT"],
    "mcp_ids": ["mcp-research-1", "mcp-research-2"],
    "extension_ids": ["ext-research-1"]
  }'
```

**Response:**

```json
{
  "status": 200,
  "message": "",
  "data": {
    "id": "d4e5f6g7-h8i9-j0k1-l2m3-n4o5p6q7r8s9",
    "user_id": "u1v2w3x4-y5z6-7a8b-9c0d-e1f2g3h4i5j6",
    "name": "Research Expert",
    "assistant_type": "ADVANCED",
    "description": "Advanced assistant for research tasks",
    "system_prompt": "You are a specialized research assistant...",
    "provider": "anthropic",
    "model_name": "claude-3",
    "temperature": 0.5,
    "ask_human": true,
    "interrupt": null,
    "main_unit": "CHATBOT",
    "support_units": ["RAGBOT", "SEARCHBOT"],
    "mcp_ids": ["mcp-research-1", "mcp-research-2"],
    "extension_ids": ["ext-research-1"],
    "teams": [
      {
        "id": "team-chatbot-2",
        "name": "Research Expert Chatbot",
        "description": "Chatbot team for Research Expert"
      },
      {
        "id": "team-ragbot-1",
        "name": "Research Expert RAG",
        "description": "RAG team for Research Expert"
      },
      {
        "id": "team-searchbot-1",
        "name": "Research Expert Search",
        "description": "Search team for Research Expert"
      }
    ],
    "created_at": "2025-07-01T14:22:00.000Z"
  }
}
```
