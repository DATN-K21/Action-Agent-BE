# Public Callback API

This documentation provides details about the Callback API endpoints available in the AI Service. The Callback API allows you to register and manage webhook callbacks for various events related to assistants and threads.

## Overview

The Callback API enables you to:

- Register webhook URLs to receive real-time notifications about specific events
- Update existing webhook configurations
- Delete webhook registrations
- View all registered webhooks

## Callback Event Types

The system supports the following event types for callbacks:

1. **Assistant Events**
   - `assistant.created` - Triggered when a new assistant is created
   - `assistant.updated` - Triggered when an assistant's properties are updated
   - `assistant.deleted` - Triggered when an assistant is deleted

2. **Thread Events**
   - `thread.created` - Triggered when a new thread is created
   - `thread.updated` - Triggered when a thread is modified
   - `thread.deleted` - Triggered when a thread is deleted

3. **Message Events**
   - `message.created` - Triggered when a new message is added to a thread
   - `message.processed` - Triggered when a message has been processed by the AI

4. **Execution Events**
   - `execution.started` - Triggered when an assistant begins processing a request
   - `execution.completed` - Triggered when an assistant completes processing
   - `execution.failed` - Triggered when an assistant encounters an error during processing

## Endpoints

### Register Callback URL

Registers a new webhook URL to receive callbacks for specified events.

**Endpoint:** `POST /callback/register`

**Request Body:**

```json
{
  "url": "https://your-service.com/webhook",
  "event_types": ["assistant.created", "thread.created", "message.created"],
  "description": "Main service webhook",
  "metadata": {
    "team": "engineering",
    "environment": "production"
  },
  "secret": "your_signing_secret"
}
```

**Request Parameters:**
- `url` (required): The HTTPS URL that will receive the webhook callbacks
- `event_types` (required): Array of event types to subscribe to
- `description` (optional): Human-readable description of the webhook
- `metadata` (optional): Additional key-value pairs for your reference
- `secret` (optional): Secret used to sign the webhook payload for verification

**Response:**

```json
{
  "status": 200,
  "message": "Callback registered successfully",
  "data": {
    "id": "cb_6f8d9e7c5b3a4a2f",
    "url": "https://your-service.com/webhook",
    "event_types": ["assistant.created", "thread.created", "message.created"],
    "description": "Main service webhook",
    "metadata": {
      "team": "engineering",
      "environment": "production"
    },
    "has_secret": true,
    "created_at": "2025-06-28T14:30:00.000Z",
    "updated_at": "2025-06-28T14:30:00.000Z"
  }
}
```

### List Callback Registrations

Retrieves all callback registrations for the authenticated user.

**Endpoint:** `GET /callback/list`

**Query Parameters:**
- `offset` (optional): Number of items to skip (default: 0)
- `limit` (optional): Maximum number of items to return (default: 10)

**Response:**

```json
{
  "status": 200,
  "message": "",
  "data": {
    "callbacks": [
      {
        "id": "cb_6f8d9e7c5b3a4a2f",
        "url": "https://your-service.com/webhook",
        "event_types": ["assistant.created", "thread.created", "message.created"],
        "description": "Main service webhook",
        "metadata": {
          "team": "engineering",
          "environment": "production"
        },
        "has_secret": true,
        "created_at": "2025-06-28T14:30:00.000Z",
        "updated_at": "2025-06-28T14:30:00.000Z"
      },
      {
        "id": "cb_a1b2c3d4e5f6g7h8",
        "url": "https://backup-service.com/webhook",
        "event_types": ["execution.completed", "execution.failed"],
        "description": "Backup notification service",
        "metadata": {
          "team": "operations",
          "environment": "production"
        },
        "has_secret": false,
        "created_at": "2025-06-29T09:15:00.000Z",
        "updated_at": "2025-06-29T09:15:00.000Z"
      }
    ],
    "total": 2,
    "offset": 0,
    "limit": 10
  }
}
```

### Get Callback by ID

Retrieves a specific callback registration by its ID.

**Endpoint:** `GET /callback/{callback_id}`

**Path Parameters:**
- `callback_id`: The unique identifier of the callback registration

**Response:**

```json
{
  "status": 200,
  "message": "",
  "data": {
    "id": "cb_6f8d9e7c5b3a4a2f",
    "url": "https://your-service.com/webhook",
    "event_types": ["assistant.created", "thread.created", "message.created"],
    "description": "Main service webhook",
    "metadata": {
      "team": "engineering",
      "environment": "production"
    },
    "has_secret": true,
    "created_at": "2025-06-28T14:30:00.000Z",
    "updated_at": "2025-06-28T14:30:00.000Z"
  }
}
```

### Update Callback

Updates an existing callback registration.

**Endpoint:** `PUT /callback/{callback_id}`

**Path Parameters:**
- `callback_id`: The unique identifier of the callback registration to update

**Request Body:**

```json
{
  "url": "https://updated-service.com/webhook",
  "event_types": ["assistant.created", "thread.created", "message.created", "execution.completed"],
  "description": "Updated main service webhook",
  "metadata": {
    "team": "engineering",
    "environment": "staging"
  },
  "secret": "new_signing_secret"
}
```

**Request Parameters:**
- All parameters are optional, only the fields you want to update need to be included

**Response:**

```json
{
  "status": 200,
  "message": "Callback updated successfully",
  "data": {
    "id": "cb_6f8d9e7c5b3a4a2f",
    "url": "https://updated-service.com/webhook",
    "event_types": ["assistant.created", "thread.created", "message.created", "execution.completed"],
    "description": "Updated main service webhook",
    "metadata": {
      "team": "engineering",
      "environment": "staging"
    },
    "has_secret": true,
    "created_at": "2025-06-28T14:30:00.000Z",
    "updated_at": "2025-07-01T11:45:00.000Z"
  }
}
```

### Delete Callback

Deletes a callback registration permanently.

**Endpoint:** `DELETE /callback/{callback_id}`

**Path Parameters:**
- `callback_id`: The unique identifier of the callback registration to delete

**Response:**

```json
{
  "status": 200,
  "message": "Callback deleted successfully",
  "data": null
}
```

## Callback Payload Structure

When an event occurs, a POST request will be sent to your registered URL with a JSON payload containing the following fields:

```json
{
  "id": "evt_a1b2c3d4e5f6g7h8",
  "type": "assistant.created",
  "created_at": "2025-07-01T14:30:00.000Z",
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
    "created_at": "2025-07-01T14:30:00.000Z"
  }
}
```

The structure of the `data` object depends on the event type:
- For assistant events, it contains the assistant details
- For thread events, it contains the thread details
- For message events, it contains the message details
- For execution events, it contains execution status information

## Security

### Webhook Signature Verification

When you provide a secret during webhook registration, all callback requests will include a signature in the `X-Signature` header. This signature is a HMAC SHA-256 hash of the request body using your secret as the key.

To verify the authenticity of the webhook:

1. Get the signature from the `X-Signature` header
2. Create an HMAC SHA-256 hash of the raw request body using your secret as the key
3. Compare the generated hash with the signature from the header

**Example (Node.js):**

```javascript
const crypto = require('crypto');

function verifyWebhookSignature(requestBody, signature, secret) {
  const hmac = crypto.createHmac('sha256', secret);
  const digest = hmac.update(requestBody).digest('hex');
  return crypto.timingSafeEqual(Buffer.from(digest), Buffer.from(signature));
}

// In your webhook handler
app.post('/webhook', (req, res) => {
  const signature = req.headers['x-signature'];
  const rawBody = JSON.stringify(req.body);
  const secret = 'your_signing_secret';
  
  if (verifyWebhookSignature(rawBody, signature, secret)) {
    // Process the webhook
    console.log('Webhook verified and processed');
    res.status(200).send('Received');
  } else {
    console.error('Invalid signature');
    res.status(401).send('Invalid signature');
  }
});
```

**Example (Python):**

```python
import hmac
import hashlib

def verify_webhook_signature(request_body, signature, secret):
    computed_signature = hmac.new(
        secret.encode('utf-8'),
        request_body.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(computed_signature, signature)

# In your webhook handler
@app.route('/webhook', methods=['POST'])
def webhook_handler():
    signature = request.headers.get('X-Signature')
    raw_body = request.data.decode('utf-8')
    secret = 'your_signing_secret'
    
    if verify_webhook_signature(raw_body, signature, secret):
        # Process the webhook
        print('Webhook verified and processed')
        return 'Received', 200
    else:
        print('Invalid signature')
        return 'Invalid signature', 401
```

### Best Practices

1. **Always use HTTPS URLs** for your webhooks to ensure data is encrypted in transit
2. **Set a unique secret** for each webhook registration
3. **Verify the signature** of each incoming webhook request
4. **Implement retry logic** in your webhook handler to deal with temporary failures
5. **Return a 2xx status code** promptly to acknowledge receipt of the webhook

## Error Handling

The API uses standard HTTP status codes to indicate success or failure of requests:

| Status Code | Description |
|-------------|-------------|
| 200 | Success |
| 400 | Bad request (client error) |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Callback registration not found |
| 500 | Internal server error |

For detailed error messages, refer to the `message` field in the response.

## Retries and Failures

If your webhook endpoint returns a non-2xx status code or times out, the system will retry the webhook delivery with an exponential backoff:

1. First retry: 5 minutes
2. Second retry: 30 minutes
3. Third retry: 2 hours
4. Fourth retry: 5 hours
5. Final retry: 10 hours

After all retry attempts fail, the webhook will be marked as failed. You can check the delivery status of webhooks in the webhook dashboard.

## Examples

### Registering a Webhook for Assistant Creation and Thread Updates

**Request:**

```bash
curl -X POST "https://your-api-domain/callback/register" \
  -H "Authorization: Bearer YOUR_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com/ai-webhook",
    "event_types": ["assistant.created", "thread.updated"],
    "description": "Monitor assistant creation and thread updates",
    "secret": "my_secure_signing_secret"
  }'
```

**Response:**

```json
{
  "status": 200,
  "message": "Callback registered successfully",
  "data": {
    "id": "cb_a1b2c3d4e5f6g7h8",
    "url": "https://example.com/ai-webhook",
    "event_types": ["assistant.created", "thread.updated"],
    "description": "Monitor assistant creation and thread updates",
    "metadata": {},
    "has_secret": true,
    "created_at": "2025-07-01T10:15:00.000Z",
    "updated_at": "2025-07-01T10:15:00.000Z"
  }
}
```

### Registering a Webhook for All Execution Events

**Request:**

```bash
curl -X POST "https://your-api-domain/callback/register" \
  -H "Authorization: Bearer YOUR_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://monitoring.example.com/execution-webhook",
    "event_types": ["execution.started", "execution.completed", "execution.failed"],
    "description": "Monitor all execution events",
    "metadata": {
      "purpose": "execution-monitoring",
      "team": "operations"
    },
    "secret": "operations_secret_key"
  }'
```

**Response:**

```json
{
  "status": 200,
  "message": "Callback registered successfully",
  "data": {
    "id": "cb_j9k8l7m6n5o4p3q2",
    "url": "https://monitoring.example.com/execution-webhook",
    "event_types": ["execution.started", "execution.completed", "execution.failed"],
    "description": "Monitor all execution events",
    "metadata": {
      "purpose": "execution-monitoring",
      "team": "operations"
    },
    "has_secret": true,
    "created_at": "2025-07-02T09:30:00.000Z",
    "updated_at": "2025-07-02T09:30:00.000Z"
  }
}
```

### Sample Webhook Payload - Assistant Created

When an assistant is created, the following payload will be sent to registered webhooks:

```json
{
  "id": "evt_f5g6h7j8k9l0",
  "type": "assistant.created",
  "created_at": "2025-07-02T15:45:22.000Z",
  "data": {
    "id": "3e4f5g6h-7i8j-9k0l-1m2n-3o4p5q6r7s8t",
    "user_id": "u7v8w9x0-y1z2-3a4b-5c6d-7e8f9g0h1i2j",
    "name": "Document Processor",
    "assistant_type": "ADVANCED",
    "description": "Processes and analyzes document content",
    "system_prompt": "You are a document processing assistant...",
    "provider": "anthropic",
    "model_name": "claude-3-opus",
    "temperature": 0.3,
    "ask_human": false,
    "interrupt": true,
    "main_unit": "CHATBOT",
    "support_units": ["RAGBOT"],
    "mcp_ids": ["mcp-document-1"],
    "extension_ids": [],
    "created_at": "2025-07-02T15:45:20.000Z"
  }
}
```

### Sample Webhook Payload - Execution Completed

When an execution is completed, the following payload will be sent to registered webhooks:

```json
{
  "id": "evt_p9o8i7u6y5t4",
  "type": "execution.completed",
  "created_at": "2025-07-02T16:12:05.000Z",
  "data": {
    "id": "exec_a1s2d3f4g5h6j7",
    "assistant_id": "3e4f5g6h-7i8j-9k0l-1m2n-3o4p5q6r7s8t",
    "thread_id": "th_m1n2b3v4c5x6z7",
    "status": "completed",
    "started_at": "2025-07-02T16:11:50.000Z",
    "completed_at": "2025-07-02T16:12:05.000Z",
    "duration_ms": 15000,
    "tokens_used": {
      "prompt": 1250,
      "completion": 425,
      "total": 1675
    },
    "units_used": ["CHATBOT", "RAGBOT"],
    "metadata": {
      "request_id": "req-2025070201"
    }
  }
}
```
