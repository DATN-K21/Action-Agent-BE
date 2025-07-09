# Public Extension API

This documentation provides details about the Extension API endpoints available in the AI Service. The Extension API allows you to manage connections to external extension services that provide AI tools and capabilities.

## Overview

The Extension API enables you to:

- Initialize connections to external extension services
- Check the status of existing connections
- Disconnect from extension services
- Retrieve a list of all connected extensions for a user
- Get detailed information about a specific connected extension

Extensions represent integrations between the AI Service and external services that provide AI tools and capabilities through standardized interfaces.

## Connected Extension Object

The Connected Extension object represents a connection between a user account and an external extension service:

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | The unique identifier of the connected extension |
| `user_id` | string | The ID of the user who owns this connection |
| `extension_enum` | string | The enum identifier of the extension type |
| `extension_name` | string | The human-readable name of the extension |
| `connection_status` | string | The status of the connection (PENDING, CONNECTED, FAILED) |
| `connected_account_id` | string | The ID of the connected account (optional) |
| `auth_scheme` | string | The authentication scheme used (optional) |
| `auth_value` | string | The authentication value/token (optional) |
| `created_at` | string | The timestamp when the connection was created (ISO format) |

## Connection Status Types

The connection status can be one of three values:

- `PENDING` - Connection is being established
- `CONNECTED` - Connection is active and ready to use
- `FAILED` - Connection failed to establish

## Endpoints

### Initialize Extension Connection

Initializes a new connection to an extension service. This creates a pending connection and returns authentication information if needed.

**Endpoint:** `POST /extension/active`

**Headers:**
- `x-user-id` (required): The ID of the authenticated user

**Query Parameters:**
- `extension_enum` (required): The enum identifier of the extension to connect to

**Response:**

```json
{
  "status": 200,
  "message": "",
  "data": {
    "is_existed": false,
    "redirect_url": "https://extension-service.example.com/oauth/authorize?client_id=abc123&redirect_uri=callback"
  }
}
```

**Response Fields:**
- `is_existed`: Boolean indicating if the connection already exists
- `redirect_url`: URL to redirect user for authentication (null if already connected)

### Check Connection Status

Checks the current status of an extension connection.

**Endpoint:** `GET /extension/check-active`

**Headers:**
- `x-user-id` (required): The ID of the authenticated user
- `x-user-role` (required): The role of the authenticated user (e.g., "user", "admin", "super_admin")

**Query Parameters:**
- `connected_extension_id` (required): The ID of the connected extension to check

**Permissions:**
- Users can only check their own connected extensions
- Admins and super admins can check any connected extension in the system

**Response:**

```json
{
  "status": 200,
  "message": "",
  "data": {
    "is_connected": true
  }
}
```

### Disconnect Extension

Disconnects from an extension service and removes the connection.

**Endpoint:** `POST /extension/disconnect`

**Headers:**
- `x-user-id` (required): The ID of the authenticated user
- `x-user-role` (required): The role of the authenticated user (e.g., "user", "admin", "super_admin")

**Query Parameters:**
- `connected_extension_id` (required): The ID of the connected extension to disconnect

**Permissions:**
- Users can only disconnect their own connected extensions
- Admins and super admins can disconnect any connected extension in the system

**Response:**

```json
{
  "status": 200,
  "message": "",
  "data": {
    "status": "success",
    "count": 1,
    "message": "Connection deleted successfully"
  }
}
```

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
        "extension_enum": "GMAIL_EXTENSION",
        "extension_name": "Gmail Integration",
        "connection_status": "CONNECTED",
        "connected_account_id": "gmail_account_123",
        "auth_scheme": "Bearer",
        "auth_value": "encrypted_token_value",
        "created_at": "2025-06-15T09:30:00.000Z"
      },
      {
        "id": "ce_2b3c4d5e6f7g8h9i",
        "user_id": "user_8h7g6f5e4d3c2b1a",
        "extension_enum": "SLACK_EXTENSION",
        "extension_name": "Slack Integration",
        "connection_status": "PENDING",
        "connected_account_id": null,
        "auth_scheme": null,
        "auth_value": null,
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
    "extension_enum": "GMAIL_EXTENSION",
    "extension_name": "Gmail Integration",
    "connection_status": "CONNECTED",
    "connected_account_id": "gmail_account_123",
    "auth_scheme": "Bearer",
    "auth_value": "encrypted_token_value",
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

### Initialize a New Extension Connection

**Request:**

```bash
curl -X POST "https://your-api-domain/extension/active?extension_enum=GMAIL_EXTENSION" \
  -H "Authorization: Bearer YOUR_API_TOKEN" \
  -H "x-user-id: user_8h7g6f5e4d3c2b1a"
```

**Response:**

```json
{
  "status": 200,
  "message": "",
  "data": {
    "is_existed": false,
    "redirect_url": "https://accounts.google.com/oauth/authorize?client_id=abc123&redirect_uri=callback&scope=gmail"
  }
}
```

### Check Connection Status

**Request:**

```bash
curl -X GET "https://your-api-domain/extension/check-active?connected_extension_id=ce_1a2b3c4d5e6f7g8h" \
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
    "is_connected": true
  }
}
```

### List All Connected Extensions

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
        "extension_enum": "GMAIL_EXTENSION",
        "extension_name": "Gmail Integration",
        "connection_status": "CONNECTED",
        "connected_account_id": "gmail_account_123",
        "auth_scheme": "Bearer",
        "auth_value": "encrypted_token_value",
        "created_at": "2025-06-15T09:30:00.000Z"
      },
      {
        "id": "ce_2b3c4d5e6f7g8h9i",
        "user_id": "user_8h7g6f5e4d3c2b1a",
        "extension_enum": "SLACK_EXTENSION",
        "extension_name": "Slack Integration",
        "connection_status": "PENDING",
        "connected_account_id": null,
        "auth_scheme": null,
        "auth_value": null,
        "created_at": "2025-06-14T14:20:00.000Z"
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
    "extension_enum": "GMAIL_EXTENSION",
    "extension_name": "Gmail Integration",
    "connection_status": "CONNECTED",
    "connected_account_id": "gmail_account_123",
    "auth_scheme": "Bearer",
    "auth_value": "encrypted_token_value",
    "created_at": "2025-06-15T09:30:00.000Z"
  }
}
```

### Disconnect an Extension

**Request:**

```bash
curl -X POST "https://your-api-domain/extension/disconnect?connected_extension_id=ce_1a2b3c4d5e6f7g8h" \
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
    "status": "success",
    "count": 1,
    "message": "Connection deleted successfully"
  }
}
```

### Example Error Response - Extension Not Found

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
  "message": "Connected Extension not found",
  "data": null
}
```

### Example Error Response - Connection Check Failed

**Request:**

```bash
curl -X GET "https://your-api-domain/extension/check-active?connected_extension_id=invalid_id" \
  -H "Authorization: Bearer YOUR_API_TOKEN" \
  -H "x-user-id: user_8h7g6f5e4d3c2b1a" \
  -H "x-user-role: user"
```

**Response:**

```json
{
  "status": 404,
  "message": "Extension Info or Extension Service not found",
  "data": null
}
```

## Extension Integration Flow

The typical flow for integrating with an extension service is:

1. **Initialize Connection**: Call `POST /extension/active` with the desired extension enum
2. **User Authentication**: If `redirect_url` is provided, redirect the user to complete authentication
3. **Check Status**: Use `GET /extension/check-active` to verify the connection is established
4. **Use Extension**: Once connected, the extension's tools and capabilities become available
5. **Manage Connection**: Use `GET /connected-extension/get-all` to view all connections
6. **Disconnect**: Use `POST /extension/disconnect` to remove the connection when no longer needed

## Security Notes

1. Always use HTTPS when interacting with this API to ensure secure transmission of credentials and data.

2. Extension connections may provide access to sensitive user data from external services. Ensure proper access controls are in place.

3. Authentication values (`auth_value`) are encrypted and stored securely. Never expose these values in client-side code.

4. Consider implementing additional security measures such as token refresh mechanisms for long-lived connections.

5. Regularly audit connected extensions to ensure they are still needed and functioning properly.

6. Users should only connect to trusted extension services from verified providers.

## Extension Development

For developers creating new extensions:

1. Each extension must have a unique `extension_enum` identifier
2. Extensions should implement proper OAuth2 or similar authentication flows
3. Extensions must handle connection status updates appropriately
4. Extensions should provide clear error messages for authentication failures
5. Extensions must support the disconnect operation to allow users to revoke access

## Rate Limiting

API endpoints may be subject to rate limiting to prevent abuse:

- Standard rate limits apply per user and per endpoint
- Higher limits may be available for admin and super admin users  
- Rate limit information is returned in response headers when applicable
- Exceeding rate limits will result in HTTP 429 responses

## Webhook Support

Some extensions may support webhook notifications for real-time updates:

- Webhook endpoints are configured during extension setup
- Webhooks provide notifications about connection status changes
- Webhook payloads include relevant extension and user information
- Proper webhook validation should be implemented for security
