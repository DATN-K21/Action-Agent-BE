# Public User API

This documentation provides detailed information about the User API endpoints available in the AI Service. The User API enables users to manage their account information and API keys for integration with various LLM providers.

## Overview

The User API enables you to:

- Retrieve API keys associated with a user account
- Set a default API key for LLM provider interactions
- Create or update API keys for different providers
- Delete API keys when they are no longer needed

API keys serve as authentication mechanisms for interacting with various LLM providers. Each user can have multiple API keys for different providers, with one designated as the default.

## Base Models

### SetDefaultApiKeyRequest

Request structure for setting a default API key:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `user_id` | string | Yes | ID of the user |
| `provider` | enum | Yes | LLM provider name (or null to clear default) |

### UpsertApiKeyRequest

Request structure for creating or updating an API key:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `user_id` | string | Yes | ID of the user |
| `encrypted_value` | string | Yes | Encrypted API key value |
| `provider` | enum | Yes | LLM provider name |

### DeleteApiKeyRequest

Request structure for deleting an API key:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `user_id` | string | Yes | ID of the user |
| `provider` | enum | Yes | LLM provider name |

### GetApiKeyResponse

Response structure for API key information:

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique identifier for the API key |
| `provider` | enum | LLM provider name |
| `created_at` | datetime | Timestamp when the API key was created |

### GetApiKeysResponse

Response structure for retrieving all API keys for a user:

| Field | Type | Description |
|-------|------|-------------|
| `user_id` | string | ID of the user |
| `default_api_key_id` | string | ID of the default API key (if set) |
| `remain_trial_tokens` | integer | Number of remaining trial tokens for the user |
| `api_keys` | array[GetApiKeyResponse] | List of API keys |

## Endpoints

### Get All API Keys

Retrieves all API keys associated with the current user.

**Endpoint:** `GET /user/key/get-all`

**Headers:**
- `x-user-id`: Current user's ID

**Response:**

```json
{
  "status": 200,
  "message": "Success",
  "data": {
    "user_id": "user-123",
    "default_api_key_id": "key-456",
    "remain_trial_tokens": 1000,
    "api_keys": [
      {
        "id": "key-456",
        "provider": "OpenAI",
        "created_at": "2025-06-30T14:30:00Z"
      },
      {
        "id": "key-789",
        "provider": "Anthropic",
        "created_at": "2025-06-29T10:15:00Z"
      }
    ]
  }
}
```

### Set Default API Key

Sets a specific API key as the default for the current user.

**Endpoint:** `POST /user/key/set-default`

**Headers:**
- `x-user-id`: Current user's ID

**Request Body:**
```json
{
  "user_id": "user-123",
  "provider": "OpenAI"
}
```

**Response:**

```json
{
  "status": 200,
  "message": "Success",
  "data": {}
}
```

### Upsert API Key

Creates a new API key or updates an existing one for a specific provider.

**Endpoint:** `PUT /user/key/upsert`

**Headers:**
- `x-user-id`: Current user's ID

**Request Body:**
```json
{
  "user_id": "user-123",
  "provider": "OpenAI",
  "encrypted_value": "encrypted-api-key-value"
}
```

**Response:**

```json
{
  "status": 200,
  "message": "Success",
  "data": {
    "id": "key-456",
    "user_id": "user-123",
    "provider": "OpenAI",
    "is_default": true
  }
}
```

### Delete API Key

Deletes an API key for a specific provider.

**Endpoint:** `DELETE /user/{user_id}/key/delete`

**Path Parameters:**
- `user_id`: ID of the user

**Headers:**
- `x-user-id`: Current user's ID

**Request Body:**
```json
{
  "user_id": "user-123",
  "provider": "OpenAI"
}
```

**Response:**

```json
{
  "status": 200,
  "message": "Success",
  "data": {}
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
  "message": "API key not found",
  "data": null
}
```

**Common Error Scenarios:**

1. **User Not Found:**
```json
{
  "status": 404,
  "message": "User not found"
}
```

2. **API Key Not Found:**
```json
{
  "status": 404,
  "message": "API key not found"
}
```

3. **Invalid Provider:**
```json
{
  "status": 400,
  "message": "Invalid provider: Unknown. Must be one of ['OpenAI', 'Anthropic', 'Azure', 'Google', 'Cohere', 'Mistral']"
}
```

4. **Server Error:**
```json
{
  "status": 500,
  "message": "Internal server error"
}
```

## Integration Examples

### JavaScript Integration Example

```javascript
// User API Client Class
class UserApiClient {
  constructor(apiBaseUrl, userId) {
    this.apiBaseUrl = apiBaseUrl;
    this.headers = {
      'Content-Type': 'application/json',
      'x-user-id': userId
    };
  }
  
  // Get all API keys
  async getAllApiKeys() {
    try {
      const response = await fetch(`${this.apiBaseUrl}/user/key/get-all`, {
        method: 'GET',
        headers: this.headers
      });
      
      const data = await response.json();
      
      if (data.status === 200) {
        return data.data;
      } else {
        console.error(`Error: ${data.message}`);
        return null;
      }
    } catch (error) {
      console.error('Failed to fetch API keys:', error);
      return null;
    }
  }
  
  // Set default API key
  async setDefaultApiKey(userId, provider) {
    try {
      const response = await fetch(`${this.apiBaseUrl}/user/key/set-default`, {
        method: 'POST',
        headers: this.headers,
        body: JSON.stringify({
          user_id: userId,
          provider: provider
        })
      });
      
      const data = await response.json();
      
      if (data.status === 200) {
        console.log('Default API key set successfully');
        return true;
      } else {
        console.error(`Error: ${data.message}`);
        return false;
      }
    } catch (error) {
      console.error('Failed to set default API key:', error);
      return false;
    }
  }
  
  // Upsert API key
  async upsertApiKey(userId, provider, encryptedValue) {
    try {
      const response = await fetch(`${this.apiBaseUrl}/user/key/upsert`, {
        method: 'PUT',
        headers: this.headers,
        body: JSON.stringify({
          user_id: userId,
          provider: provider,
          encrypted_value: encryptedValue
        })
      });
      
      const data = await response.json();
      
      if (data.status === 200) {
        console.log('API key created/updated successfully');
        return data.data;
      } else {
        console.error(`Error: ${data.message}`);
        return null;
      }
    } catch (error) {
      console.error('Failed to upsert API key:', error);
      return null;
    }
  }
  
  // Delete API key
  async deleteApiKey(userId, provider) {
    try {
      const response = await fetch(`${this.apiBaseUrl}/user/${userId}/key/delete`, {
        method: 'DELETE',
        headers: this.headers,
        body: JSON.stringify({
          user_id: userId,
          provider: provider
        })
      });
      
      const data = await response.json();
      
      if (data.status === 200) {
        console.log('API key deleted successfully');
        return true;
      } else {
        console.error(`Error: ${data.message}`);
        return false;
      }
    } catch (error) {
      console.error('Failed to delete API key:', error);
      return false;
    }
  }
}

// Example usage
async function exampleUserApiWorkflow() {
  // Initialize client
  const client = new UserApiClient('https://your-api-domain', 'your-user-id');
  
  // Get all API keys
  const apiKeysData = await client.getAllApiKeys();
  
  if (apiKeysData) {
    console.log(`User has ${apiKeysData.api_keys.length} API keys`);
    console.log(`Default API key ID: ${apiKeysData.default_api_key_id || 'None'}`);
    console.log(`Remaining trial tokens: ${apiKeysData.remain_trial_tokens}`);
    
    // List all API keys
    apiKeysData.api_keys.forEach(key => {
      console.log(`- Provider: ${key.provider}, Created: ${new Date(key.created_at).toLocaleDateString()}`);
    });
  }
  
  // Add or update an API key
  const newApiKey = await client.upsertApiKey(
    'your-user-id',
    'OpenAI',
    'encrypted-api-key-value'
  );
  
  if (newApiKey) {
    console.log(`New API key created with ID: ${newApiKey.id}`);
    
    // Set as default
    const setDefault = await client.setDefaultApiKey('your-user-id', 'OpenAI');
    
    if (setDefault) {
      console.log('OpenAI set as default provider');
    }
  }
  
  // After some time, delete the API key when no longer needed
  const deleted = await client.deleteApiKey('your-user-id', 'OpenAI');
  
  if (deleted) {
    console.log('OpenAI API key deleted successfully');
  }
}

// Run the example workflow
document.getElementById('manageApiKeysButton').addEventListener('click', exampleUserApiWorkflow);
```

### Python Integration Example

```python
import requests
import json

class UserApiClient:
    def __init__(self, api_base_url, user_id):
        self.api_base_url = api_base_url
        self.headers = {
            'Content-Type': 'application/json',
            'x-user-id': user_id
        }
    
    def get_all_api_keys(self):
        """Get all API keys for the current user."""
        try:
            response = requests.get(
                f"{self.api_base_url}/user/key/get-all",
                headers=self.headers
            )
            
            response_data = response.json()
            
            if response_data["status"] == 200:
                return response_data["data"]
            else:
                print(f"Error: {response_data['message']}")
                return None
        except Exception as e:
            print(f"Failed to fetch API keys: {e}")
            return None
    
    def set_default_api_key(self, user_id, provider):
        """Set a default API key for the given provider."""
        try:
            payload = {
                'user_id': user_id,
                'provider': provider
            }
            
            response = requests.post(
                f"{self.api_base_url}/user/key/set-default",
                headers=self.headers,
                json=payload
            )
            
            response_data = response.json()
            
            if response_data["status"] == 200:
                print("Default API key set successfully")
                return True
            else:
                print(f"Error: {response_data['message']}")
                return False
        except Exception as e:
            print(f"Failed to set default API key: {e}")
            return False
    
    def upsert_api_key(self, user_id, provider, encrypted_value):
        """Create or update an API key."""
        try:
            payload = {
                'user_id': user_id,
                'provider': provider,
                'encrypted_value': encrypted_value
            }
            
            response = requests.put(
                f"{self.api_base_url}/user/key/upsert",
                headers=self.headers,
                json=payload
            )
            
            response_data = response.json()
            
            if response_data["status"] == 200:
                print("API key created/updated successfully")
                return response_data["data"]
            else:
                print(f"Error: {response_data['message']}")
                return None
        except Exception as e:
            print(f"Failed to upsert API key: {e}")
            return None
    
    def delete_api_key(self, user_id, provider):
        """Delete an API key."""
        try:
            payload = {
                'user_id': user_id,
                'provider': provider
            }
            
            response = requests.delete(
                f"{self.api_base_url}/user/{user_id}/key/delete",
                headers=self.headers,
                json=payload
            )
            
            response_data = response.json()
            
            if response_data["status"] == 200:
                print("API key deleted successfully")
                return True
            else:
                print(f"Error: {response_data['message']}")
                return False
        except Exception as e:
            print(f"Failed to delete API key: {e}")
            return False


# Example usage
def example_user_api_workflow():
    # Initialize client
    client = UserApiClient("https://your-api-domain", "your-user-id")
    
    # Get all API keys
    api_keys_data = client.get_all_api_keys()
    
    if api_keys_data:
        print(f"User has {len(api_keys_data['api_keys'])} API keys")
        print(f"Default API key ID: {api_keys_data.get('default_api_key_id', 'None')}")
        print(f"Remaining trial tokens: {api_keys_data['remain_trial_tokens']}")
        
        # List all API keys
        for key in api_keys_data["api_keys"]:
            print(f"- Provider: {key['provider']}, Created: {key['created_at']}")
    
    # Add a new API key
    new_api_key = client.upsert_api_key(
        "your-user-id",
        "OpenAI",
        "encrypted-api-key-value"
    )
    
    if new_api_key:
        print(f"New API key created with ID: {new_api_key['id']}")
        
        # Set as default
        set_default = client.set_default_api_key("your-user-id", "OpenAI")
        
        if set_default:
            print("OpenAI set as default provider")
    
    # After some time, delete the API key
    deleted = client.delete_api_key("your-user-id", "OpenAI")
    
    if deleted:
        print("OpenAI API key deleted successfully")

if __name__ == "__main__":
    example_user_api_workflow()
```

## Best Practices

1. **Security Considerations**: 
   - Always encrypt API key values before sending them to the server
   - Never store API keys in client-side code or expose them in URLs
   - Consider using environment variables for storing sensitive API keys

2. **Default API Key Management**: 
   - Set a default API key for the most commonly used provider
   - Remove default API key settings when they are no longer needed by passing null as the provider

3. **Multiple Provider Support**:
   - Maintain API keys for multiple providers to ensure fallback options
   - Regularly rotate API keys for security reasons

4. **Error Handling**:
   - Implement appropriate error handling for API key operations
   - Check API key validity before attempting operations that require them

5. **Rate Limiting Awareness**:
   - Be aware that the API may implement rate limiting for operations
   - Implement exponential backoff for retries when API key operations fail

## Performance Considerations

1. **Caching**: Consider caching API key IDs (not the actual keys) client-side to reduce the number of API calls.

2. **Batch Operations**: When managing multiple API keys, try to minimize the number of API calls by planning operations efficiently.

3. **Key Rotation**: When rotating API keys, ensure that there is a smooth transition period where both old and new keys are valid to avoid service disruption.

This comprehensive API documentation provides developers with all the information needed to effectively integrate and leverage the User API endpoints in their applications.
