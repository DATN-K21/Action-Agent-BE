from email.header import Header
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import ValidationError
from sqlalchemy import col, func, or_, select, update

from app.api.deps import SessionDep
from app.core import logging
from app.core.enums import StorageStrategy
from app.core.tools.api_tool import ToolDefinition
from app.core.tools.tool_invoker import ToolInvokeResponse, invoke_tool
from app.db_models import Skill
from app.schemas.base import ResponseWrapper, MessageResponse
from app.schemas.skill import SkillsResponse, SkillResponse, CreateSkillRequest, SkillUpdateRequest, \
    ValidateToolDefinitionRequest

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
def read_skills(
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
        if x_user_role == "superuser":
            count_statement = select(func.count()).select_from(Skill).where(Skill.is_deleted.is_(False))
            count = session.exec(count_statement).one()
            statement = (
                select(Skill)
                .where(Skill.is_deleted.is_(False))
                .order_by(col(Skill.id).desc())
                .offset(skip)
                .limit(limit)
            )
        else:
            count_statement = (
                select(func.count())
                .select_from(Skill)
                .where(
                    or_(Skill.strategy == StorageStrategy.GLOBAL_TOOLS, Skill.user_id == x_user_id),
                    Skill.is_deleted.is_(False)
                )
            )
            count = session.exec(count_statement).one()

            statement = (
                select(Skill)
                .where(
                    or_(Skill.strategy == StorageStrategy.GLOBAL_TOOLS, Skill.user_id == x_user_id),
                    Skill.is_deleted.is_(False)
                )
                .order_by(col(Skill.id).desc())
                .offset(skip)
                .limit(limit)
            )

        skills = session.exec(statement).all()
        converted_skills = [SkillResponse.model_validate(skill) for skill in skills]
        data = SkillsResponse(
            skills=converted_skills,
            count=count
        )
        return ResponseWrapper(status=200, data=data).to_response()

    except Exception as e:
        logger.error(f"Error retrieving skills: {str(e)}")
        return ResponseWrapper(status=500, message="Internal Server Error").to_response()


@router.get("/{id}", response_model=ResponseWrapper[SkillResponse])
def read_skill(
        session: SessionDep,
        skill_id: str,
        x_user_id: str = Header(None)
) -> Any:
    """
    Get skill by ID.
    """
    try:
        statement = select(Skill).where(Skill.id == skill_id, Skill.is_deleted.is_(False))
        skill = session.exec(statement).one_or_none()

        if not skill:
            return ResponseWrapper(status=404, message="Skill not found")
        if skill.strategy != StorageStrategy.GLOBAL_TOOLS and (skill.user_id != x_user_id):
            return ResponseWrapper(status=403, message="Not enough permissions")

        data = SkillResponse.model_validate(skill)
        return ResponseWrapper(status=200, data=data).to_response()
    except Exception as e:
        logger.error(f"Error retrieving skill with ID {skill_id}: {str(e)}")
        raise ResponseWrapper(status=500, message="Internal Server Error").to_response()


@router.post("/", response_model=ResponseWrapper[SkillResponse])
def create_skill(
        *,
        session: SessionDep,
        skill_in: CreateSkillRequest,
        x_user_id: str = Header(None),
        x_user_role: str = Header(None),
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
        session.commit()
        session.refresh(skill)

        data = SkillResponse.model_validate(skill)
        return ResponseWrapper(status=200, data=data).to_response()
    except Exception as e:
        logger.error(f"Error creating new skill: {str(e)}")
        return ResponseWrapper(status=500, message="Internal Server Error")


@router.put("/{id}", response_model=ResponseWrapper[SkillResponse])
def update_skill(
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
        skill = session.get(Skill, skill_id)
        if not skill:
            return ResponseWrapper(status=404, message="Skill not found").to_response()
        if x_user_role != "admin" and (skill.user_id != x_user_id):
            return ResponseWrapper(status=403, message="Not enough permissions").to_response()

        if skill_in.tool_definition:
            validate_tool_definition(skill_in.tool_definition)

        update_dict = skill_in.model_dump(exclude_unset=True)

        statement = (
            update(Skill)
            .where(
                Skill.id == skill_id,
                Skill.is_deleted.is_(False)
            )
            .values(
                **update_dict
            )
        )
        session.exec(statement)
        session.commit()
        session.refresh(skill)

        data = SkillResponse.model_validate(skill)
        return ResponseWrapper(status=200, data=data).to_response()
    except Exception as e:
        logger.error(f"Error updating skill with ID {skill_id}: {str(e)}")
        return ResponseWrapper(status=500, message="Internal Server Error").to_response()


@router.delete("/{id}", response_model=ResponseWrapper[MessageResponse])
def delete_skill(
        session: SessionDep,
        skill_id: int,
        x_user_id: str = Header(None),
        x_user_role: str = Header(None),
) -> Any:
    """
    Delete a skill.
    """
    try:
        skill = session.get(Skill, skill_id)
        if not skill:
            return ResponseWrapper(status=404, message="Skill not found").to_response()
        if x_user_role != "admin" and (skill.user_id != x_user_id):
            return ResponseWrapper(status=403, message="Not enough permissions").to_response()
        if skill.Strategy == StorageStrategy.GLOBAL_TOOLS:
            return ResponseWrapper(status=400, message="Cannot delete global tools").to_response()
        session.delete(skill)
        session.commit()
        message = MessageResponse(message="Skill deleted successfully")
        return ResponseWrapper(status=200, data=message).to_response()
    except Exception as e:
        logger.error(f"Error deleting skill with ID {skill_id}: {str(e)}")
        return ResponseWrapper(status=500, message="Internal Server Error").to_response()


@router.post("/validate")
def validate_skill(tool_definition_in: ValidateToolDefinitionRequest) -> Any:
    """
    Validate skill's tool definition.
    """
    try:
        validated_tool_definition = validate_tool_definition(
            tool_definition_in.tool_definition
        )
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


@router.post("/update-credentials/{id}", response_model=ResponseWrapper[SkillResponse])
def update_skill_credentials(
        *,
        session: SessionDep,
        skill_id: int,
        credentials: dict[str, dict[str, Any]],
        x_user_id: str = Header(None),
        x_user_role: str = Header(None),
) -> Any:
    """
    Update a skill's credentials.
    """
    try:
        skill = session.get(Skill, skill_id)
        if not skill:
            return ResponseWrapper(status=404, message="Skill not found").to_response()
        if not x_user_role != "admin" and (skill.user_id != x_user_id):
            return ResponseWrapper(status=403, message="Not enough permissions").to_response()

        statement = (
            update(Skill)
            .where(
                Skill.id == skill_id,
                Skill.is_deleted.is_(False)
            )
            .values(
                credentials=credentials
            )
        )

        session.exec(statement)
        session.commit()
        session.refresh(skill)

        return ResponseWrapper(status=200, data=skill).to_response()
    except Exception as e:
        logger.error(f"Error updating skill credentials with ID {skill_id}: {str(e)}")
        return ResponseWrapper(status=500, message="Internal Server Error").to_response()


@router.post("/mcp/tools")
async def get_mcp_tools(mcp_config: dict[str, Any]) -> Any:
    pass
