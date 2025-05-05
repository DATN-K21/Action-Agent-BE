from datetime import datetime
from typing import Optional

from fastapi import Depends
from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.sql.elements import or_

from app.core import logging
from app.core.session import get_db_session
from app.models.extension_assistant import ExtensionAssistant
from app.schemas.base import ResponseWrapper, PagingRequest
from app.schemas.extension_assistant import CreateExtensionAssistantRequest, CreateExtensionAssistantResponse, \
    GetExtensionAssistantsResponse, GetExtensionAssistantResponse, UpdateExtensionAssistantRequest, \
    UpdateExtensionAssistantResponse, DeleteExtensionAssistantResponse, GetExtensionsOfAssistantResponse, \
    GetExtensionOfAssistantResponse

logger = logging.get_logger(__name__)


class ExtensionAssistantService:
    def __init__(self, db: AsyncSession):
        self.db = db

    @logging.log_function_inputs(logger)
    async def create_extension_assistant(self, request: CreateExtensionAssistantRequest) -> ResponseWrapper[
        CreateExtensionAssistantResponse]:
        """Create a new extension-assistant in the database."""
        try:
            db_extension_assistant = ExtensionAssistant(
                **request.model_dump()
            )
            self.db.add(db_extension_assistant)
            await self.db.commit()
            await self.db.refresh(db_extension_assistant)

            response_data = CreateExtensionAssistantResponse.model_validate(db_extension_assistant)
            return ResponseWrapper.wrap(status=200, data=response_data)

        except Exception as e:
            logger.exception("Has error: %s", str(e))
            await self.db.rollback()
            return ResponseWrapper.wrap(status=500, message="Internal server error")

    @logging.log_function_inputs(logger)
    async def get_extension_assistant_by_id(self, extension_assistant_id: str) -> ResponseWrapper[
        GetExtensionAssistantResponse]:
        """Get an assistant by user_id and assistant_id."""
        try:
            stmt = (
                select(
                    ExtensionAssistant.id.label("id"),
                    ExtensionAssistant.assistant_id.label("assistant_id"),
                    ExtensionAssistant.extension_id.label("extension_id"),
                    ExtensionAssistant.created_at.label("created_at"),
                )
                .where(
                    ExtensionAssistant.id == extension_assistant_id,
                    ExtensionAssistant.is_deleted.is_(False),
                )
                .limit(1)
            )

            result = await self.db.execute(stmt)
            db_extension_assistant = result.mappings().first()

            if not db_extension_assistant:
                return ResponseWrapper.wrap(status=404, message="Extension-Assistant not found")

            response_data = GetExtensionAssistantResponse.model_validate(db_extension_assistant)
            return ResponseWrapper.wrap(status=200, data=response_data)

        except Exception as e:
            logger.exception("Has error: %s", str(e))
            return ResponseWrapper.wrap(status=500, message="Internal server error")

    @logging.log_function_inputs(logger)
    async def list_extension_assistants(
            self,
            paging: PagingRequest,
            assistant_id: Optional[str] = None,
            extension_id: Optional[str] = None,
    ) -> ResponseWrapper[GetExtensionAssistantsResponse]:
        """Get list of extension-assistants of a user."""
        try:
            page_number = paging.page_number
            max_per_page = paging.max_per_page

            # COUNT total connected apps
            count_stmt = select(func.count(ExtensionAssistant.id)).where(
                or_(assistant_id is None, ExtensionAssistant.assistant_id == assistant_id),
                or_(extension_id is None, ExtensionAssistant.extension_id == extension_id),
                ExtensionAssistant.is_deleted.is_(False),
            )
            count_result = await self.db.execute(count_stmt)
            total_extension_assistants = count_result.scalar_one()
            logger.info(f"total_extension_assistants: {total_extension_assistants}")
            if total_extension_assistants == 0:
                return ResponseWrapper.wrap(status=200, data=
                GetExtensionAssistantsResponse(
                    extension_assistants=[],
                    page_number=page_number,
                    max_per_page=max_per_page,
                    total_page=0
                )
                                            )

            total_pages = (total_extension_assistants + max_per_page - 1) // max_per_page

            # GET connected apps
            query = (
                select(ExtensionAssistant)
                .where(
                    or_(assistant_id is None, ExtensionAssistant.assistant_id == assistant_id),
                    or_(extension_id is None, ExtensionAssistant.extension_id == extension_id),
                    ExtensionAssistant.is_deleted.is_(False),
                )
                .offset((page_number - 1) * max_per_page)
                .limit(max_per_page)
                .order_by(ExtensionAssistant.created_at.desc())
            )

            result = await self.db.execute(query)
            extension_assistants = result.scalars().all()
            wrapped_extension_assistant = [GetExtensionAssistantResponse.model_validate(extension_assistant) for
                                           extension_assistant
                                           in
                                           extension_assistants]
            return ResponseWrapper.wrap(status=200, data=
            GetExtensionAssistantsResponse(
                extension_assistants=wrapped_extension_assistant,
                page_number=page_number,
                max_per_page=max_per_page,
                total_page=total_pages
            )
                                        )
        except Exception as e:
            logger.exception("Has error: %s", str(e))
            return ResponseWrapper.wrap(status=500, message="Internal server error")

    @logging.log_function_inputs(logger)
    async def update_extension_assistant(
            self,
            extension_assistant_id: str,
            extension_assistant: UpdateExtensionAssistantRequest,
    ) -> ResponseWrapper[UpdateExtensionAssistantResponse]:
        """Update an extension-assistant."""
        try:
            stmt = (
                update(ExtensionAssistant)
                .where(
                    ExtensionAssistant.id == extension_assistant_id,
                    ExtensionAssistant.is_deleted.is_(False),
                )
                .values(**extension_assistant.model_dump(exclude_unset=True))
                .returning(ExtensionAssistant)
            )

            result = await self.db.execute(stmt)
            db_extension_assistant = result.scalar_one_or_none()
            if not db_extension_assistant:
                return ResponseWrapper.wrap(status=404, message="Extension-Assistant not found")

            await self.db.commit()
            await self.db.refresh(db_extension_assistant)

            response_data = UpdateExtensionAssistantResponse.model_validate(db_extension_assistant)
            return ResponseWrapper.wrap(status=200, data=response_data)

        except Exception as e:
            logger.exception("Has error: %s", str(e))
            await self.db.rollback()
            return ResponseWrapper.wrap(status=500, message="Internal server error")

    @logging.log_function_inputs(logger)
    async def delete_extension_assistant(
            self,
            extension_assistant_id: str,
    ) -> ResponseWrapper[DeleteExtensionAssistantResponse]:
        """Delete an extension-assistant."""
        try:
            stmt = (
                update(ExtensionAssistant)
                .where(
                    ExtensionAssistant.id == extension_assistant_id,
                    ExtensionAssistant.is_deleted.is_(False),
                )
                .values(
                    is_deleted=True,
                    deleted_at=datetime.now(),
                )
                .returning(
                    ExtensionAssistant.id.label("id"),
                    ExtensionAssistant.assistant_id.label("assistant_id"),
                    ExtensionAssistant.extension_id.label("extension_id")
                )
            )

            result = await self.db.execute(stmt)
            deleted_extension_assistant = result.mappings().first()
            if not deleted_extension_assistant:
                return ResponseWrapper.wrap(status=404, message="Extension-Assistant not found")

            await self.db.commit()
            response_data = DeleteExtensionAssistantResponse.model_validate(deleted_extension_assistant)
            return ResponseWrapper.wrap(status=200, data=response_data)

        except Exception as e:
            logger.exception("Has error: %s", str(e))
            await self.db.rollback()
            return ResponseWrapper.wrap(status=500, message="Internal server error")

    @logging.log_function_inputs(logger)
    async def list_extensions_of_assistant(
            self,
            assistant_id: str,
            paging: PagingRequest,
    ) -> ResponseWrapper[GetExtensionsOfAssistantResponse]:
        """List all extensions of an assistant"""
        try:
            page_number = paging.page_number
            max_per_page = paging.max_per_page

            # COUNT total connected apps
            count_stmt = select(func.count(ExtensionAssistant.id)).where(
                ExtensionAssistant.assistant_id == assistant_id,
                ExtensionAssistant.is_deleted.is_(False),
            )
            count_result = await self.db.execute(count_stmt)
            total_extension_assistants = count_result.scalar_one()
            logger.info(f"total_extension_assistants: {total_extension_assistants}")
            if total_extension_assistants == 0:
                return ResponseWrapper.wrap(status=200, data=
                GetExtensionsOfAssistantResponse(
                    extensions=[],
                    page_number=page_number,
                    max_per_page=max_per_page,
                    total_page=0
                )
                                            )
            total_pages = (total_extension_assistants + max_per_page - 1) // max_per_page

            # GET connected apps
            query = (
                select(ExtensionAssistant)
                .options(
                    selectinload(ExtensionAssistant.extension)
                )
                .where(
                    ExtensionAssistant.assistant_id == assistant_id,
                    ExtensionAssistant.is_deleted.is_(False),
                )
                .offset((page_number - 1) * max_per_page)
                .limit(max_per_page)
                .order_by(ExtensionAssistant.created_at.desc())
            )

            result = await self.db.execute(query)
            extension_assistants = result.scalars().all()
            wrapped_extensions = [GetExtensionOfAssistantResponse(
                id=extension_assistant.id,
                user_id=extension_assistant.extension.user_id,
                assistant_id=extension_assistant.assistant_id,
                extension_id=extension_assistant.extension_id,
                app_name=extension_assistant.extension.app_name,
                connected_account_id=extension_assistant.extension.connected_account_id,
                auth_scheme=extension_assistant.extension.auth_scheme,
                auth_value=extension_assistant.extension.auth_value,
                created_at=extension_assistant.created_at
            ) for
                extension_assistant
                in
                extension_assistants]
            return ResponseWrapper.wrap(status=200, data=
            GetExtensionsOfAssistantResponse(
                extensions=wrapped_extensions,
                page_number=page_number,
                max_per_page=max_per_page,
                total_page=total_pages
            )
                                        )
        except Exception as e:
            logger.exception("Has error: %s", str(e))
            return ResponseWrapper.wrap(status=500, message="Internal server error")


def get_extension_assistant_service(
        db: AsyncSession = Depends(get_db_session),
):
    return ExtensionAssistantService(db=db)
