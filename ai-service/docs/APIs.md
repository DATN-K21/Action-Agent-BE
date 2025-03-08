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

## 3. Agent APIs

Agent functionalities are still accessible via HTTP APIs.
You can explore these APIs using the Swagger documentation.

## 4. Multi-agent APIs

## 5. History APIs

## 6. Upload APIs

## 7. User APIs

## 8. Thread APIs

## 9. Connected apps APIs

