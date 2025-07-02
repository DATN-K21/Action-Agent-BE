# Public Connected Extension API

This documentation provides details about the Connected Extension API endpoints available in the AI Service. The Connected Extension API allows you to retrieve information about external service extensions that are connected to user accounts.

## Overview

The Connected Extension API enables you to:

- Retrieve a list of all connected extensions for a user
- Get detailed information about a specific connected extension

Connected extensions represent integrations between the AI Service and external services or applications. These connections allow the AI Service to interact with external systems through authentication mechanisms like API keys or OAuth tokens.

## Connected Extension Object

The Connected Extension object represents a connection between a user account and an external service:

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | The unique identifier of the connected extension |
| `user_id` | string | The ID of the user who owns this connection |
| `extension_enum` | string | A unique enum identifier for the extension type |
| `extension_name` | string | The human-readable name of the extension |
| `connection_status` | string | The status of the connection (PENDING, SUCCESS, FAILED) |
| `connected_account_id` | string | The account ID in the external system (optional) |
| `auth_scheme` | string | The authentication scheme used (e.g., "Bearer") (optional) |
| `auth_value` | string | The authentication token or key value (optional) |
| `created_at` | string | The timestamp when the connection was created (ISO format) |

## Connection Status

The connection status can be one of three values:

- `PENDING` - The connection is being established or awaiting authentication
- `SUCCESS` - The connection is successfully established and active
- `FAILED` - The connection attempt failed or the connection has been invalidated

## Endpoints

### List Connected Extensions

Retrieves all connected extensions for the authenticated user with pagination support.

**Endpoint:** `GET /connected-extension/get-all`

**Headers:**
- `x-user-id` (required): The ID of the authenticated user
- `x-user-role` (required): The role of the authenticated user (e.g., "user", "admin", "super_admin")

**Query Parameters:**
- `page_number` (optional): The page number for pagination (default: 1)
- `max_per_page` (optional): Maximum number of items per page (default: 10)

**Permissions:**
- Users can only see their own connected extensions
- Admins and super admins can see all connected extensions in the system

**Response:**

```json
{
  "status": 200,
  "message": "",
  "data": {
    "connected_extensions": [
      {
        "id": "ce_1a2b3c4d5e6f7g8h",
        "user_id": "user_8h7g6f5e4d3c2b1a",
        "extension_enum": "GITHUB",
        "extension_name": "GitHub",
        "connection_status": "SUCCESS",
        "connected_account_id": "github_user123",
        "auth_scheme": "Bearer",
        "auth_value": "gho_XXXXXXXXXXXXXXXXXXXX", 
        "created_at": "2025-06-15T09:30:00.000Z"
      },
      {
        "id": "ce_2b3c4d5e6f7g8h9i",
        "user_id": "user_8h7g6f5e4d3c2b1a",
        "extension_enum": "SLACK",
        "extension_name": "Slack",
        "connection_status": "SUCCESS",
        "connected_account_id": "slack_user456",
        "auth_scheme": "Bearer",
        "auth_value": "xoxp-XXXXXXXXXXXXXXXXXXXX",
        "created_at": "2025-06-14T14:20:00.000Z"
      }
    ],
    "page_number": 1,
    "max_per_page": 10,
    "total_page": 1
  }
}
```

### Get Connected Extension Details

Retrieves detailed information about a specific connected extension.

**Endpoint:** `GET /connected-extension/{connected_extension_id}/get-detail`

**Path Parameters:**
- `connected_extension_id` (required): The ID of the connected extension to retrieve

**Headers:**
- `x-user-id` (required): The ID of the authenticated user
- `x-user-role` (required): The role of the authenticated user (e.g., "user", "admin", "super_admin")

**Permissions:**
- Users can only see details of their own connected extensions
- Admins and super admins can see details of any connected extension in the system

**Response:**

```json
{
  "status": 200,
  "message": "",
  "data": {
    "id": "ce_1a2b3c4d5e6f7g8h",
    "user_id": "user_8h7g6f5e4d3c2b1a",
    "extension_enum": "GITHUB",
    "extension_name": "GitHub",
    "connection_status": "SUCCESS",
    "connected_account_id": "github_user123",
    "auth_scheme": "Bearer",
    "auth_value": "gho_XXXXXXXXXXXXXXXXXXXX",
    "created_at": "2025-06-15T09:30:00.000Z"
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
| 404 | Connected extension not found |
| 500 | Internal server error |

For detailed error messages, refer to the `message` field in the response.

## Examples

### List All Connected Extensions for a User

**Request:**

```bash
curl -X GET "https://your-api-domain/connected-extension/get-all?page_number=1&max_per_page=10" \
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
    "connected_extensions": [
      {
        "id": "ce_1a2b3c4d5e6f7g8h",
        "user_id": "user_8h7g6f5e4d3c2b1a",
        "extension_enum": "GITHUB",
        "extension_name": "GitHub",
        "connection_status": "SUCCESS",
        "connected_account_id": "github_user123",
        "auth_scheme": "Bearer",
        "auth_value": "gho_XXXXXXXXXXXXXXXXXXXX",
        "created_at": "2025-06-15T09:30:00.000Z"
      },
      {
        "id": "ce_2b3c4d5e6f7g8h9i",
        "user_id": "user_8h7g6f5e4d3c2b1a",
        "extension_enum": "JIRA",
        "extension_name": "Jira",
        "connection_status": "PENDING",
        "connected_account_id": null,
        "auth_scheme": null,
        "auth_value": null,
        "created_at": "2025-07-01T11:45:00.000Z"
      }
    ],
    "page_number": 1,
    "max_per_page": 10,
    "total_page": 1
  }
}
```

### Get Details for a Specific Connected Extension

**Request:**

```bash
curl -X GET "https://your-api-domain/connected-extension/ce_1a2b3c4d5e6f7g8h/get-detail" \
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
    "id": "ce_1a2b3c4d5e6f7g8h",
    "user_id": "user_8h7g6f5e4d3c2b1a",
    "extension_enum": "GITHUB",
    "extension_name": "GitHub",
    "connection_status": "SUCCESS",
    "connected_account_id": "github_user123",
    "auth_scheme": "Bearer",
    "auth_value": "gho_XXXXXXXXXXXXXXXXXXXX",
    "created_at": "2025-06-15T09:30:00.000Z"
  }
}
```

### Example Error Response - Connected Extension Not Found

**Request:**

```bash
curl -X GET "https://your-api-domain/connected-extension/non_existent_id/get-detail" \
  -H "Authorization: Bearer YOUR_API_TOKEN" \
  -H "x-user-id: user_8h7g6f5e4d3c2b1a" \
  -H "x-user-role: user"
```

**Response:**

```json
{
  "status": 404,
  "message": "Connected extension not found",
  "data": null
}
```

## Security Notes

1. The `auth_value` field typically contains sensitive information like access tokens. In most responses, these values may be masked or partially hidden for security reasons.

2. Always use HTTPS when interacting with this API to ensure secure transmission of credentials and tokens.

3. Regular rotation of access tokens and API keys is recommended as a security best practice for connected extensions.
