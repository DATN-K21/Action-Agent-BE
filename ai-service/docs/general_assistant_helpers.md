# General Assistant Helpers

This module provides comprehensive helper functions for creating and managing general assistants in the system. General assistants are system-initiated assistants that each user has exactly one of, with a CHATBOT as the main team and RAGBOT/SEARCHBOT as support units.

## Overview

### Key Characteristics of General Assistants:
- **System-initiated**: Created automatically by the system, not through user API calls
- **One per user**: Each user can have only one general assistant
- **Main team**: CHATBOT (handles general conversations)
- **Support units**: RAGBOT (knowledge base/document search) and SEARCHBOT (internet search)
- **Auto-provisioned**: Created during user registration or first access

## Architecture

### Consolidated Module

All general assistant functionality has been consolidated into a single module:

**GeneralAssistantHelpers** (`app/core/utils/general_assistant_helpers.py`)
- Core service for CRUD operations
- Handles creation, deletion, and management
- Validates business rules (one per user)
- API-level helper functions
- Response formatting
- Integration utilities
- Public utility functions for external use

## Usage

### 1. During User Registration
```python
from app.core.utils.general_assistant_helpers import initialize_general_assistant_for_new_user

# Call this during user registration
success = await initialize_general_assistant_for_new_user(
    session=session,
    user_id=new_user.id,
    user_name=new_user.name
)
```

### 2. Ensure User Has General Assistant
```python
from app.core.utils.general_assistant_helpers import ensure_user_general_assistant

# Safe to call anytime - creates if doesn't exist, returns existing if it does
assistant = await ensure_user_general_assistant(
    session=session,
    user_id=user.id,
    user_name=user.name
)
```

### 3. Get User's General Assistant
```python
from app.core.utils.general_assistant_helpers import get_user_general_assistant

# Get existing general assistant (returns None if doesn't exist)
assistant = await get_user_general_assistant(session=session, user_id=user.id)
```

### 4. During User Deletion
```python
from app.core.utils.general_assistant_helpers import cleanup_user_general_assistant

# Call this during user deletion
success = await cleanup_user_general_assistant(session=session, user_id=user.id)
```

### 5. Format for API Response
```python
from app.services.general_assistant_helpers import GeneralAssistantHelpers

# Format general assistant for API response
response = await GeneralAssistantHelpers.format_general_assistant_response(
    session=session, 
    assistant=assistant
)
```

## Team Structure

General assistants have the following team structure:

### Main Team (CHATBOT)
- **Type**: `WorkflowType.CHATBOT`
- **Purpose**: Handle general conversations and coordinate with support units
- **Members**: 
  - Main chatbot member with search skills (DuckDuckGo, Wikipedia)

### Support Teams
1. **RAGBOT Team**
   - **Type**: `WorkflowType.RAGBOT`
   - **Purpose**: Search through uploaded documents and knowledge bases
   - **Members**: RAG specialist member

2. **SEARCHBOT Team**
   - **Type**: `WorkflowType.SEARCHBOT`
   - **Purpose**: Search the internet for current information
   - **Members**: Search specialist with web search tools

## Configuration

### Default Configuration
The helper automatically creates a general assistant with these default settings:
- Name: `"{user_name}'s General Assistant"`
- Description: `"A helpful general assistant for everyday tasks and conversations."`
- System prompt: `"You are a helpful, friendly, and knowledgeable general assistant..."`
- Provider: `"openai"`
- Model: `"gpt-4"`
- Temperature: `0.7`
- Support units: `[WorkflowType.RAGBOT, WorkflowType.SEARCHBOT]`

### Custom Configuration
```python
from app.core.utils.general_assistant_helpers import GeneralAssistantHelpers

# Create with custom parameters
assistant = await GeneralAssistantHelpers.create_general_assistant(
    session=session,
    user_id=user_id,
    name="Custom Assistant Name",
    description="Custom description",
    system_prompt="Custom system prompt",
    provider="anthropic",
    model_name="claude-3",
    temperature=0.5,
    support_units=[WorkflowType.SEARCHBOT]  # Only search support
)
```

## Integration Points

### User Service Integration
```python
# In user registration
async def create_user(user_data):
    user = create_user_record(user_data)
    
    # Initialize general assistant
    await initialize_general_assistant_for_new_user(
        session=session,
        user_id=user.id,
        user_name=user.name
    )
    
    return user

# In user deletion
async def delete_user(user_id):
    # Cleanup general assistant first
    await cleanup_user_general_assistant(session=session, user_id=user_id)
    
    # Then delete user
    delete_user_record(user_id)
```

### Chat Service Integration
```python
# Before starting a chat
async def start_chat(user_id):
    # Ensure user has general assistant
    assistant = await ensure_user_general_assistant(
        session=session,
        user_id=user_id,
        user_name="User"  # or get from user record
    )
    
    if assistant:
        # Use assistant for chat
        return assistant
    else:
        raise Exception("Failed to initialize general assistant")
```

### API Integration
```python
# In assistant list endpoint
async def get_assistants(user_id):
    assistants = []
    
    # Get general assistant
    general_assistant = await get_user_general_assistant(session, user_id)
    if general_assistant:
        formatted = await GeneralAssistantHelpers.format_general_assistant_response(
            session, general_assistant
        )
        assistants.append(formatted)
    
    # Get advanced assistants
    # ... existing code ...
    
    return assistants
```

## Error Handling

All helper functions include comprehensive error handling:

```python
try:
    assistant = await ensure_user_general_assistant(session, user_id, user_name)
    if assistant:
        # Success
        pass
    else:
        # Failed - log error and handle gracefully
        logger.error("Failed to ensure general assistant")
except Exception as e:
    # Exception occurred - log and handle
    logger.error(f"Exception ensuring general assistant: {e}")
```

## Database Schema

General assistants use the same `assistants` table with:
- `assistant_type = AssistantType.GENERAL_ASSISTANT`
- Associated teams with appropriate workflow types
- Members with search skills pre-configured

## Testing

See `docs/examples/general_assistant_examples.py` for comprehensive usage examples and testing scenarios.

## Notes

1. **One Per User Rule**: The system enforces that each user can have only one general assistant
2. **System Managed**: General assistants are created and managed by the system, not user requests
3. **Automatic Provisioning**: Should be created during user registration or first access
4. **Search Skills**: Both main chatbot and search support team get DuckDuckGo and Wikipedia search skills
5. **Consistent Structure**: All general assistants have the same team structure for predictability

## Future Enhancements

- Add configuration options for different skill sets
- Support for custom system prompts per user
- Integration with user preferences
- Advanced RAG capabilities
- Multi-language support
