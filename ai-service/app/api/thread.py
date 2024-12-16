from datetime import datetime
import logging
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.future import select

from app.db.models import Thread
from app.db.session import get_db
from app.models.schemas.base import BaseResponse
from app.models.schemas.paging import PagingRequest
from app.models.schemas.thread import CreateThreadResponse, CreateThreadRequest, ReadThreadResponse, \
    UpdateThreadResponse, UpdateThreadRequest, DeleteThreadResponse, ReadListThreadsResponse
from app.utils.constants import SYSTEM

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/", response_model=BaseResponse[CreateThreadResponse])
async def create_new_thread(thread: CreateThreadRequest, db: AsyncSession = Depends(get_db)) -> BaseResponse[CreateThreadRequest]:
    try:
        db_thread = Thread(
            user_id=thread.userId,
            name=thread.name,
            created_by=SYSTEM
        )

        db.add(db_thread)
        await db.commit()
        await db.refresh(db_thread)

        data = CreateThreadResponse(
            id=db_thread.id,
            userId=db_thread.user_id,
            name=db_thread.name,
            createdAt=db_thread.created_at,
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


@router.get("/{thread_id}", response_model=BaseResponse[ReadThreadResponse])
async def get_thread_by_id(thread_id: UUID, db: AsyncSession = Depends(get_db)) -> BaseResponse[ReadThreadResponse]:
    try:
        query = (
            select(Thread)
            .options(selectinload(Thread.user))
            .where(Thread.id == thread_id and not Thread.is_deleted)
        )
        result = await db.execute(query)
        db_thread = result.scalar_one_or_none()

        if not db_thread:
            return BaseResponse(
                status=404,
                message="User not found"
            )

        data = ReadThreadResponse(
            id=db_thread.id,
            userId=db_thread.user_id,
            name=db_thread.name,
            createdAt=db_thread.created_at,
        )

        return BaseResponse(status=200, data=data)

    except Exception as e:
        logger.error("An error occurred", exc_info=e)
        return BaseResponse(
            status=500,
            message="An error occurred"
        )

@router.get("/", response_model=BaseResponse[ReadListThreadsResponse])
async def get_all_threads(request: PagingRequest = Depends(), db: AsyncSession = Depends(get_db)) -> BaseResponse[ReadListThreadsResponse]:
    try:
        pageNumber = request.pageNumber
        maxPerPage = request.maxPerPage

        skip = (pageNumber - 1) * maxPerPage
        limit = maxPerPage

        query = (
            select(Thread)
            .where(Thread.is_deleted == False)
            .options(selectinload(Thread.user))
            .order_by(Thread.created_at.desc())
            .offset(skip)
            .limit(limit))

        result = await db.execute(query)
        db_threads = result.scalars().all()

        threads = [ReadThreadResponse(
            id=db_thread.id,
            userId=db_thread.user_id,
            name=db_thread.name,
            createdAt=db_thread.created_at,
        ) for db_thread in db_threads]

        data = ReadListThreadsResponse(
            threads=threads,
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

@router.patch("/{thread_id}", response_model=BaseResponse[UpdateThreadResponse])
async def update_thread(thread_id: UUID, thread: UpdateThreadRequest, db: AsyncSession = Depends(get_db)) -> BaseResponse[UpdateThreadResponse]:
    try:
        query = (
            select(Thread)
            .where(Thread.id == thread_id and not Thread.is_deleted)
            .options(selectinload(Thread.user))
        )
        result = await db.execute(query)
        db_thread = result.scalar_one_or_none()
        if not db_thread:
            return BaseResponse(
                status=404,
                message="User not found"
            )

        db_thread.name = thread.name if thread.name else db_thread.name

        await db.commit()
        await db.refresh(db_thread)

        data = UpdateThreadResponse(
            id=db_thread.id,
            userId=db_thread.user_id,
            name=db_thread.name,
            createdAt=db_thread.created_at,
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


@router.delete("/{thread_id}", response_model=BaseResponse[DeleteThreadResponse])
async def delete_thread(thread_id: UUID, db: AsyncSession = Depends(get_db)) -> BaseResponse[DeleteThreadResponse]:
    try:
        query = (
            select(Thread)
            .where(Thread.id == thread_id and not Thread.is_deleted)
            .options(selectinload(Thread.user))
        )
        result = await db.execute(query)
        db_thread = result.scalar_one_or_none()
        if not db_thread:
            return BaseResponse(
                status=404,
                message="User not found"
            )

        db_thread.is_deleted = True
        db_thread.deleted_at = datetime.utcnow()
        await db.commit()

        return BaseResponse(
            status=200,
            data=DeleteThreadResponse(
                id=db_thread.id
            )
        )

    except Exception as e:
        logger.error("An error occurred", exc_info=e)
        return BaseResponse(
            status=500,
            message="An error occurred"
        )
