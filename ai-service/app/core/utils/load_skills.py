import uuid

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.db_session import AsyncSessionLocal
from app.core.enums import ConnectedServiceType, StorageStrategy
from app.core.tools.tool_manager import create_unique_key, global_tools, tool_manager
from app.core.utils.convert_type import convert_base_tool_to_tool_info
from app.db_models.connected_extension import ConnectedExtension
from app.db_models.connected_mcp import ConnectedMcp
from app.db_models.member import Member
from app.db_models.member_skill_link import MemberSkillLink
from app.db_models.skill import Skill
from app.services.extensions import extension_service_manager
from app.services.mcps.mcp_service import McpService


async def aload_skills(member_id: str, mcp: str | ConnectedMcp | None, extension: str | ConnectedExtension | None):
    if mcp is not None and extension is not None:
        raise ValueError("Only one of mcp or extension can be provided, not both.")

    async with AsyncSessionLocal() as session:
        try:
            # Get member
            statement = select(Member).select_from(Member).where(Member.id == member_id, Member.is_deleted.is_(False))

            result = await session.execute(statement)
            member = result.scalar_one_or_none()
            if not member:
                raise ValueError(f"Member with ID {member_id} not found or is deleted.")

            if mcp:
                if isinstance(mcp, str):
                    # mcp is a string, assume it's an ID
                    mcp_id = mcp
                    statement = select(ConnectedMcp).where(ConnectedMcp.id == mcp_id, ConnectedMcp.is_deleted.is_(False))

                    result = await session.execute(statement)
                    mcp = result.scalar_one_or_none()

                    if not mcp:
                        raise ValueError(f"MCP with ID {mcp} not found or is deleted.")

                # Now, mcp is an instance of ConnectedMcp. Let us proceed to load skills.
                connections = {}
                connections[mcp.mcp_name] = {
                    "url": mcp.url,
                    "transport": mcp.transport,
                }

                tool_infos = await McpService.aget_mcp_tool_info(connections=connections)

                # Create skills
                for tool_info in tool_infos:
                    # Create skill
                    skill = Skill(
                        id=str(uuid.uuid4()),
                        user_id=str(mcp.user_id),
                        name=tool_info.display_name,
                        description=tool_info.description,
                        icon="",
                        display_name=tool_info.display_name,
                        strategy=StorageStrategy.PERSONAL_TOOL_CACHE,
                        input_parameters=tool_info.input_parameters,
                        reference_type=ConnectedServiceType.MCP,
                        mcp_id=mcp.id,
                    )
                    session.add(skill)

                    # Add link to member
                    member_skill_link = MemberSkillLink(
                        member_id=member.id,
                        skill_id=skill.id,
                    )
                    session.add(member_skill_link)

                    # Add tool to cache
                    tool_manager.add_personal_tool(
                        user_id=str(mcp.user_id),
                        tool_key=create_unique_key(id_=str(skill.id), name=str(skill.name)),
                        tool_info=tool_info,
                    )

            elif extension:
                if isinstance(extension, str):
                    # extension is a string, assume it's an ID
                    extension_id = extension
                    statement = select(ConnectedExtension).where(ConnectedExtension.id == extension_id, ConnectedExtension.is_deleted.is_(False))

                    result = await session.execute(statement)
                    extension = result.scalar_one_or_none()
                    if not extension:
                        raise ValueError(f"Extension with ID {extension} not found or is deleted.")

                # Now, extension is an instance of ConnectedExtension. Let us proceed to load skills.
                extension_service_info = extension_service_manager.get_service_info(service_enum=str(extension.extension_enum))

                if not extension_service_info or not extension_service_info.service_object:
                    raise ValueError(f"Extension service info for {extension.extension_enum} not found or service object is None.")

                extension_service = extension_service_info.service_object
                tools = extension_service.get_authed_tools(user_id=str(extension.user_id))

                tool_infos = [convert_base_tool_to_tool_info(tool) for tool in tools]

                for tool_info in tool_infos:
                    # Create skill
                    skill = Skill(
                        id=str(uuid.uuid4()),
                        user_id=str(extension.user_id),
                        name=tool_info.display_name,
                        description=tool_info.description,
                        icon="",
                        display_name=tool_info.display_name,
                        strategy=StorageStrategy.PERSONAL_TOOL_CACHE,
                        input_parameters=tool_info.input_parameters,
                        reference_type=ConnectedServiceType.EXTENSION,
                        extension_id=extension.id,
                    )
                    session.add(skill)

                    # Add link to member
                    member_skill_link = MemberSkillLink(
                        member_id=member.id,
                        skill_id=skill.id,
                    )
                    session.add(member_skill_link)

                    # Add tool to cache
                    tool_manager.add_personal_tool(
                        user_id=str(extension.user_id),
                        tool_key=create_unique_key(id_=str(skill.id), name=str(skill.name)),
                        tool_info=tool_info,
                    )

            await session.commit()
        except:
            await session.rollback()
            raise


async def aload_skills_for_chatbot(member_id: str):
    async with AsyncSessionLocal() as session:
        try:
            # Get member
            statement = (
                select(Member).select_from(Member).options(selectinload(Member.team)).where(Member.id == member_id, Member.is_deleted.is_(False))
            )

            result = await session.execute(statement)
            member = result.scalar_one_or_none()
            if not member:
                raise ValueError(f"Member with ID {member_id} not found or is deleted.")

            if member.team.user_id is None:
                raise ValueError("User ID for member's team is None.")

            # Create a skill for the chatbot

            # RAG tool
            rag_skill = Skill(
                id=str(uuid.uuid4()),
                user_id=str(member.team.user_id),
                name="KnowledgeBase",
                description="Query documents for answers.",
                icon="",
                display_name="Knowledge Base",
                strategy=StorageStrategy.PERSONAL_TOOL_CACHE,
                input_parameters={},
                reference_type=ConnectedServiceType.NONE,
            )
            session.add(rag_skill)

            # Add link to member
            member_skill_link = MemberSkillLink(
                member_id=member.id,
                skill_id=rag_skill.id,
            )
            session.add(member_skill_link)

            # Wikipedia tool
            ddg_tool_info = global_tools.get("duckduckgo-search")
            if not ddg_tool_info:
                raise ValueError("DuckDuckGo search tool not found in global tools.")

            ddg_skill = Skill(
                id=str(uuid.uuid4()),
                user_id=str(member.team.user_id),
                name=ddg_tool_info.display_name,
                description=ddg_tool_info.description,
                icon="",
                display_name=ddg_tool_info.display_name,
                strategy=StorageStrategy.GLOBAL_TOOLS,
                input_parameters=ddg_tool_info.input_parameters,
                reference_type=ConnectedServiceType.NONE,
            )
            session.add(ddg_skill)

            # Add link to member
            member_skill_link = MemberSkillLink(
                member_id=member.id,
                skill_id=ddg_skill.id,
            )
            session.add(member_skill_link)

            # Wikipedia tool
            wikipedia_tool_info = global_tools.get("wikipedia")
            if not wikipedia_tool_info:
                raise ValueError("Wikipedia tool not found in global tools.")
            wikipedia_skill = Skill(
                id=str(uuid.uuid4()),
                user_id=str(member.team.user_id),
                name=wikipedia_tool_info.display_name,
                description=wikipedia_tool_info.description,
                icon="",
                display_name=wikipedia_tool_info.display_name,
                strategy=StorageStrategy.GLOBAL_TOOLS,
                input_parameters=wikipedia_tool_info.input_parameters,
                reference_type=ConnectedServiceType.NONE,
            )
            session.add(wikipedia_skill)

            # Add link to member
            member_skill_link = MemberSkillLink(
                member_id=member.id,
                skill_id=wikipedia_skill.id,
            )
            session.add(member_skill_link)

            # Successfully loaded skills for chatbot
            # Commit the session
            await session.commit()
        except:
            await session.rollback()
            raise


async def aload_skills_for_rag(member_id: str):
    async with AsyncSessionLocal() as session:
        try:
            # Get member
            statement = (
                select(Member).select_from(Member).options(selectinload(Member.team)).where(Member.id == member_id, Member.is_deleted.is_(False))
            )

            result = await session.execute(statement)
            member = result.scalar_one_or_none()
            if not member:
                raise ValueError(f"Member with ID {member_id} not found or is deleted.")

            # Create a skill for the RAG tool
            rag_skill = Skill(
                id=str(uuid.uuid4()),
                user_id=str(member.team.user_id),
                name="KnowledgeBase",
                description="Query documents for answers.",
                icon="",
                display_name="Knowledge Base",
                strategy=StorageStrategy.PERSONAL_TOOL_CACHE,
                input_parameters={},
                reference_type=ConnectedServiceType.NONE,
            )
            session.add(rag_skill)

            # Add link to member
            member_skill_link = MemberSkillLink(
                member_id=member.id,
                skill_id=rag_skill.id,
            )
            session.add(member_skill_link)

            # Commit the session
            await session.commit()
        except:
            await session.rollback()
            raise

async def aload_skills_for_searchbot(member_id: str):
    async with AsyncSessionLocal() as session:
        try:
            # Get member
            statement = (
                select(Member).select_from(Member).options(selectinload(Member.team)).where(Member.id == member_id, Member.is_deleted.is_(False))
            )

            result = await session.execute(statement)
            member = result.scalar_one_or_none()
            if not member:
                raise ValueError(f"Member with ID {member_id} not found or is deleted.")

            # DDG tool
            ddg_tool_info = global_tools.get("duckduckgo-search")
            if not ddg_tool_info:
                raise ValueError("DuckDuckGo search tool not found in global tools.")

            ddg_skill = Skill(
                id=str(uuid.uuid4()),
                user_id=str(member.team.user_id),
                name=ddg_tool_info.display_name,
                description=ddg_tool_info.description,
                icon="",
                display_name=ddg_tool_info.display_name,
                strategy=StorageStrategy.GLOBAL_TOOLS,
                input_parameters=ddg_tool_info.input_parameters,
                reference_type=ConnectedServiceType.NONE,
            )
            session.add(ddg_skill)

            # Add link to member
            member_skill_link = MemberSkillLink(
                member_id=member.id,
                skill_id=ddg_skill.id,
            )
            session.add(member_skill_link)

            # Wikipedia tool
            wikipedia_tool_info = global_tools.get("wikipedia")
            if not wikipedia_tool_info:
                raise ValueError("Wikipedia tool not found in global tools.")
            wikipedia_skill = Skill(
                id=str(uuid.uuid4()),
                user_id=str(member.team.user_id),
                name=wikipedia_tool_info.display_name,
                description=wikipedia_tool_info.description,
                icon="",
                display_name=wikipedia_tool_info.display_name,
                strategy=StorageStrategy.GLOBAL_TOOLS,
                input_parameters=wikipedia_tool_info.input_parameters,
                reference_type=ConnectedServiceType.NONE,
            )
            session.add(wikipedia_skill)

            # Add link to member
            member_skill_link = MemberSkillLink(
                member_id=member.id,
                skill_id=wikipedia_skill.id,
            )
            session.add(member_skill_link)

            # Commit the session
            await session.commit()
        except:
            await session.rollback()
            raise