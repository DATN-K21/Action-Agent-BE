from datetime import datetime
from typing import Any

from fastapi import APIRouter, Header, HTTPException
from pydantic import ValidationError
from sqlalchemy import func, or_, select, update

from app.api.deps import SessionDep
from app.core import logging
from app.core.enums import StorageStrategy
from app.core.tools.api_tool import ToolDefinition
from app.core.tools.tool_invoker import ToolInvokeResponse, invoke_tool
from app.db_models import Skill
from app.schemas.base import MessageResponse, ResponseWrapper
from app.schemas.skill import CreateSkillRequest, SkillResponse, SkillsResponse, SkillUpdateRequest, ValidateToolDefinitionRequest

logger = logging.get_logger(__name__)

router = APIRouter()


def validate_tool_definition(tool_definition: dict[str, Any]) -> ToolDefinition | None:
    """
    Validates the tool_definition.
    Raises an HTTPException with messaged validation errors if invalid.
    """
    try:
        return ToolDefinition.model_validate(tool_definition)
    except ValidationError as e:
        error_messages = []
        for error in e.errors():
            loc = " -> ".join(map(str, error["loc"]))
            msg = error["msg"]
            error_messages.append(f"Field '{loc}': {msg}")
        raise HTTPException(status_code=400, detail="; ".join(error_messages))


@router.get("/", response_model=ResponseWrapper[SkillsResponse])
async def aread_skills(
    session: SessionDep,
    skip: int = 0,
    limit: int = 100,
    x_user_id: str = Header(None),
    x_user_role: str = Header(None),
) -> Any:
    """
    Retrieve skills
    """
    try:
        if x_user_role in ["admin", "super_admin"]:
            count_statement = select(func.count()).select_from(Skill.__table__).where(Skill.is_deleted.is_(False))
            result = await session.execute(count_statement)
            count = result.scalar_one()
            statement = select(Skill).where(Skill.is_deleted.is_(False)).order_by(Skill.id.desc()).offset(skip).limit(limit)
        else:
            count_statement = (
                select(func.count())
                .select_from(Skill.__table__)
                .where(or_(Skill.strategy == StorageStrategy.GLOBAL_TOOLS, Skill.user_id == x_user_id), Skill.is_deleted.is_(False))
            )
            result = await session.execute(count_statement)
            count = result.scalar_one()

            statement = (
                select(Skill)
                .where(or_(Skill.strategy == StorageStrategy.GLOBAL_TOOLS, Skill.user_id == x_user_id), Skill.is_deleted.is_(False))
                .order_by(Skill.id.desc())
                .offset(skip)
                .limit(limit)
            )

        result = await session.execute(statement)
        skills = result.scalars().all()
        converted_skills = [SkillResponse.model_validate(skill) for skill in skills]
        data = SkillsResponse(skills=converted_skills, count=count)
        return ResponseWrapper(status=200, data=data).to_response()

    except Exception as e:
        logger.error(f"Error retrieving skills: {str(e)}")
        return ResponseWrapper(status=500, message="Internal Server Error").to_response()


@router.get("/{skill_id}", response_model=ResponseWrapper[SkillResponse])
async def aread_skill(session: SessionDep, skill_id: str, x_user_id: str = Header(None), x_user_role: str = Header(None)) -> Any:
    """
    Get skill by ID.
    """
    try:
        statement = select(Skill).where(Skill.id == skill_id, Skill.is_deleted.is_(False))
        result = await session.execute(statement)
        skill = result.scalar_one_or_none()

        if not skill:
            return ResponseWrapper(status=404, message="Skill not found")
        if (
            x_user_id not in ["admin", "super admin"]
            and str(skill.strategy) != str(StorageStrategy.GLOBAL_TOOLS)
            and (str(skill.user_id) != x_user_id)
        ):
            return ResponseWrapper(status=403, message="Not enough permissions")

        data = SkillResponse.model_validate(skill)
        return ResponseWrapper(status=200, data=data).to_response()
    except Exception as e:
        logger.error(f"Error retrieving skill with ID {skill_id}: {str(e)}")
        return ResponseWrapper(status=500, message="Internal Server Error").to_response()


@router.post("/", response_model=ResponseWrapper[SkillResponse])
async def acreate_skill(
    session: SessionDep,
    skill_in: CreateSkillRequest,
    x_user_id: str = Header(None),
) -> Any:
    """
    Create new skill.
    """
    try:
        validate_tool_definition(skill_in.tool_definition)

        skill_data = skill_in.model_dump(exclude_unset=True)
        skill_data["user_id"] = x_user_id
        skill = Skill(**skill_data)
        session.add(skill)
        await session.commit()
        await session.refresh(skill)

        data = SkillResponse.model_validate(skill)
        return ResponseWrapper(status=200, data=data).to_response()
    except Exception as e:
        logger.error(f"Error creating new skill: {str(e)}")
        await session.rollback()
        return ResponseWrapper(status=500, message="Internal Server Error")


@router.patch("/{skill_id}", response_model=ResponseWrapper[SkillResponse])
async def aupdate_skill(
    *,
    session: SessionDep,
    skill_id: str,
    skill_in: SkillUpdateRequest,
    x_user_id: str = Header(None),
    x_user_role: str = Header(None),
) -> Any:
    """
    Update a skill.
    """
    try:
        statement = select(Skill).where(Skill.id == skill_id, Skill.is_deleted.is_(False))

        result = await session.execute(statement)
        skill = result.scalar_one_or_none()

        if not skill:
            return ResponseWrapper(status=404, message="Skill not found").to_response()
        if x_user_role not in ["admin", "super admin"] and (str(skill.user_id) != x_user_id):
            return ResponseWrapper(status=403, message="Not enough permissions").to_response()

        if skill_in.tool_definition:
            validate_tool_definition(skill_in.tool_definition)

        update_dict = skill_in.model_dump(exclude_unset=True)

        statement = update(Skill).where(Skill.id == skill_id, Skill.is_deleted.is_(False)).values(**update_dict)
        await session.execute(statement)
        await session.commit()
        await session.refresh(skill)

        data = SkillResponse.model_validate(skill)
        return ResponseWrapper(status=200, data=data).to_response()

    except Exception as e:
        logger.error(f"Error updating skill with ID {skill_id}: {str(e)}")
        await session.rollback()
        return ResponseWrapper(status=500, message="Internal Server Error").to_response()


@router.delete("/{skill_id}", response_model=ResponseWrapper[MessageResponse])
async def adelete_skill(
    session: SessionDep,
    skill_id: str,
    x_user_id: str = Header(None),
    x_user_role: str = Header(None),
) -> Any:
    """
    Delete a skill.
    """
    try:
        statement = select(Skill).where(Skill.id == skill_id, Skill.is_deleted.is_(False))

        result = await session.execute(statement)
        skill = result.scalar_one_or_none()

        if not skill:
            return ResponseWrapper(status=404, message="Skill not found").to_response()
        if x_user_role not in ["admin", "super admin"] and (str(skill.user_id) != x_user_id):
            return ResponseWrapper(status=403, message="Not enough permissions").to_response()
        if str(skill.strategy) == str(StorageStrategy.GLOBAL_TOOLS):
            return ResponseWrapper(status=400, message="Cannot delete global tools").to_response()

        statement = update(Skill).where(Skill.id == skill_id, Skill.is_deleted.is_(False)).values(is_deleted=True, deleted_at=datetime.now())

        await session.execute(statement)
        await session.commit()

        data = MessageResponse(message="Skill deleted successfully")
        return ResponseWrapper(status=200, data=data).to_response()
    except Exception as e:
        logger.error(f"Error deleting skill with ID {skill_id}: {str(e)}")
        await session.rollback()
        return ResponseWrapper(status=500, message="Internal Server Error").to_response()


@router.post("/validate")
def validate_skill(tool_definition_in: ValidateToolDefinitionRequest) -> Any:
    """
    Validate skill's tool definition.
    """
    try:
        validated_tool_definition = validate_tool_definition(tool_definition_in.tool_definition)
        return validated_tool_definition
    except Exception as e:
        logger.error(f"Error validating tool definition: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/invoke-tool")
def invoke_tools(tool_name: str, args: dict) -> ToolInvokeResponse:
    """
    Invoke a tool by name with the provided arguments.
    """
    result = invoke_tool(tool_name, args)
    return result


@router.post("/update-credentials/{skill_id}", response_model=ResponseWrapper[SkillResponse])
async def aupdate_skill_credentials(
    *,
    session: SessionDep,
    skill_id: str,
    credentials: dict[str, dict[str, Any]],
    x_user_id: str = Header(None),
    x_user_role: str = Header(None),
) -> Any:
    """
    Update a skill's credentials.
    """
    try:
        statement = select(Skill).where(Skill.id == skill_id, Skill.is_deleted.is_(False))

        result = await session.execute(statement)
        skill = result.scalar_one_or_none()

        if not skill:
            return ResponseWrapper(status=404, message="Skill not found").to_response()
        if x_user_role not in ["admin", "super admin"] and (str(skill.user_id) != x_user_id):
            return ResponseWrapper(status=403, message="Not enough permissions").to_response()

        statement = update(Skill).where(Skill.id == skill_id, Skill.is_deleted.is_(False)).values(credentials=credentials)

        await session.execute(statement)
        await session.commit()
        await session.refresh(skill)

        response_data = SkillResponse.model_validate(skill)
        return ResponseWrapper(status=200, data=response_data).to_response()

    except Exception as e:
        logger.error(f"Error updating skill credentials with ID {skill_id}: {str(e)}")
        await session.rollback()
        return ResponseWrapper(status=500, message="Internal Server Error").to_response()


@router.post("/mcp/tools")
async def get_mcp_tools(mcp_config: dict[str, Any]) -> Any:
    pass