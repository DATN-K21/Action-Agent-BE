"""
Helper functions for loading tools into cache based on skills.
"""

from sqlalchemy import select

from app.core import logging
from app.core.db_session import AsyncSessionLocal
from app.core.enums import ConnectedServiceType
from app.core.tools.tool_manager import tool_manager
from app.core.utils.convert_type import convert_base_tool_to_tool_info
from app.db_models.connected_extension import ConnectedExtension
from app.db_models.connected_mcp import ConnectedMcp
from app.db_models.member_skill_link import MemberSkillLink
from app.db_models.skill import Skill
from app.services.extensions import extension_service_manager
from app.services.mcps.mcp_service import McpService

logger = logging.get_logger(__name__)


async def aload_tools_to_cache_by_skill(skill_id: str, member_id: str) -> None:
    """
    Load tools into cache based on a skill ID and member ID.

    This function:
    1. Gets the skill from skill_id to determine if it belongs to MCP or extension
    2. Loads all tools from the corresponding MCP or extension
    3. Gets all skills from member_id that have the same reference_type and same reference ID
    4. Caches each tool based on the name of each skill

    Args:
        skill_id: The ID of the skill to determine the service type and reference
        member_id: The ID of the member to find related skills for caching

    Raises:
        ValueError: If skill not found, invalid reference type, or service not found
        Exception: If database operations fail
    """
    async with AsyncSessionLocal() as session:
        try:
            # Step 1: Get the skill to determine service type and reference
            skill_statement = select(Skill).where(Skill.id == skill_id, Skill.is_deleted.is_(False))

            result = await session.execute(skill_statement)
            skill = result.scalar_one_or_none()

            if not skill:
                raise ValueError(f"Skill with ID {skill_id} not found or is deleted")

            logger.info(f"Found skill '{skill.name}' with reference_type: {skill.reference_type}")

            # Step 2: Load tools based on reference type
            if skill.reference_type == ConnectedServiceType.MCP:
                if not skill.mcp_id:
                    raise ValueError(f"Skill {skill_id} has MCP reference type but no mcp_id")

                await _aload_mcp_tools_to_cache(session, skill.mcp_id, member_id)

            elif skill.reference_type == ConnectedServiceType.EXTENSION:
                if not skill.extension_id:
                    raise ValueError(f"Skill {skill_id} has extension reference type but no extension_id")

                await _aload_extension_tools_to_cache(session, skill.extension_id, member_id)

            else:
                logger.warning(f"Skill {skill_id} has reference_type {skill.reference_type}, no tools to cache")
                return

            logger.info(f"Successfully loaded tools to cache for skill {skill_id} and member {member_id}")

        except Exception as e:
            logger.error(f"Error loading tools to cache for skill {skill_id}: {e}")
            raise


async def _aload_mcp_tools_to_cache(session, mcp_id: str, member_id: str) -> None:
    """
    Load MCP tools to cache for related skills.

    Args:
        session: Database session
        mcp_id: The ID of the MCP connection
        member_id: The ID of the member to find related skills
    """
    # Get the MCP connection details
    mcp_statement = select(ConnectedMcp).where(ConnectedMcp.id == mcp_id, ConnectedMcp.is_deleted.is_(False))

    result = await session.execute(mcp_statement)
    connected_mcp = result.scalar_one_or_none()

    if not connected_mcp:
        raise ValueError(f"Connected MCP with ID {mcp_id} not found or is deleted")

    logger.info(f"Loading MCP tools for connection '{connected_mcp.mcp_name}'")
    # Prepare connection configuration for MCP service
    connections = {
        connected_mcp.mcp_name: {
            "url": connected_mcp.url,
            "transport": connected_mcp.transport.value,  # Convert enum to string
        }
    }
    # Get tool information from MCP service
    tool_infos = await McpService.aget_mcp_tool_info(connections=connections)  # type: ignore
    logger.info(f"Retrieved {len(tool_infos)} tools from MCP service")

    # Get all skills from member that have the same MCP reference
    related_skills = await _aget_related_skills_by_reference(session, member_id, ConnectedServiceType.MCP, mcp_id)

    # Create a mapping of tool display names to tool infos for efficient lookup
    tool_by_display_name = {tool_info.display_name: tool_info for tool_info in tool_infos}

    # Cache tools for each related skill
    cached_count = 0
    for skill in related_skills:
        # Find matching tool by display name
        matching_tool_info = tool_by_display_name.get(skill.display_name)
        if matching_tool_info:
            # Add tool to cache
            await tool_manager.aadd_personal_tool(
                user_id=skill.user_id,
                tool_key=skill.name,
                tool_info=matching_tool_info,
            )

            cached_count += 1
            logger.debug(f"Cached MCP tool '{skill.display_name}' with key '{skill.name}' for user {skill.user_id}")
        else:
            logger.warning(f"No matching MCP tool found for skill '{skill.display_name}' (ID: {skill.id})")

    logger.info(f"Successfully cached {cached_count} MCP tools for member {member_id}")


async def _aload_extension_tools_to_cache(session, extension_id: str, member_id: str) -> None:
    """
    Load extension tools to cache for related skills.

    Args:
        session: Database session
        extension_id: The ID of the extension connection
        member_id: The ID of the member to find related skills
    """
    # Get the extension connection details
    extension_statement = select(ConnectedExtension).where(ConnectedExtension.id == extension_id, ConnectedExtension.is_deleted.is_(False))

    result = await session.execute(extension_statement)
    connected_extension = result.scalar_one_or_none()

    if not connected_extension:
        raise ValueError(f"Connected extension with ID {extension_id} not found or is deleted")

    logger.info(f"Loading extension tools for '{connected_extension.extension_name}'")

    # Get extension service info
    extension_service_info = extension_service_manager.get_service_info(service_enum=connected_extension.extension_enum)

    if not extension_service_info or not extension_service_info.service_object:
        raise ValueError(f"Extension service info for {connected_extension.extension_enum} not found or service object is None")

    # Get authenticated tools from extension service
    extension_service = extension_service_info.service_object
    tools = extension_service.get_authed_tools(user_id=connected_extension.user_id)

    # Convert BaseTool instances to ToolInfo instances
    tool_infos = [convert_base_tool_to_tool_info(tool) for tool in tools]
    logger.info(f"Retrieved {len(tool_infos)} tools from extension service")

    # Get all skills from member that have the same extension reference
    related_skills = await _aget_related_skills_by_reference(session, member_id, ConnectedServiceType.EXTENSION, extension_id)

    # Create a mapping of tool display names to tool infos for efficient lookup
    tool_by_display_name = {tool_info.display_name: tool_info for tool_info in tool_infos}

    # Cache tools for each related skill
    cached_count = 0
    for skill in related_skills:
        # Find matching tool by display name
        matching_tool_info = tool_by_display_name.get(skill.display_name)
        if matching_tool_info:
            # Add tool to cache
            await tool_manager.aadd_personal_tool(
                user_id=skill.user_id,
                tool_key=skill.name,
                tool_info=matching_tool_info,
            )

            cached_count += 1
            logger.debug(f"Cached extension tool '{skill.display_name}' with key '{skill.name}' for user {skill.user_id}")
        else:
            logger.warning(f"No matching extension tool found for skill '{skill.display_name}' (ID: {skill.id})")

    logger.info(f"Successfully cached {cached_count} extension tools for member {member_id}")


async def _aget_related_skills_by_reference(session, member_id: str, reference_type: ConnectedServiceType, reference_id: str) -> list[Skill]:
    """
    Get all skills from a member that have the same reference type and reference ID.

    Args:
        session: Database session
        member_id: The ID of the member
        reference_type: The type of connected service (MCP or EXTENSION)
        reference_id: The ID of the connected service (mcp_id or extension_id)

    Returns:
        List of skills that match the criteria
    """
    # Build query based on reference type
    if reference_type == ConnectedServiceType.MCP:
        skills_statement = (
            select(Skill)
            .select_from(Skill)
            .join(MemberSkillLink, Skill.id == MemberSkillLink.skill_id)
            .where(
                MemberSkillLink.member_id == member_id,
                Skill.reference_type == ConnectedServiceType.MCP,
                Skill.mcp_id == reference_id,
                Skill.is_deleted.is_(False),
            )
        )
    elif reference_type == ConnectedServiceType.EXTENSION:
        skills_statement = (
            select(Skill)
            .select_from(Skill)
            .join(MemberSkillLink, Skill.id == MemberSkillLink.skill_id)
            .where(
                MemberSkillLink.member_id == member_id,
                Skill.reference_type == ConnectedServiceType.EXTENSION,
                Skill.extension_id == reference_id,
                Skill.is_deleted.is_(False),
            )
        )
    else:
        return []

    result = await session.execute(skills_statement)
    skills = result.scalars().all()

    logger.info(f"Found {len(skills)} related skills for member {member_id} with {reference_type} reference {reference_id}")

    return list(skills)


async def apreload_member_tools_cache(member_id: str) -> None:
    """
    Preload all MCP and extension tools for a member into cache.

    This function finds all MCP and extension skills for a member and loads
    the corresponding tools into cache.

    Args:
        member_id: The ID of the member to preload tools for

    Raises:
        ValueError: If member not found or no skills found
        Exception: If database operations or tool loading fails
    """
    async with AsyncSessionLocal() as session:
        try:
            # Get all MCP and extension skills for the member
            skills_statement = (
                select(Skill)
                .select_from(Skill)
                .join(MemberSkillLink, Skill.id == MemberSkillLink.skill_id)
                .where(
                    MemberSkillLink.member_id == member_id,
                    Skill.reference_type.in_([ConnectedServiceType.MCP, ConnectedServiceType.EXTENSION]),
                    Skill.is_deleted.is_(False),
                )
            )

            result = await session.execute(skills_statement)
            skills = result.scalars().all()

            if not skills:
                logger.info(f"No MCP or extension skills found for member {member_id}")
                return

            logger.info(f"Found {len(skills)} MCP/extension skills for member {member_id}")

            # Group skills by reference type and reference ID
            mcp_groups = {}
            extension_groups = {}

            for skill in skills:
                if skill.reference_type == ConnectedServiceType.MCP and skill.mcp_id:
                    if skill.mcp_id not in mcp_groups:
                        mcp_groups[skill.mcp_id] = []
                    mcp_groups[skill.mcp_id].append(skill)
                elif skill.reference_type == ConnectedServiceType.EXTENSION and skill.extension_id:
                    if skill.extension_id not in extension_groups:
                        extension_groups[skill.extension_id] = []
                    extension_groups[skill.extension_id].append(skill)

            # Load MCP tools
            for mcp_id in mcp_groups:
                logger.info(f"Loading MCP tools for connection {mcp_id}")
                await _aload_mcp_tools_to_cache(session, mcp_id, member_id)

            # Load extension tools
            for extension_id in extension_groups:
                logger.info(f"Loading extension tools for connection {extension_id}")
                await _aload_extension_tools_to_cache(session, extension_id, member_id)

            logger.info(f"Successfully preloaded all tools for member {member_id}")

        except Exception as e:
            logger.error(f"Error preloading tools for member {member_id}: {e}", exc_info=True)
            raise
