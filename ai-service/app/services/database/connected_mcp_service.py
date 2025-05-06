from datetime import datetime
from typing import Optional

from fastapi import Depends
from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import logging
from app.core.constants import SYSTEM
from app.core.session import get_db_session
from app.models.connected_mcp import ConnectedMcp
from app.schemas.base import PagingRequest, ResponseWrapper
from app.schemas.connected_mcp import GetConnectedMcpResponse, GetConnectedMcpsResponse, CreateConnectedMcpResponse, \
    UpdateConnectedMcpRequest, UpdateConnectedMcpResponse, DeleteConnectedMcpResponse

logger = logging.get_logger(__name__)


# noinspection DuplicatedCode
class ConnectedMcpService:
    def __init__(self, db: AsyncSession):
        self.db = db

    @logging.log_function_inputs(logger)
    async def create_connected_mcp(
            self, user_id: str, mcp_name: str, url: str, connection_type: Optional[str] = None
    ) -> ResponseWrapper[CreateConnectedMcpResponse]:
        """Create a connected mcp."""
        try:
            db_thread = ConnectedMcp(
                user_id=user_id,
                mcp_name=mcp_name,
                url=url,
                connection_type=connection_type
            )
            self.db.add(db_thread)
            await self.db.commit()
            await self.db.refresh(db_thread)

            response_data = CreateConnectedMcpResponse.model_validate(db_thread)
            return ResponseWrapper.wrap(status=200, data=response_data)

        except Exception as e:
            logger.error(f"Has error: {str(e)}", exc_info=True)
            await self.db.rollback()
            return ResponseWrapper.wrap(status=500, message="Internal server error")

    @logging.log_function_inputs(logger)
    async def update_connected_mcp(
            self, user_id: str, connected_mcp_id: str, connected_app: UpdateConnectedMcpRequest
    ) -> ResponseWrapper[UpdateConnectedMcpResponse]:
        """Update a thread."""
        try:
            stmt = (
                update(ConnectedMcp)
                .where(
                    ConnectedMcp.user_id == user_id,
                    ConnectedMcp.id == connected_mcp_id,
                    ConnectedMcp.is_deleted.is_(False),
                )
                .values(**connected_app.model_dump(exclude_unset=True))
                .returning(ConnectedMcp)
            )

            result = await self.db.execute(stmt)
            db_thread = result.scalar_one_or_none()
            if not db_thread:
                return ResponseWrapper.wrap(status=404, message="Thread not found")

            await self.db.commit()
            await self.db.refresh(db_thread)

            response_data = UpdateConnectedMcpResponse.model_validate(db_thread)
            return ResponseWrapper.wrap(status=200, data=response_data)

        except Exception as e:
            logger.error(f"Has error: {str(e)}", exc_info=True)
            await self.db.rollback()
            return ResponseWrapper.wrap(status=500, message="Internal server error")

    @logging.log_function_inputs(logger)
    async def delete_connected_mcp(
            self, user_id: str, connected_mcp_id: str, deleted_by: str = SYSTEM
    ) -> ResponseWrapper[DeleteConnectedMcpResponse]:
        """Delete a thread."""
        try:
            stmt = (
                update(ConnectedMcp)
                .where(
                    ConnectedMcp.user_id == user_id,
                    ConnectedMcp.id == connected_mcp_id,
                    ConnectedMcp.is_deleted.is_(False),
                )
                .values(
                    is_deleted=True,
                    deleted_at=datetime.now(),
                )
                .returning(ConnectedMcp.id.label("id"), ConnectedMcp.user_id.label("user_id"))
            )

            result = await self.db.execute(stmt)
            deleted_thread = result.mappings().first()
            if not deleted_thread:
                return ResponseWrapper.wrap(status=404, message="Connected MCP not found")

            await self.db.commit()
            response_data = DeleteConnectedMcpResponse.model_validate(deleted_thread)
            return ResponseWrapper.wrap(status=200, data=response_data)

        except Exception as e:
            logger.error(f"Has error: {str(e)}", exc_info=True)
            await self.db.rollback()
            return ResponseWrapper.wrap(status=500, message="Internal server error")

    @logging.log_function_inputs(logger)
    async def get_connected_mcp(self, user_id: str, connected_mcp_id: str) -> ResponseWrapper[GetConnectedMcpResponse]:
        """Get a connected app by user_id and app_name."""
        try:
            query = (
                select(ConnectedMcp)
                .where(
                    ConnectedMcp.user_id == user_id,
                    ConnectedMcp.id == connected_mcp_id,
                    ConnectedMcp.is_deleted.is_(False),
                )
                .limit(1)
            )

            result = await self.db.execute(query)
            connected_mcp = result.scalar_one()

            return ResponseWrapper.wrap(
                status=200,
                data=GetConnectedMcpResponse.model_validate(connected_mcp)
            )

        except Exception as e:
            logger.error(f"Has error: {str(e)}", exc_info=True)
            return ResponseWrapper.wrap(
                status=500,
                message="Internal server error",
            )

    @logging.log_function_inputs(logger)
    async def get_all_connected_mcps(self, user_id: str, paging: Optional[PagingRequest] = None) -> ResponseWrapper[
        GetConnectedMcpsResponse]:
        """Get all connected apps by user_id."""
        try:
            if paging is None:
                query = (
                    select(ConnectedMcp)
                    .where(
                        ConnectedMcp.user_id == user_id,
                        ConnectedMcp.is_deleted.is_(False),
                    )
                    .order_by(ConnectedMcp.created_at.desc())
                )

                result = await self.db.execute(query)
                connected_mcps = result.scalars().all()
                wrapped_connected_mcps = [GetConnectedMcpResponse.model_validate(connected_mcp) for connected_mcp in
                                          connected_mcps]
                return ResponseWrapper.wrap(
                    status=200,
                    data=GetConnectedMcpsResponse(
                        connected_mcps=wrapped_connected_mcps,
                        page_number=1,
                        max_per_page=len(connected_mcps),
                        total_page=1
                    )
                )

            page_number = paging.page_number
            max_per_page = paging.max_per_page

            # COUNT total connected apps
            count_stmt = select(func.count(ConnectedMcp.id)).where(
                ConnectedMcp.user_id == user_id,
                ConnectedMcp.is_deleted.is_(False),
            )
            count_result = await self.db.execute(count_stmt)
            total_connected_apps = count_result.scalar_one()
            logger.info(f"total_connected_apps: {total_connected_apps}")
            if total_connected_apps == 0:
                return ResponseWrapper.wrap(
                    status=200,
                    data=GetConnectedMcpsResponse(
                        connected_mcps=[],
                        page_number=page_number,
                        max_per_page=max_per_page,
                        total_page=0
                    )
                )
            # Calculate total pages
            total_pages = (total_connected_apps + max_per_page - 1) // max_per_page

            # GET connected apps
            query = (
                select(ConnectedMcp)
                .where(
                    ConnectedMcp.user_id == user_id,
                    ConnectedMcp.is_deleted.is_(False),
                )
                .offset((page_number - 1) * max_per_page)
                .limit(max_per_page)
                .order_by(ConnectedMcp.created_at.desc())
            )

            result = await self.db.execute(query)
            connected_mcps = result.scalars().all()
            wrapped_connected_mcps = [GetConnectedMcpResponse.model_validate(connected_mcp) for connected_mcp in
                                      connected_mcps]
            return ResponseWrapper.wrap(
                status=200,
                data=GetConnectedMcpsResponse(
                    connected_mcps=wrapped_connected_mcps,
                    page_number=page_number,
                    max_per_page=max_per_page,
                    total_page=total_pages
                )
            )

        except Exception as e:
            logger.error(f"Has error: {str(e)}", exc_info=True)
            return ResponseWrapper.wrap(status=500, message="Internal server error")


def get_connected_mcp_service(db: AsyncSession = Depends(get_db_session)):
    return ConnectedMcpService(db)
