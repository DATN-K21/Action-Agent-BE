"""
General Assistant Helpers

This module provides comprehensive helper functions for creating and managing general assistants.
General assistants are system-initiated assistants with CHATBOT as main team and
RAGBOT/SEARCHBOT as support units. Each user can only have one general assistant.

This consolidates all general assistant functionality into a single module.
"""

import uuid
from typing import Any, Dict, List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core import logging
from app.core.constants import SYSTEM
from app.core.enums import AssistantType, ConnectedServiceType, StorageStrategy, WorkflowType
from app.core.settings import env_settings
from app.core.tools.tool_manager import create_unique_key, global_tools
from app.db_models.assistant import Assistant
from app.db_models.member import Member
from app.db_models.member_skill_link import MemberSkillLink
from app.db_models.skill import Skill
from app.db_models.team import Team
from app.schemas.assistant import GetGeneralAssistantResponse

logger = logging.get_logger(__name__)


class GeneralAssistantHelpers:
    """Helper functions for general assistant operations"""

    @staticmethod
    async def check_user_has_general_assistant(session: AsyncSession, user_id: str) -> bool:
        """
        Check if user already has a general assistant.

        Args:
            session: Database session
            user_id: User ID to check

        Returns:
            True if user has general assistant, False otherwise
        """
        statement = select(func.count(Assistant.id)).where(
            Assistant.user_id == user_id, Assistant.assistant_type == AssistantType.GENERAL_ASSISTANT, Assistant.is_deleted.is_(False)
        )
        result = await session.execute(statement)
        count = result.scalar_one()
        return count > 0

    @staticmethod
    async def get_user_general_assistant(session: AsyncSession, user_id: str) -> Optional[Assistant]:
        """
        Get user's general assistant if exists.

        Args:
            session: Database session
            user_id: User ID

        Returns:
            General assistant if exists, None otherwise
        """
        statement = (
            select(Assistant)
            .options(selectinload(Assistant.teams).selectinload(Team.members))
            .where(Assistant.user_id == user_id, Assistant.assistant_type == AssistantType.GENERAL_ASSISTANT, Assistant.is_deleted.is_(False))
        )
        result = await session.execute(statement)
        return result.scalar_one_or_none()

    @staticmethod
    async def create_general_assistant(
        session: AsyncSession,
        user_id: str,
        name: str,
        description: Optional[str] = None,
        system_prompt: Optional[str] = None,
        provider: str = env_settings.OPENAI_PROVIDER,
        model_name: str = env_settings.LLM_BASIC_MODEL,
        temperature: float = env_settings.BASIC_MODEL_TEMPERATURE,
        support_units: Optional[List[WorkflowType]] = None,
    ) -> Assistant:
        """
        Create a general assistant for a user.

        Args:
            session: Database session
            user_id: User ID
            name: Assistant name
            description: Assistant description
            system_prompt: System prompt for the assistant
            provider: AI provider
            model_name: Model name to use
            temperature: Response temperature
            support_units: List of support workflow types

        Returns:
            Created general assistant

        Raises:
            ValueError: If user already has a general assistant
        """
        # Check if user already has a general assistant
        if await GeneralAssistantHelpers.check_user_has_general_assistant(session, user_id):
            raise ValueError("User already has a general assistant")

        # Set default support units if not provided
        if support_units is None:
            support_units = [WorkflowType.RAGBOT, WorkflowType.SEARCHBOT]

        # Create the general assistant instance
        assistant_id = str(uuid.uuid4())
        general_assistant = Assistant(
            id=assistant_id,
            user_id=user_id,
            name=name,
            description=description,
            system_prompt=system_prompt,
            assistant_type=AssistantType.GENERAL_ASSISTANT,
            provider=provider or env_settings.OPENAI_PROVIDER,
            model_name=model_name or env_settings.LLM_BASIC_MODEL,
            temperature=temperature if temperature is not None else env_settings.BASIC_MODEL_TEMPERATURE,
            ask_human=None,
            interrupt=None,
        )
        session.add(general_assistant)
        await session.flush()

        # Create main chatbot team
        await GeneralAssistantHelpers._create_main_chatbot_team(session, general_assistant, provider, model_name, temperature, user_id)

        # Create support teams
        if support_units:
            for workflow_type in support_units:
                await GeneralAssistantHelpers._create_support_team(
                    session, general_assistant, workflow_type, provider, model_name, temperature, user_id
                )

        return general_assistant

    @staticmethod
    async def _create_main_chatbot_team(
        session: AsyncSession, assistant: Assistant, provider: str, model_name: str, temperature: float, user_id: str
    ) -> Team:
        """
        Create the main chatbot team for general assistant.

        Args:
            session: Database session
            assistant: Assistant instance
            request: Creation request
            user_id: User ID

        Returns:
            Created main team
        """
        # Create main chatbot team
        main_team_id = str(uuid.uuid4())
        main_team_name = create_unique_key(id_=main_team_id, name="Main Chatbot Unit")
        main_team = Team(
            id=main_team_id,
            name=main_team_name,
            description="Main chatbot unit for general assistant, handles conversations and general queries.",
            workflow_type=WorkflowType.CHATBOT,
            user_id=user_id,
            assistant_id=assistant.id,
        )
        session.add(main_team)
        await session.flush()  # Create main chatbot member
        await GeneralAssistantHelpers._create_chatbot_member(session, main_team.id, provider, model_name, temperature, user_id)

        return main_team

    @staticmethod
    async def _create_chatbot_member(session: AsyncSession, team_id: str, provider: str, model_name: str, temperature: float, user_id: str) -> Member:
        """
        Create the main chatbot member for general assistant.

        Args:
            session: Database session
            team_id: Team ID
            request: Creation request
            user_id: User ID

        Returns:
            Created chatbot member
        """
        chatbot_member_id = str(uuid.uuid4())
        chatbot_member_name = create_unique_key(id_=chatbot_member_id, name="General Assistant Chatbot")
        chatbot_member = Member(
            id=chatbot_member_id,
            name=chatbot_member_name,
            team_id=team_id,
            backstory="A friendly and helpful general assistant designed to handle conversations, answer questions, and assist users with various tasks using available tools and knowledge.",
            role="Handle general conversations, answer user questions, provide assistance with various tasks, and coordinate with support units when needed. Use search and knowledge tools when appropriate.",
            type="chatbot",
            provider=provider,
            model=model_name,
            temperature=temperature,
            interrupt=False,
            position_x=0.0,
            position_y=0.0,
            created_by=SYSTEM,
        )
        session.add(chatbot_member)
        await session.flush()

        # Add basic search skills to the chatbot
        await GeneralAssistantHelpers._create_search_skills(session, chatbot_member.id, user_id)

        return chatbot_member

    @staticmethod
    async def _create_support_team(
        session: AsyncSession, assistant: Assistant, workflow_type: WorkflowType, provider: str, model_name: str, temperature: float, user_id: str
    ) -> Team:
        """
        Create a support team for specific workflow type.

        Args:
            session: Database session
            assistant: Assistant instance
            workflow_type: Type of support team (RAGBOT or SEARCHBOT)
            request: Creation request
            user_id: User ID

        Returns:
            Created support team
        """
        # Create support team
        support_team_id = str(uuid.uuid4())
        support_team_name = create_unique_key(id_=support_team_id, name=f"{workflow_type.title()} Support Unit")
        support_team = Team(
            id=support_team_id,
            name=support_team_name,
            description=f"Support unit for {workflow_type} in general assistant.",
            workflow_type=workflow_type,
            user_id=user_id,
            assistant_id=assistant.id,
        )
        session.add(support_team)
        await session.flush()

        # Create support team member
        support_member_id = str(uuid.uuid4())
        support_member_name = create_unique_key(id_=support_member_id, name=f"{workflow_type.title()} Assistant")

        # Set backstory and role based on workflow type
        if workflow_type == WorkflowType.RAGBOT:
            backstory = "Specialized in retrieving and processing information from knowledge bases and documents."
            role = "Search through uploaded documents and knowledge bases to find relevant information for user queries."
        elif workflow_type == WorkflowType.SEARCHBOT:
            backstory = "Specialized in searching the internet and external sources for information."
            role = "Search the internet and external sources to find relevant and up-to-date information for user queries."
        else:
            backstory = f"Support unit for {workflow_type} functionality."
            role = "Provide specialized support for user queries."

        support_member = Member(
            id=support_member_id,
            name=support_member_name,
            team_id=support_team.id,
            backstory=backstory,
            role=role,
            type=workflow_type.value,
            provider=provider,
            model=model_name,
            temperature=temperature,
            interrupt=False,
            position_x=0.0,
            position_y=0.0,
            created_by=SYSTEM,
        )
        session.add(support_member)
        await session.flush()

        # Add appropriate skills based on workflow type
        if workflow_type == WorkflowType.SEARCHBOT:
            await GeneralAssistantHelpers._create_search_skills(session, support_member.id, user_id)

        return support_team

    @staticmethod
    async def _create_search_skills(session: AsyncSession, member_id: str, user_id: str) -> None:
        """
        Create search skills for members (both main chatbot and searchbot support).

        Args:
            session: Database session
            member_id: Member ID to assign skills to
            user_id: User ID
        """
        # DuckDuckGo search skill
        ddg_tool_info = global_tools.get("duckduckgo-search")
        if ddg_tool_info:
            ddg_skill_id = str(uuid.uuid4())
            ddg_skill = Skill(
                id=ddg_skill_id,
                name="duckduckgo-search",
                user_id=user_id,
                description=ddg_tool_info.description,
                icon="",
                display_name=ddg_tool_info.display_name,
                strategy=StorageStrategy.GLOBAL_TOOLS,
                input_parameters=ddg_tool_info.input_parameters,
                reference_type=ConnectedServiceType.NONE,
            )
            session.add(ddg_skill)
            await session.flush()

            member_skill_link = MemberSkillLink(
                member_id=member_id,
                skill_id=ddg_skill.id,
            )
            session.add(member_skill_link)
            await session.flush()

        # Wikipedia search skill
        wikipedia_tool_info = global_tools.get("wikipedia")
        if wikipedia_tool_info:
            wikipedia_skill_id = str(uuid.uuid4())
            wikipedia_skill = Skill(
                id=wikipedia_skill_id,
                name="wikipedia",
                user_id=user_id,
                description=wikipedia_tool_info.description,
                icon="",
                display_name=wikipedia_tool_info.display_name,
                strategy=StorageStrategy.GLOBAL_TOOLS,
                input_parameters=wikipedia_tool_info.input_parameters,
                reference_type=ConnectedServiceType.NONE,
            )
            session.add(wikipedia_skill)
            await session.flush()

            member_skill_link = MemberSkillLink(
                member_id=member_id,
                skill_id=wikipedia_skill.id,
            )
            session.add(member_skill_link)
            await session.flush()

    @staticmethod
    async def delete_general_assistant(session: AsyncSession, user_id: str) -> bool:
        """
        Delete user's general assistant and all related entities.

        Args:
            session: Database session
            user_id: User ID

        Returns:
            True if deleted successfully, False if not found
        """
        # Get the general assistant
        general_assistant = await GeneralAssistantHelpers.get_user_general_assistant(session, user_id)
        if not general_assistant:
            return False

        # Use the existing cascade delete helper from assistant API
        # This will properly delete all related entities
        from app.api.public.v1.assistant import _ahard_delete_assistant_cascade

        await _ahard_delete_assistant_cascade(session, general_assistant.id)

        return True

    @staticmethod
    async def ensure_user_has_general_assistant(session: AsyncSession, user_id: str, user_name: str = "User") -> Assistant:
        """
        Ensure user has a general assistant. Create one if it doesn't exist.

        Args:
            session: Database session
            user_id: User ID
            user_name: User's display name for personalization

        Returns:
            User's general assistant (existing or newly created)
        """
        try:
            # Check if user already has a general assistant
            existing_assistant = await GeneralAssistantHelpers.get_user_general_assistant(session, user_id)
            if existing_assistant:
                return existing_assistant  # Create new general assistant with default configuration
            general_assistant = await GeneralAssistantHelpers.create_general_assistant(
                session=session,
                user_id=user_id,
                name=f"{user_name}'s General Assistant",
                description="A helpful general assistant for everyday tasks and conversations.",
                system_prompt="You are a helpful, friendly, and knowledgeable general assistant. Help users with their questions, tasks, and conversations. Use your available tools when needed to provide accurate and helpful information.",
                provider=env_settings.OPENAI_PROVIDER,
                model_name=env_settings.LLM_BASIC_MODEL,
                temperature=env_settings.BASIC_MODEL_TEMPERATURE,
                support_units=[WorkflowType.RAGBOT, WorkflowType.SEARCHBOT],
            )

            # Commit the creation
            await session.commit()

            logger.info(f"Created general assistant for user {user_id}")
            return general_assistant

        except Exception as e:
            logger.error(f"Error ensuring general assistant for user {user_id}: {e}")
            await session.rollback()
            raise

    @staticmethod
    async def get_general_assistant_with_teams(session: AsyncSession, user_id: str) -> Optional[Assistant]:
        """
        Get user's general assistant with teams loaded.

        Args:
            session: Database session
            user_id: User ID

        Returns:
            General assistant with teams, or None if not found
        """
        return await GeneralAssistantHelpers.get_user_general_assistant(session, user_id)

    @staticmethod
    def format_general_assistant_teams(teams: List[Team]) -> List[Dict[str, Any]]:
        """
        Format teams data for general assistant response.

        Args:
            teams: List of team objects

        Returns:
            Formatted teams data
        """
        formatted_teams = []

        for team in teams:
            team_data = {"id": team.id, "name": team.name, "description": team.description, "workflow_type": team.workflow_type, "members": []}

            # Format members
            for member in team.members or []:
                member_data = {
                    "id": member.id,
                    "name": member.name,
                    "role": member.role,
                    "type": member.type,
                    "backstory": member.backstory,
                    "provider": member.provider,
                    "model": member.model,
                    "temperature": member.temperature,
                }
                team_data["members"].append(member_data)

            formatted_teams.append(team_data)

        return formatted_teams

    @staticmethod
    async def format_general_assistant_response(session: AsyncSession, assistant: Assistant) -> GetGeneralAssistantResponse:
        """
        Format general assistant for API response.

        Args:
            session: Database session
            assistant: General assistant instance

        Returns:
            Formatted general assistant response
        """
        # Ensure teams are loaded
        if not assistant.teams:
            statement = select(Assistant).options(selectinload(Assistant.teams).selectinload(Team.members)).where(Assistant.id == assistant.id)
            result = await session.execute(statement)
            assistant = result.scalar_one()

        # Format teams data
        teams_data = GeneralAssistantHelpers.format_general_assistant_teams(assistant.teams or [])

        return GetGeneralAssistantResponse(
            id=assistant.id,
            user_id=assistant.user_id,
            name=assistant.name,
            assistant_type=assistant.assistant_type,
            description=assistant.description,
            system_prompt=assistant.system_prompt,
            provider=assistant.provider or env_settings.OPENAI_PROVIDER,
            model_name=assistant.model_name or env_settings.LLM_BASIC_MODEL,
            temperature=assistant.temperature or env_settings.BASIC_MODEL_TEMPERATURE,
            main_unit=WorkflowType.CHATBOT,
            support_units=[WorkflowType.RAGBOT, WorkflowType.SEARCHBOT],
            teams=teams_data,
            created_at=assistant.created_at,
            ask_human=None,
            interrupt=None,
        )

    @staticmethod
    async def initialize_general_assistant_for_new_user(session: AsyncSession, user_id: str, user_name: str = "User") -> bool:
        """
        Initialize general assistant for a new user during user registration/first login.

        Args:
            session: Database session
            user_id: New user's ID
            user_name: User's display name

        Returns:
            True if successfully initialized, False otherwise
        """
        try:
            # Check if user already has a general assistant (shouldn't happen for new users)
            if await GeneralAssistantHelpers.check_user_has_general_assistant(session, user_id):
                logger.warning(f"User {user_id} already has a general assistant")
                return True

            # Create general assistant
            await GeneralAssistantHelpers.ensure_user_has_general_assistant(session, user_id, user_name)

            logger.info(f"Successfully initialized general assistant for new user {user_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize general assistant for new user {user_id}: {e}")
            return False

    @staticmethod
    async def cleanup_general_assistant(session: AsyncSession, user_id: str) -> bool:
        """
        Clean up user's general assistant (for user deletion scenarios).

        Args:
            session: Database session
            user_id: User ID

        Returns:
            True if successfully cleaned up, False otherwise
        """
        try:
            success = await GeneralAssistantHelpers.delete_general_assistant(session, user_id)
            if success:
                await session.commit()
                logger.info(f"Successfully cleaned up general assistant for user {user_id}")
            else:
                logger.info(f"No general assistant found for user {user_id} during cleanup")

            return True

        except Exception as e:
            logger.error(f"Failed to cleanup general assistant for user {user_id}: {e}")
            await session.rollback()
            return False

    @staticmethod
    def extract_support_units_from_general_assistant(assistant: Assistant) -> List[WorkflowType]:
        """
        Extract support units from general assistant.
        For general assistants, this is always [RAGBOT, SEARCHBOT].

        Args:
            assistant: General assistant instance

        Returns:
            List of support workflow types
        """
        if assistant.assistant_type != AssistantType.GENERAL_ASSISTANT:
            raise ValueError("This helper is only for general assistants")

        return [WorkflowType.RAGBOT, WorkflowType.SEARCHBOT]

    @staticmethod
    async def get_general_assistant_status(session: AsyncSession, user_id: str) -> Dict[str, Any]:
        """
        Get status information about user's general assistant.

        Args:
            session: Database session
            user_id: User ID

        Returns:
            Status information dictionary
        """
        try:
            assistant = await GeneralAssistantHelpers.get_user_general_assistant(session, user_id)

            if not assistant:
                return {"exists": False, "message": "No general assistant found for user"}

            # Count teams and members
            team_count = len(assistant.teams or [])
            member_count = sum(len(team.members or []) for team in (assistant.teams or []))

            return {
                "exists": True,
                "assistant_id": assistant.id,
                "name": assistant.name,
                "created_at": assistant.created_at,
                "team_count": team_count,
                "member_count": member_count,
                "main_unit": WorkflowType.CHATBOT.value,
                "support_units": [unit.value for unit in [WorkflowType.RAGBOT, WorkflowType.SEARCHBOT]],
                "provider": assistant.provider,
                "model_name": assistant.model_name,
            }

        except Exception as e:
            logger.error(f"Error getting general assistant status for user {user_id}: {e}")
            return {"exists": False, "error": str(e)}


# Public utility functions for external use
async def ensure_user_general_assistant(session: AsyncSession, user_id: str, user_name: str = "User") -> Optional[Assistant]:
    """
    Ensure a user has a general assistant. This is the main entry point
    for other services to ensure general assistant exists.

    Args:
        session: Database session
        user_id: User ID
        user_name: User's display name for personalization

    Returns:
        General assistant if successful, None if failed
    """
    try:
        return await GeneralAssistantHelpers.ensure_user_has_general_assistant(session, user_id, user_name)
    except Exception as e:
        logger.error(f"Failed to ensure general assistant for user {user_id}: {e}")
        return None


async def get_user_general_assistant(session: AsyncSession, user_id: str) -> Optional[Assistant]:
    """
    Get user's general assistant if it exists.

    Args:
        session: Database session
        user_id: User ID

    Returns:
        General assistant if exists, None otherwise
    """
    try:
        return await GeneralAssistantHelpers.get_general_assistant_with_teams(session, user_id)
    except Exception as e:
        logger.error(f"Failed to get general assistant for user {user_id}: {e}")
        return None


async def initialize_general_assistant_for_new_user(session: AsyncSession, user_id: str, user_name: str = "User") -> bool:
    """
    Initialize general assistant for a new user. Call this during user registration.

    Args:
        session: Database session
        user_id: New user's ID
        user_name: User's display name

    Returns:
        True if successful, False otherwise
    """
    try:
        return await GeneralAssistantHelpers.initialize_general_assistant_for_new_user(session, user_id, user_name)
    except Exception as e:
        logger.error(f"Failed to initialize general assistant for new user {user_id}: {e}")
        return False


async def cleanup_user_general_assistant(session: AsyncSession, user_id: str) -> bool:
    """
    Clean up user's general assistant. Call this during user deletion.

    Args:
        session: Database session
        user_id: User ID

    Returns:
        True if successful, False otherwise
    """
    try:
        return await GeneralAssistantHelpers.cleanup_general_assistant(session, user_id)
    except Exception as e:
        logger.error(f"Failed to cleanup general assistant for user {user_id}: {e}")
        return False
