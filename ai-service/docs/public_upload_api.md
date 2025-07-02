# Public Upload API

This documentation provides detailed information about the Upload API endpoints available in the AI Service. The Upload API enables users to upload, manage, and search within various types of documents and web content for use with AI assistants.

## Overview

The Upload API enables you to:

- Upload files (PDF, DOCX, PPTX, XLSX, TXT, HTML, MD) or web content
- Retrieve individual uploads or lists of uploads
- Update upload information or replace uploaded content
- Delete uploads when they are no longer needed
- Perform semantic searches within uploaded content
- Associate uploads with specific conversation threads

Uploads serve as knowledge sources for AI assistants, enabling them to access and reference external information during conversations. Each upload is processed into chunks for efficient retrieval and can be linked to specific threads or assistants.

## Base Models

### UploadBase

Core upload information structure:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Name of the uploaded file |
| `description` | string | Yes | Description of the uploaded content |
| `file_type` | string | Yes | Type of the file (e.g., 'pdf', 'docx', 'web') |
| `web_url` | string | Yes | URL for web content uploads or empty for file uploads |
| `thread_id` | string | No | ID of the thread to associate with the upload |

### CreateUploadRequest

Request structure for creating a new upload - inherits all fields from UploadBase and adds:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `chunk_size` | integer | Yes | Size of each chunk in bytes for processing the content |
| `chunk_overlap` | integer | Yes | Overlap size in bytes between consecutive chunks |

### UpdateUploadRequest

Request structure for updating an upload:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | No | Updated name of the upload |
| `description` | string | No | Updated description of the upload |
| `file_type` | string | No | Updated file type |
| `web_url` | string | No | Updated web URL |
| `thread_id` | string | No | Updated thread association |
| `chunk_size` | integer | No | Updated chunk size |
| `chunk_overlap` | integer | No | Updated chunk overlap |
| `last_modified` | datetime | Yes | Timestamp when the upload was last modified |

### UploadResponse

Response structure for upload information:

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique identifier for the upload |
| `name` | string | Name of the upload |
| `description` | string | Description of the upload |
| `file_type` | string | Type of the file |
| `web_url` | string | URL for web content (if applicable) |
| `thread_id` | string | ID of the associated thread (if any) |
| `user_id` | string | ID of the user who created the upload |
| `status` | enum | Current status of the upload (IN_PROGRESS, COMPLETED, FAILED) |
| `last_modified` | datetime | Timestamp when the upload was last modified |
| `chunk_size` | integer | Size of each chunk in bytes |
| `chunk_overlap` | integer | Overlap size in bytes between consecutive chunks |

### UploadsResponse

Response structure for listing multiple uploads:

| Field | Type | Description |
|-------|------|-------------|
| `uploads` | array[UploadResponse] | List of uploads |
| `count` | integer | Total number of uploads matching the query |

## Endpoints

### Get All Uploads

Retrieves a list of all uploads accessible to the current user.

**Endpoint:** `GET /upload/`

**Query Parameters:**
- `status` (optional): Filter uploads by status (IN_PROGRESS, COMPLETED, FAILED)
- `skip` (optional): Number of uploads to skip for pagination
- `limit` (optional): Maximum number of uploads to return (default: 100)

**Headers:**
- `x-user-id`: Current user's ID
- `x-user-role`: Current user's role

**Response:**

```json
{
  "status": 200,
  "message": "Success",
  "data": {
    "uploads": [
      {
        "id": "upload-123",
        "name": "Company Overview",
        "description": "Company overview document with mission and vision",
        "file_type": "pdf",
        "web_url": null,
        "thread_id": "thread-456",
        "user_id": "user-789",
        "status": "Completed",
        "last_modified": "2025-06-30T14:30:00Z",
        "chunk_size": 1024,
        "chunk_overlap": 200
      },
      {
        "id": "upload-124",
        "name": "Q2 Financial Report",
        "description": "Financial results for Q2 2025",
        "file_type": "xlsx",
        "web_url": null,
        "thread_id": null,
        "user_id": "user-789",
        "status": "Completed",
        "last_modified": "2025-06-25T09:15:00Z",
        "chunk_size": 1024,
        "chunk_overlap": 200
      }
    ],
    "count": 2
  }
}
```

### Create Upload

Uploads a new file or web content.

**Endpoint:** `POST /upload/`

**Headers:**
- `x-user-id`: Current user's ID

**Form Parameters:**
- `name`: Name of the upload
- `description`: Description of the content
- `file_type`: Type of upload ("file" or "web")
- `chunk_size`: Size of each chunk in bytes
- `chunk_overlap`: Overlap size in bytes
- `web_url` (optional): URL for web content uploads
- `thread_id` (optional): ID of the thread to associate with the upload
- `file` (optional): File to upload (required if file_type is "file")

**Response:**

```json
{
  "status": 200,
  "message": "Success",
  "data": {
    "id": "upload-125",
    "name": "Product Roadmap",
    "description": "2025-2026 Product Development Roadmap",
    "file_type": "pdf",
    "web_url": null,
    "thread_id": "thread-456",
    "user_id": "user-789",
    "status": "In Progress",
    "last_modified": "2025-07-01T10:30:00Z",
    "chunk_size": 1024,
    "chunk_overlap": 200
  }
}
```

### Update Upload

Updates an existing upload's information or content.

**Endpoint:** `PUT /upload/{upload_id}`

**Path Parameters:**
- `upload_id`: ID of the upload to update

**Headers:**
- `x-user-id`: Current user's ID
- `x-user-role`: Current user's role

**Form Parameters:**
- `name` (optional): Updated name of the upload
- `description` (optional): Updated description of the content
- `file_type` (optional): Updated type of the file
- `chunk_size` (optional): Updated size of each chunk in bytes
- `chunk_overlap` (optional): Updated overlap size in bytes
- `web_url` (optional): Updated URL for web content
- `file` (optional): New file to replace the existing one

**Response:**

```json
{
  "status": 200,
  "message": "Success",
  "data": {
    "id": "upload-125",
    "name": "Updated Product Roadmap",
    "description": "2025-2026 Product Development Roadmap (Revised)",
    "file_type": "pdf",
    "web_url": null,
    "thread_id": "thread-456",
    "user_id": "user-789",
    "status": "In Progress",
    "last_modified": "2025-07-01T11:45:00Z",
    "chunk_size": 1024,
    "chunk_overlap": 200
  }
}
```

### Delete Upload

Initiates the deletion of an upload. This is an asynchronous operation.

**Endpoint:** `DELETE /upload/{upload_id}`

**Path Parameters:**
- `upload_id`: ID of the upload to delete

**Headers:**
- `x-user-id`: Current user's ID
- `x-user-role`: Current user's role

**Response:**

```json
{
  "status": 200,
  "message": "Success",
  "data": {
    "message": "Upload deletion initiated successfully"
  }
}
```

### Search Upload

Initiates an asynchronous search within a specific upload's content.

**Endpoint:** `POST /upload/{upload_id}/search`

**Path Parameters:**
- `upload_id`: ID of the upload to search within

**Headers:**
- `x-user-id`: Current user's ID

**Request Body:**
```json
{
  "query": "financial projections for Q3",
  "search_type": "vector",
  "top_k": 5,
  "score_threshold": 0.5
}
```

**Response:**

```json
{
  "task_id": "task-987654"
}
```

### Get Search Results

Retrieves the results of a previously initiated search operation.

**Endpoint:** `GET /upload/{upload_id}/search/{task_id}`

**Path Parameters:**
- `upload_id`: ID of the upload that was searched
- `task_id`: ID of the search task

**Response (Pending):**

```json
{
  "status": "pending"
}
```

**Response (Completed):**

```json
{
  "status": "completed",
  "results": [
    {
      "chunk_id": "chunk-1",
      "content": "Q3 financial projections indicate a 15% growth in revenue compared to Q2...",
      "score": 0.92,
      "metadata": {
        "page": 3,
        "position": 450
      }
    },
    {
      "chunk_id": "chunk-2",
      "content": "Based on current trends, Q3 projections have been adjusted to account for seasonal variations...",
      "score": 0.85,
      "metadata": {
        "page": 4,
        "position": 120
      }
    }
  ]
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
| 413 | Request Entity Too Large (file exceeds maximum size) |
| 500 | Internal Server Error |

**Error Response Format:**

```json
{
  "status": 404,
  "message": "Upload not found",
  "data": null
}
```

**Common Error Scenarios:**

1. **Upload Not Found:**
```json
{
  "status": 404,
  "message": "Upload not found"
}
```

2. **File Size Exceeded:**
```json
{
  "status": 413,
  "message": "Too large"
}
```

3. **Invalid File Type:**
```json
{
  "status": 400,
  "message": "Invalid file type. Supported types: pdf, docx, pptx, xlsx, txt, html, md"
}
```

4. **Insufficient Permissions:**
```json
{
  "status": 403,
  "message": "Not enough permissions"
}
```

## Integration Examples

### JavaScript Integration Example

```javascript
// Function to get all uploads
async function getUploads(status = null, skip = 0, limit = 100) {
  try {
    let url = `https://your-api-domain/upload/?skip=${skip}&limit=${limit}`;
    if (status) {
      url += `&status=${encodeURIComponent(status)}`;
    }
    
    const response = await fetch(url, {
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
    console.error('Failed to fetch uploads:', error);
    return null;
  }
}

// Function to upload a file
async function uploadFile(file, name, description, threadId = null, chunkSize = 1024, chunkOverlap = 200) {
  try {
    const formData = new FormData();
    formData.append('name', name);
    formData.append('description', description);
    formData.append('file_type', 'file');
    formData.append('chunk_size', chunkSize);
    formData.append('chunk_overlap', chunkOverlap);
    formData.append('file', file);
    
    if (threadId) {
      formData.append('thread_id', threadId);
    }
    
    const response = await fetch('https://your-api-domain/upload/', {
      method: 'POST',
      headers: {
        'x-user-id': 'your-user-id'
      },
      body: formData
    });
    
    const data = await response.json();
    
    if (data.status === 200) {
      console.log('File uploaded successfully');
      return data.data;
    } else {
      console.error(`Error: ${data.message}`);
      return null;
    }
  } catch (error) {
    console.error('Failed to upload file:', error);
    return null;
  }
}

// Function to upload web content
async function uploadWebContent(webUrl, name, description, threadId = null, chunkSize = 1024, chunkOverlap = 200) {
  try {
    const formData = new FormData();
    formData.append('name', name);
    formData.append('description', description);
    formData.append('file_type', 'web');
    formData.append('web_url', webUrl);
    formData.append('chunk_size', chunkSize);
    formData.append('chunk_overlap', chunkOverlap);
    
    if (threadId) {
      formData.append('thread_id', threadId);
    }
    
    const response = await fetch('https://your-api-domain/upload/', {
      method: 'POST',
      headers: {
        'x-user-id': 'your-user-id'
      },
      body: formData
    });
    
    const data = await response.json();
    
    if (data.status === 200) {
      console.log('Web content uploaded successfully');
      return data.data;
    } else {
      console.error(`Error: ${data.message}`);
      return null;
    }
  } catch (error) {
    console.error('Failed to upload web content:', error);
    return null;
  }
}

// Function to search within an upload
async function searchUpload(uploadId, query, searchType = 'vector', topK = 5, scoreThreshold = 0.5) {
  try {
    const response = await fetch(`https://your-api-domain/upload/${uploadId}/search`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-user-id': 'your-user-id'
      },
      body: JSON.stringify({
        query: query,
        search_type: searchType,
        top_k: topK,
        score_threshold: scoreThreshold
      })
    });
    
    const data = await response.json();
    const taskId = data.task_id;
    
    // Poll for results
    return await pollSearchResults(uploadId, taskId);
  } catch (error) {
    console.error('Failed to search upload:', error);
    return null;
  }
}

// Function to poll for search results
async function pollSearchResults(uploadId, taskId, maxAttempts = 30, interval = 1000) {
  let attempts = 0;
  
  while (attempts < maxAttempts) {
    try {
      const response = await fetch(`https://your-api-domain/upload/${uploadId}/search/${taskId}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'x-user-id': 'your-user-id'
        }
      });
      
      const data = await response.json();
      
      if (data.status === 'completed') {
        return data.results;
      }
      
      // Wait before polling again
      await new Promise(resolve => setTimeout(resolve, interval));
      attempts++;
    } catch (error) {
      console.error('Error polling search results:', error);
      return null;
    }
  }
  
  console.error('Search timed out');
  return null;
}

// Example usage
async function exampleUploadWorkflow() {
  // Upload a PDF file
  const fileInput = document.getElementById('fileInput');
  const file = fileInput.files[0];
  
  if (file) {
    const upload = await uploadFile(
      file,
      "Q2 Financial Report",
      "Financial results for Q2 2025",
      null, // No thread association
      1024, // Chunk size
      200   // Chunk overlap
    );
    
    if (upload) {
      console.log(`Uploaded file with ID: ${upload.id}`);
      
      // Wait for processing to complete (in a real app, you would check the status periodically)
      await new Promise(resolve => setTimeout(resolve, 5000));
      
      // Search within the uploaded content
      const searchResults = await searchUpload(
        upload.id,
        "revenue growth projections",
        "hybrid",
        5,
        0.5
      );
      
      if (searchResults) {
        console.log(`Found ${searchResults.length} matching chunks:`);
        searchResults.forEach((result, index) => {
          console.log(`Result ${index + 1}:`);
          console.log(`- Score: ${result.score}`);
          console.log(`- Content: ${result.content.substring(0, 100)}...`);
        });
      }
    }
  }
}

// Run the example workflow
document.getElementById('uploadButton').addEventListener('click', exampleUploadWorkflow);
```

### Python Integration Example

```python
import requests
import json
import time
import os

class UploadApiClient:
    def __init__(self, api_base_url, user_id, user_role):
        self.api_base_url = api_base_url
        self.headers = {
            'x-user-id': user_id,
            'x-user-role': user_role
        }
    
    def get_uploads(self, status=None, skip=0, limit=100):
        """Get all uploads accessible to the current user."""
        try:
            url = f"{self.api_base_url}/upload/?skip={skip}&limit={limit}"
            if status:
                url += f"&status={status}"
                
            response = requests.get(
                url,
                headers=self.headers
            )
            response_data = response.json()
            
            if response_data["status"] == 200:
                return response_data["data"]
            else:
                print(f"Error: {response_data['message']}")
                return None
        except Exception as e:
            print(f"Failed to fetch uploads: {e}")
            return None
    
    def upload_file(self, file_path, name, description, thread_id=None, chunk_size=1024, chunk_overlap=200):
        """Upload a file."""
        try:
            file_name = os.path.basename(file_path)
            
            with open(file_path, 'rb') as file:
                files = {'file': (file_name, file)}
                
                form_data = {
                    'name': name,
                    'description': description,
                    'file_type': 'file',
                    'chunk_size': str(chunk_size),
                    'chunk_overlap': str(chunk_overlap)
                }
                
                if thread_id:
                    form_data['thread_id'] = thread_id
                
                response = requests.post(
                    f"{self.api_base_url}/upload/",
                    headers=self.headers,
                    data=form_data,
                    files=files
                )
                
                response_data = response.json()
                
                if response_data["status"] == 200:
                    print("File uploaded successfully")
                    return response_data["data"]
                else:
                    print(f"Error: {response_data['message']}")
                    return None
        except Exception as e:
            print(f"Failed to upload file: {e}")
            return None
    
    def upload_web_content(self, web_url, name, description, thread_id=None, chunk_size=1024, chunk_overlap=200):
        """Upload web content."""
        try:
            form_data = {
                'name': name,
                'description': description,
                'file_type': 'web',
                'web_url': web_url,
                'chunk_size': str(chunk_size),
                'chunk_overlap': str(chunk_overlap)
            }
            
            if thread_id:
                form_data['thread_id'] = thread_id
            
            response = requests.post(
                f"{self.api_base_url}/upload/",
                headers=self.headers,
                data=form_data
            )
            
            response_data = response.json()
            
            if response_data["status"] == 200:
                print("Web content uploaded successfully")
                return response_data["data"]
            else:
                print(f"Error: {response_data['message']}")
                return None
        except Exception as e:
            print(f"Failed to upload web content: {e}")
            return None
    
    def update_upload(self, upload_id, name=None, description=None, file_path=None, chunk_size=None, chunk_overlap=None):
        """Update an upload."""
        try:
            form_data = {}
            files = {}
            
            if name:
                form_data['name'] = name
            
            if description:
                form_data['description'] = description
            
            if chunk_size:
                form_data['chunk_size'] = str(chunk_size)
            
            if chunk_overlap:
                form_data['chunk_overlap'] = str(chunk_overlap)
            
            if file_path:
                file_name = os.path.basename(file_path)
                with open(file_path, 'rb') as file:
                    files = {'file': (file_name, file)}
            
            response = requests.put(
                f"{self.api_base_url}/upload/{upload_id}",
                headers=self.headers,
                data=form_data,
                files=files
            )
            
            response_data = response.json()
            
            if response_data["status"] == 200:
                print("Upload updated successfully")
                return response_data["data"]
            else:
                print(f"Error: {response_data['message']}")
                return None
        except Exception as e:
            print(f"Failed to update upload: {e}")
            return None
    
    def delete_upload(self, upload_id):
        """Delete an upload."""
        try:
            response = requests.delete(
                f"{self.api_base_url}/upload/{upload_id}",
                headers=self.headers
            )
            
            response_data = response.json()
            
            if response_data["status"] == 200:
                print("Upload deletion initiated successfully")
                return True
            else:
                print(f"Error: {response_data['message']}")
                return False
        except Exception as e:
            print(f"Failed to delete upload: {e}")
            return False
    
    def search_upload(self, upload_id, query, search_type='vector', top_k=5, score_threshold=0.5):
        """Search within an upload."""
        try:
            search_params = {
                'query': query,
                'search_type': search_type,
                'top_k': top_k,
                'score_threshold': score_threshold
            }
            
            response = requests.post(
                f"{self.api_base_url}/upload/{upload_id}/search",
                headers=self.headers,
                json=search_params
            )
            
            data = response.json()
            task_id = data.get('task_id')
            
            if not task_id:
                print("Failed to start search task")
                return None
            
            # Poll for results
            return self._poll_search_results(upload_id, task_id)
        except Exception as e:
            print(f"Failed to search upload: {e}")
            return None
    
    def _poll_search_results(self, upload_id, task_id, max_attempts=30, interval=1):
        """Poll for search results."""
        attempts = 0
        
        while attempts < max_attempts:
            try:
                response = requests.get(
                    f"{self.api_base_url}/upload/{upload_id}/search/{task_id}",
                    headers=self.headers
                )
                
                data = response.json()
                
                if data.get('status') == 'completed':
                    return data.get('results')
                
                # Wait before polling again
                time.sleep(interval)
                attempts += 1
            except Exception as e:
                print(f"Error polling search results: {e}")
                return None
        
        print("Search timed out")
        return None


# Example usage
def example_upload_workflow():
    # Initialize client
    client = UploadApiClient("https://your-api-domain", "your-user-id", "your-user-role")
    
    # Upload a file
    file_upload = client.upload_file(
        file_path="path/to/financial_report.pdf",
        name="Q2 Financial Report",
        description="Financial results for Q2 2025",
        chunk_size=1024,
        chunk_overlap=200
    )
    
    if file_upload:
        upload_id = file_upload["id"]
        print(f"Uploaded file with ID: {upload_id}")
        
        # Wait for processing to complete (in a real app, you would check the status periodically)
        time.sleep(5)
        
        # Search within the uploaded content
        search_results = client.search_upload(
            upload_id=upload_id,
            query="revenue growth projections",
            search_type="hybrid",
            top_k=5,
            score_threshold=0.5
        )
        
        if search_results:
            print(f"Found {len(search_results)} matching chunks:")
            for i, result in enumerate(search_results):
                print(f"Result {i+1}:")
                print(f"- Score: {result['score']}")
                content_preview = result['content'][:100] + "..." if len(result['content']) > 100 else result['content']
                print(f"- Content: {content_preview}")
    
    # Upload web content
    web_upload = client.upload_web_content(
        web_url="https://example.com/annual-report-2025",
        name="Annual Report 2025",
        description="Company's annual report for 2025",
        chunk_size=1024,
        chunk_overlap=200
    )
    
    if web_upload:
        print(f"Uploaded web content with ID: {web_upload['id']}")

if __name__ == "__main__":
    example_upload_workflow()
```

## Best Practices

1. **File Types**: Only upload supported file types (PDF, DOCX, PPTX, XLSX, TXT, HTML, MD) to ensure proper processing.

2. **File Size**: Be mindful of the maximum file size limit. Large files may take longer to process.

3. **Chunking Strategy**: Choose appropriate chunk sizes based on your content. Smaller chunks (e.g., 512-1024 bytes) work well for precise retrieval, while larger chunks provide more context.

4. **Chunk Overlap**: Use adequate overlap between chunks (typically 10-20% of chunk size) to ensure context is preserved across chunk boundaries.

5. **Thread Association**: Associate uploads with specific threads when the content is relevant to an ongoing conversation for better context.

6. **Search Types**:
   - Use "vector" search for semantic understanding and concept matching
   - Use "fulltext" search for exact keyword matching
   - Use "hybrid" search to combine both approaches

7. **Status Monitoring**: Check the status of uploads after creation to ensure they are processed successfully.

## Performance Considerations

1. **Upload Processing**: Processing large files or web content may take time. Implement polling or webhooks in your application to be notified when processing completes.

2. **Search Asynchronicity**: Search operations are asynchronous. Your application should handle polling for results.

3. **File Size Impact**: Larger files will take longer to process and may require different chunking strategies.

4. **Thread-Upload Linking**: Associating uploads with threads automatically makes content available to the assistant in that thread.

5. **Rate Limiting**: Be aware that the API may implement rate limiting for operations like creating or searching uploads.

This comprehensive API documentation provides developers with all the information needed to effectively integrate and leverage the Upload API endpoints in their applications.
