from datetime import datetime

from fastapi import APIRouter, Depends, Header
from langchain.prompts import PromptTemplate
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload

from app.api.deps import SessionDep
from app.core import logging
from app.db_models.thread import Thread
from app.schemas.base import CursorPagingRequest, MessageResponse, ResponseWrapper
from app.schemas.thread import (
    CreateThreadRequest,
    CreateThreadResponse,
    GetThreadResponse,
    GetThreadsResponse,
    UpdateThreadRequest,
    UpdateThreadResponse,
)
from app.services.llm_service import get_llm_chat_model

logger = logging.get_logger(__name__)

router = APIRouter(prefix="/thread", tags=["Thread"])


@router.get("/get-all", summary="Get threads of a user.", response_model=ResponseWrapper[GetThreadsResponse])
async def aget_all_threads(session: SessionDep, paging: CursorPagingRequest = Depends(), x_user_id: str = Header(None)):
    try:
        statement = (
            select(Thread)
            .options(selectinload(Thread.assistant))
            .where(
                Thread.user_id == x_user_id,
                Thread.is_deleted.is_(False),
            )
            .order_by(Thread.created_at.desc())
        )

        if paging.cursor:
            statement = statement.where(Thread.created_at < datetime.fromisoformat(paging.cursor))

        statement = statement.limit(paging.max_per_page)
        result = await session.execute(statement)
        threads = result.mappings().all()

        prev_cursor = threads[0].created_at.isoformat() if threads else None
        next_cursor = threads[-1].created_at.isoformat() if threads else None

        response_data = GetThreadsResponse(
            threads=[GetThreadResponse.model_validate(thread) for thread in threads],
            cursor=paging.cursor,
            next_cursor=next_cursor,
            prev_cursor=prev_cursor,
        )
        return ResponseWrapper.wrap(status=200, data=response_data)

    except Exception as e:
        logger.exception(f"Has error: {str(e)}", exc_info=True)
        return ResponseWrapper.wrap(status=500, message="Internal server error")


@router.post("/create", summary="Create a new thread.", response_model=ResponseWrapper[CreateThreadResponse])
async def acreate_new_thread(session: SessionDep, request: CreateThreadRequest, x_user_id: str = Header(None), x_user_role: str = Header(None)):
    try:
        thread = Thread(
            **request.model_dump(),
            user_id=x_user_id,
            created_by=x_user_id,
        )
        session.add(thread)
        await session.commit()
        await session.refresh(thread)

        response_data = CreateThreadResponse.model_validate(thread)
        return ResponseWrapper.wrap(status=200, data=response_data)

    except Exception as e:
        logger.exception("Create thread failed: %s", str(e), exc_info=True)
        await session.rollback()
        return ResponseWrapper.wrap(status=500, message="Internal server error")


@router.get("/{thread_id}/get-detail", summary="Get thread details.", response_model=ResponseWrapper[GetThreadResponse])
async def aget_thread_by_id(session: SessionDep, thread_id: str, x_user_id: str = Header(None)):
    try:
        statement = (
            select(Thread)
            .options(selectinload(Thread.assistant))
            .where(
                Thread.user_id == x_user_id,
                Thread.id == thread_id,
                Thread.is_deleted.is_(False),
            )
            .limit(1)
        )

        result = await session.execute(statement)
        thread = result.mappings().first()

        if not thread:
            return ResponseWrapper.wrap(status=404, message="Thread not found")

        response_data = GetThreadResponse.model_validate(thread)
        return ResponseWrapper.wrap(status=200, data=response_data)

    except Exception as e:
        logger.exception("Has error: %s", str(e))
        return ResponseWrapper.wrap(status=500, message="Internal server error")


@router.patch("/{thread_id}/update", summary="Update thread information.", response_model=ResponseWrapper[UpdateThreadResponse])
async def update_thread(session: SessionDep, thread_id: str, request: UpdateThreadRequest, x_user_id: str = Header(None)):
    try:
        statement = (
            update(Thread)
            .where(
                Thread.user_id == x_user_id,
                Thread.id == thread_id,
                Thread.is_deleted.is_(False),
            )
            .values(**request.model_dump(exclude_unset=True))
        )

        result = await session.execute(statement)
        thread = result.scalar_one_or_none()
        if not thread:
            return ResponseWrapper.wrap(status=404, message="Thread not found")

        await session.commit()
        await session.refresh(thread)

        response_data = UpdateThreadResponse.model_validate(thread)
        return ResponseWrapper.wrap(status=200, data=response_data)

    except Exception as e:
        logger.exception("Update thread failed: %s", str(e), exc_info=True)
        await session.rollback()
        return ResponseWrapper.wrap(status=500, message="Internal server error")


@router.delete("/{thread_id}/delete", summary="Delete a thread.", response_model=ResponseWrapper[MessageResponse])
async def delete_thread(session: SessionDep, thread_id: str, x_user_id: str = Header(None)):
    try:
        statement = (
            update(Thread)
            .where(
                Thread.user_id == x_user_id,
                Thread.id == thread_id,
                Thread.is_deleted.is_(False),
            )
            .values(is_deleted=True, deleted_at=datetime.now())
        )

        await session.execute(statement)
        await session.commit()

        response_data = MessageResponse(message="Thread deleted successfully")
        return ResponseWrapper.wrap(status=200, data=response_data)

    except Exception as e:
        logger.exception("Delete thread failed: %s", str(e), exc_info=True)
        await session.rollback()
        return ResponseWrapper.wrap(status=500, message="Internal server error")


@router.post("/{thread_id}/generate-title", summary="Generate title from the content.", response_model=ResponseWrapper[UpdateThreadResponse])
async def generate_title(
    session: SessionDep,
    thread_id: str,
    x_user_id: str = Header(None),
):
    try:
        # Check the thread
        statement = (
            select(Thread.id)
            .where(
                Thread.user_id == x_user_id,
                Thread.id == thread_id,
                Thread.is_deleted.is_(False),
            )
            .limit(1)
        )

        result = await session.execute(statement)
        thread = result.scalar_one_or_none()

        if thread is None:
            return ResponseWrapper.wrap(status=404, message="Thread not found")

        # Get the thread messages
        # TODO: get messages from the thread
        # This is a placeholder for the actual message retrieval logic.
        # ...
        messages = []
        if not messages:
            return ResponseWrapper.wrap(status=404, message="Thread not found")

        thread_messages_str = "".join([f"{message.type}: {message.content}\n" for message in messages])

        # Invoke the model to generate a title
        model = get_llm_chat_model()
        prompt = PromptTemplate(
            template="""
You are a helpful assistant that generates a concise and descriptive title for a thread based on its content.
Given the following content, please generate a suitable title:
{content}

# Requrements:
1. The title should be concise and descriptive.
2. It should capture the main theme or topic of the content.
3. Avoid using special characters or excessive punctuation.
4. The title should be suitable for a general audience.
5. The title should be no longer than 10 words.
            """,
            input_variables=["content"],
        )
        chain = prompt | model
        llm_response = await chain.ainvoke({"content": thread_messages_str})
        gen_title = llm_response.content.replace("'", "") if llm_response and isinstance(llm_response.content, str) else "General topic"
        logger.info(f"Generated title: |{gen_title}|")

        # Update the thread title in the database
        statement = (
            update(Thread)
            .where(
                Thread.user_id == x_user_id,
                Thread.id == thread_id,
                Thread.is_deleted.is_(False),
            )
            .values(title=gen_title)
        )

        await session.execute(statement)
        await session.commit()
        await session.refresh(thread)

        response_data = UpdateThreadResponse.model_validate(thread)
        return ResponseWrapper.wrap(status=200, data=response_data)

    except Exception as e:
        logger.exception("Has error: %s", str(e))
        await session.rollback()
        return ResponseWrapper.wrap(status=500, message="Internal server error")
