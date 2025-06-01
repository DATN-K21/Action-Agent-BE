from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy import func, select, update

from app.api.deps import SessionDep
from app.core import logging
from app.core.settings import env_settings
from app.db_models import Member, Team, Skill, Upload
from app.schemas.base import MessageResponse
from app.schemas.base import ResponseWrapper
from app.schemas.member import CreateMemberRequest, UpdateMemberRequest, MembersResponse, MemberResponse

router = APIRouter()

logger = logging.get_logger(__name__)


def validate_name_on_create(
        session: SessionDep, team_id: str, member_in: CreateMemberRequest
) -> None:
    """Check if (name, team_id) is unique and name is not a protected name"""
    if member_in.name in env_settings.PROTECTED_NAMES:
        raise HTTPException(
            status_code=400, detail="Name is a protected name. Choose another name."
        )
    statement = select(Member).where(
        Member.name == member_in.name,
        Member.team_id == team_id,
        Member.is_deleted.is_(False)
    )
    member_unique = session.exec(statement).first()
    if member_unique:
        raise HTTPException(
            status_code=400, detail="Member with this name already exists"
        )


def validate_names_on_update(
        session: SessionDep, team_id: str, member_in: UpdateMemberRequest, member_id: str
) -> None:
    """Check if (name, team_id) is unique and name is not a protected name"""
    if member_in.name in env_settings.PROTECTED_NAMES:
        raise HTTPException(
            status_code=400, detail="Name is a protected name. Choose another name."
        )
    statement = select(Member).where(
        Member.name == member_in.name,
        Member.team_id == team_id,
        Member.id != member_id,
        Member.is_deleted.is_(False)
    )
    member_unique = session.exec(statement).first()
    if member_unique:
        raise HTTPException(
            status_code=400, detail="Member with this name already exists"
        )


@router.get("/", response_model=ResponseWrapper[MembersResponse])
def read_members(
        session: SessionDep,
        team_id: str,
        skip: int = 0,
        limit: int = 100,
        x_user_id: str = Header(None),
        x_user_role: str = Header(None),
) -> Any:
    """
    Retrieve members from team.
    """
    # TODO: Use new way of getting members from teams. Get team first then use team.members
    try:
        if x_user_role.lower() == "admin":
            count_statement = select(func.count()).select_from(Member)
            count = session.exec(count_statement).one()
            statement = (
                select(Member).where(Member.team_id == team_id).offset(skip).limit(limit)
            )
            members = session.exec(statement).all()
        else:
            count_statement = (
                select(func.count())
                .select_from(Member)
                .join(Team)
                .where(
                    Team.user_id == x_user_id,
                    Member.team_id == team_id,
                    Member.is_deleted.is_(False)
                )
            )
            count = session.exec(count_statement).one()
            statement = (
                select(Member)
                .join(Team)
                .where(
                    Team.user_id == x_user_id,
                    Member.team_id == team_id,
                    Member.is_deleted.is_(False)
                )
                .offset(skip)
                .limit(limit)
            )
            members = session.exec(statement).all()

        converted_members = [MemberResponse.model_validate(member) for member in members]
        data = MembersResponse(members=converted_members, count=count)
        return ResponseWrapper.wrap(status=200, data=data).to_response()
    except Exception as e:
        logger.error(f"Error retrieving members: {e}", exc_info=True)
        return ResponseWrapper(status=500, message="Internal server error").to_response()


@router.get("/{id}", response_model=ResponseWrapper[MemberResponse])
def read_member(
        session: SessionDep,
        team_id: str,
        member_id: str,
        x_user_id: str = Header(None),
        x_user_role: str = Header(None),
) -> Any:
    """
    Get member by ID.
    """
    try:
        if x_user_role.lower() == "admin":
            statement = (
                select(Member)
                .join(Team)
                .where(Member.id == member_id, Member.team_id == team_id)
            )
            member = session.exec(statement).first()
        else:
            statement = (
                select(Member)
                .join(Team)
                .where(
                    Member.id == member_id,
                    Member.team_id == team_id,
                    Team.user_id == x_user_id,
                    Member.is_deleted.is_(False)
                )
            )
            member = session.exec(statement).first()

        if not member:
            return ResponseWrapper(status=404, message="Member not found").to_response()

        data = MemberResponse.model_validate(member)
        return ResponseWrapper.wrap(status=200, data=data).to_response()
    except Exception as e:
        logger.error(f"Error retrieving member: {e}", exc_info=True)
        return ResponseWrapper(status=500, message="Internal server error").to_response()


@router.post("/", response_model=ResponseWrapper[MemberResponse])
def create_member(
        *,
        session: SessionDep,
        team_id: str,
        member_in: CreateMemberRequest,
        x_user_id: str = Header(None),
        x_user_role: str = Header(None),
        _: bool = Depends(validate_name_on_create),
) -> Any:
    """
    Create new member.
    """
    try:
        team = session.get(Team, team_id)
        if not team:
            return ResponseWrapper(status=404, message="Team not found").to_response()

        if x_user_role.lower() != "admin":
            if team.user_id != x_user_id:
                return ResponseWrapper(status=403, message="Not enough permissions").to_response()

        member_data = member_in.model_dump()
        member_data["team_id"] = team_id
        member = Member(**member_data)
        session.add(member)
        session.commit()
        session.refresh(member)

        data = MemberResponse.model_validate(member)
        return ResponseWrapper(status=200, data=data).to_response()
    except Exception as e:
        logger.error(f"Error creating new member: {e}", exc_info=True)
        return ResponseWrapper(status=500, message="Internal server error").to_response()


@router.put("/{id}", response_model=ResponseWrapper[MemberResponse])
def update_member(
        *,
        session: SessionDep,
        team_id: str,
        member_id: str,
        member_in: UpdateMemberRequest,
        x_user_id: str = Header(None),
        x_user_role: str = Header(None),
        _: bool = Depends(validate_names_on_update),
) -> Any:
    """
    Update a member.
    """
    try:
        if x_user_role.lower() == "admin":
            statement = (
                select(Member)
                .join(Team)
                .where(
                    Member.id == member_id,
                    Member.team_id == team_id,
                    Member.is_deleted.is_(False)
                )
            )
            member = session.exec(statement).first()
        else:
            statement = (
                select(Member)
                .join(Team)
                .where(
                    Member.id == member_id,
                    Member.team_id == team_id,
                    Team.user_id == x_user_id,
                    Member.is_deleted.is_(False)
                )
            )
            member = session.exec(statement).first()

        if not member:
            return ResponseWrapper(status=404, message="Member not found").to_response()

        # update member's skills if required
        if member_in.skills is not None:
            skill_ids = [skill.id for skill in member_in.skills]
            skills = session.exec(
                select(Skill)
                .where(Skill.id.in_(skill_ids), Skill.is_deleted.is_(False))
            ).all()
            member.skills = list(skills)

        # update member's accessible uploads if required
        if member_in.uploads is not None:
            upload_ids = [upload.id for upload in member_in.uploads]
            uploads = session.exec(
                select(Upload)
                .where(
                    Upload.id.in_(upload_ids),
                    Upload.is_deleted.is_(False)
                )
            ).all()
            member.uploads = list(uploads)

        update_dict = member_in.model_dump(exclude_unset=True)
        statement = (
            update(Member)
            .where(
                Member.id == member_id,
                Member.team_id == team_id,
                Member.is_deleted.is_(False)
            )
            .values(**update_dict)
        )
        session.exec(statement)
        session.commit()
        session.refresh(member)

        data = MemberResponse.model_validate(member)
        return ResponseWrapper.wrap(status=200, data=data).to_response()
    except Exception as e:
        logger.error(f"Error updating member: {e}", exc_info=True)
        return ResponseWrapper(status=500, message="Internal server error").to_response()


@router.delete("/{id}", response_model=ResponseWrapper[MessageResponse])
def delete_member(
        session: SessionDep,
        team_id: str,
        member_id: str,
        x_user_id: str = Header(None),
        x_user_role: str = Header(None),
):
    """
    Delete a member.
    """
    try:
        if x_user_role.lower() == "admin":
            statement = (
                select(Member)
                .join(Team)
                .where(Member.id == member_id, Member.team_id == team_id)
            )
            member = session.exec(statement).first()
        else:
            statement = (
                select(Member)
                .join(Team)
                .where(
                    Member.id == member_id,
                    Member.team_id == team_id,
                    Team.user_id == x_user_id,
                )
            )
            member = session.exec(statement).first()

        if not member:
            return ResponseWrapper(status=404, message="Member not found").to_response()

        statement = (
            update(Member)
            .where(
                Member.id == member_id,
                Member.team_id == team_id,
                Member.is_deleted.is_(False)
            )
            .values(
                is_deleted=True,
                deleted_at=func.now()
            )
        )
        session.exec(statement)
        session.commit()

        data = MessageResponse(message="Member deleted successfully")
        return ResponseWrapper.wrap(status=200, data=data).to_response()

    except Exception as e:
        logger.error(f"Error deleting member: {e}", exc_info=True)
        return ResponseWrapper(status=500, message="Internal server error").to_response()
