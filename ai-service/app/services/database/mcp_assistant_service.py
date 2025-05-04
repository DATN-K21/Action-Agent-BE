from datetime import datetime
from typing import Optional

from fastapi import Depends
from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.elements import or_

from app.core import logging
from app.core.session import get_db_session
from app.models.mcp_assistant import McpAssistant
from app.schemas.base import ResponseWrapper, PagingRequest
from app.schemas.mcp_assistant import CreateMcpAssistantRequest, CreateMcpAssistantResponse, GetMcpAssistantResponse, \
    GetMcpAssistantsResponse, UpdateMcpAssistantRequest, UpdateMcpAssistantResponse, DeleteMcpAssistantResponse, \
    GetMcpsOfAssistantResponse, GetMcpOfAssistantResponse

logger = logging.get_logger(__name__)


# noinspection DuplicatedCode
class McpAssistantService:
    def __init__(self, db: AsyncSession):
        self.db = db

    @logging.log_function_inputs(logger)
    async def create_mcp_assistant(self, request: CreateMcpAssistantRequest) -> ResponseWrapper[
        CreateMcpAssistantResponse]:
        """Create a new extension-assistant in the database."""
        try:
            db_mcp_assistant = McpAssistant(
                **request.model_dump()
            )
            self.db.add(db_mcp_assistant)
            await self.db.commit()
            await self.db.refresh(db_mcp_assistant)

            response_data = CreateMcpAssistantResponse.model_validate(db_mcp_assistant)
            return ResponseWrapper.wrap(status=200, data=response_data)

        except Exception as e:
            logger.exception("Has error: %s", str(e))
            await self.db.rollback()
            return ResponseWrapper.wrap(status=500, message="Internal server error")

    @logging.log_function_inputs(logger)
    async def get_mcp_assistant_by_id(self, mcp_assistant_id: str) -> ResponseWrapper[
        GetMcpAssistantResponse]:
        """Get a mcp-assistant by mcp-assistant_id."""
        try:
            stmt = (
                select(
                    McpAssistant.id.label("id"),
                    McpAssistant.assistant_id.label("assistant_id"),
                    McpAssistant.mcp_id.label("mcp_id"),
                    McpAssistant.created_at.label("created_at"),
                )
                .where(
                    McpAssistant.id == mcp_assistant_id,
                    McpAssistant.is_deleted.is_(False),
                )
                .limit(1)
            )

            result = await self.db.execute(stmt)
            db_mcp_assistant = result.mappings().first()

            if not db_mcp_assistant:
                return ResponseWrapper.wrap(status=404, message="MCP-Assistant not found")

            response_data = GetMcpAssistantResponse.model_validate(db_mcp_assistant)
            return ResponseWrapper.wrap(status=200, data=response_data)

        except Exception as e:
            logger.exception("Has error: %s", str(e))
            return ResponseWrapper.wrap(status=500, message="Internal server error")

    @logging.log_function_inputs(logger)
    async def get_list_mcp_assistants(
            self,
            paging: PagingRequest,
            assistant_id: Optional[str] = None,
            mcp_id: Optional[str] = None,
    ) -> ResponseWrapper[GetMcpAssistantsResponse]:
        """Get list of mcp-assistants of a user."""
        try:
            page_number = paging.page_number
            max_per_page = paging.max_per_page

            # COUNT total connected apps
            count_stmt = select(func.count(McpAssistant.id)).where(
                or_(assistant_id is None, McpAssistant.assistant_id == assistant_id),
                or_(mcp_id is None, McpAssistant.mcp_id == mcp_id),
                McpAssistant.is_deleted.is_(False),
            )
            count_result = await self.db.execute(count_stmt)
            total_mcp_assistants = count_result.scalar_one()
            logger.info(f"total_mcp_assistants: {total_mcp_assistants}")
            if total_mcp_assistants == 0:
                return ResponseWrapper.wrap(status=200, data=
                GetMcpAssistantsResponse(
                    mcp_assistants=[],
                    page_number=page_number,
                    max_per_page=max_per_page,
                    total_page=0
                )
                                            )

            total_pages = (total_mcp_assistants + max_per_page - 1) // max_per_page

            # GET connected apps
            query = (
                select(McpAssistant)
                .where(
                    or_(assistant_id is None, McpAssistant.assistant_id == assistant_id),
                    or_(mcp_id is None, McpAssistant.mcp_id == mcp_id),
                    McpAssistant.is_deleted.is_(False),
                )
                .offset((page_number - 1) * max_per_page)
                .limit(max_per_page)
                .order_by(McpAssistant.created_at.desc())
            )

            result = await self.db.execute(query)
            mcp_assistant = result.scalars().all()
            wrapped_mcp_assistant = [GetMcpAssistantResponse.model_validate(connected_app) for connected_app
                                     in
                                     mcp_assistant]
            return ResponseWrapper.wrap(status=200, data=
            GetMcpAssistantsResponse(
                mcp_assistants=wrapped_mcp_assistant,
                page_number=page_number,
                max_per_page=max_per_page,
                total_page=total_pages
            )
                                        )
        except Exception as e:
            logger.exception("Has error: %s", str(e))
            return ResponseWrapper.wrap(status=500, message="Internal server error")

    @logging.log_function_inputs(logger)
    async def update_mcp_assistant(
            self,
            mcp_assistant_id: str,
            mcp_assistant: UpdateMcpAssistantRequest,
    ) -> ResponseWrapper[UpdateMcpAssistantResponse]:
        """Update a mcp-assistant."""
        try:
            stmt = (
                update(McpAssistant)
                .where(
                    McpAssistant.id == mcp_assistant_id,
                    McpAssistant.is_deleted.is_(False),
                )
                .values(**mcp_assistant.model_dump(exclude_unset=True))
                .returning(McpAssistant)
            )

            result = await self.db.execute(stmt)
            db_mcp_assistant = result.scalar_one_or_none()
            if not db_mcp_assistant:
                return ResponseWrapper.wrap(status=404, message="Mcp-Assistant not found")

            await self.db.commit()
            await self.db.refresh(db_mcp_assistant)

            response_data = UpdateMcpAssistantResponse.model_validate(db_mcp_assistant)
            return ResponseWrapper.wrap(status=200, data=response_data)

        except Exception as e:
            logger.exception("Has error: %s", str(e))
            await self.db.rollback()
            return ResponseWrapper.wrap(status=500, message="Internal server error")

    @logging.log_function_inputs(logger)
    async def delete_mcp_assistant(
            self,
            mcp_assistant_id: str,
    ) -> ResponseWrapper[DeleteMcpAssistantResponse]:
        """Delete a mcp-assistant."""
        try:
            stmt = (
                update(McpAssistant)
                .where(
                    McpAssistant.id == mcp_assistant_id,
                    McpAssistant.is_deleted.is_(False),
                )
                .values(
                    is_deleted=True,
                    deleted_at=datetime.now(),
                )
                .returning(
                    McpAssistant.id.label("id"),
                    McpAssistant.assistant_id.label("assistant_id"),
                    McpAssistant.mcp_id.label("mcp_id")
                )
            )

            result = await self.db.execute(stmt)
            deleted_mcp_assistant = result.mappings().first()
            if not deleted_mcp_assistant:
                return ResponseWrapper.wrap(status=404, message="MCP-Assistant not found")

            await self.db.commit()
            response_data = DeleteMcpAssistantResponse.model_validate(deleted_mcp_assistant)
            return ResponseWrapper.wrap(status=200, data=response_data)

        except Exception as e:
            logger.exception("Has error: %s", str(e))
            await self.db.rollback()
            return ResponseWrapper.wrap(status=500, message="Internal server error")

    @logging.log_function_inputs(logger)
    async def list_mcps_of_assistant(
            self,
            assistant_id: str,
            paging: PagingRequest,
    ) -> ResponseWrapper[GetMcpsOfAssistantResponse]:
        """List all extensions of an assistant"""
        try:
            page_number = paging.page_number
            max_per_page = paging.max_per_page

            # COUNT total connected apps
            count_stmt = select(func.count(McpAssistant.id)).where(
                McpAssistant.assistant_id == assistant_id,
                McpAssistant.is_deleted.is_(False),
            )
            count_result = await self.db.execute(count_stmt)
            total_extension_assistants = count_result.scalar_one()
            logger.info(f"total_extension_assistants: {total_extension_assistants}")
            if total_extension_assistants == 0:
                return ResponseWrapper.wrap(status=200, data=
                GetMcpsOfAssistantResponse(
                    mcps=[],
                    page_number=page_number,
                    max_per_page=max_per_page,
                    total_page=0
                )
                                            )
            total_pages = (total_extension_assistants + max_per_page - 1) // max_per_page

            # GET connected apps
            query = (
                select(McpAssistant)
                .where(
                    McpAssistant.assistant_id == assistant_id,
                    McpAssistant.is_deleted.is_(False),
                )
                .offset((page_number - 1) * max_per_page)
                .limit(max_per_page)
                .order_by(McpAssistant.created_at.desc())
            )

            result = await self.db.execute(query)
            mcp_assistants = result.scalars().all()
            wrapped_mcps = [GetMcpOfAssistantResponse(
                id=mcp_assistant.id,
                user_id=mcp_assistant.mcp.user_id,
                assistant_id=mcp_assistant.assistant_id,
                mcp_id=mcp_assistant.mcp_id,
                mcp_name=mcp_assistant.mcp.mcp_name,
                url=mcp_assistant.mcp.url,
                connection_type=mcp_assistant.mcp.connection_type,
                created_at=mcp_assistant.created_at,
            ) for
                mcp_assistant
                in
                mcp_assistants]
            return ResponseWrapper.wrap(status=200, data=
            GetMcpsOfAssistantResponse(
                mcps=wrapped_mcps,
                page_number=page_number,
                max_per_page=max_per_page,
                total_page=total_pages
            )
                                        )
        except Exception as e:
            logger.exception("Has error: %s", str(e))
            return ResponseWrapper.wrap(status=500, message="Internal server error")


def get_mcp_assistant_service(
        db: AsyncSession = Depends(get_db_session),
):
    return McpAssistantService(db=db)
