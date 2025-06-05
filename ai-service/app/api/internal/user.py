from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy import func, select, update

from app.api.deps import SessionDep
from app.core import logging
from app.core.constants import SYSTEM, TRIAL_TOKENS
from app.db_models.user import User
from app.schemas.base import PagingRequest, ResponseWrapper
from app.schemas.user import (
    CreateUserRequest,
    CreateUserResponse,
    DeleteUserResponse,
    GetUserResponse,
    GetUsersResponse,
    UpdateUserRequest,
    UpdateUserResponse,
)

logger = logging.get_logger(__name__)

router = APIRouter(prefix="/user", tags=["User"])


@router.post("/create", summary="Create a new user.", response_model=ResponseWrapper[CreateUserResponse])
async def create_new_user(
    session: SessionDep,
    request: CreateUserRequest,
):
    """
    Create a new user.
    """
    try:
        # Check if user already exists
        stmt = (
            select(User.id)
            .where(
                User.email == request.email,
                User.is_deleted.is_(False),
            )
            .limit(1)
        )

        result = await session.execute(stmt)
        existing_user = result.scalar_one_or_none()
        if existing_user:
            return ResponseWrapper.wrap(status=400, message="User already exists").to_response()

        # Create new user
        db_user = User(
            **request.model_dump(),
            default_api_key_id=None,
            remain_trial_tokens=TRIAL_TOKENS,
            created_by=SYSTEM,
        )

        session.add(db_user)
        await session.commit()
        await session.refresh(db_user)

        response_data = CreateUserResponse.model_validate(db_user)
        return ResponseWrapper.wrap(status=200, data=response_data)

    except Exception as e:
        logger.exception("Has error: %s", str(e))
        await session.rollback()
        return ResponseWrapper.wrap(status=500, message="Internal server error").to_response()


@router.patch("/{user_id}/update", summary="Update the given user.", response_model=ResponseWrapper[UpdateUserResponse])
async def update_user(
    session: SessionDep,
    user_id: str,
    user: UpdateUserRequest,
):
    """
    Update the given user.
    """
    try:
        stmt = (
            update(User)
            .where(
                User.id == user_id,
                User.is_deleted.is_(False),
            )
            .values(**user.model_dump(exclude_unset=True))
            .returning(User)
        )

        result = await session.execute(stmt)
        db_user = result.scalar_one_or_none()
        if not db_user:
            return ResponseWrapper.wrap(status=404, message="User not found").to_response()

        await session.commit()
        await session.refresh(db_user)

        response_data = CreateUserResponse.model_validate(db_user)
        return ResponseWrapper.wrap(status=200, data=response_data)

    except Exception as e:
        logger.exception(f"Has error: {str(e)}")
        await session.rollback()
        return ResponseWrapper.wrap(status=500, message="Internal server error").to_response()


@router.delete("/{user_id}/delete", summary="Delete the given user.",
               response_model=ResponseWrapper[DeleteUserResponse])
async def delete_user(session: SessionDep, user_id: str):
    """
    Delete the given user.
    """
    try:
        stmt = (
            update(User)
            .where(
                User.id == user_id,
                User.is_deleted.is_(False),
            )
            .values(
                is_deleted=True,
                deleted_at=datetime.now(),
            )
            .returning(User.id)
        )

        result = await session.execute(stmt)
        deleted_user_id = result.scalar_one_or_none()
        if not deleted_user_id:
            return ResponseWrapper.wrap(status=404, message="User not found").to_response()

        await session.commit()
        return ResponseWrapper.wrap(status=200, data=DeleteUserResponse(id=deleted_user_id)).to_response()

    except Exception as e:
        logger.exception(f"Has error: {str(e)}")
        await session.rollback()
        return ResponseWrapper.wrap(status=500, message="Internal server error").to_response()


@router.get("/get-all", summary="Get all users.", response_model=ResponseWrapper[GetUsersResponse])
async def get_all_users(
    session: SessionDep,
    paging: PagingRequest = Depends(),
):
    """
    Get all users.
    """
    try:
        page_number = paging.page_number
        max_per_page = paging.max_per_page

        # COUNT total users
        count_stmt = select(func.count(User.id)).where(User.is_deleted.is_(False))
        count_result = await session.execute(count_stmt)
        total_users = count_result.scalar_one()
        logger.info(f"total_users: {total_users}")
        if total_users == 0:
            response_data = GetUsersResponse(
                users=[],
                page_number=page_number,
                max_per_page=max_per_page,
                total_page=0,
            )
            return ResponseWrapper.wrap(status=200, data=response_data).to_response()

        # Calculate total pages
        total_pages = (total_users + max_per_page - 1) // max_per_page

        # GET users
        stmt = (
            select(
                User.id.label("id"),
                User.username.label("username"),
                User.email.label("email"),
                User.first_name.label("first_name"),
                User.last_name.label("last_name"),
                User.created_at.label("created_at"),
            )
            .where(
                User.is_deleted.is_(False),
            )
            .offset((page_number - 1) * max_per_page)
            .limit(paging.max_per_page)
            .order_by(User.created_at.desc())
        )

        result = await session.execute(stmt)
        db_users = result.mappings().all()

        users = [GetUserResponse.model_validate(db_user) for db_user in db_users]
        response_data = GetUsersResponse(
            users=users,
            page_number=paging.page_number,
            max_per_page=paging.max_per_page,
            total_page=total_pages,
        )
        return ResponseWrapper.wrap(status=200, data=response_data).to_response()

    except Exception as e:
        logger.exception(f"Has error: {str(e)}")
        return ResponseWrapper.wrap(status=500, message="Internal server error").to_response()


@router.get("/{user_id}/get-detail", summary="Get details of the given user.",
            response_model=ResponseWrapper[GetUserResponse])
async def get_user_by_user_id(session: SessionDep, user_id: str):
    """
    Get details of the given user.
    """
    try:
        stmt = (
            select(
                User.id.label("id"),
                User.username.label("username"),
                User.email.label("email"),
                User.first_name.label("first_name"),
                User.last_name.label("last_name"),
                User.created_at.label("created_at"),
            )
            .where(
                User.id == user_id,
                User.is_deleted.is_(False),
            )
            .limit(1)
        )

        result = await session.execute(stmt)
        db_user = result.mappings().one_or_none()
        logger.info(f"db_user: {db_user}")

        if not db_user:
            return ResponseWrapper.wrap(status=404, message="User not found")

        response_data = GetUserResponse.model_validate(db_user)
        return ResponseWrapper.wrap(status=200, data=response_data)

    except Exception as e:
        logger.exception(f"Has error: {str(e)}")
        return ResponseWrapper.wrap(status=500, message="Internal server error")
