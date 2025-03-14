# APIs Documentation

This documentation explains how to utilize the APIs offered by the project to interact with the system and perform
different operations.

For complete API details, visit http://localhost:5001/docs after deploying the project.

The following code examples are written in Python and are intended to be executed in a Jupyter Notebook.

## 1. Flow to use APIs

### 1.1 Start conversation

1. Create a user to get user id.
2. Use the user id to create a thread.
3. Use the thread id to start a conversation.

### 1.2 Start with an extension

1. Create a user to get user id.
2. Use the user id to initiate connection to external app (like: Gmail, Slack, etc.).
3. Use a user id to create thread id.
4. Use the thread id to start a conversation.

## 2. Extension APIs

The Extension APIs exclusively support Socket.io for chat and streaming functionalities.

1. General Information
    - URL: http://hostdomain/
    - Namespace: /extension
    - Some client listeners: error, connect, disconnect
    - Some server listeners: connect, disconnect, message, set_timezone

2. Chat Endpoint:
    - Event name: chat, handle_chat_interrupt
    - Client listens to: chat_response, chat_interrupt
    - Description: This Socket.io endpoint enables agent communication through message-based chatting.

3. Stream Endpoint:
    - Event name: stream, handle_stream_interrupt
    - Client listens to: stream_response, stream_interrupt
    - Description: This Socket.io endpoint facilitates agent communication through message streaming.

**Note:** There are two ways to set timezone:

- Set timezone using extraHeaders in the connection options (with JavaScript).

```javascript
const socket = io('http://localhost:5001/extension', {
    extraHeaders: {
        timezone: 'Asia/Kolkata'
    }
});
```

- Set timezone using the set_timezone event (for both Python and JavaScript).
  Using set_timezone event, you can set the timezone when you connect to server

```python
import socketio
import pytz

sio = socketio.Client()
namespace = "/extension"


# Event handler for connection
@sio.on("connect", namespace=namespace)
def connect():
    print("Connected to server")
    timezone_str = pytz.timezone("Asia/Ho_Chi_Minh").zone  # Example: "Asia/Ho_Chi_Minh"
    sio.emit("set_timezone", timezone_str, namespace=namespace)
```

**How to get timezone:**

```javascript
const timeZone = Intl.DateTimeFormat().resolvedOptions().timeZone;
```

### 2.1 Schema for chat and stream events (send to server - ExtensionRequest)

- **user_id:** String type - User ID (required)
- **thread_id:** String type - Thread ID (required)
- **extension_name:** String type - Extension name (required)
- **input:** String type - Input message (required)
- **max_recursion:** Specifies the recursion limit when executing the graph (optional)

### 2.2 Schema for chat_response and stream_response events (send to client - ExtensionResponse)

- **user_id:** String type - User ID (required)
- **thread_id:** String type - Thread ID (required)
- **extension_name:** String type - Extension name (required)
- **interrupted:** Boolean type – Indicates whether human intervention is required in the process (required)
- **output:** String type - Output message (required)

**Note:** When the interrupted field is set to True, the output field contains a dictionary with "tool_calls".
Otherwise, output is a string representing the AI's response to your question.

### 2.3 Schema for handle_chat_interrupt and handle_stream_interrupt events (send to Server - ExtensionCallBack)

- **user_id:** String type - User ID (required)
- **thread_id:** String type - Thread ID (required)
- **extension_name:** String type - Extension name (required)
- **execute:** Boolean type - Indicates whether to continue executing the action (required)
- **tool_calls:** List type - List of the updated tool calls (Optional)
- **max_recursion:** Specifies the recursion limit when executing the graph (optional)

### 2.4 Schema for chat_interrupt and stream_interrupt events (send to client - ExtensionResponse)

- **user_id:** String type - User ID (required)
- **thread_id:** String type - Thread ID (required)
- **extension_name:** String type - Extension name (required)
- **interrupted:** Boolean type – Indicates whether human intervention is required in the process (required)
- **output:** String type - Output message (required)

**Note:** The interrupted field is always set to False, and the output field contains a string summarizing the result of
the tool call.

## 3. Agent APIs

- Agent functionalities are still accessible via HTTP APIs.
  You can explore these APIs using the Swagger documentation.
- Stream APIs utilize Server-Sent Events (SSE)

## 4. Multi-agent APIs

## 5. History APIs

## 6. Upload APIs

## 7. User APIs

## 8. Thread APIs

## 9. Connected apps APIs

