from datetime import datetime

from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import update
from sqlalchemy.exc import SQLAlchemyError

from app.api.deps import SessionDep
from app.core import logging
from app.core.enums import ConnectionStatus
from app.core.settings import env_settings
from app.db_models.connected_extension import ConnectedExtension
from app.schemas.base import ResponseWrapper
from app.services.extensions import extension_service_manager

logger = logging.get_logger(__name__)

router = APIRouter(prefix="/callback", tags=["Callback"], include_in_schema=False)


@router.get("/extension/{user_id}", summary="Handle connection success.")
async def connection_success(
    session: SessionDep,
    user_id: str,
    request: Request,
):
    try:
        url = env_settings.FRONTEND_REDIRECT_URL

        connection_status = request.query_params.get("status")
        connected_account_id = request.query_params.get("connectedAccountId")
        app_name = request.query_params.get("appName")

        if app_name is None:
            return ResponseWrapper(status=400, message="App name is missed").to_response()

        extension_service_info = await extension_service_manager.aget_service_info(app_name)
        if extension_service_info is None or extension_service_info.service_object is None:
            return ResponseWrapper.wrap(status=404, message="Extension Info or Extension Service not found").to_response()

        extension_service = extension_service_info.service_object

        # Create the connected extension
        connected_extension = ConnectedExtension(
            user_id=user_id,
            extension_enum=str(extension_service.get_app_enum()),
            extension_name=extension_service.get_name(),
            connection_status=ConnectionStatus.PENDING,
        )

        session.add(connected_extension)
        await session.flush()
        await session.refresh(connected_extension)

        if connection_status is None or connected_account_id is None or app_name is None:
            full_url = f"{url}?success=false&message=missing%20parameters"

            statement = (
                update(ConnectedExtension)
                .where(
                    ConnectedExtension.id == connected_extension.id,
                    ConnectedExtension.user_id == user_id,
                    ConnectedExtension.is_deleted.is_(False),
                )
                .values(
                    connection_status=ConnectionStatus.FAILED,
                    is_deleted=True,
                    deleted_at=datetime.now(),
                )
            )
        elif connection_status != "success":
            full_url = f"{url}?success=false&message=connection%20failed%20or%20is%20still%20pending"

            statement = (
                update(ConnectedExtension)
                .where(
                    ConnectedExtension.id == connected_extension.id,
                    ConnectedExtension.user_id == user_id,
                    ConnectedExtension.is_deleted.is_(False),
                )
                .values(
                    connection_status=ConnectionStatus.FAILED,
                    is_deleted=True,
                    deleted_at=datetime.now(),
                )
            )
        else:
            full_url = f"{url}?success=true&message=successfully%20connected"

            statement = (
                update(ConnectedExtension)
                .where(
                    ConnectedExtension.id == connected_extension.id,
                    ConnectedExtension.user_id == user_id,
                    ConnectedExtension.is_deleted.is_(False),
                )
                .values(
                    connection_status=ConnectionStatus.SUCCESS,
                    connected_account_id=connected_account_id,
                )
            )

        await session.execute(statement)
        await session.commit()

        return RedirectResponse(full_url)

    except SQLAlchemyError as e:
        logger.error(f"Database error when creating connected extension: {e}", exc_info=True)
        await session.rollback()

    full_url = f"{url}?success=false&message=failed%20to%20establish%20connection"
    return RedirectResponse(full_url)
