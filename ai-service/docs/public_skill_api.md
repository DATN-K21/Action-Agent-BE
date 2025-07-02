# Public Skill API

This documentation provides comprehensive details about the Skill API endpoints available in the AI Service. The Skill API enables management of skills within the system, including creating, retrieving, updating, and deleting skills that can be associated with team members.

## Overview

The Skill API enables you to:

- Create new skills with specific tool definitions and configurations
- Retrieve individual skills or lists of skills
- Update skill information and tool definitions
- Delete skills from the system
- Validate tool definitions before saving them
- Update skill credentials securely
- Invoke tools directly through the API
- Manage skills associated with Model Context Protocol (MCP) services and extensions

Skills represent capabilities that can be assigned to team members, enabling them to perform specific actions or access particular resources.

## Base Models

### SkillBase

Core skill information structure:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Unique skill name |
| `description` | string | No | Brief description of the skill (optional) |
| `icon` | string | No | Icon image reference for the skill (optional) |
| `strategy` | string | No | Storage strategy for the skill (e.g., "definition", "file", "global_tools", "personal_tool_cache") |
| `display_name` | string | No | Human-readable display name for the skill |
| `tool_definition` | object | Yes | The tool definition object that defines the skill's functionality |
| `input_parameters` | object | Yes | Parameters defining expected inputs for the skill |
| `credentials` | object | No | Credentials for accessing external services (stored securely) |
| `reference_type` | string | Yes | Type of connected service: "none", "extension", "mcp" |
| `extension_id` | string | No | The ID of the associated extension (if applicable) |
| `mcp_id` | string | No | The ID of the associated MCP service (if applicable) |

### CreateSkillRequest

Request structure for creating a new skill - inherits all fields from SkillBase.

### SkillUpdateRequest

Request structure for updating a skill:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | No | Updated skill name |
| `description` | string | No | Updated description |
| `managed` | boolean | No | Updated managed status |
| `display_name` | string | No | Updated display name |
| `tool_definition` | object | No | Updated tool definition object |
| `input_schema` | object | No | Updated input schema |
| `credentials` | object | No | Updated credentials |
| `reference_type` | string | No | Updated reference type |
| `extension_id` | string | No | Updated extension ID |
| `mcp_id` | string | No | Updated MCP service ID |

### ValidateToolDefinitionRequest

Request structure for validating a tool definition:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `tool_definition` | object | Yes | The tool definition object to validate |

### SkillResponse

Response structure for skill data:

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique skill identifier |
| All SkillBase fields | - | All base skill information |

### SkillsResponse

Response structure for multiple skills:

| Field | Type | Description |
|-------|------|-------------|
| `skills` | SkillResponse[] | Array of skill objects |
| `count` | integer | Total number of skills |

## Endpoints

### Get All Skills

Retrieves all skills accessible to the current user.

**Endpoint:** `GET /skill/`

**Query Parameters:**
- `skip` (optional): Number of records to skip (default: 0)
- `limit` (optional): Maximum number of records to return (default: 100)

**Headers:**
- `x-user-id` (required): User identifier
- `x-user-role` (required): User role ("admin", "super admin", or other role)

**Response:**

```json
{
  "status": 200,
  "message": "Success",
  "data": {
    "skills": [
      {
        "id": "6f8b2e4a-c5d1-49e3-93a7-2f8de72cb4e2",
        "name": "web_search",
        "description": "Search the web for information",
        "icon": "search_icon",
        "strategy": "definition",
        "display_name": "Web Search",
        "tool_definition": {
          "name": "web_search",
          "description": "Search the web for up-to-date information on any topic",
          "parameters": {
            "type": "object",
            "properties": {
              "query": {"type": "string", "description": "The search query"}
            },
            "required": ["query"]
          }
        },
        "input_parameters": {
          "query": {"type": "string", "description": "The search query"}
        },
        "credentials": {},
        "reference_type": "none",
        "extension_id": null,
        "mcp_id": null,
        "created_at": "2025-07-01T09:00:00Z",
        "updated_at": "2025-07-01T09:00:00Z"
      }
    ],
    "count": 1
  }
}
```

### Get Skill by ID

Retrieves a specific skill by its ID.

**Endpoint:** `GET /skill/{skill_id}`

**Path Parameters:**
- `skill_id` (required): The ID of the skill to retrieve

**Headers:**
- `x-user-id` (required): User identifier
- `x-user-role` (required): User role

**Response:**

```json
{
  "status": 200,
  "message": "Success",
  "data": {
    "id": "6f8b2e4a-c5d1-49e3-93a7-2f8de72cb4e2",
    "name": "data_analysis",
    "description": "Analyze datasets and generate insights",
    "icon": "chart_icon",
    "strategy": "definition",
    "display_name": "Data Analysis",
    "tool_definition": {
      "name": "analyze_data",
      "description": "Analyze data and generate insights",
      "parameters": {
        "type": "object",
        "properties": {
          "dataset_url": {"type": "string", "description": "URL to the dataset"},
          "analysis_type": {"type": "string", "description": "Type of analysis to perform"}
        },
        "required": ["dataset_url", "analysis_type"]
      }
    },
    "input_parameters": {
      "dataset_url": {"type": "string"},
      "analysis_type": {"type": "string"}
    },
    "credentials": {},
    "reference_type": "none",
    "extension_id": null,
    "mcp_id": null,
    "created_at": "2025-07-01T10:15:00Z",
    "updated_at": "2025-07-01T10:15:00Z"
  }
}
```

### Create Skill

Creates a new skill in the system.

**Endpoint:** `POST /skill/`

**Headers:**
- `x-user-id` (required): User identifier
- `x-user-role` (required): User role

**Request Body:**

```json
{
  "name": "content_generation",
  "description": "Generate high-quality content for various purposes",
  "icon": "document_icon",
  "strategy": "definition",
  "display_name": "Content Generation",
  "tool_definition": {
    "name": "generate_content",
    "description": "Generate content based on given parameters",
    "parameters": {
      "type": "object",
      "properties": {
        "topic": {"type": "string", "description": "Content topic"},
        "length": {"type": "string", "enum": ["short", "medium", "long"], "description": "Content length"},
        "style": {"type": "string", "description": "Writing style"}
      },
      "required": ["topic", "length"]
    }
  },
  "input_parameters": {
    "topic": {"type": "string"},
    "length": {"type": "string"},
    "style": {"type": "string"}
  },
  "reference_type": "none"
}
```

**Response:**

```json
{
  "status": 200,
  "message": "Success",
  "data": {
    "id": "7d9c3f5b-a6e2-48f4-91b8-3e9dc83a5fd3",
    "name": "content_generation",
    "description": "Generate high-quality content for various purposes",
    "icon": "document_icon",
    "strategy": "definition",
    "display_name": "Content Generation",
    "tool_definition": {
      "name": "generate_content",
      "description": "Generate content based on given parameters",
      "parameters": {
        "type": "object",
        "properties": {
          "topic": {"type": "string", "description": "Content topic"},
          "length": {"type": "string", "enum": ["short", "medium", "long"], "description": "Content length"},
          "style": {"type": "string", "description": "Writing style"}
        },
        "required": ["topic", "length"]
      }
    },
    "input_parameters": {
      "topic": {"type": "string"},
      "length": {"type": "string"},
      "style": {"type": "string"}
    },
    "credentials": {},
    "reference_type": "none",
    "extension_id": null,
    "mcp_id": null,
    "created_at": "2025-07-02T14:30:00Z",
    "updated_at": "2025-07-02T14:30:00Z"
  }
}
```

### Update Skill

Updates an existing skill's information.

**Endpoint:** `PATCH /skill/{skill_id}`

**Path Parameters:**
- `skill_id` (required): The ID of the skill to update

**Headers:**
- `x-user-id` (required): User identifier
- `x-user-role` (required): User role

**Request Body:**

```json
{
  "description": "Generate high-quality content for blogs, articles, and marketing materials",
  "display_name": "Advanced Content Generator",
  "tool_definition": {
    "name": "generate_content",
    "description": "Generate professional content based on given parameters",
    "parameters": {
      "type": "object",
      "properties": {
        "topic": {"type": "string", "description": "Content topic"},
        "length": {"type": "string", "enum": ["short", "medium", "long"], "description": "Content length"},
        "style": {"type": "string", "description": "Writing style"},
        "target_audience": {"type": "string", "description": "Target audience for the content"}
      },
      "required": ["topic", "length", "target_audience"]
    }
  }
}
```

**Response:**

```json
{
  "status": 200,
  "message": "Success",
  "data": {
    "id": "7d9c3f5b-a6e2-48f4-91b8-3e9dc83a5fd3",
    "name": "content_generation",
    "description": "Generate high-quality content for blogs, articles, and marketing materials",
    "icon": "document_icon",
    "strategy": "definition",
    "display_name": "Advanced Content Generator",
    "tool_definition": {
      "name": "generate_content",
      "description": "Generate professional content based on given parameters",
      "parameters": {
        "type": "object",
        "properties": {
          "topic": {"type": "string", "description": "Content topic"},
          "length": {"type": "string", "enum": ["short", "medium", "long"], "description": "Content length"},
          "style": {"type": "string", "description": "Writing style"},
          "target_audience": {"type": "string", "description": "Target audience for the content"}
        },
        "required": ["topic", "length", "target_audience"]
      }
    },
    "input_parameters": {
      "topic": {"type": "string"},
      "length": {"type": "string"},
      "style": {"type": "string"},
      "target_audience": {"type": "string"}
    },
    "credentials": {},
    "reference_type": "none",
    "extension_id": null,
    "mcp_id": null,
    "created_at": "2025-07-02T14:30:00Z",
    "updated_at": "2025-07-02T15:45:00Z"
  }
}
```

### Delete Skill

Soft deletes a skill from the system (marks as deleted rather than permanently removing).

**Endpoint:** `DELETE /skill/{skill_id}`

**Path Parameters:**
- `skill_id` (required): The ID of the skill to delete

**Headers:**
- `x-user-id` (required): User identifier
- `x-user-role` (required): User role

**Response:**

```json
{
  "status": 200,
  "message": "Success",
  "data": {
    "message": "Skill deleted successfully"
  }
}
```

### Validate Tool Definition

Validates a tool definition schema without creating a skill.

**Endpoint:** `POST /skill/validate`

**Request Body:**

```json
{
  "tool_definition": {
    "name": "email_analyzer",
    "description": "Analyze email content for sentiment and key information",
    "parameters": {
      "type": "object",
      "properties": {
        "email_text": {"type": "string", "description": "The full email text to analyze"},
        "analysis_depth": {"type": "string", "enum": ["basic", "detailed"], "description": "Level of analysis to perform"}
      },
      "required": ["email_text"]
    }
  }
}
```

**Response:**
Returns the validated tool definition object if valid, or error details if invalid.

### Invoke Tool

Invokes a tool by name with the provided arguments.

**Endpoint:** `POST /skill/invoke-tool`

**Query Parameters:**
- `tool_name` (required): The name of the tool to invoke
- `args` (required): The arguments to pass to the tool

**Response:**
Returns the result of the tool invocation.

### Update Skill Credentials

Updates a skill's credentials for accessing external services.

**Endpoint:** `POST /skill/update-credentials/{skill_id}`

**Path Parameters:**
- `skill_id` (required): The ID of the skill to update credentials for

**Headers:**
- `x-user-id` (required): User identifier
- `x-user-role` (required): User role

**Request Body:**

```json
{
  "api_key": {
    "value": "sk_1234567890abcdef",
    "description": "API key for accessing the service"
  },
  "endpoint": {
    "value": "https://api.example.com/v1",
    "description": "API endpoint URL"
  }
}
```

**Response:**

```json
{
  "status": 200,
  "message": "Success",
  "data": {
    "id": "7d9c3f5b-a6e2-48f4-91b8-3e9dc83a5fd3",
    "name": "content_generation",
    "description": "Generate high-quality content for blogs, articles, and marketing materials",
    "icon": "document_icon",
    "strategy": "definition",
    "display_name": "Advanced Content Generator",
    "tool_definition": {
      "name": "generate_content",
      "description": "Generate professional content based on given parameters",
      "parameters": {
        "type": "object",
        "properties": {
          "topic": {"type": "string", "description": "Content topic"},
          "length": {"type": "string", "enum": ["short", "medium", "long"], "description": "Content length"},
          "style": {"type": "string", "description": "Writing style"},
          "target_audience": {"type": "string", "description": "Target audience for the content"}
        },
        "required": ["topic", "length", "target_audience"]
      }
    },
    "input_parameters": {
      "topic": {"type": "string"},
      "length": {"type": "string"},
      "style": {"type": "string"},
      "target_audience": {"type": "string"}
    },
    "credentials": {
      "api_key": {
        "value": "[PROTECTED]",
        "description": "API key for accessing the service"
      },
      "endpoint": {
        "value": "https://api.example.com/v1",
        "description": "API endpoint URL"
      }
    },
    "reference_type": "none",
    "extension_id": null,
    "mcp_id": null,
    "created_at": "2025-07-02T14:30:00Z",
    "updated_at": "2025-07-02T16:20:00Z"
  }
}
```

## Error Handling

All endpoints use standard HTTP status codes and return consistent error responses:

| Status Code | Description |
|-------------|-------------|
| 200 | Success |
| 400 | Bad Request (validation errors, incorrect formats) |
| 403 | Forbidden (insufficient permissions) |
| 404 | Not Found (skill not found) |
| 500 | Internal Server Error |

**Error Response Format:**

```json
{
  "status": 400,
  "message": "Invalid tool definition",
  "data": null
}
```

**Common Error Scenarios:**

1. **Invalid Tool Definition:**
```json
{
  "status": 400,
  "message": "Field 'parameters.properties.query': missing required field"
}
```

2. **Skill Not Found:**
```json
{
  "status": 404,
  "message": "Skill not found"
}
```

3. **Insufficient Permissions:**
```json
{
  "status": 403,
  "message": "Not enough permissions"
}
```

4. **Global Tool Deletion Attempt:**
```json
{
  "status": 400,
  "message": "Cannot delete global tools"
}
```

## Validation Rules

### Tool Definition Validation
- Must include required fields: `name`, `description`, and `parameters`
- Parameters must follow JSON Schema format
- Required parameters must be specified correctly
- Property types must be valid according to JSON Schema

### Name Validation
- Must be unique within the user's skills
- Special characters may be restricted

### Storage Strategy
- Determines how the skill is stored and accessed
- Valid values: `definition`, `file`, `global_tools`, `personal_tool_cache`

### Reference Type
- Indicates the skill's connection to external services
- Valid values: `none`, `extension`, `mcp`

## Examples

### Complete Skill Management Workflow

**1. Create a Web Search Skill:**

```bash
curl -X POST "https://your-api-domain/skill/" \
  -H "Content-Type: application/json" \
  -H "x-user-id: user_123" \
  -H "x-user-role: admin" \
  -d '{
    "name": "web_search",
    "description": "Search the web for information",
    "icon": "search_icon",
    "strategy": "definition",
    "display_name": "Web Search",
    "tool_definition": {
      "name": "web_search",
      "description": "Search the web for up-to-date information on any topic",
      "parameters": {
        "type": "object",
        "properties": {
          "query": {"type": "string", "description": "The search query"}
        },
        "required": ["query"]
      }
    },
    "input_parameters": {
      "query": {"type": "string", "description": "The search query"}
    },
    "reference_type": "none"
  }'
```

**2. Validate a Tool Definition First:**

```bash
curl -X POST "https://your-api-domain/skill/validate" \
  -H "Content-Type: application/json" \
  -d '{
    "tool_definition": {
      "name": "image_generator",
      "description": "Generate images based on text descriptions",
      "parameters": {
        "type": "object",
        "properties": {
          "prompt": {"type": "string", "description": "Text description of the image to generate"},
          "style": {"type": "string", "description": "Art style for the image"}
        },
        "required": ["prompt"]
      }
    }
  }'
```

**3. Create the Validated Skill:**

```bash
curl -X POST "https://your-api-domain/skill/" \
  -H "Content-Type: application/json" \
  -H "x-user-id: user_123" \
  -H "x-user-role: admin" \
  -d '{
    "name": "image_generator",
    "description": "Generate images based on text descriptions",
    "strategy": "definition",
    "display_name": "Image Generator",
    "tool_definition": {
      "name": "image_generator",
      "description": "Generate images based on text descriptions",
      "parameters": {
        "type": "object",
        "properties": {
          "prompt": {"type": "string", "description": "Text description of the image to generate"},
          "style": {"type": "string", "description": "Art style for the image"}
        },
        "required": ["prompt"]
      }
    },
    "input_parameters": {
      "prompt": {"type": "string", "description": "Text description of the image to generate"},
      "style": {"type": "string", "description": "Art style for the image"}
    },
    "reference_type": "none"
  }'
```

**4. Update the Skill with Credentials:**

```bash
curl -X POST "https://your-api-domain/skill/update-credentials/5e9a2d7c-b8f3-47e6-82a1-4f6d8c93e5d2" \
  -H "Content-Type: application/json" \
  -H "x-user-id: user_123" \
  -H "x-user-role: admin" \
  -d '{
    "api_key": {
      "value": "sk_1234567890abcdef",
      "description": "API key for the image generation service"
    },
    "organization_id": {
      "value": "org_9876543210",
      "description": "Organization ID for the service"
    }
  }'
```

**5. Invoke the Tool:**

```bash
curl -X POST "https://your-api-domain/skill/invoke-tool?tool_name=image_generator" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "A futuristic city with flying cars and neon lights",
    "style": "cyberpunk"
  }'
```

**6. Delete the Skill:**

```bash
curl -X DELETE "https://your-api-domain/skill/5e9a2d7c-b8f3-47e6-82a1-4f6d8c93e5d2" \
  -H "x-user-id: user_123" \
  -H "x-user-role: admin"
```

### Skill Types and Use Cases

**API Tool Skill:**

```json
{
  "name": "weather_info",
  "description": "Get current weather information for a location",
  "strategy": "definition",
  "display_name": "Weather Information",
  "tool_definition": {
    "name": "get_weather",
    "description": "Get current weather information for a specific location",
    "parameters": {
      "type": "object",
      "properties": {
        "location": {"type": "string", "description": "City name or geographic coordinates"},
        "units": {"type": "string", "enum": ["metric", "imperial"], "description": "Unit system to use for results"}
      },
      "required": ["location"]
    }
  }
}
```

**MCP-Connected Skill:**

```json
{
  "name": "data_processing",
  "description": "Process data through the MCP service",
  "strategy": "personal_tool_cache",
  "display_name": "Data Processing",
  "reference_type": "mcp",
  "mcp_id": "mcp_abc123",
  "tool_definition": {
    "name": "process_data",
    "description": "Process data through the MCP service",
    "parameters": {
      "type": "object",
      "properties": {
        "data_url": {"type": "string", "description": "URL to the data to process"},
        "processing_type": {"type": "string", "description": "Type of processing to perform"}
      },
      "required": ["data_url", "processing_type"]
    }
  }
}
```

**Extension-Connected Skill:**

```json
{
  "name": "document_analysis",
  "description": "Analyze documents using the Document Analysis Extension",
  "strategy": "personal_tool_cache",
  "display_name": "Document Analysis",
  "reference_type": "extension",
  "extension_id": "ext_def456",
  "tool_definition": {
    "name": "analyze_document",
    "description": "Extract information and insights from documents",
    "parameters": {
      "type": "object",
      "properties": {
        "document_url": {"type": "string", "description": "URL to the document to analyze"},
        "analysis_types": {"type": "array", "items": {"type": "string"}, "description": "Types of analysis to perform"}
      },
      "required": ["document_url"]
    }
  }
}
```

### Managing Skill Credentials

**Updating API Credentials:**

```javascript
// Update credentials for a weather API skill
await fetch('/skill/update-credentials/6f8b2e4a-c5d1-49e3-93a7-2f8de72cb4e2', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'x-user-id': 'user_123',
    'x-user-role': 'admin'
  },
  body: JSON.stringify({
    'api_key': {
      'value': 'weather_api_key_12345',
      'description': 'API key for accessing the weather service'
    },
    'base_url': {
      'value': 'https://api.weather-service.com/v2/',
      'description': 'Base URL for the weather API'
    }
  })
});
```

**Credential Security:**

Credentials are:
- Stored securely in the database
- Never exposed in full through API responses
- Protected with access controls
- Properly validated before storage

## Advanced Features

### Tool Definition Validation

The system validates tool definitions according to JSON Schema standards:

```json
{
  "name": "tool_name",
  "description": "Tool description",
  "parameters": {
    "type": "object",
    "properties": {
      "param1": {"type": "string", "description": "Description of param1"},
      "param2": {"type": "number", "description": "Description of param2"}
    },
    "required": ["param1"]
  }
}
```

Key validation checks:
- Required fields presence
- Parameter types correctness
- Schema structure validity
- Description completeness

### Tool Invocation

The API allows direct invocation of tools, which is useful for:
- Testing tool functionality
- Debugging tool issues
- Demonstrating capabilities
- Creating automated workflows

### Storage Strategies

Different strategies for how skills are stored and accessed:

| Strategy | Description |
|----------|-------------|
| `definition` | Skill definition is stored directly in the database |
| `file` | Skill functionality is defined by a file in the system |
| `global_tools` | System-provided tools available to all users |
| `personal_tool_cache` | User-specific tools with cached functionality |

## Performance Considerations

1. **Pagination**: Use `skip` and `limit` parameters when retrieving multiple skills
2. **Validation**: Validate tool definitions before creating or updating skills
3. **Credentials Management**: Update credentials in separate requests to minimize payload size
4. **Tool Invocation**: Be aware of rate limits when invoking tools directly
5. **Query Optimization**: Filter skills efficiently to improve performance

## Security Notes

1. **Access Control**: All operations verify user permissions
2. **Credential Protection**: Sensitive credentials are stored securely and not exposed in responses
3. **Validation**: Tool definitions are validated to prevent injection attacks
4. **Soft Deletion**: Skills are marked as deleted rather than permanently removed
5. **Permission Checks**: Non-admin users can only access their own skills or global tools

## Integration Patterns

### Skill Management Dashboard

```javascript
class SkillManager {
  constructor(apiClient) {
    this.api = apiClient;
  }
  
  async loadUserSkills() {
    const response = await this.api.get('/skill/');
    return response.data.skills;
  }
  
  async createSkill(skillData) {
    // Validate first
    await this.api.post('/skill/validate', {
      tool_definition: skillData.tool_definition
    });
    
    // Then create
    return await this.api.post('/skill/', skillData);
  }
  
  async updateSkillCredentials(skillId, credentials) {
    return await this.api.post(`/skill/update-credentials/${skillId}`, credentials);
  }
  
  async testSkill(skillId, args) {
    const skill = await this.api.get(`/skill/${skillId}`);
    return await this.api.post(`/skill/invoke-tool?tool_name=${skill.data.name}`, args);
  }
}
```

### Member-Skill Assignment

```javascript
async function assignSkillsToMember(memberId, skillIds) {
  // First, get the member
  const memberResponse = await fetch(`/member/${memberId}?assistant_id=team_123`, {
    headers: {
      'x-user-id': 'user_456',
      'x-user-role': 'admin'
    }
  });
  const member = await memberResponse.json();
  
  // Then, get the skills
  const skills = await Promise.all(skillIds.map(async (skillId) => {
    const skillResponse = await fetch(`/skill/${skillId}`, {
      headers: {
        'x-user-id': 'user_456',
        'x-user-role': 'admin'
      }
    });
    return (await skillResponse.json()).data;
  }));
  
  // Update the member with the skills
  return await fetch(`/member/${memberId}?assistant_id=team_123`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
      'x-user-id': 'user_456',
      'x-user-role': 'admin'
    },
    body: JSON.stringify({
      skills: skills
    })
  });
}
```

## Troubleshooting

### Common Issues

1. **Invalid Tool Definition**: Ensure all required fields are present and correctly formatted
   ```
   Error: Field 'parameters.properties.query': missing required field
   ```

2. **Permissions Error**: Verify the user has appropriate roles for the operation
   ```
   Error: Not enough permissions
   ```

3. **Global Tool Deletion**: Global tools cannot be deleted
   ```
   Error: Cannot delete global tools
   ```

4. **Skill Not Found**: The skill may have been deleted or does not exist
   ```
   Error: Skill not found
   ```

5. **Invalid Credentials Format**: Credentials must follow the correct format
   ```
   Error: Invalid credentials format
   ```

### Debug Checklist

1. **Check Request Format**: Ensure all required fields are provided
2. **Verify Permissions**: Confirm the user has necessary access rights
3. **Validate Tool Definition**: Pre-validate complex tool definitions
4. **Check Credentials**: Verify credentials format and completeness
5. **Review Error Messages**: Error responses contain specific details about issues

This comprehensive API documentation provides developers with all the information needed to effectively work with the Skill API endpoints.
