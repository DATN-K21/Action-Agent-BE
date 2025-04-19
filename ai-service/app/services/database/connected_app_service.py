from typing import Optional

from fastapi import Depends
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import logging
from app.core.session import get_db_session
from app.models.connected_app import ConnectedApp
from app.schemas._base import PagingRequest
from app.schemas.connected_app import GetAllConnectedAppsRequest, GetConnectedAppResponse

logger = logging.get_logger(__name__)


class ConnectedAppService:
    def __init__(self, db: AsyncSession):
        self.db = db

    @logging.log_function_inputs(logger)
    async def get_account_id(
        self,
        user_id: str,
        app_name: str,
    ) -> Optional[str]:
        """Get a connected account id by user_id and app_name."""
        try:
            stmt = (
                select(ConnectedApp.connected_account_id)
                .where(
                    ConnectedApp.user_id == user_id,
                    ConnectedApp.app_name == app_name,
                    ConnectedApp.is_deleted.is_(False),
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
    async def create_connected_app(
        self,
        user_id: str,
        app_name: str,
        connected_account_id: str,
        auth_scheme: str = "Bearer",
    ) -> bool:
        """Create a connected app."""
        try:
            connected_app_db = ConnectedApp(
                user_id=user_id,
                app_name=app_name,
                connected_account_id=connected_account_id,
                auth_scheme=auth_scheme,
            )

            self.db.add(connected_app_db)
            await self.db.commit()
            return True

        except Exception as e:
            logger.exception("Has error: %s", str(e))
            await self.db.rollback()
            return False

    @logging.log_function_inputs(logger)
    async def delete_connected_app(
        self,
        user_id: str,
        app_name: str,
    ) -> bool:
        """Delete a connected app."""
        try:
            stmt = (
                update(ConnectedApp)
                .where(
                    ConnectedApp.user_id == user_id,
                    ConnectedApp.app_name == app_name,
                    ConnectedApp.is_deleted.is_(False),
                )
                .values(is_deleted=True)
            )

            result = await self.db.execute(stmt)
            if result.rowcount == 0:
                logger.warning(f"Connected app not found for user_id: {user_id}, app_name: {app_name}")
                return False

            await self.db.commit()
            logger.info(f"Connected app deleted for user_id: {user_id}, app_name: {app_name}")
            return True

        except Exception as e:
            logger.exception("Has error: %s", str(e))
            await self.db.rollback()
            return False

    @logging.log_function_inputs(logger)
    async def get_connected_app(
        self,
        user_id: str,
        app_name: str,
    ) -> Optional[GetConnectedAppResponse]:
        """Get a connected app by user_id and app_name."""
        try:
            query = (
                select(ConnectedApp)
                .where(
                    ConnectedApp.user_id == user_id,
                    ConnectedApp.app_name == app_name,
                    ConnectedApp.is_deleted.is_(False),
                )
                .limit(1)
            )

            result = await self.db.execute(query)
            connected_app = result.scalar_one()

            return GetConnectedAppResponse.model_validate(connected_app)

        except Exception as e:
            logger.exception("Has error: %s", str(e))
            return None

    @logging.log_function_inputs(logger)
    async def get_all_connected_apps(
        self,
        user_id: str,
        paging: PagingRequest,
    ) -> GetAllConnectedAppsRequest:
        """Get all connected apps by user_id."""
        try:
            page_number = paging.page_number
            max_per_page = paging.max_per_page

            # COUNT total connected apps
            count_stmt = select(func.count(ConnectedApp.id)).where(
                ConnectedApp.user_id == user_id,
                ConnectedApp.is_deleted.is_(False),
            )
            count_result = await self.db.execute(count_stmt)
            total_connected_apps = count_result.scalar_one()
            logger.info(f"total_connected_apps: {total_connected_apps}")
            if total_connected_apps == 0:
                return GetAllConnectedAppsRequest(
                    connected_apps=[],
                    page_number=page_number,
                    max_per_page=max_per_page,
                    total_page=0
                )
            total_pages = (total_connected_apps + max_per_page - 1) // max_per_page

            # GET connected apps
            query = (
                select(ConnectedApp)
                .where(
                    ConnectedApp.user_id == user_id,
                    ConnectedApp.is_deleted.is_(False),
                )
                .offset((page_number - 1) * max_per_page)
                .limit(max_per_page)
                .order_by(ConnectedApp.created_at.desc())
            )

            result = await self.db.execute(query)
            connected_apps = result.scalars().all()
            wrapped_connected_apps = [GetConnectedAppResponse.model_validate(connected_app) for connected_app in connected_apps]
            return GetAllConnectedAppsRequest(
                connected_apps=wrapped_connected_apps,
                page_number=page_number,
                max_per_page=max_per_page,
                total_page=total_pages
            )

        except Exception as e:
            logger.exception("Has error: %s", str(e))
            return GetAllConnectedAppsRequest(
                connected_apps=[],
                page_number=paging.page_number,
                max_per_page=paging.max_per_page,
                total_page=0
            )


def get_connected_app_service(db: AsyncSession = Depends(get_db_session)):
    return ConnectedAppService(db)