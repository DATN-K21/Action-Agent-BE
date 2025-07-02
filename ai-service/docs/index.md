# API Documentation

Welcome to the AI Service API documentation. This documentation provides detailed information about the internal and public APIs available in the system.

## Available Documentation

### Internal APIs
- [User API](./internal_user_api.md) - Documentation for user management endpoints

### Public APIs
- [Assistant API](./public_assistant_api.md) - Documentation for assistant management endpoints

## Documentation Structure

Each API documentation includes:

1. **Overview** - A brief description of what the API does
2. **Endpoints** - Detailed information about each available endpoint
3. **Data Schemas** - Description of request and response data structures
4. **Error Handling** - Information about error responses and codes
5. **Examples** - Code samples showing how to use the API

## General Response Format

All API responses follow a standard format using the `ResponseWrapper` class:

```json
{
  "status": 200,  // HTTP status code
  "message": "",  // Optional message (empty when successful)
  "data": {       // The actual response data or null in case of error
    // Response data varies by endpoint
  }
}
```

## Authentication

Most API endpoints require authentication. Please ensure you include the appropriate authentication headers when making requests.

## Error Codes

Common error codes used across the APIs:

- `200`: Success
- `400`: Bad request (client error)
- `401`: Unauthorized
- `403`: Forbidden
- `404`: Not found
- `500`: Internal server error

For specific error details, refer to the individual API documentation pages.
