import traceback
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import logging
from app.models.connected_app import ConnectedApp

logger = logging.get_logger(__name__)


class ConnectedAppService:
    def __init__(self, db: AsyncSession):
        self.db = db

    @logging.log_function_inputs(logger)
    async def get_account_id(self, user_id: str, app_name) -> Optional[str]:
        """Get a connected account id by user_id and app_name."""
        try:
            query = (
                select(ConnectedApp.connected_account_id)
                .where(
                    ConnectedApp.user_id == user_id,
                    ConnectedApp.app_name == app_name,
                    ConnectedApp.is_deleted.is_(False),
                )
                .limit(1)
            )

            result = await self.db.execute(query)
            connected_account_id = result.scalar_one()
            return connected_account_id

        except Exception as e:
            logger.error(f"Has error: {str(e)}", exc_info=True)
            return None

    @logging.log_function_inputs(logger)
    async def create_connected_app(
        self, user_id: str, app_name: str, connected_account_id: str, auth_scheme: str = "Bearer"
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
            logger.error(f"Has error: {str(e)}", exc_info=True)
            return False
