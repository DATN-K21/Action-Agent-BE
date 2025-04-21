from datetime import datetime
from typing import Optional

from fastapi import Depends
from sqlalchemy import or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import logging
from app.core.agents.agent_manager import AgentManager, get_agent_manager
from app.core.constants import SYSTEM
from app.core.session import get_db_session
from app.models.thread import Thread
from app.prompts.prompt_templates import get_title_generation_prompt_template
from app.schemas.base import CursorPagingRequest, ResponseWrapper
from app.schemas.thread import (
    CreateThreadRequest,
    CreateThreadResponse,
    DeleteThreadResponse,
    GetListThreadsResponse,
    GetThreadResponse,
    UpdateThreadRequest,
    UpdateThreadResponse,
)
from app.services.llm_service import get_llm_chat_model

logger = logging.get_logger(__name__)


class ThreadService:
    def __init__(self, db: AsyncSession, agent_manager: AgentManager):
        self.db = db
        self.agent_manager = agent_manager

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
            logger.exception("Has error: %s", str(e))
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
            logger.exception("Has error: %s", str(e))
            return ResponseWrapper.wrap(status=500, message="Internal server error")

    @logging.log_function_inputs(logger)
    async def get_all_threads(
            self,
            user_id: str,
            paging: CursorPagingRequest,
            thread_type: Optional[str] = None,
    ) -> ResponseWrapper[GetListThreadsResponse]:
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
                    or_(Thread.thread_type == thread_type, thread_type is None),  # type: ignore
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
            self,
            user_id: str,
            thread_id: str,
            thread: UpdateThreadRequest,
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
            logger.exception("Has error: %s", str(e))
            await self.db.rollback()
            return ResponseWrapper.wrap(status=500, message="Internal server error")

    @logging.log_function_inputs(logger)
    async def delete_thread(
            self,
            user_id: str,
            thread_id: str,
            deleted_by: str = SYSTEM,
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
            logger.exception("Has error: %s", str(e))
            await self.db.rollback()
            return ResponseWrapper.wrap(status=500, message="Internal server error")

    @logging.log_function_inputs(logger)
    async def generate_thread_title(
            self,
            user_id: str,
            thread_id: str,
    ) -> ResponseWrapper[UpdateThreadResponse]:
        """
        Generate a thread title based on the thread's messages.
        """
        try:
            # Check the thread
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
                return ResponseWrapper.wrap(status=404, message="Thread not found")

            # Get the thread messages
            agent = self.agent_manager.get_agent(name="chat-agent")
            if agent is None:
                return ResponseWrapper.wrap(status=404, message="Agent not found")
            state = await agent.async_get_state(thread_id)  # type: ignore
            if state is None or "messages" not in state.values:
                return ResponseWrapper.wrap(status=404, message="Thread not found")

            messages = state.values["messages"]
            if not messages:
                return ResponseWrapper.wrap(status=404, message="Thread not found")

            thread_messages_str = "".join([f"{message.type}: {message.content}\n" for message in messages])

            # Invoke the model to generate a title
            model = get_llm_chat_model()
            prompt = get_title_generation_prompt_template()
            chain = prompt | model
            llm_response = await chain.ainvoke({"content": thread_messages_str})
            gen_title = llm_response.content.replace("'", "") if llm_response and isinstance(llm_response.content,
                                                                                             str) else "General topic"
            logger.info(f"Generated title: |{gen_title}|")

            # Update the thread title in the database
            stmt = (
                update(Thread)
                .where(
                    Thread.user_id == user_id,
                    Thread.id == thread_id,
                    Thread.is_deleted.is_(False),
                )
                .values(title=gen_title)
                .returning(
                    Thread.id.label("id"),
                    Thread.user_id.label("user_id"),
                    Thread.title.label("title"),
                    Thread.thread_type.label("thread_type"),
                    Thread.created_at.label("created_at"),
                )
            )

            result = await self.db.execute(stmt)
            db_thread = result.mappings().first()
            if not db_thread:
                return ResponseWrapper.wrap(status=404, message="Thread not found")

            await self.db.commit()
            response_data = CreateThreadResponse.model_validate(db_thread)
            return ResponseWrapper.wrap(status=200, data=response_data)

        except Exception as e:
            logger.exception("Has error: %s", str(e))
            await self.db.rollback()
            return ResponseWrapper.wrap(status=500, message="Internal server error")


def get_thread_service(
        db: AsyncSession = Depends(get_db_session),
        agent_manager: AgentManager = Depends(get_agent_manager),
):
    return ThreadService(db=db, agent_manager=agent_manager)
