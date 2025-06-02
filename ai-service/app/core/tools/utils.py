from sqlmodel import select

from app.core.db_session import get_db_session
from app.db_models.skill import Skill


async def aget_tool_credentials(tool_name: str) -> dict:
    session = await anext(get_db_session())
    result = await session.execute(select(Skill).where(Skill.display_name == tool_name))
    skill = result.first()
    if skill and skill.credentials:
        return skill.credentials
    return {}


async def aget_credential_value(tool_name: str, credential_key: str) -> str:
    credentials = await aget_tool_credentials(tool_name)
    return credentials.get(credential_key, {}).get("value", "")
