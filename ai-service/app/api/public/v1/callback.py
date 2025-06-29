from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import select, update
from sqlalchemy.exc import SQLAlchemyError

from app.api.deps import SessionDep
from app.core import logging
from app.core.enums import ConnectionStatus
from app.core.settings import env_settings
from app.db_models.connected_extension import ConnectedExtension
from app.schemas.base import ResponseWrapper

logger = logging.get_logger(__name__)

router = APIRouter(prefix="/callback", tags=["Callback"], include_in_schema=False)


@router.get("/extension/{user_id}/{connected_extension_id}", summary="Handle connection success.")
async def connection_success(
    sessions: SessionDep,
    user_id: str,
    connected_extension_id: str,
    request: Request,
):
    try:
        url = env_settings.FRONTEND_REDIRECT_URL

        connection_status = request.query_params.get("status")
        connected_account_id = request.query_params.get("connectedAccountId")
        app_name = request.query_params.get("appName")

        # Get the connected extension by ID
        result = await sessions.execute(
            select(ConnectedExtension).where(
                ConnectedExtension.id == connected_extension_id,
                ConnectedExtension.user_id == user_id,
                ConnectedExtension.is_deleted.is_(False),
            )
        )

        connected_extension = result.scalar_one_or_none()
        if connected_extension is None:
            return ResponseWrapper(status=404, message="Connected extension not found").to_response()

        if connection_status is None or connected_account_id is None or app_name is None:
            full_url = f"{url}?success=false&message=missing%20parameters"

            statement = (
                update(ConnectedExtension)
                .where(
                    ConnectedExtension.id == connected_extension_id, ConnectedExtension.user_id == user_id, ConnectedExtension.is_deleted.is_(False)
                )
                .values(connection_status=ConnectionStatus.FAILED)
            )
        elif connection_status != "success":
            full_url = f"{url}?success=false&message=connection%20failed%20or%20is%20still%20pending"

            statement = (
                update(ConnectedExtension)
                .where(
                    ConnectedExtension.id == connected_extension_id, ConnectedExtension.user_id == user_id, ConnectedExtension.is_deleted.is_(False)
                )
                .values(connection_status=ConnectionStatus.FAILED)
            )
        else:
            full_url = f"{url}?success=true&message=successfully%20connected"

            statement = (
                update(ConnectedExtension)
                .where(
                    ConnectedExtension.id == connected_extension_id, ConnectedExtension.user_id == user_id, ConnectedExtension.is_deleted.is_(False)
                )
                .values(connection_status=ConnectionStatus.SUCCESS, connected_account_id=connected_account_id)
            )

        await sessions.execute(statement)
        await sessions.commit()

        return RedirectResponse(full_url)

    except SQLAlchemyError as e:
        logger.error(f"Database error when creating connected extension: {e}", exc_info=True)
        await sessions.rollback()

    full_url = f"{url}?success=false&message=failed%20to%20establish%20connection"
    return RedirectResponse(full_url)
