from sqlalchemy import select

from app.core.db_session import AsyncSessionLocal
from app.db_models.skill import Skill


async def aget_tool_credentials(tool_name: str) -> dict:
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Skill).where(Skill.display_name == tool_name, Skill.is_deleted.is_(False)))
        skill = result.scalar_one_or_none()
        if skill and skill.credentials is not None:
            return skill.credentials  # type: ignore
        return {}


async def aget_credential_value(tool_name: str, credential_key: str) -> str:
    credentials = await aget_tool_credentials(tool_name)
    return credentials.get(credential_key, {}).get("value", "")
