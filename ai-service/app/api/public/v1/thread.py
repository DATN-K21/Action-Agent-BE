from datetime import datetime

from fastapi import APIRouter, Depends, Header
from langchain.prompts import PromptTemplate
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload

from app.api.deps import SessionDep
from app.core import logging
from app.core.graph.checkpoint.utils import (
    convert_checkpoint_tuple_to_messages,
    get_checkpoint_tuples,
)
from app.db_models.thread import Thread
from app.schemas.base import CursorPagingRequest, MessageResponse, ResponseWrapper
from app.schemas.thread import (
    CreateThreadRequest,
    CreateThreadResponse,
    GetHistoryResponse,
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
        threads = result.scalars().all()

        prev_cursor = threads[0].created_at.isoformat() if threads else None
        next_cursor = threads[-1].created_at.isoformat() if threads else None

        # Convert threads to response format with proper assistant serialization
        thread_responses = []
        for thread in threads:
            thread_dict = {
                "id": thread.id,
                "user_id": thread.user_id,
                "title": thread.title,
                "assistant_id": thread.assistant_id,
                "created_at": thread.created_at,
                "assistant": None,
            }

            # Convert assistant object to dictionary if it exists
            if thread.assistant:
                thread_dict["assistant"] = {
                    "id": thread.assistant.id,
                    "name": thread.assistant.name,
                    "description": thread.assistant.description,
                    "system_prompt": thread.assistant.system_prompt,
                    "assistant_type": thread.assistant.assistant_type,
                    "provider": thread.assistant.provider,
                    "model_name": thread.assistant.model_name,
                    "temperature": thread.assistant.temperature,
                    "ask_human": thread.assistant.ask_human,
                    "interrupt": thread.assistant.interrupt,
                    "created_at": thread.assistant.created_at,
                }

            thread_responses.append(GetThreadResponse(**thread_dict))

        response_data = GetThreadsResponse(
            threads=thread_responses,
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

        response_data = CreateThreadResponse.model_validate(thread, from_attributes=True)
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
        thread = result.scalar_one_or_none()

        if not thread:
            return ResponseWrapper.wrap(status=404, message="Thread not found")

        # Create thread dictionary with proper assistant serialization
        thread_dict = {
            "id": thread.id,
            "user_id": thread.user_id,
            "title": thread.title,
            "assistant_id": thread.assistant_id,
            "created_at": thread.created_at,
            "assistant": None,
        }

        # Convert assistant object to dictionary if it exists
        if thread.assistant:
            thread_dict["assistant"] = {
                "id": thread.assistant.id,
                "name": thread.assistant.name,
                "description": thread.assistant.description,
                "system_prompt": thread.assistant.system_prompt,
                "assistant_type": thread.assistant.assistant_type,
                "provider": thread.assistant.provider,
                "model_name": thread.assistant.model_name,
                "temperature": thread.assistant.temperature,
                "ask_human": thread.assistant.ask_human,
                "interrupt": thread.assistant.interrupt,
                "created_at": thread.assistant.created_at,
            }

        response_data = GetThreadResponse(**thread_dict)
        return ResponseWrapper.wrap(status=200, data=response_data)

    except Exception as e:
        logger.exception("Has error: %s", str(e))
        return ResponseWrapper.wrap(status=500, message="Internal server error")


@router.patch("/{thread_id}/update", summary="Update thread information.", response_model=ResponseWrapper[UpdateThreadResponse])
async def update_thread(session: SessionDep, thread_id: str, request: UpdateThreadRequest, x_user_id: str = Header(None)):
    try:
        # First check if thread exists
        check_statement = select(Thread).where(
            Thread.user_id == x_user_id,
            Thread.id == thread_id,
            Thread.is_deleted.is_(False),
        )

        check_result = await session.execute(check_statement)
        existing_thread = check_result.scalar_one_or_none()

        if not existing_thread:
            return ResponseWrapper.wrap(status=404, message="Thread not found")

        # Update the thread
        update_statement = (
            update(Thread)
            .where(
                Thread.user_id == x_user_id,
                Thread.id == thread_id,
                Thread.is_deleted.is_(False),
            )
            .values(**request.model_dump(exclude_unset=True))
        )

        await session.execute(update_statement)
        await session.commit()  # Fetch the updated thread
        updated_statement = select(Thread).where(
            Thread.user_id == x_user_id,
            Thread.id == thread_id,
            Thread.is_deleted.is_(False),
        )

        updated_result = await session.execute(updated_statement)
        updated_thread = updated_result.scalar_one()

        response_data = UpdateThreadResponse.model_validate(updated_thread, from_attributes=True)
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
    try:  # Check the thread
        statement = (
            select(Thread)
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

        # Get the thread messages from the latest checkpoint
        checkpoint_tuple = await get_checkpoint_tuples(thread_id)
        messages = (
            convert_checkpoint_tuple_to_messages(checkpoint_tuple)
            if checkpoint_tuple
            else []
        )
        if not messages:
            # Let's update the thread title to a default value (New thread)
            gen_title = "New thread"
            logger.info(f"No messages found, setting default title: |{gen_title}|")
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
            response_data = UpdateThreadResponse.model_validate(thread, from_attributes=True)
            return ResponseWrapper.wrap(status=200, data=response_data)

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

        # Fetch the updated thread
        updated_statement = select(Thread).where(
            Thread.user_id == x_user_id,
            Thread.id == thread_id,
            Thread.is_deleted.is_(False),
        )

        updated_result = await session.execute(updated_statement)
        updated_thread = updated_result.scalar_one()

        response_data = UpdateThreadResponse.model_validate(updated_thread, from_attributes=True)
        return ResponseWrapper.wrap(status=200, data=response_data)

    except Exception as e:
        logger.exception("Has error: %s", str(e))
        await session.rollback()
        return ResponseWrapper.wrap(status=500, message="Internal server error")


@router.post("/{thread_id}/get-history", summary="Get history of the thread", response_model=ResponseWrapper[GetHistoryResponse])
async def get_thread_history(
    session: SessionDep,
    thread_id: str,
    x_user_id: str = Header(None),
):
    try:
        # Check the thread
        statement = (
            select(Thread)
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

        # Get the thread messages from the latest checkpoint
        checkpoint_tuple = await get_checkpoint_tuples(thread_id)
        messages = convert_checkpoint_tuple_to_messages(checkpoint_tuple) if checkpoint_tuple else []
        if not messages:
            return ResponseWrapper.wrap(status=404, message="Thread not found")

        response_data = GetHistoryResponse(
            user_id=x_user_id,
            thread_id=thread_id,
            assistant_id=thread.assistant_id,
            messages=messages,
        )
        return ResponseWrapper.wrap(status=200, data=response_data)

    except Exception as e:
        logger.exception("Has error: %s", str(e))
        return ResponseWrapper.wrap(status=500, message="Internal server error")
