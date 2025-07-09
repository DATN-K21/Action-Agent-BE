# Public Connected MCP API

This documentation provides details about the Connected Model Context Protocol (MCP) API endpoints available in the AI Service. The Connected MCP API allows you to manage connections to external MCP servers that provide AI tools and capabilities.

## Overview

The Connected MCP API enables you to:

- Create new MCP server connections
- Retrieve a list of all connected MCP servers for a user
- Get detailed information about a specific connected MCP
- Update existing MCP server connections
- Delete MCP server connections
- Retrieve tool information from connected MCP servers

Connected MCPs represent integrations between the AI Service and external Model Context Protocol servers. These connections allow the AI Service to discover and use AI tools provided by external services through standardized MCP interfaces.

## Connected MCP Object

The Connected MCP object represents a connection between a user account and an external MCP server:

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | The unique identifier of the connected MCP |
| `user_id` | string | The ID of the user who owns this connection |
| `mcp_name` | string | The human-readable name of the MCP server |
| `url` | string | The URL endpoint of the MCP server |
| `transport` | string | The transport protocol used for communication (SSE, WEBSOCKET, or STREAMABLE_HTTP) |
| `description` | string | Optional description of the MCP server and its purpose |
| `created_at` | string | The timestamp when the connection was created (ISO format) |

## Transport Types

The transport protocol can be one of three values:

- `sse` - Server-Sent Events protocol
- `websocket` - WebSocket protocol
- `streamable_http` - HTTP protocol with streaming capabilities (default)

## Endpoints

### List Connected MCPs

Retrieves all connected MCPs for the authenticated user with pagination support.

**Endpoint:** `GET /mcp/get-all`

**Headers:**
- `x-user-id` (required): The ID of the authenticated user
- `x-user-role` (required): The role of the authenticated user (e.g., "user", "admin", "super_admin")

**Query Parameters:**
- `page_number` (optional): The page number for pagination (default: 1)
- `max_per_page` (optional): Maximum number of items per page (default: 10)

**Permissions:**
- Users can only see their own connected MCPs
- Admins and super admins can see all connected MCPs in the system

**Response:**

```json
{
  "status": 200,
  "message": "",
  "data": {
    "connected_mcps": [
      {
        "id": "cm_1a2b3c4d5e6f7g8h",
        "user_id": "user_8h7g6f5e4d3c2b1a",
        "mcp_name": "AI Tool Provider",
        "url": "https://mcp-server.example.com/api",
        "transport": "streamable_http",
        "description": "External AI tool provider with image analysis capabilities",
        "created_at": "2025-06-15T09:30:00.000Z"
      },
      {
        "id": "cm_2b3c4d5e6f7g8h9i",
        "user_id": "user_8h7g6f5e4d3c2b1a",
        "mcp_name": "Data Processing Tools",
        "url": "https://data-tools.example.org/mcp",
        "transport": "websocket",
        "description": "Data processing and analysis tools",
        "created_at": "2025-06-14T14:20:00.000Z"
      }
    ],
    "page_number": 1,
    "max_per_page": 10,
    "total_page": 1
  }
}
```

### Get Connected MCP Details

Retrieves detailed information about a specific connected MCP.

**Endpoint:** `GET /mcp/{connected_mcp_id}/get-detail`

**Path Parameters:**
- `connected_mcp_id` (required): The ID of the connected MCP to retrieve

**Headers:**
- `x-user-id` (required): The ID of the authenticated user
- `x-user-role` (required): The role of the authenticated user (e.g., "user", "admin", "super_admin")

**Permissions:**
- Users can only see details of their own connected MCPs
- Admins and super admins can see details of any connected MCP in the system

**Response:**

```json
{
  "status": 200,
  "message": "",
  "data": {
    "id": "cm_1a2b3c4d5e6f7g8h",
    "user_id": "user_8h7g6f5e4d3c2b1a",
    "mcp_name": "AI Tool Provider",
    "url": "https://mcp-server.example.com/api",
    "transport": "streamable_http",
    "description": "External AI tool provider with image analysis capabilities",
    "created_at": "2025-06-15T09:30:00.000Z"
  }
}
```

### Create Connected MCP

Creates a new connection to an MCP server.

**Endpoint:** `POST /mcp/create`

**Headers:**
- `x-user-id` (required): The ID of the authenticated user
- `x-user-role` (required): The role of the authenticated user (e.g., "user", "admin", "super_admin")

**Request Body:**
```json
{
  "mcp_name": "Document Analysis Tools",
  "url": "https://doc-analysis.example.com/mcp-api",
  "transport": "streamable_http",
  "description": "Document analysis and processing tools"
}
```

**Fields:**
- `mcp_name` (required): Name of the MCP server (3-50 characters)
- `url` (required): URL endpoint of the MCP server (3-200 characters)
- `transport` (optional): Transport protocol (default: "streamable_http")
- `description` (optional): Description of the MCP server (3-1000 characters)

**Response:**

```json
{
  "status": 200,
  "message": "",
  "data": {
    "id": "cm_3c4d5e6f7g8h9i0j",
    "user_id": "user_8h7g6f5e4d3c2b1a",
    "mcp_name": "Document Analysis Tools",
    "url": "https://doc-analysis.example.com/mcp-api",
    "transport": "streamable_http",
    "description": "Document analysis and processing tools",
    "created_at": "2025-07-02T10:15:00.000Z"
  }
}
```

### Update Connected MCP

Updates an existing MCP server connection.

**Endpoint:** `PATCH /mcp/{connected_mcp_id}/update`

**Path Parameters:**
- `connected_mcp_id` (required): The ID of the connected MCP to update

**Headers:**
- `x-user-id` (required): The ID of the authenticated user
- `x-user-role` (required): The role of the authenticated user (e.g., "user", "admin", "super_admin")

**Request Body:**
```json
{
  "mcp_name": "Updated Document Analysis Tools",
  "url": "https://new-endpoint.example.com/mcp-api",
  "transport": "websocket",
  "description": "Updated document analysis and processing tools"
}
```

**Fields:**
- All fields are optional. Only include the fields you want to update.

**Permissions:**
- Users can only update their own connected MCPs
- Admins and super admins can update any connected MCP in the system

**Response:**

```json
{
  "status": 200,
  "message": "",
  "data": {
    "id": "cm_3c4d5e6f7g8h9i0j",
    "user_id": "user_8h7g6f5e4d3c2b1a",
    "mcp_name": "Updated Document Analysis Tools",
    "url": "https://new-endpoint.example.com/mcp-api",
    "transport": "websocket",
    "description": "Updated document analysis and processing tools",
    "created_at": "2025-07-02T10:15:00.000Z"
  }
}
```

### Delete Connected MCP

Deletes a connected MCP (marks it as deleted in the database).

**Endpoint:** `DELETE /mcp/{connected_mcp_id}/delete`

**Path Parameters:**
- `connected_mcp_id` (required): The ID of the connected MCP to delete

**Headers:**
- `x-user-id` (required): The ID of the authenticated user
- `x-user-role` (required): The role of the authenticated user (e.g., "user", "admin", "super_admin")

**Permissions:**
- Users can only delete their own connected MCPs
- Admins and super admins can delete any connected MCP in the system

**Response:**

```json
{
  "status": 200,
  "message": "",
  "data": {
    "message": "Connected MCP deleted successfully"
  }
}
```

### Get Tool Infos

Retrieves information about the AI tools available from a specific connected MCP.

**Endpoint:** `GET /mcp/{connected_mcp_id}/tool-infos`

**Path Parameters:**
- `connected_mcp_id` (required): The ID of the connected MCP to retrieve tools from

**Headers:**
- `x-user-id` (required): The ID of the authenticated user
- `x-user-role` (required): The role of the authenticated user (e.g., "user", "admin", "super_admin")

**Permissions:**
- Users can only retrieve tool information from their own connected MCPs
- Admins and super admins can retrieve tool information from any connected MCP in the system

**Response:**

```json
{
  "status": 200,
  "message": "",
  "data": {
    "tool_infos": [
      {
        "description": "Analyzes an image and provides a detailed description",
        "tool": {
          "name": "image_analyzer",
          "description": "Analyzes an image and provides a detailed description",
          "schema": {
            "type": "object",
            "properties": {
              "image_url": {
                "type": "string",
                "description": "URL of the image to analyze"
              },
              "analysis_depth": {
                "type": "string", 
                "enum": ["basic", "detailed", "comprehensive"],
                "description": "Depth of analysis to perform"
              }
            },
            "required": ["image_url"]
          }
        },
        "display_name": "Image Analyzer",
        "input_parameters": {
          "type": "object",
          "properties": {
            "image_url": {
              "type": "string",
              "description": "URL of the image to analyze"
            },
            "analysis_depth": {
              "type": "string",
              "enum": ["basic", "detailed", "comprehensive"],
              "description": "Depth of analysis to perform"
            }
          },
          "required": ["image_url"]
        }
      },
      {
        "description": "Extracts text from a document image",
        "tool": {
          "name": "document_ocr",
          "description": "Extracts text from a document image",
          "schema": {
            "type": "object",
            "properties": {
              "document_url": {
                "type": "string",
                "description": "URL of the document image"
              },
              "language": {
                "type": "string",
                "description": "Optional language code to optimize OCR"
              }
            },
            "required": ["document_url"]
          }
        },
        "display_name": "Document OCR",
        "input_parameters": {
          "type": "object",
          "properties": {
            "document_url": {
              "type": "string",
              "description": "URL of the document image"
            },
            "language": {
              "type": "string",
              "description": "Optional language code to optimize OCR"
            }
          },
          "required": ["document_url"]
        }
      }
    ]
  }
}
```

## Error Handling

The API uses standard HTTP status codes to indicate success or failure of requests:

| Status Code | Description |
|-------------|-------------|
| 200 | Success |
| 400 | Bad request (client error) |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Connected MCP not found |
| 500 | Internal server error |

For detailed error messages, refer to the `message` field in the response.

## Examples

### List All Connected MCPs for a User

**Request:**

```bash
curl -X GET "https://your-api-domain/mcp/get-all?page_number=1&max_per_page=10" \
  -H "Authorization: Bearer YOUR_API_TOKEN" \
  -H "x-user-id: user_8h7g6f5e4d3c2b1a" \
  -H "x-user-role: user"
```

**Response:**

```json
{
  "status": 200,
  "message": "",
  "data": {
    "connected_mcps": [
      {
        "id": "cm_1a2b3c4d5e6f7g8h",
        "user_id": "user_8h7g6f5e4d3c2b1a",
        "mcp_name": "AI Tool Provider",
        "url": "https://mcp-server.example.com/api",
        "transport": "streamable_http",
        "description": "External AI tool provider with image analysis capabilities",
        "created_at": "2025-06-15T09:30:00.000Z"
      },
      {
        "id": "cm_2b3c4d5e6f7g8h9i",
        "user_id": "user_8h7g6f5e4d3c2b1a",
        "mcp_name": "Data Processing Tools",
        "url": "https://data-tools.example.org/mcp",
        "transport": "websocket",
        "description": "Data processing and analysis tools",
        "created_at": "2025-06-14T14:20:00.000Z"
      }
    ],
    "page_number": 1,
    "max_per_page": 10,
    "total_page": 1
  }
}
```

### Create a New Connected MCP

**Request:**

```bash
curl -X POST "https://your-api-domain/mcp/create" \
  -H "Authorization: Bearer YOUR_API_TOKEN" \
  -H "x-user-id: user_8h7g6f5e4d3c2b1a" \
  -H "x-user-role: user" \
  -H "Content-Type: application/json" \
  -d '{
    "mcp_name": "Document Analysis Tools",
    "url": "https://doc-analysis.example.com/mcp-api",
    "transport": "streamable_http",
    "description": "Document analysis and processing tools"
  }'
```

**Response:**

```json
{
  "status": 200,
  "message": "",
  "data": {
    "id": "cm_3c4d5e6f7g8h9i0j",
    "user_id": "user_8h7g6f5e4d3c2b1a",
    "mcp_name": "Document Analysis Tools",
    "url": "https://doc-analysis.example.com/mcp-api",
    "transport": "streamable_http",
    "description": "Document analysis and processing tools",
    "created_at": "2025-07-02T10:15:00.000Z"
  }
}
```

### Get Details for a Specific Connected MCP

**Request:**

```bash
curl -X GET "https://your-api-domain/mcp/cm_1a2b3c4d5e6f7g8h/get-detail" \
  -H "Authorization: Bearer YOUR_API_TOKEN" \
  -H "x-user-id: user_8h7g6f5e4d3c2b1a" \
  -H "x-user-role: user"
```

**Response:**

```json
{
  "status": 200,
  "message": "",
  "data": {
    "id": "cm_1a2b3c4d5e6f7g8h",
    "user_id": "user_8h7g6f5e4d3c2b1a",
    "mcp_name": "AI Tool Provider",
    "url": "https://mcp-server.example.com/api",
    "transport": "streamable_http",
    "description": "External AI tool provider with image analysis capabilities",
    "created_at": "2025-06-15T09:30:00.000Z"
  }
}
```

### Update a Connected MCP

**Request:**

```bash
curl -X PATCH "https://your-api-domain/mcp/cm_1a2b3c4d5e6f7g8h/update" \
  -H "Authorization: Bearer YOUR_API_TOKEN" \
  -H "x-user-id: user_8h7g6f5e4d3c2b1a" \
  -H "x-user-role: user" \
  -H "Content-Type: application/json" \
  -d '{
    "mcp_name": "Updated AI Tool Provider",
    "description": "Updated description for AI tool provider"
  }'
```

**Response:**

```json
{
  "status": 200,
  "message": "",
  "data": {
    "id": "cm_1a2b3c4d5e6f7g8h",
    "user_id": "user_8h7g6f5e4d3c2b1a",
    "mcp_name": "Updated AI Tool Provider",
    "url": "https://mcp-server.example.com/api",
    "transport": "streamable_http",
    "description": "Updated description for AI tool provider",
    "created_at": "2025-06-15T09:30:00.000Z"
  }
}
```

### Delete a Connected MCP

**Request:**

```bash
curl -X DELETE "https://your-api-domain/mcp/cm_1a2b3c4d5e6f7g8h/delete" \
  -H "Authorization: Bearer YOUR_API_TOKEN" \
  -H "x-user-id: user_8h7g6f5e4d3c2b1a" \
  -H "x-user-role: user"
```

**Response:**

```json
{
  "status": 200,
  "message": "",
  "data": {
    "message": "Connected MCP deleted successfully"
  }
}
```

### Get Tool Information from a Connected MCP

**Request:**

```bash
curl -X GET "https://your-api-domain/mcp/cm_1a2b3c4d5e6f7g8h/tool-infos" \
  -H "Authorization: Bearer YOUR_API_TOKEN" \
  -H "x-user-id: user_8h7g6f5e4d3c2b1a" \
  -H "x-user-role: user"
```

**Response:**

```json
{
  "status": 200,
  "message": "",
  "data": {
    "tool_infos": [
      {
        "description": "Analyzes an image and provides a detailed description",
        "tool": {
          "name": "image_analyzer",
          "description": "Analyzes an image and provides a detailed description",
          "schema": {
            "type": "object",
            "properties": {
              "image_url": {
                "type": "string",
                "description": "URL of the image to analyze"
              },
              "analysis_depth": {
                "type": "string", 
                "enum": ["basic", "detailed", "comprehensive"],
                "description": "Depth of analysis to perform"
              }
            },
            "required": ["image_url"]
          }
        },
        "display_name": "Image Analyzer",
        "input_parameters": {
          "type": "object",
          "properties": {
            "image_url": {
              "type": "string",
              "description": "URL of the image to analyze"
            },
            "analysis_depth": {
              "type": "string",
              "enum": ["basic", "detailed", "comprehensive"],
              "description": "Depth of analysis to perform"
            }
          },
          "required": ["image_url"]
        }
      }
    ]
  }
}
```

### Example Error Response - Connected MCP Not Found

**Request:**

```bash
curl -X GET "https://your-api-domain/mcp/non_existent_id/get-detail" \
  -H "Authorization: Bearer YOUR_API_TOKEN" \
  -H "x-user-id: user_8h7g6f5e4d3c2b1a" \
  -H "x-user-role: user"
```

**Response:**

```json
{
  "status": 404,
  "message": "Connected MCP not found.",
  "data": null
}
```

## Security Notes

1. Always use HTTPS when interacting with this API to ensure secure transmission of credentials and data.

2. The MCP connections can potentially provide access to powerful AI tools and capabilities. Ensure proper access controls are in place.

3. Validate the security and trustworthiness of any MCP server before connecting to it in production environments.

4. Consider implementing additional authentication mechanisms for the MCP servers themselves to ensure only authorized systems can use their capabilities.
