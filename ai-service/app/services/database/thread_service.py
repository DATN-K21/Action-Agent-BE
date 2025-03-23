from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import logging
from app.core.constants import SYSTEM
from app.models.thread import Thread
from app.schemas.base import CursorPagingRequest, ResponseWrapper
from app.schemas.thread import (
    CreateThreadRequest,
    CreateThreadResponse,
    DeleteThreadResponse,
    GetListThreadsResponse,
    GetThreadResponse,
    UpdateThreadRequest,
)

logger = logging.get_logger(__name__)


class ThreadService:
    def __init__(self, db: AsyncSession):
        self.db = db

    @logging.log_function_inputs(logger)
    async def create_thread(self, user_id: str, request: CreateThreadRequest) -> ResponseWrapper[CreateThreadResponse]:
        """Create a new thread in the database."""
        try:
            db_thread = Thread(
                **request.model_dump(),
                user_id=user_id,
                created_by=user_id,
            )
            self.db.add(db_thread)
            await self.db.commit()
            await self.db.refresh(db_thread)

            response_data = CreateThreadResponse.model_validate(db_thread)
            return ResponseWrapper.wrap(status=200, data=response_data)

        except Exception as e:
            logger.error(f"Has error: {str(e)}", exc_info=True)
            await self.db.rollback()
            return ResponseWrapper.wrap(status=500, message="Internal server error")

    @logging.log_function_inputs(logger)
    async def get_thread_by_id(self, user_id: str, thread_id: str) -> ResponseWrapper[GetThreadResponse]:
        """Get a thread by user_id and thread_id."""
        try:
            stmt = (
                select(
                    Thread.id.label("id"),
                    Thread.user_id.label("user_id"),
                    Thread.title.label("title"),
                    Thread.thread_type.label("thread_type"),
                    Thread.created_at.label("created_at"),
                )
                .where(
                    Thread.user_id == user_id,
                    Thread.id == thread_id,
                    Thread.is_deleted.is_(False),
                )
                .limit(1)
            )

            result = await self.db.execute(stmt)
            db_thread = result.mappings().first()

            if not db_thread:
                return ResponseWrapper.wrap(status=404, message="Thread not found")

            response_data = GetThreadResponse.model_validate(db_thread)
            return ResponseWrapper.wrap(status=200, data=response_data)

        except Exception as e:
            logger.error(f"Has error: {str(e)}", exc_info=True)
            return ResponseWrapper.wrap(status=500, message="Internal server error")

    @logging.log_function_inputs(logger)
    async def get_all_threads(self, user_id: str, paging: CursorPagingRequest) -> ResponseWrapper[
        GetListThreadsResponse]:
        """Get all threads of a user."""
        try:
            stmt = (
                select(
                    Thread.id.label("id"),
                    Thread.user_id.label("user_id"),
                    Thread.title.label("title"),
                    Thread.thread_type.label("thread_type"),
                    Thread.created_at.label("created_at"),
                )
                .where(
                    Thread.user_id == user_id,
                    Thread.is_deleted.is_(False),
                )
                .order_by(Thread.created_at.desc())
            )

            if paging.cursor:
                stmt = stmt.where(Thread.created_at < datetime.fromisoformat(paging.cursor))

            stmt = stmt.limit(paging.max_per_page)
            result = await self.db.execute(stmt)
            db_threads = result.mappings().all()

            prev_cursor = db_threads[0].created_at.isoformat() if db_threads else None
            next_cursor = db_threads[-1].created_at.isoformat() if db_threads else None

            response_data = GetListThreadsResponse(
                threads=[GetThreadResponse.model_validate(db_thread) for db_thread in db_threads],
                cursor=paging.cursor,
                next_cursor=next_cursor,
                prev_cursor=prev_cursor,
            )
            return ResponseWrapper.wrap(status=200, data=response_data)

        except Exception as e:
            logger.exception(f"Has error: {str(e)}", exc_info=True)
            return ResponseWrapper.wrap(status=500, message="Internal server error")

    @logging.log_function_inputs(logger)
    async def update_thread(
            self, user_id: str, thread_id: str, thread: UpdateThreadRequest
    ) -> ResponseWrapper[CreateThreadResponse]:
        """Update a thread."""
        try:
            stmt = (
                update(Thread)
                .where(
                    Thread.user_id == user_id,
                    Thread.id == thread_id,
                    Thread.is_deleted.is_(False),
                )
                .values(**thread.model_dump(exclude_unset=True))
                .returning(Thread)
            )

            result = await self.db.execute(stmt)
            db_thread = result.scalar_one_or_none()
            if not db_thread:
                return ResponseWrapper.wrap(status=404, message="Thread not found")

            await self.db.commit()
            await self.db.refresh(db_thread)

            response_data = CreateThreadResponse.model_validate(db_thread)
            return ResponseWrapper.wrap(status=200, data=response_data)

        except Exception as e:
            logger.error(f"Has error: {str(e)}", exc_info=True)
            await self.db.rollback()
            return ResponseWrapper.wrap(status=500, message="Internal server error")

    @logging.log_function_inputs(logger)
    async def delete_thread(
            self, user_id: str, thread_id: str, deleted_by: str = SYSTEM
    ) -> ResponseWrapper[DeleteThreadResponse]:
        """Delete a thread."""
        try:
            stmt = (
                update(Thread)
                .where(
                    Thread.user_id == user_id,
                    Thread.id == thread_id,
                    Thread.is_deleted.is_(False),
                )
                .values(
                    is_deleted=True,
                    deleted_at=datetime.now(),
                )
                .returning(Thread.id.label("id"), Thread.user_id.label("user_id"))
            )

            result = await self.db.execute(stmt)
            deleted_thread = result.mappings().first()
            if not deleted_thread:
                return ResponseWrapper.wrap(status=404, message="Thread not found")

            await self.db.commit()
            response_data = DeleteThreadResponse.model_validate(deleted_thread)
            return ResponseWrapper.wrap(status=200, data=response_data)

        except Exception as e:
            logger.error(f"Has error: {str(e)}", exc_info=True)
            await self.db.rollback()
            return ResponseWrapper.wrap(status=500, message="Internal server error")
