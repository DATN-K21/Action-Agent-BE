from datetime import datetime
from typing import BinaryIO, Optional, cast

from fastapi import UploadFile
from langchain_core.documents.base import Blob
from langchain_core.runnables import RunnableConfig
from sqlalchemy import and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import logging
from app.core.constants import SYSTEM
from app.core.enums import MessageFormat, MessageRole
from app.core.utils.uploading import convert_ingestion_input_to_blob, ingest_runnable
from app.models.message import Message
from app.models.thread import Thread
from app.models.thread_file import ThreadFile
from app.prompts.prompt_templates import get_title_generation_prompt_template
from app.schemas.base import CursorPagingRequest, ResponseWrapper
from app.schemas.history import GetHistoryMessageResponse, GetHistoryMessagesResponse, MessageInteruption
from app.schemas.ingest import IngestFileResponse
from app.schemas.thread import (
    CreateThreadRequest,
    CreateThreadResponse,
    DeleteThreadResponse,
    GetListThreadsResponse,
    GetThreadResponse,
    UpdateThreadRequest,
)
from app.services.model_service import get_openai_model

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
    async def get_all_threads(
        self, user_id: str, paging: CursorPagingRequest, thread_type: Optional[str] = None
    ) -> ResponseWrapper[GetListThreadsResponse]:
        """Get all threads of a user."""
        try:
            conditions = [
                Thread.user_id == user_id,
                Thread.is_deleted.is_(False),
            ]
            if thread_type:
                conditions.append(Thread.thread_type == thread_type)

            stmt = (
                select(
                    Thread.id.label("id"),
                    Thread.user_id.label("user_id"),
                    Thread.title.label("title"),
                    Thread.thread_type.label("thread_type"),
                    Thread.created_at.label("created_at"),
                )
                .where(and_(*conditions))
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

    @logging.log_function_inputs(logger)
    async def get_history_messages(self, user_id: str, thread_id: str, paging: CursorPagingRequest) -> ResponseWrapper[GetHistoryMessagesResponse]:
        """Get history messages of a thread."""
        try:
            conditions = [
                Thread.is_deleted.is_(False),
                Thread.user_id == user_id,
                Thread.id == thread_id,
            ]
            if paging.cursor:
                conditions.append(Thread.created_at < datetime.fromisoformat(paging.cursor))

            stmt = (
                select(
                    Thread.id.label("thread_id"),
                    Message.id.label("id"),
                    Message.content.label("content"),
                    Message.role.label("role"),
                    Message.format.label("format"),
                    Message.created_at.label("created_at"),
                    Message.question.label("question"),
                    Message.choices.label("choices"),
                    Message.answer_idx.label("answer_idx"),
                    Message.file_id.label("file_name"),
                )
                .select_from(Thread)
                .outerjoin(Message, Thread.id == Message.thread_id)
                .where(and_(*conditions))
                .order_by(Message.created_at.desc())
                .limit(paging.max_per_page)
            )

            result = await self.db.execute(stmt)
            db_messages = result.mappings().all()
            logger.debug(f"Get history messages: user_id={user_id}, thread_id={thread_id}, messages={db_messages}, length={len(db_messages)}")

            if not db_messages:
                logger.warning(f"Thread not found: user_id={user_id}, thread_id={thread_id}")
                return ResponseWrapper.wrap(status=404, message="Invalid thread")

            # If there is only one message and it is None, return an empty list
            if len(db_messages) == 1 and db_messages[0].id is None:
                next_cursor = None
                prev_cursor = None
            else:
                next_cursor = db_messages[-1].created_at.isoformat()
                prev_cursor = db_messages[0].created_at.isoformat()

            response_data = GetHistoryMessagesResponse(
                user_id=user_id,
                thread_id=thread_id,
                messages=[],
                cursor=paging.cursor,
                next_cursor=next_cursor if next_cursor else None,
                prev_cursor=prev_cursor if prev_cursor else None,
            )
            for db_message in db_messages:
                if db_message.id:
                    message = GetHistoryMessageResponse.model_validate(db_message)
                    if db_message.question:
                        message.interuption = MessageInteruption(
                            question=db_message.question,
                            choices=db_message.choices.split(",") if db_message.choices else [],
                            answer_idx=db_message.answer_idx,
                        )
                    response_data.messages.append(message)

            return ResponseWrapper.wrap(status=200, data=response_data)

        except Exception as e:
            logger.error(f"Has error: {str(e)}", exc_info=True)
            return ResponseWrapper.wrap(status=500, message="Internal server error")

    # @logging.log_function_inputs(logger)
    # async def insert_history_messages(self, user_id: str, thread_id: str, role: MessageRole, ) -> ResponseWrapper[bool]:
    #     """Insert a history message."""
    #     try:
    #         db_message = Message(
    #             **request.model_dump(),
    #             user_id=user_id,
    #             thread_id=thread_id,
    #             created_by=user_id,
    #         )
    #         self.db.add(db_message)
    #         await self.db.commit()
    #         await self.db.refresh(db_message)

    #         response_data = CreateThreadResponse.model_validate(db_message)
    #         return ResponseWrapper.wrap(status=200, data=response_data)

    #     except Exception as e:
    #         logger.error(f"Has error: {str(e)}", exc_info=True)
    #         return ResponseWrapper.wrap(status=500, message="Internal server error")

    @logging.log_function_inputs(logger)
    async def upload_file_to_thread(self, user_id: str, thread_id: str, file: UploadFile) -> ResponseWrapper[IngestFileResponse]:
        """Upload a file to a thread."""
        try:
            # 1. Check the thread
            stmt = (
                select(Thread.id)
                .where(
                    Thread.user_id == user_id,
                    Thread.id == thread_id,
                    Thread.is_deleted.is_(False),
                )
                .limit(1)
            )
            db_thread = (await self.db.execute(stmt)).scalar_one_or_none()
            if db_thread is None:
                logger.warning(f"Thread not found: user_id={user_id}, thread_id={thread_id}")
                return ResponseWrapper.wrap(status=404, message="Thread not found")

            # 2. Check the file
            file_name = file.filename
            file_size = file.file._file.tell()  # type: ignore
            file.file.seek(0)  # Reset file pointer to the beginning
            logger.info(f"File name: {file_name}, File size: {file_size}")
            if file_size > 10 * 1024 * 1024:  # 10 MB limit
                logger.warning(f"File size exceeds the limit: {file_size} bytes")
                return ResponseWrapper.wrap(status=400, message="File size exceeds the limit of 10 MB")

            # 3.1. Save the file to table ThreadFile
            db_file = ThreadFile(
                thread_id=thread_id,
                url="",
                name=file_name,
                size=file_size,
                status=3,
            )
            self.db.add(db_file)

            # 3.2. Save the file to table Message
            db_message = Message(
                thread_id=thread_id,
                role=MessageRole.HUMAN,
                format=MessageFormat.FILE,
                content=file_name,
                file_id=db_file.id,
            )
            self.db.add(db_message)
            await self.db.commit()

            # 4. Ingest the file
            file_blob: Blob = convert_ingestion_input_to_blob(file)
            config = RunnableConfig(configurable={"thread_id": thread_id})
            ingest_runnable.batch(cast(list[BinaryIO], [file_blob]), config)
            response_data = IngestFileResponse(
                user_id=user_id,
                thread_id=thread_id,
                is_success=True,
                output="Files ingested successfully",
            )

            response_data = IngestFileResponse.model_validate(db_message)
            return ResponseWrapper.wrap(status=200, data=response_data)

        except Exception as e:
            logger.error(f"Has error: {str(e)}", exc_info=True)
            await self.db.rollback()
            return ResponseWrapper.wrap(status=500, message="Internal server error")

    @logging.log_function_inputs(logger)
    async def generate_title(self, user_id: str, thread_id: str) -> ResponseWrapper[GetThreadResponse]:
        """Generate title for the thread."""
        try:
            # 1. Check the thread
            stmt = (
                select(Thread.id)
                .where(
                    Thread.user_id == user_id,
                    Thread.id == thread_id,
                    Thread.is_deleted.is_(False),
                )
                .limit(1)
            )
            db_thread = (await self.db.execute(stmt)).scalar_one_or_none()
            if db_thread is None:
                logger.warning(f"Thread not found: user_id={user_id}, thread_id={thread_id}")
                return ResponseWrapper.wrap(status=404, message="Thread not found")

            # 2. Get the first message of the thread
            stmt = (
                select(Message.content)
                .where(
                    Message.thread_id == thread_id,
                    Message.is_deleted.is_(False),
                    Message.role == MessageRole.HUMAN,
                    Message.format == MessageFormat.MARKDOWN,
                )
                .order_by(Message.created_at.asc())
                .limit(1)
            )

            db_message = (await self.db.execute(stmt)).scalar_one_or_none()
            if db_message is None:
                logger.warning(f"Message not found: user_id={user_id}, thread_id={thread_id}")
                return ResponseWrapper.wrap(status=404, message="Message not found")

            # 3. Generate title using LLM
            model = get_openai_model()
            prompt = get_title_generation_prompt_template()
            chain = prompt | model
            title = await chain.ainvoke({"content": db_message})
            logger.info(f"Generated title: {title}")

            # 4. Update the thread with the generated title
            stmt = (
                update(Thread)
                .where(
                    Thread.user_id == user_id,
                    Thread.id == thread_id,
                    Thread.is_deleted.is_(False),
                )
                .values(title=title)
                .returning(Thread.id.label("id"), Thread.user_id.label("user_id"))
            )
            result = await self.db.execute(stmt)
            updated_thread = result.mappings().first()
            if not updated_thread:
                return ResponseWrapper.wrap(status=404, message="Thread not found")

            await self.db.commit()
            response_data = GetThreadResponse.model_validate(updated_thread)
            return ResponseWrapper.wrap(status=200, data=response_data)

        except Exception as e:
            logger.error(f"Has error: {str(e)}", exc_info=True)
            await self.db.rollback()
            return ResponseWrapper.wrap(status=500, message="Internal server error")