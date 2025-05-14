from typing import Optional

from fastapi import Depends
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import logging
from app.core.session import get_db_session
from app.models.connected_extension import ConnectedExtension
from app.schemas.base import PagingRequest, ResponseWrapper
from app.schemas.connected_extension import GetConnectedExtensionResponse, GetConnectedExtensionsResponse

logger = logging.get_logger(__name__)


class ConnectedExtensionService:
    def __init__(self, db: AsyncSession):
        self.db = db

    @logging.log_function_inputs(logger)
    async def get_account_id(
            self,
            user_id: str,
            extension_name: str,
    ) -> Optional[str]:
        """Get a connected account id by user_id and extension_name."""
        try:
            stmt = (
                select(ConnectedExtension.connected_account_id)
                .where(
                    ConnectedExtension.user_id == user_id,
                    ConnectedExtension.extension_name == extension_name,
                    ConnectedExtension.is_deleted.is_(False),
                )
                .limit(1)
            )

            result = await self.db.execute(stmt)
            connected_account_id = result.scalar_one()
            return connected_account_id

        except Exception as e:
            logger.exception("Has error: %s", str(e))
            return None

    @logging.log_function_inputs(logger)
    async def create_connected_extension(
            self,
            user_id: str,
            extension_name: str,
            connected_account_id: str,
            auth_scheme: Optional[str] = None,
    ) -> bool:
        """Create a connected app."""
        try:
            connected_extension_db = ConnectedExtension(
                user_id=user_id,
                extension_name=extension_name,
                connected_account_id=connected_account_id,
                auth_scheme=auth_scheme,
            )

            self.db.add(connected_extension_db)
            await self.db.commit()
            return True

        except Exception as e:
            logger.exception("Has error: %s", str(e))
            await self.db.rollback()
            return False

    @logging.log_function_inputs(logger)
    async def delete_connected_extension(
            self,
            user_id: str,
            extension_name: str,
    ) -> bool:
        """Delete a connected extension."""
        try:
            stmt = (
                update(ConnectedExtension)
                .where(
                    ConnectedExtension.user_id == user_id,
                    ConnectedExtension.extension_name == extension_name,
                    ConnectedExtension.is_deleted.is_(False),
                )
                .values(is_deleted=True)
            )

            result = await self.db.execute(stmt)
            if result.rowcount == 0:
                logger.warning(
                    f"Connected extension not found for user_id: {user_id}, extension_name: {extension_name}")
                return False

            await self.db.commit()
            logger.info(f"Connected extension deleted for user_id: {user_id}, extension_name: {extension_name}")
            return True

        except Exception as e:
            logger.exception("Has error: %s", str(e))
            await self.db.rollback()
            return False

    @logging.log_function_inputs(logger)
    async def get_connected_extension_by_id(
            self,
            user_id: str,
            connected_extension_id: str,
    ) -> ResponseWrapper[GetConnectedExtensionResponse]:
        """Get a connected extension by user_id and extension_name."""
        try:
            query = (
                select(ConnectedExtension)
                .where(
                    ConnectedExtension.user_id == user_id,
                    ConnectedExtension.id == connected_extension_id,
                    ConnectedExtension.is_deleted.is_(False),
                )
                .limit(1)
            )

            result = await self.db.execute(query)
            connected_extension = result.scalar_one()

            data = GetConnectedExtensionResponse.model_validate(connected_extension)

            return ResponseWrapper.wrap(
                status=200,
                data=data,
            )

        except Exception as e:
            logger.exception("Has error: %s", str(e))
            return ResponseWrapper.wrap(status=500, message="Internal server error")

    @logging.log_function_inputs(logger)
    async def list_connected_extensions(
            self,
            user_id: str,
            paging: Optional[PagingRequest] = None
    ) -> ResponseWrapper[GetConnectedExtensionsResponse]:
        """List connected extensions by user_id."""
        try:
            # COUNT total connected apps
            count_stmt = select(
                func.count(ConnectedExtension.id)).where(
                ConnectedExtension.user_id == user_id,
                ConnectedExtension.is_deleted.is_(False),
            )

            count_result = await self.db.execute(count_stmt)
            total_connected_extensions = count_result.scalar_one()
            logger.info(f"total_connected_extensions: {total_connected_extensions}")

            if paging is None:
                paging = PagingRequest(
                    page_number=1,
                    max_per_page=total_connected_extensions if total_connected_extensions > 0 else 1
                )

            page_number = paging.page_number
            max_per_page = paging.max_per_page

            if total_connected_extensions == 0:
                return ResponseWrapper.wrap(
                    status=200,
                    data=GetConnectedExtensionsResponse(
                        connected_extensions=[],
                        page_number=page_number,
                        max_per_page=max_per_page,
                        total_page=0
                    )
                )

            total_pages = (total_connected_extensions + max_per_page - 1) // max_per_page

            # GET connected extensions
            query = (
                select(ConnectedExtension)
                .where(
                    ConnectedExtension.user_id == user_id,
                    ConnectedExtension.is_deleted.is_(False),
                )
                .offset((page_number - 1) * max_per_page)
                .limit(max_per_page)
                .order_by(ConnectedExtension.created_at.desc())
            )

            result = await self.db.execute(query)
            connected_extensions = result.scalars().all()
            wrapped_connected_extensions = [GetConnectedExtensionResponse.model_validate(connected_extension) for
                                            connected_extension in
                                            connected_extensions]
            return ResponseWrapper.wrap(
                status=200,
                data=GetConnectedExtensionsResponse(
                    connected_extensions=wrapped_connected_extensions,
                    page_number=page_number,
                    max_per_page=max_per_page,
                    total_page=total_pages
                )
            )

        except Exception as e:
            logger.exception("Has error: %s", str(e))
            return ResponseWrapper.wrap(status=500, message="Internal server error")


def get_connected_extension_service(db: AsyncSession = Depends(get_db_session)):
    return ConnectedExtensionService(db)
