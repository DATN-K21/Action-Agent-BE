from datetime import datetime

from fastapi import Depends
from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import logging
from app.core.session import get_db_session
from app.models.assistant import Assistant
from app.schemas.assistant import CreateAssistantRequest, CreateAssistantResponse, GetAssistantResponse, \
    GetAssistantsResponse, UpdateAssistantRequest, DeleteAssistantResponse
from app.schemas.base import ResponseWrapper, PagingRequest

logger = logging.get_logger(__name__)


# noinspection DuplicatedCode
class AssistantService:
    def __init__(self, db: AsyncSession):
        self.db = db

    @logging.log_function_inputs(logger)
    async def create_assistant(self, user_id: str, request: CreateAssistantRequest) -> ResponseWrapper[
        CreateAssistantResponse]:
        """Create a new thread in the database."""
        try:
            db_assistant = Assistant(
                **request.model_dump(),
                user_id=user_id,
                created_by=user_id,
            )
            self.db.add(db_assistant)
            await self.db.commit()
            await self.db.refresh(db_assistant)

            response_data = CreateAssistantResponse.model_validate(db_assistant)
            return ResponseWrapper.wrap(status=200, data=response_data)

        except Exception as e:
            logger.exception("Has error: %s", str(e))
            await self.db.rollback()
            return ResponseWrapper.wrap(status=500, message="Internal server error")

    @logging.log_function_inputs(logger)
    async def get_assistant_by_id(self, user_id: str, assistant_id: str) -> ResponseWrapper[GetAssistantResponse]:
        """Get an assistant by user_id and assistant_id."""
        try:
            stmt = (
                select(
                    Assistant.id.label("id"),
                    Assistant.user_id.label("user_id"),
                    Assistant.name.label("name"),
                    Assistant.description.label("description"),
                    Assistant.type.label("type"),
                    Assistant.created_at.label("created_at"),
                )
                .where(
                    Assistant.user_id == user_id,
                    Assistant.id == assistant_id,
                    Assistant.is_deleted.is_(False),
                )
                .limit(1)
            )

            result = await self.db.execute(stmt)
            db_assistant = result.mappings().first()

            if not db_assistant:
                return ResponseWrapper.wrap(status=404, message="Assistant not found")

            response_data = GetAssistantResponse.model_validate(db_assistant)
            return ResponseWrapper.wrap(status=200, data=response_data)

        except Exception as e:
            logger.exception("Has error: %s", str(e))
            return ResponseWrapper.wrap(status=500, message="Internal server error")

    @logging.log_function_inputs(logger)
    async def list_assistants(
            self,
            user_id: str,
            paging: PagingRequest,
    ) -> ResponseWrapper[GetAssistantsResponse]:
        """Get all assistants of a user."""
        try:
            page_number = paging.page_number
            max_per_page = paging.max_per_page

            # COUNT total connected apps
            count_stmt = select(func.count(Assistant.id)).where(
                Assistant.user_id == user_id,
                Assistant.is_deleted.is_(False),
            )
            count_result = await self.db.execute(count_stmt)
            total_assistants = count_result.scalar_one()
            logger.info(f"total_assistants: {total_assistants}")
            if total_assistants == 0:
                return ResponseWrapper.wrap(status=200, data=
                GetAssistantsResponse(
                    assistants=[],
                    page_number=page_number,
                    max_per_page=max_per_page,
                    total_page=0
                )
                                            )

            total_pages = (total_assistants + max_per_page - 1) // max_per_page

            # GET connected apps
            query = (
                select(Assistant)
                .where(
                    Assistant.user_id == user_id,
                    Assistant.is_deleted.is_(False),
                )
                .offset((page_number - 1) * max_per_page)
                .limit(max_per_page)
                .order_by(Assistant.created_at.desc())
            )

            result = await self.db.execute(query)
            assistants = result.scalars().all()
            wrapped_assistants = [GetAssistantResponse.model_validate(assistant) for assistant in
                                  assistants]
            return ResponseWrapper.wrap(status=200, data=
            GetAssistantsResponse(
                assistants=wrapped_assistants,
                page_number=page_number,
                max_per_page=max_per_page,
                total_page=total_pages
            )
                                        )
        except Exception as e:
            logger.exception("Has error: %s", str(e))
            return ResponseWrapper.wrap(status=500, message="Internal server error")

    @logging.log_function_inputs(logger)
    async def update_assistant(
            self,
            user_id: str,
            assistant_id: str,
            assistant: UpdateAssistantRequest,
    ) -> ResponseWrapper[CreateAssistantResponse]:
        """Update an assistant."""
        try:
            stmt = (
                update(Assistant)
                .where(
                    Assistant.user_id == user_id,
                    Assistant.id == assistant_id,
                    Assistant.is_deleted.is_(False),
                )
                .values(**assistant.model_dump(exclude_unset=True))
                .returning(Assistant)
            )

            result = await self.db.execute(stmt)
            db_assistant = result.scalar_one_or_none()
            if not db_assistant:
                return ResponseWrapper.wrap(status=404, message="Assistant not found")

            await self.db.commit()
            await self.db.refresh(db_assistant)

            response_data = CreateAssistantResponse.model_validate(db_assistant)
            return ResponseWrapper.wrap(status=200, data=response_data)

        except Exception as e:
            logger.exception("Has error: %s", str(e))
            await self.db.rollback()
            return ResponseWrapper.wrap(status=500, message="Internal server error")

    @logging.log_function_inputs(logger)
    async def delete_assistant(
            self,
            user_id: str,
            assistant_id: str,
    ) -> ResponseWrapper[DeleteAssistantResponse]:
        """Delete an assistant."""
        try:
            stmt = (
                update(Assistant)
                .where(
                    Assistant.user_id == user_id,
                    Assistant.id == assistant_id,
                    Assistant.is_deleted.is_(False),
                )
                .values(
                    is_deleted=True,
                    deleted_at=datetime.now(),
                )
                .returning(Assistant.id.label("id"), Assistant.user_id.label("user_id"))
            )

            result = await self.db.execute(stmt)
            deleted_assistant = result.mappings().first()
            if not deleted_assistant:
                return ResponseWrapper.wrap(status=404, message="Thread not found")

            await self.db.commit()
            response_data = DeleteAssistantResponse.model_validate(deleted_assistant)
            return ResponseWrapper.wrap(status=200, data=response_data)

        except Exception as e:
            logger.exception("Has error: %s", str(e))
            await self.db.rollback()
            return ResponseWrapper.wrap(status=500, message="Internal server error")


def get_assistant_service(
        db: AsyncSession = Depends(get_db_session),
):
    return AssistantService(db=db)
