# Internal User API Documentation

This documentation covers the internal user management API endpoints provided by the `app.api.internal.user` module. These endpoints are designed for internal system use and provide functionality for creating, updating, retrieving, and deleting user records.

## Table of Contents

1. [Overview](#overview)
2. [Endpoints](#endpoints)
   - [Create a New User](#create-a-new-user)
   - [Update User](#update-user)
   - [Delete User](#delete-user)
   - [Get All Users](#get-all-users)
   - [Get User Details](#get-user-details)
3. [Data Schemas](#data-schemas)
4. [Error Handling](#error-handling)
5. [Examples](#examples)

## Overview

The User API provides a set of endpoints for managing user records in the system. It handles operations such as user creation, updates, deletion (soft delete), and retrieval. Each endpoint returns a standardized response wrapped in a `ResponseWrapper` object that includes status codes and relevant messages.

The API also automatically creates a General Assistant for each new user to help them with basic tasks.

## Endpoints

### Create a New User

Creates a new user in the system and automatically generates a General Assistant for them.

- **URL**: `/user/create`
- **Method**: `POST`
- **Summary**: Create a new user.
- **Response Model**: `ResponseWrapper[CreateUserResponse]`

#### Request Body

```json
{
  "username": "johndoe",
  "email": "john.doe@example.com",
  "first_name": "John",
  "last_name": "Doe"
}
```

#### Success Response

```json
{
  "status": 200,
  "message": "",
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "john.doe@example.com",
    "username": "johndoe",
    "first_name": "John",
    "last_name": "Doe",
    "created_at": "2025-07-02T10:30:15.123Z"
  }
}
```

#### Error Response

- **User Already Exists**:
```json
{
  "status": 400,
  "message": "User already exists",
  "data": null
}
```

- **Server Error**:
```json
{
  "status": 500,
  "message": "Internal server error",
  "data": null
}
```

### Update User

Updates information for an existing user.

- **URL**: `/user/{user_id}/update`
- **Method**: `PATCH`
- **Summary**: Update the given user.
- **Response Model**: `ResponseWrapper[UpdateUserResponse]`

#### Path Parameters

- `user_id` (string, required): The unique identifier of the user to update

#### Request Body

```json
{
  "username": "johndoe_updated",
  "first_name": "Johnny",
  "last_name": "Doe"
}
```

Note: You can include only the fields you want to update.

#### Success Response

```json
{
  "status": 200,
  "message": "",
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "john.doe@example.com",
    "username": "johndoe_updated",
    "first_name": "Johnny",
    "last_name": "Doe",
    "created_at": "2025-07-02T10:30:15.123Z"
  }
}
```

#### Error Response

- **User Not Found**:
```json
{
  "status": 404,
  "message": "User not found",
  "data": null
}
```

- **Server Error**:
```json
{
  "status": 500,
  "message": "Internal server error",
  "data": null
}
```

### Delete User

Performs a soft delete on a user by marking them as deleted and recording the deletion time.

- **URL**: `/user/{user_id}/delete`
- **Method**: `DELETE`
- **Summary**: Delete the given user.
- **Response Model**: `ResponseWrapper[DeleteUserResponse]`

#### Path Parameters

- `user_id` (string, required): The unique identifier of the user to delete

#### Success Response

```json
{
  "status": 200,
  "message": "",
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000"
  }
}
```

#### Error Response

- **User Not Found**:
```json
{
  "status": 404,
  "message": "User not found",
  "data": null
}
```

- **Server Error**:
```json
{
  "status": 500,
  "message": "Internal server error",
  "data": null
}
```

### Get All Users

Retrieves a paginated list of all non-deleted users in the system.

- **URL**: `/user/get-all`
- **Method**: `GET`
- **Summary**: Get all users.
- **Response Model**: `ResponseWrapper[GetUsersResponse]`

#### Query Parameters

- `page_number` (integer, optional, default=1): The page number to retrieve
- `max_per_page` (integer, optional, default=10): Maximum number of items per page

#### Success Response

```json
{
  "status": 200,
  "message": "",
  "data": {
    "users": [
      {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "email": "john.doe@example.com",
        "username": "johndoe",
        "first_name": "John",
        "last_name": "Doe",
        "created_at": "2025-07-02T10:30:15.123Z"
      },
      {
        "id": "550e8400-e29b-41d4-a716-446655440001",
        "email": "jane.doe@example.com",
        "username": "janedoe",
        "first_name": "Jane",
        "last_name": "Doe",
        "created_at": "2025-07-01T15:45:22.456Z"
      }
    ],
    "page_number": 1,
    "max_per_page": 10,
    "total_page": 1
  }
}
```

#### Error Response

- **Server Error**:
```json
{
  "status": 500,
  "message": "Internal server error",
  "data": null
}
```

### Get User Details

Retrieves detailed information for a specific user.

- **URL**: `/user/{user_id}/get-detail`
- **Method**: `GET`
- **Summary**: Get details of the given user.
- **Response Model**: `ResponseWrapper[GetUserResponse]`

#### Path Parameters

- `user_id` (string, required): The unique identifier of the user

#### Success Response

```json
{
  "status": 200,
  "message": "",
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "john.doe@example.com",
    "username": "johndoe",
    "first_name": "John",
    "last_name": "Doe",
    "created_at": "2025-07-02T10:30:15.123Z"
  }
}
```

#### Error Response

- **User Not Found**:
```json
{
  "status": 404,
  "message": "User not found",
  "data": null
}
```

- **Server Error**:
```json
{
  "status": 500,
  "message": "Internal server error",
  "data": null
}
```

## Data Schemas

### Request Schemas

#### CreateUserRequest

```python
class CreateUserRequest(BaseRequest):
    id: Optional[str] = None
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr = Field(..., max_length=50)
    first_name: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=50)
```

#### UpdateUserRequest

```python
class UpdateUserRequest(BaseModel):
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[EmailStr] = Field(None, max_length=50)
    first_name: Optional[str] = Field(None, min_length=1, max_length=50)
    last_name: Optional[str] = Field(None, min_length=1, max_length=50)
```

### Response Schemas

#### CreateUserResponse

```python
class CreateUserResponse(BaseResponse):
    id: str = Field(...)
    email: str = Field(...)
    username: str = Field(...)
    first_name: str = Field(...)
    last_name: str = Field(...)
    created_at: datetime = Field(...)
```

#### GetUserResponse

```python
class GetUserResponse(BaseResponse):
    id: str = Field(...)
    email: Optional[str] = Field(None)
    username: Optional[str] = Field(None)
    first_name: Optional[str] = Field(None)
    last_name: Optional[str] = Field(None)
    created_at: Optional[datetime] = Field(None)
```

#### GetUsersResponse

```python
class GetUsersResponse(PagingResponse):
    users: list[GetUserResponse]
```

#### UpdateUserResponse

Inherits all fields from `GetUserResponse`.

#### DeleteUserResponse

```python
class DeleteUserResponse(BaseResponse):
    id: str = Field(...)
```

## Error Handling

All endpoints follow a consistent error handling pattern:

1. Each endpoint wraps its response in a `ResponseWrapper` object.
2. In case of an error, the appropriate status code and error message are included in the response.
3. Common error scenarios include:
   - `404 Not Found`: When a specified user doesn't exist or has been deleted
   - `400 Bad Request`: When there's an issue with the input data (e.g., trying to create a user that already exists)
   - `500 Internal Server Error`: For unexpected server errors

All database operations are wrapped in try-except blocks with proper transaction handling (commit or rollback).

## Examples

### Creating a New User with Python Requests

```python
import requests
import json

url = "http://your-api-domain/user/create"
headers = {
    "Content-Type": "application/json",
    "Authorization": "Bearer YOUR_ACCESS_TOKEN"
}
payload = {
    "username": "newuser123",
    "email": "newuser@example.com",
    "first_name": "New",
    "last_name": "User"
}

response = requests.post(url, headers=headers, data=json.dumps(payload))
print(response.json())
```

### Updating a User with cURL

```bash
curl -X PATCH "http://your-api-domain/user/550e8400-e29b-41d4-a716-446655440000/update" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "username": "updated_username",
    "first_name": "Updated"
  }'
```

### Retrieving All Users with JavaScript Fetch API

```javascript
const fetchUsers = async () => {
  try {
    const response = await fetch('http://your-api-domain/user/get-all?page_number=1&max_per_page=20', {
      method: 'GET',
      headers: {
        'Authorization': 'Bearer YOUR_ACCESS_TOKEN'
      }
    });
    
    const data = await response.json();
    console.log(data);
    
    // Process user data
    if (data.status === 200) {
      data.data.users.forEach(user => {
        console.log(`User: ${user.first_name} ${user.last_name} (${user.email})`);
      });
    }
  } catch (error) {
    console.error('Error fetching users:', error);
  }
};

fetchUsers();
```

### Deleting a User with Python Requests

```python
import requests

user_id = "550e8400-e29b-41d4-a716-446655440000"
url = f"http://your-api-domain/user/{user_id}/delete"
headers = {
    "Authorization": "Bearer YOUR_ACCESS_TOKEN"
}

response = requests.delete(url, headers=headers)
print(response.json())
```
