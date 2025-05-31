from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Header
from posthog.ai.openai.openai import WrappedResponses
from sqlmodel import col, func, select

from app.api.deps import SessionDep
from app.core import logging
from app.core.settings import env_settings
from app.db_models import Member, Team, Skill, Upload
from app.schemas.base import MessageResponse
from app.schemas.member import CreateMemberRequest, UpdateMemberRequest, MembersResponse, MemberResponse

router = APIRouter()

logger = logging.get_logger(__name__)


def validate_name_on_create(
        session: SessionDep, team_id: int, member_in: CreateMemberRequest
) -> None:
    """Check if (name, team_id) is unique and name is not a protected name"""
    if member_in.name in env_settings.PROTECTED_NAMES:
        raise HTTPException(
            status_code=400, detail="Name is a protected name. Choose another name."
        )
    statement = select(Member).where(
        Member.name == member_in.name,
        Member.team_id == team_id,
    )
    member_unique = session.exec(statement).first()
    if member_unique:
        raise HTTPException(
            status_code=400, detail="Member with this name already exists"
        )


def validate_names_on_update(
        session: SessionDep, team_id: int, member_in: UpdateMemberRequest, member_id: int
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
    )
    member_unique = session.exec(statement).first()
    if member_unique:
        raise HTTPException(
            status_code=400, detail="Member with this name already exists"
        )


@router.get("/", response_model=WrappedResponses[MembersResponse])
def read_members(
        session: SessionDep,
        team_id: int,
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
                .where(Team.user_id == x_user_id, Member.team_id == team_id)
            )
            count = session.exec(count_statement).one()
            statement = (
                select(Member)
                .join(Team)
                .where(Team.user_id == x_user_id, Member.team_id == team_id)
                .offset(skip)
                .limit(limit)
            )
            members = session.exec(statement).all()

        data = MembersResponse(members=members, count=count)
        return WrappedResponses.wrap(status=200, data=data)
    except Exception as e:
        logger.error(f"Error retrieving members: {e}", exc_info=True)
        return WrappedResponses(status=500, message="Internal server error")


@router.get("/{id}", response_model=WrappedResponses[MemberResponse])
def read_member(
        session: SessionDep,
        team_id: int,
        member_id: int,
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
                )
            )
            member = session.exec(statement).first()

        if not member:
            return WrappedResponses(status=404, message="Member not found")

        return WrappedResponses.wrap(status=200, data=member.data)
    except Exception as e:
        logger.error(f"Error retrieving member: {e}", exc_info=True)
        return WrappedResponses(status=500, message="Internal server error")


@router.post("/", response_model=WrappedResponses[MemberResponse])
def create_member(
        *,
        session: SessionDep,
        team_id: int,
        member_in: CreateMemberRequest,
        x_user_id: str = Header(None),
        x_user_role: str = Header(None),
        _: bool = Depends(validate_name_on_create),
) -> Any:
    """
    Create new member.
    """
    try:
        if x_user_role.lower() != "admin":
            team = session.get(Team, team_id)
            if not team:
                return WrappedResponses(status=404, message="Team not found")
            if team.user_id != x_user_id:
                return WrappedResponses(status=403, message="Not enough permissions")

        member_data = member_in.model_dump()
        member_data["team_id"] = team_id
        member = Member(**member_data)
        session.add(member)
        session.commit()
        session.refresh(member)
        return member
    except Exception as e:
        logger.error(f"Error creating new member: {e}", exc_info=True)
        return WrappedResponses(status=500, message="Internal server error")


@router.put("/{id}", response_model=WrappedResponses[MemberResponse])
def update_member(
        *,
        session: SessionDep,
        team_id: int,
        member_id: int,
        member_in: UpdateMemberRequest,
        x_user_id: str = Header(None),
        x_user_role: str = Header(None),
        _: bool = Depends(validate_names_on_update),
) -> Any:
    """
    Update a member.
    """
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
        raise HTTPException(status_code=404, detail="Member not found")

    # update member's skills if required
    if member_in.skills is not None:
        skill_ids = [skill.id for skill in member_in.skills]
        skills = session.exec(select(Skill).where(col(Skill.id).in_(skill_ids))).all()
        member.skills = list(skills)

    # update member's accessible uploads if required
    if member_in.uploads is not None:
        upload_ids = [upload.id for upload in member_in.uploads]
        uploads = session.exec(
            select(Upload).where(col(Upload.id).in_(upload_ids))
        ).all()
        member.uploads = list(uploads)

    update_dict = member_in.model_dump(exclude_unset=True)
    member.sqlmodel_update(update_dict)
    session.add(member)
    session.commit()
    session.refresh(member)
    return member


@router.delete("/{id}")
def delete_member(
        session: SessionDep,
        team_id: int,
        member_id: int,
        x_user_id: str = Header(None),
        x_user_role: str = Header(None),
) -> WrappedResponses[MessageResponse]:
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
            raise HTTPException(status_code=404, detail="Member not found")

        session.delete(member)
        session.commit()
        data = MessageResponse(message="Member deleted successfully")
        return WrappedResponses.wrap(status=200, data=data)

    except Exception as e:
        logger.error(f"Error deleting member: {e}", exc_info=True)
        return WrappedResponses(status=500, message="Internal server error")
