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

2. Chat Endpoint:
    - Event name: chat, chat_interrupt
    - Client listens to: chat_response, handle_chat_interrupt
    - Description: This Socket.io endpoint enables agent communication through message-based chatting.

3. Stream Endpoint:
    - Event name: stream, stream_interrupt
    - Client listens to: stream_response, handle_stream_interrupt
    - Description: This Socket.io endpoint facilitates agent communication through message streaming.

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

### 2.3 Schema for handle_chat_interrupt and handle_stream_interrupt events (send to Server)

- **user_id:** String type - User ID (required)
- **thread_id:** String type - Thread ID (required)
- **extension_name:** String type - Extension name (required)
- **input:** String type - Input message (required)
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

Agent functionalities are still accessible via HTTP APIs.
You can explore these APIs using the Swagger documentation.

## 4. Multi-agent APIs

## 5. History APIs

## 6. Upload APIs

## 7. User APIs

## 8. Thread APIs

## 9. Connected apps APIs

