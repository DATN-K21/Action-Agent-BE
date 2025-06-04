from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import func, select, update

from app.api.deps import SessionDep
from app.core import logging
from app.core.settings import env_settings
from app.db_models import Assistant, Member, Skill, Upload
from app.schemas.base import MessageResponse, ResponseWrapper
from app.schemas.member import CreateMemberRequest, MemberResponse, MembersResponse, UpdateMemberRequest

router = APIRouter()

logger = logging.get_logger(__name__)


async def async_validate_name_on_create(session: SessionDep, assistant_id: str, member_in: CreateMemberRequest) -> None:
    """Check if (name, assistant_id) is unique and name is not a protected name"""
    if member_in.name in env_settings.PROTECTED_NAMES:
        raise HTTPException(
            status_code=400, detail="Name is a protected name. Choose another name."
        )
    statement = select(Member).where(Member.name == member_in.name, Member.assistant_id == assistant_id, Member.is_deleted.is_(False))
    member_unique = await session.execute(statement)
    member_unique = member_unique.scalar_one_or_none()
    if member_unique:
        raise HTTPException(
            status_code=400, detail="Member with this name already exists"
        )


async def async_validate_names_on_update(session: SessionDep, assistant_id: str, member_in: UpdateMemberRequest, member_id: str) -> None:
    """Check if (name, assistant_id) is unique and name is not a protected name"""
    if member_in.name in env_settings.PROTECTED_NAMES:
        raise HTTPException(
            status_code=400, detail="Name is a protected name. Choose another name."
        )
    statement = select(Member).where(
        Member.name == member_in.name, Member.assistant_id == assistant_id, Member.id != member_id, Member.is_deleted.is_(False)
    )
    member_unique = await session.execute(statement)
    member_unique = member_unique.scalar_one_or_none()
    if member_unique:
        raise HTTPException(
            status_code=400, detail="Member with this name already exists"
        )


@router.get("/", response_model=ResponseWrapper[MembersResponse])
async def aread_members(
    session: SessionDep,
    assistant_id: str,
    skip: int = 0,
    limit: int = 100,
    x_user_id: str = Header(None),
    x_user_role: str = Header(None),
) -> Any:
    """
    Retrieve members from assistant.
    """
    # TODO: Use new way of getting members from assistants. Get assistant first then use assistant.members
    try:
        if x_user_role.lower() == "admin" or x_user_role.lower() == "super admin":
            count_statement = select(func.count()).select_from(Member).where(Member.is_deleted.is_(False))
            count_result = await session.execute(count_statement)
            count = count_result.scalar_one()
            statement = select(Member).where(Member.assistant_id == assistant_id, Member.is_deleted.is_(False)).offset(skip).limit(limit)
            result = await session.execute(statement)
            members = result.scalars().all()
        else:
            count_statement = (
                select(func.count())
                .select_from(Member)
                .join(Assistant)
                .where(Assistant.user_id == x_user_id, Member.assistant_id == assistant_id, Member.is_deleted.is_(False))
            )
            count_result = await session.execute(count_statement)
            count = count_result.scalar_one()
            statement = (
                select(Member)
                .join(Assistant)
                .where(Assistant.user_id == x_user_id, Member.assistant_id == assistant_id, Member.is_deleted.is_(False))
                .offset(skip)
                .limit(limit)
            )
            result = await session.execute(statement)
            members = result.scalars().all()

        converted_members = [MemberResponse.model_validate(member) for member in members]
        data = MembersResponse(members=converted_members, count=count)
        return ResponseWrapper.wrap(status=200, data=data).to_response()
    except Exception as e:
        logger.error(f"Error retrieving members: {e}", exc_info=True)
        return ResponseWrapper(status=500, message="Internal server error").to_response()


@router.get("/{member_id}", response_model=ResponseWrapper[MemberResponse])
async def aread_member(
    session: SessionDep,
    assistant_id: str,
    member_id: str,
    x_user_id: str = Header(None),
    x_user_role: str = Header(None),
) -> Any:
    """
    Get member by ID.
    """
    try:
        if x_user_role.lower() == "admin" or x_user_role.lower() == "super admin":
            statement = (
                select(Member).join(Assistant).where(Member.id == member_id, Member.assistant_id == assistant_id, Member.is_deleted.is_(False))
            )
            result = await session.execute(statement)
            member = result.scalar_one_or_none()
        else:
            statement = (
                select(Member)
                .join(Assistant)
                .where(Member.id == member_id, Member.assistant_id == assistant_id, Assistant.user_id == x_user_id, Member.is_deleted.is_(False))
            )
            result = await session.execute(statement)
            member = result.scalar_one_or_none()

        if not member:
            return ResponseWrapper(status=404, message="Member not found").to_response()

        data = MemberResponse.model_validate(member)
        return ResponseWrapper.wrap(status=200, data=data).to_response()
    except Exception as e:
        logger.error(f"Error retrieving member: {e}", exc_info=True)
        return ResponseWrapper(status=500, message="Internal server error").to_response()


@router.post("/", response_model=ResponseWrapper[MemberResponse])
async def acreate_member(
    session: SessionDep,
    assistant_id: str,
    member_in: CreateMemberRequest,
    x_user_id: str = Header(None),
    x_user_role: str = Header(None),
    _: bool = Depends(async_validate_name_on_create),
) -> Any:
    """
    Create new member.
    """
    try:
        statement = select(Assistant).where(Assistant.id == assistant_id, Assistant.is_deleted.is_(False))
        result = await session.execute(statement)
        assistant = result.scalar_one_or_none()
        if not assistant:
            return ResponseWrapper(status=404, message="assistant not found").to_response()

        if x_user_role.lower() != "admin" and x_user_role.lower() != "super admin":
            if str(assistant.user_id) != x_user_id:
                return ResponseWrapper(status=403, message="Not enough permissions").to_response()

        member_data = member_in.model_dump()
        member_data["assistant_id"] = assistant_id
        member = Member(**member_data)
        session.add(member)
        await session.commit()
        await session.refresh(member)

        data = MemberResponse.model_validate(member)
        return ResponseWrapper(status=200, data=data).to_response()
    except Exception as e:
        logger.error(f"Error creating new member: {e}", exc_info=True)
        return ResponseWrapper(status=500, message="Internal server error").to_response()


@router.put("/{id}", response_model=ResponseWrapper[MemberResponse])
async def async_update_member(
    *,
    session: SessionDep,
    assistant_id: str,
    member_id: str,
    member_in: UpdateMemberRequest,
    x_user_id: str = Header(None),
    x_user_role: str = Header(None),
    _: bool = Depends(async_validate_names_on_update),
) -> Any:
    """
    Update a member.
    """
    try:
        if x_user_role.lower() == "admin" or x_user_role.lower() == "super admin":
            statement = (
                select(Member).join(Assistant).where(Member.id == member_id, Member.assistant_id == assistant_id, Member.is_deleted.is_(False))
            )
            result = await session.execute(statement)
            member = result.scalar_one_or_none()
        else:
            statement = (
                select(Member)
                .join(Assistant)
                .where(Member.id == member_id, Member.assistant_id == assistant_id, Assistant.user_id == x_user_id, Member.is_deleted.is_(False))
            )
            result = await session.execute(statement)
            member = result.scalar_one_or_none()

        if not member:
            return ResponseWrapper(status=404, message="Member not found").to_response()

        # Create update dictionary with regular fields
        update_dict = member_in.model_dump(exclude_unset=True)

        # Remove relationship fields from the update dict as they're handled separately
        if "skills" in update_dict:
            del update_dict["skills"]
        if "uploads" in update_dict:
            del update_dict["uploads"]

        # Update regular fields directly on the member object
        for key, value in update_dict.items():
            setattr(member, key, value)

        # update member's skills if required
        if member_in.skills is not None:
            skill_ids = [skill.id for skill in member_in.skills]
            skills_statement = select(Skill).where(Skill.id.in_(skill_ids), Skill.is_deleted.is_(False))
            skills_result = await session.execute(skills_statement)
            skills = skills_result.scalars().all()
            member.skills = list(skills)

        # update member's accessible uploads if required
        if member_in.uploads is not None:
            upload_ids = [upload.id for upload in member_in.uploads]
            uploads_statement = select(Upload).where(Upload.id.in_(upload_ids), Upload.is_deleted.is_(False))
            uploads_result = await session.execute(uploads_statement)
            uploads = uploads_result.scalars().all()
            member.uploads = list(uploads)

        # No need for an explicit update statement as we're modifying the member object directly
        await session.commit()
        await session.refresh(member)

        data = MemberResponse.model_validate(member)
        return ResponseWrapper.wrap(status=200, data=data).to_response()
    except Exception as e:
        logger.error(f"Error updating member: {e}", exc_info=True)
        return ResponseWrapper(status=500, message="Internal server error").to_response()


@router.delete("/{id}", response_model=ResponseWrapper[MessageResponse])
async def async_delete_member(
    session: SessionDep,
    assistant_id: str,
    member_id: str,
    x_user_id: str = Header(None),
    x_user_role: str = Header(None),
):
    """
    Delete a member.
    """
    try:
        if x_user_role.lower() == "admin" or x_user_role.lower() == "super admin":
            statement = (
                select(Member).join(Assistant).where(Member.id == member_id, Member.assistant_id == assistant_id, Member.is_deleted.is_(False))
            )
            result = await session.execute(statement)
            member = result.scalar_one_or_none()
        else:
            statement = (
                select(Member)
                .join(Assistant)
                .where(Member.id == member_id, Member.assistant_id == assistant_id, Assistant.user_id == x_user_id, Member.is_deleted.is_(False))
            )
            result = await session.execute(statement)
            member = result.scalar_one_or_none()

        if not member:
            return ResponseWrapper(status=404, message="Member not found").to_response()

        statement = (
            update(Member)
            .where(Member.id == member_id, Member.assistant_id == assistant_id, Member.is_deleted.is_(False))
            .values(is_deleted=True, deleted_at=func.now())
        )
        await session.execute(statement)
        await session.commit()

        data = MessageResponse(message="Member deleted successfully")
        return ResponseWrapper.wrap(status=200, data=data).to_response()

    except Exception as e:
        logger.error(f"Error deleting member: {e}", exc_info=True)
        return ResponseWrapper(status=500, message="Internal server error").to_response()
