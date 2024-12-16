import logging
from datetime import datetime
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import User
from app.db.session import get_db
from app.models.schemas.base import BaseResponse
from app.models.schemas.paging import PagingRequest
from app.models.schemas.user import CreateUserResponse, CreateUserRequest, ReadUserResponse, UpdateUserResponse, \
    UpdateUserRequest, DeleteUserResponse, ReadListUsersResponse
from app.utils.constants import SYSTEM

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/", response_model=BaseResponse[CreateUserResponse])
async def create_new_user(user: CreateUserRequest, db: AsyncSession = Depends(get_db)) -> BaseResponse[CreateUserResponse]:
    try:
        db_user = User(
            username=user.userName,
            email=user.email,
            first_name=user.firstName,
            last_name=user.lastName,
            created_by=SYSTEM
        )

        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)

        data = CreateUserResponse(
            id=db_user.id,
            email=db_user.email,
            username=db_user.username,
            firstName=db_user.first_name,
            lastName=db_user.last_name,
            createdAt=db_user.created_at,
        )

        return BaseResponse(
            status=201,
            data=data
        )

    except Exception as e:
        logger.error("An error occurred", exc_info=e)
        return BaseResponse(
            status=500,
            message="An error occurred"
        )


@router.get("/{user_id}", response_model=BaseResponse[ReadUserResponse])
async def get_user_by_id(user_id: UUID, db: AsyncSession = Depends(get_db)):
    try:
        query = (
            select(User)
            .options(selectinload(User.threads))
            .where(User.id == user_id and not User.is_deleted)
        )
        result = await db.execute(query)
        db_user = result.scalar_one_or_none()

        if not db_user:
            return BaseResponse(
                status=404,
                message="User not found"
            )

        data = ReadUserResponse(
            id=db_user.id,
            email=db_user.email,
            username=db_user.username,
            firstName=db_user.first_name,
            lastName=db_user.last_name,
            createdAt=db_user.created_at,
        )

        return BaseResponse(status=200, data=data)

    except Exception as e:
        logger.error("An error occurred", exc_info=e)
        return BaseResponse(
            status=500,
            message="An error occurred"
        )

@router.get("/", response_model=BaseResponse[ReadListUsersResponse])
async def get_all_users(request: PagingRequest = Depends(), db: AsyncSession = Depends(get_db)):
    try:
        pageNumber = request.pageNumber
        maxPerPage = request.maxPerPage

        skip = (pageNumber - 1) * maxPerPage
        limit = maxPerPage

        query = (
            select(User)
            .where(User.is_deleted == False)
            .options(selectinload(User.threads))
            .order_by(User.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(query)
        db_users = result.scalars().all()

        users = [ReadUserResponse(
            id=db_user.id,
            email=db_user.email,
            username=db_user.username,
            firstName=db_user.first_name,
            lastName=db_user.last_name,
            createdAt=db_user.created_at,
        ) for db_user in db_users]

        data = ReadListUsersResponse(
            users=users,
            pageNumber=pageNumber,
            maxPerPage=maxPerPage,
            totalPage=10
        )

        return BaseResponse(
            status=200,
            data=data
        )

    except Exception as e:
        logger.error("An error occurred", exc_info=e)
        return BaseResponse(
            status=500,
            message="An error occurred"
        )

@router.patch("/{user_id}", response_model=BaseResponse[UpdateUserResponse])
async def update_user(user_id: UUID, user: UpdateUserRequest, db: AsyncSession = Depends(get_db)):
    try:
        query = (
            select(User)
            .where(User.id == user_id and not User.is_deleted)
            .options(selectinload(User.threads))
        )
        result = await db.execute(query)
        db_user = result.scalar_one_or_none()
        if not db_user:
            return BaseResponse(
                status=404,
                message="User not found"
            )

        db_user.username = user.userName if user.userName else db_user.username
        db_user.email = user.email if user.email else db_user.email
        db_user.first_name = user.firstName if user.firstName else db_user.first_name
        db_user.last_name = user.lastName if user.lastName else db_user.last_name

        await db.commit()
        await db.refresh(db_user)

        data = UpdateUserResponse(
            id=db_user.id,
            email=db_user.email,
            username=db_user.username,
            firstName=db_user.first_name,
            lastName=db_user.last_name,
            createdAt=db_user.created_at,
        )

        return BaseResponse(
            status=200,
            data=data
        )

    except Exception as e:
        logger.error("An error occurred", exc_info=e)
        return BaseResponse(
            status=500,
            message="An error occurred"
        )


@router.delete("/{user_id}", response_model=BaseResponse[DeleteUserResponse])
async def delete_user(user_id: UUID, db: AsyncSession = Depends(get_db)):
    try:
        query = (
            select(User)
            .where(User.id == user_id and not User.is_deleted)
            .options(selectinload(User.threads))
        )
        result = await db.execute(query)
        db_user = result.scalar_one_or_none()
        if not db_user:
            return BaseResponse(
                status=404,
                message="User not found"
            )

        db_user.is_deleted = True
        db_user.deleted_at = datetime.utcnow()
        await db.commit()

        return BaseResponse(
            status=200,
            data=DeleteUserResponse(
                id=db_user.id
            )
        )

    except Exception as e:
        logger.error("An error occurred", exc_info=e)
        return BaseResponse(
            status=500,
            message="An error occurred"
        )
