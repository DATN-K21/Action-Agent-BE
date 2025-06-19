# Assistant API Documentation

This document provides comprehensive information about the Assistant API endpoints in the AI Service.

## Overview

The Assistant API allows you to manage AI assistants within the system. There are two types of assistants:

- **General Assistant**: A simple, pre-configured assistant for everyday tasks
- **Advanced Assistant**: A customizable assistant with multiple units, extensions, and MCPs

## Base URL

```
http://localhost:8000/api/v1/assistant
```

## Authentication

All API requests require authentication headers:

- `x-user-id`: **Required** - The user ID making the request
- `x-user-role`: **Optional** - The user role (admin, super_admin, etc.)

## Response Format

All API responses follow this structure:

```json
{
  "status": 200,
  "message": "Success message or null",
  "data": {
    // Response data object
  }
}
```

## Error Handling

### Common Error Responses

- **400 Bad Request**: Validation errors or malformed requests
- **404 Not Found**: Resource not found
- **500 Internal Server Error**: Server-side errors

Example error response:
```json
{
  "status": 400,
  "message": "Validation error - \"name\": String should have at least 3 characters",
  "data": null
}
```

## API Endpoints

### 1. Get All Assistants

Retrieve a paginated list of assistants for the authenticated user.

**Endpoint:** `GET /get-all`

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `assistant_type` | `AssistantType` | No | `null` | Filter by assistant type (`general_assistant` or `advanced_assistant`) |
| `page_number` | `integer` | No | `1` | Page number (≥ 1) |
| `max_per_page` | `integer` | No | `10` | Items per page (1-100) |

**Response Model:** `ResponseWrapper<GetAssistantsResponse>`

**Success Response (200):**
```json
{
  "status": 200,
  "message": null,
  "data": {
    "assistants": [
      {
        "id": "uuid-string",
        "userId": "user-id",
        "name": "My Assistant",
        "assistantType": "advanced_assistant",
        "description": "A helpful assistant",
        "systemPrompt": "You are a helpful assistant",
        "provider": "openai",
        "modelName": "gpt-4",
        "temperature": 0.7,
        "askHuman": false,
        "interrupt": false,
        "mainUnit": "hierarchical",
        "supportUnits": ["ragbot", "searchbot"],
        "mcpIds": ["mcp-id-1"],
        "extensionIds": ["ext-id-1"],
        "teams": [
          {
            "id": "team-id",
            "name": "Main Team",
            "workflowType": "hierarchical"
          }
        ],
        "createdAt": "2024-01-01T00:00:00Z"
      }
    ],
    "pageNumber": 1,
    "maxPerPage": 10,
    "totalPage": 1
  }
}
```

### 2. Get or Create General Assistant

Get existing general assistant or create a new one if it doesn't exist.

**Endpoint:** `GET /get-or-create-general-assistant`

**Query Parameters:** None

**Response Model:** `ResponseWrapper<GetGeneralAssistantResponse>`

**Success Response (200/201):**
```json
{
  "status": 200,
  "message": null,
  "data": {
    "id": "uuid-string",
    "userId": "user-id",
    "name": "General Assistant",
    "assistantType": "general_assistant",
    "description": "A helpful general assistant for everyday tasks and conversations.",
    "systemPrompt": "You are a helpful, friendly, and knowledgeable general assistant.",
    "provider": "openai",
    "modelName": "gpt-3.5-turbo",
    "temperature": 0.7,
    "askHuman": false,
    "interrupt": false,
    "mainUnit": "chatbot",
    "supportUnits": ["ragbot", "searchbot"],
    "teams": [
      {
        "id": "team-id",
        "name": "Main Team",
        "workflowType": "chatbot"
      }
    ],
    "createdAt": "2024-01-01T00:00:00Z"
  }
}
```

### 3. Create Advanced Assistant

Create a new advanced assistant with custom configuration.

**Endpoint:** `POST /create`

**Request Body:** `CreateAdvancedAssistantRequest`

**Required Fields:**
- `name` (string, 3-100 chars): Assistant name
- `description` (string, 3-5000 chars): Assistant description
- `system_prompt` (string, 3-5000 chars): System prompt for the assistant

**Optional Fields:**
- `provider` (string, 3-50 chars): Model provider (e.g., "openai", "anthropic")
- `model_name` (string, 1-50 chars): Model name (e.g., "gpt-4", "claude-3")
- `temperature` (float, 0.0-2.0): Model temperature for randomness control
- `ask_human` (boolean): Whether to ask human for confirmation before execution
- `interrupt` (boolean): Whether to interrupt the assistant's current task
- `support_units` (array of `WorkflowType`): List of support units/teams
- `mcp_ids` (array of strings): List of MCP (Model Context Protocol) IDs
- `extension_ids` (array of strings): List of extension IDs

**Request Example:**
```json
{
  "name": "Research Assistant",
  "description": "An advanced assistant for research and analysis tasks",
  "systemPrompt": "You are a research assistant specialized in finding and analyzing information.",
  "provider": "openai",
  "modelName": "gpt-4",
  "temperature": 0.3,
  "askHuman": true,
  "interrupt": false,
  "supportUnits": ["ragbot", "searchbot"],
  "mcpIds": ["mcp-id-1", "mcp-id-2"],
  "extensionIds": ["ext-id-1"]
}
```

**Response Model:** `ResponseWrapper<CreateAdvancedAssistantResponse>`

**Success Response (201):**
```json
{
  "status": 201,
  "message": null,
  "data": {
    "id": "new-assistant-uuid",
    "userId": "user-id",
    "name": "Research Assistant",
    "assistantType": "advanced_assistant",
    "description": "An advanced assistant for research and analysis tasks",
    "systemPrompt": "You are a research assistant specialized in finding and analyzing information.",
    "provider": "openai",
    "modelName": "gpt-4",
    "temperature": 0.3,
    "askHuman": true,
    "interrupt": false,
    "mainUnit": "hierarchical",
    "supportUnits": ["ragbot", "searchbot"],
    "mcpIds": ["mcp-id-1", "mcp-id-2"],
    "extensionIds": ["ext-id-1"],
    "teams": [
      {
        "id": "main-team-id",
        "name": "Main Team",
        "workflowType": "hierarchical"
      },
      {
        "id": "ragbot-team-id",
        "name": "RAG Team",
        "workflowType": "ragbot"
      },
      {
        "id": "searchbot-team-id",
        "name": "Search Team",
        "workflowType": "searchbot"
      }
    ],
    "createdAt": "2024-01-01T00:00:00Z"
  }
}
```

### 4. Get Assistant Details

Retrieve detailed information about a specific assistant.

**Endpoint:** `GET /{assistant_id}/get-detail`

**Path Parameters:**
- `assistant_id` (string, required): The ID of the assistant to retrieve

**Response Model:** `ResponseWrapper<GetGeneralAssistantResponse | GetAdvancedAssistantResponse>`

**Success Response (200):**
```json
{
  "status": 200,
  "message": null,
  "data": {
    "id": "assistant-uuid",
    "userId": "user-id",
    "name": "My Assistant",
    "assistantType": "advanced_assistant",
    "description": "Assistant description",
    "systemPrompt": "System prompt",
    "provider": "openai",
    "modelName": "gpt-4",
    "temperature": 0.7,
    "askHuman": false,
    "interrupt": false,
    "mainUnit": "hierarchical",
    "supportUnits": ["ragbot"],
    "mcpIds": ["mcp-id"],
    "extensionIds": ["ext-id"],
    "teams": [
      {
        "id": "team-id",
        "name": "Team Name",
        "workflowType": "hierarchical"
      }
    ],
    "createdAt": "2024-01-01T00:00:00Z"
  }
}
```

**Error Response (404):**
```json
{
  "status": 404,
  "message": "Assistant not found",
  "data": null
}
```

### 5. Update Advanced Assistant

Update an existing advanced assistant's information.

**Endpoint:** `PATCH /{assistant_id}/update-advanced-assistant`

**Path Parameters:**
- `assistant_id` (string, required): The ID of the assistant to update

**Request Body:** `UpdateAdvancedAssistantRequest`

**Optional Fields (all fields are optional):**
- `name` (string, 3-100 chars): Assistant name
- `description` (string, 3-5000 chars): Assistant description
- `system_prompt` (string, 3-5000 chars): System prompt
- `provider` (string, 3-50 chars): Model provider
- `model_name` (string, 1-50 chars): Model name
- `temperature` (float, 0.0-2.0): Model temperature
- `ask_human` (boolean): Ask human confirmation setting
- `interrupt` (boolean): Interrupt setting
- `support_units` (array): List of support units
- `mcp_ids` (array): List of MCP IDs
- `extension_ids` (array): List of extension IDs

**Request Example:**
```json
{
  "name": "Updated Research Assistant",
  "temperature": 0.5,
  "supportUnits": ["ragbot", "searchbot"],
  "mcpIds": ["new-mcp-id"]
}
```

**Response Model:** `ResponseWrapper<UpdateAdvancedAssistantResponse>`

**Success Response (200):**
```json
{
  "status": 200,
  "message": null,
  "data": {
    "id": "assistant-uuid",
    "userId": "user-id",
    "name": "Updated Research Assistant",
    "assistantType": "advanced_assistant",
    "description": "Updated description",
    "systemPrompt": "Updated system prompt",
    "provider": "openai",
    "modelName": "gpt-4",
    "temperature": 0.5,
    "askHuman": true,
    "interrupt": false,
    "mainUnit": "hierarchical",
    "supportUnits": ["ragbot", "searchbot"],
    "mcpIds": ["new-mcp-id"],
    "extensionIds": ["ext-id"],
    "teams": [
      {
        "id": "team-id",
        "name": "Team Name",
        "workflowType": "hierarchical"
      }
    ],
    "createdAt": "2024-01-01T00:00:00Z"
  }
}
```

### 6. Update Assistant Configuration

Update only the configuration settings of an assistant without affecting connected services.

**Endpoint:** `PATCH /{assistant_id}/update-config`

**Path Parameters:**
- `assistant_id` (string, required): The ID of the assistant to update

**Request Body:** `UpdateAssistantConfigRequest`

**Optional Fields:**
- `system_prompt` (string, 3-500 chars): System prompt
- `provider` (string, 3-50 chars): Model provider
- `model_name` (string, 1-50 chars): Model name
- `temperature` (float, 0.0-2.0): Model temperature
- `ask_human` (boolean): Ask human confirmation setting
- `interrupt` (boolean): Interrupt setting

**Request Example:**
```json
{
  "systemPrompt": "Updated system prompt for better performance",
  "temperature": 0.8,
  "askHuman": false
}
```

**Response Model:** `ResponseWrapper<MessageResponse>`

**Success Response (200):**
```json
{
  "status": 200,
  "message": null,
  "data": {
    "message": "Assistant configuration updated successfully"
  }
}
```

### 7. Soft Delete Assistant

Soft delete an advanced assistant (mark as deleted but keep in database).

**Endpoint:** `DELETE /{assistant_id}/soft-delete-advanced-assistant`

**Path Parameters:**
- `assistant_id` (string, required): The ID of the assistant to soft delete

**Response Model:** `ResponseWrapper<MessageResponse>`

**Success Response (200):**
```json
{
  "status": 200,
  "message": null,
  "data": {
    "message": "Assistant soft deleted successfully"
  }
}
```

### 8. Hard Delete Assistant

Permanently delete an advanced assistant and all related data.

**Endpoint:** `DELETE /{user_id}/{assistant_id}/hard-delete-advanced-assistant`

**Path Parameters:**
- `user_id` (string, required): The user ID (must match authenticated user)
- `assistant_id` (string, required): The ID of the assistant to delete

**Response Model:** `ResponseWrapper<MessageResponse>`

**Success Response (200):**
```json
{
  "status": 200,
  "message": null,
  "data": {
    "message": "Assistant deleted successfully"
  }
}
```

**Error Response (404):**
```json
{
  "status": 404,
  "message": "Assistant not found",
  "data": null
}
```

## Data Models

### AssistantType Enum
- `general_assistant`: Simple, pre-configured assistant
- `advanced_assistant`: Customizable assistant with multiple capabilities

### WorkflowType Enum
- `chatbot`: Basic conversational assistant
- `ragbot`: Retrieval-Augmented Generation assistant
- `searchbot`: Web search assistant
- `sequential`: Sequential workflow processing
- `hierarchical`: Hierarchical team-based processing
- `workflow`: Custom workflow processing

### Team Object
```json
{
  "id": "string",
  "name": "string",
  "workflowType": "WorkflowType"
}
```

## Common Use Cases

### Creating a Simple Research Assistant
```json
{
  "name": "Research Helper",
  "description": "Helps with research tasks and information gathering",
  "systemPrompt": "You are a research assistant. Help users find and analyze information.",
  "provider": "openai",
  "modelName": "gpt-4",
  "temperature": 0.3,
  "supportUnits": ["ragbot", "searchbot"]
}
```

### Creating an Assistant with Extensions
```json
{
  "name": "Productivity Assistant",
  "description": "Assists with productivity tasks using various tools",
  "systemPrompt": "You are a productivity assistant with access to various tools.",
  "provider": "anthropic",
  "modelName": "claude-3-sonnet",
  "temperature": 0.5,
  "askHuman": true,
  "supportUnits": ["ragbot"],
  "extensionIds": ["calendar-ext", "email-ext"]
}
```

### Updating Assistant Configuration Only
```json
{
  "systemPrompt": "Updated prompt for better performance",
  "temperature": 0.7,
  "askHuman": false
}
```

## Rate Limiting

Currently, there are no specific rate limits documented for the Assistant API. However, it's recommended to implement reasonable request rates to avoid overwhelming the server.

## Security Considerations

1. **Authentication Required**: All endpoints require valid user authentication headers
2. **User Isolation**: Users can only access and modify their own assistants
3. **Input Validation**: All inputs are validated according to the defined schemas
4. **Soft Delete**: Important data can be recovered using soft delete functionality

## Troubleshooting

### Common Issues

1. **Missing Authentication Headers**: Ensure `x-user-id` header is included in all requests
2. **Validation Errors**: Check that all required fields are provided and within valid ranges
3. **Assistant Not Found**: Verify the assistant ID and ensure it belongs to the authenticated user
4. **Invalid Enum Values**: Use correct enum values for `assistant_type` and `workflow_type` fields

### Debug Tips

1. Check the response `status` and `message` fields for error details
2. Validate request payload against the schema requirements
3. Ensure proper Content-Type headers for POST/PATCH requests (`application/json`)
4. Verify that referenced MCP and extension IDs exist and belong to the user
