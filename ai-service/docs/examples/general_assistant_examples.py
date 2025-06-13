"""
General Assistant Usage Examples

This file demonstrates how to use the general assistant helpers.
These examples show the main operations available for general assistants.
"""

from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.utils.general_assistant_helpers import (
    GeneralAssistantHelpers,
    cleanup_user_general_assistant,
    ensure_user_general_assistant,
    get_user_general_assistant,
    initialize_general_assistant_for_new_user,
)
from app.db_models.assistant import Assistant


class GeneralAssistantExamples:
    """Examples of general assistant operations"""

    @staticmethod
    async def example_create_general_assistant(session: AsyncSession, user_id: str) -> Optional[Assistant]:
        """
        Example: Create a general assistant for a user with custom configuration
        """
        # Check if user already has one
        if await GeneralAssistantHelpers.check_user_has_general_assistant(session, user_id):
            print(f"User {user_id} already has a general assistant")
            return None  # Create the assistant with custom parameters
        assistant = await GeneralAssistantHelpers.create_general_assistant(
            session=session,
            user_id=user_id,
            name="My Personal Assistant",
            description="A personalized general assistant for daily tasks",
            system_prompt="You are my helpful personal assistant. Be friendly and professional.",
            provider="openai",
            model_name="gpt-4",
            temperature=0.7,
        )

        await session.commit()
        print(f"Created general assistant: {assistant.name}")
        return assistant

    @staticmethod
    async def example_ensure_user_has_assistant(session: AsyncSession, user_id: str, user_name: str) -> Optional[Assistant]:
        """
        Example: Ensure user has a general assistant (recommended approach)
        This will create one if it doesn't exist, or return existing one
        """
        assistant = await ensure_user_general_assistant(session, user_id, user_name)

        if assistant:
            print(f"User {user_name} has general assistant: {assistant.name}")
        else:
            print(f"Failed to ensure general assistant for user {user_name}")

        return assistant

    @staticmethod
    async def example_get_user_assistant(session: AsyncSession, user_id: str) -> Optional[Assistant]:
        """
        Example: Get user's existing general assistant
        """
        assistant = await get_user_general_assistant(session, user_id)

        if assistant:
            print(f"Found general assistant: {assistant.name}")
            print(f"Created at: {assistant.created_at}")
            print(f"Teams count: {len(assistant.teams or [])}")
        else:
            print("No general assistant found for user")

        return assistant

    @staticmethod
    async def example_format_assistant_response(session: AsyncSession, user_id: str) -> dict:
        """
        Example: Format general assistant for API response
        """
        assistant = await GeneralAssistantHelpers.get_general_assistant_with_teams(session, user_id)

        if not assistant:
            return {"error": "No general assistant found"}

        # Format for API response
        response = await GeneralAssistantHelpers.format_general_assistant_response(session, assistant)

        print(f"Formatted response for assistant: {response.name}")
        print(f"Main unit: {response.main_unit}")
        print(f"Support units: {response.support_units}")

        return response.dict()

    @staticmethod
    async def example_get_assistant_status(session: AsyncSession, user_id: str) -> dict:
        """
        Example: Get detailed status of user's general assistant
        """
        status = await GeneralAssistantHelpers.get_general_assistant_status(session, user_id)

        print("General Assistant Status:")
        print(f"  Exists: {status.get('exists', False)}")

        if status.get("exists"):
            print(f"  Name: {status.get('name')}")
            print(f"  Team Count: {status.get('team_count')}")
            print(f"  Member Count: {status.get('member_count')}")
            print(f"  Main Unit: {status.get('main_unit')}")
            print(f"  Support Units: {status.get('support_units')}")

        return status

    @staticmethod
    async def example_new_user_initialization(session: AsyncSession, user_id: str, user_name: str) -> bool:
        """
        Example: Initialize general assistant for a new user during registration
        Call this during user registration process
        """
        success = await initialize_general_assistant_for_new_user(session, user_id, user_name)

        if success:
            print(f"Successfully initialized general assistant for new user: {user_name}")
        else:
            print(f"Failed to initialize general assistant for new user: {user_name}")

        return success

    @staticmethod
    async def example_cleanup_user_assistant(session: AsyncSession, user_id: str) -> bool:
        """
        Example: Cleanup user's general assistant during user deletion
        Call this during user deletion process
        """
        success = await cleanup_user_general_assistant(session, user_id)

        if success:
            print(f"Successfully cleaned up general assistant for user: {user_id}")
        else:
            print(f"Failed to cleanup general assistant for user: {user_id}")

        return success


# Usage workflow example
async def example_workflow(session: AsyncSession, user_id: str, user_name: str):
    """
    Complete workflow example showing typical usage patterns
    """
    examples = GeneralAssistantExamples()

    print("=== General Assistant Workflow Example ===")

    # 1. For new user registration
    print("\n1. New User Registration:")
    await examples.example_new_user_initialization(session, user_id, user_name)
    # 2. Ensure user has assistant (safe to call anytime)
    print("\n2. Ensure User Has Assistant:")
    await examples.example_ensure_user_has_assistant(session, user_id, user_name)

    # 3. Get assistant status
    print("\n3. Get Assistant Status:")
    await examples.example_get_assistant_status(session, user_id)

    # 4. Format for API response
    print("\n4. Format for API Response:")
    await examples.example_format_assistant_response(session, user_id)

    # 5. Get existing assistant
    print("\n5. Get Existing Assistant:")
    await examples.example_get_user_assistant(session, user_id)

    print("\n=== Workflow Complete ===")


# Integration points for other services
class GeneralAssistantIntegration:
    """Integration helpers for other services"""

    @staticmethod
    async def on_user_registration(session: AsyncSession, user_id: str, user_name: str):
        """Call this during user registration"""
        return await initialize_general_assistant_for_new_user(session, user_id, user_name)

    @staticmethod
    async def on_user_login(session: AsyncSession, user_id: str, user_name: str):
        """Call this during user login to ensure assistant exists"""
        return await ensure_user_general_assistant(session, user_id, user_name)

    @staticmethod
    async def on_user_deletion(session: AsyncSession, user_id: str):
        """Call this during user deletion"""
        return await cleanup_user_general_assistant(session, user_id)

    @staticmethod
    async def get_for_chat(session: AsyncSession, user_id: str):
        """Get general assistant for chat/conversation"""
        return await get_user_general_assistant(session, user_id)
