from datetime import datetime

from fastapi import APIRouter, Header
from sqlalchemy import select, update

from app.api.deps import SessionDep
from app.core import logging
from app.core.enums import ConnectionStatus
from app.db_models.connected_extension import ConnectedExtension
from app.schemas.base import ResponseWrapper
from app.schemas.extension import ActiveAccountResponse, CheckConnectionResponse, DeleteConnectionResponse
from app.services.extensions import extension_service_manager

logger = logging.get_logger(__name__)

router = APIRouter(prefix="/extension", tags=["Extension"])


@router.post(path="/active", summary="Initialize the connection.", response_model=ResponseWrapper[ActiveAccountResponse])
async def active(
    session: SessionDep,
    extension_enum: str,
    x_user_id: str = Header(None),
):
    try:
        # Get the extension service
        extension_service_info = extension_service_manager.get_service(extension_enum)
        if extension_service_info is None or extension_service_info.service_object is None:
            return ResponseWrapper.wrap(status=404, message="Extension Info or Extension Service not found").to_response()

        # Get the service object
        extension_service = extension_service_info.service_object

        # Create connected extension
        connected_extension = ConnectedExtension(
            user_id=x_user_id,
            extension_enum=extension_service.get_app_enum(),
            extension_name=extension_service.get_name(),
            connection_status=ConnectionStatus.PENDING,
        )

        session.add(connected_extension)
        await session.commit()
        await session.refresh(connected_extension)

        # Initialize the connection
        connection_request = extension_service.initialize_connection(user_id=x_user_id, connected_extension_id=str(connected_extension.id))

        if connection_request is None:
            response_data = ActiveAccountResponse(is_existed=True, redirect_url=None)
            return ResponseWrapper.wrap(status=200, data=response_data).to_response()

        response_data = ActiveAccountResponse(is_existed=False, redirect_url=connection_request.redirectUrl)
        return ResponseWrapper.wrap(status=200, data=response_data).to_response()

    except Exception as e:
        logger.exception("Error activating the extension: %s", str(e), exc_info=True)
        # Rollback the session in case of an error
        await session.rollback()
        return ResponseWrapper.wrap(status=500, message="Internal server error").to_response()


@router.post(path="/disconnect", summary="Disconnect the account.", response_model=ResponseWrapper[DeleteConnectionResponse])
async def disconnect(
    session: SessionDep,
    connected_extension_id: str,
    x_user_id: str = Header(None),
    x_user_role: str = Header(None),
):
    try:
        # Get connected extension

        if x_user_role in ["admin", "super admin"]:
            statement = (
                select(ConnectedExtension).where(ConnectedExtension.id == connected_extension_id, ConnectedExtension.is_deleted.is_(False)).limit(1)
            )
        else:
            statement = (
                select(ConnectedExtension)
                .where(
                    ConnectedExtension.id == connected_extension_id, ConnectedExtension.user_id == x_user_id, ConnectedExtension.is_deleted.is_(False)
                )
                .limit(1)
            )

        result = await session.execute(statement)
        connected_extension = result.scalar_one_or_none()

        if connected_extension is None:
            return ResponseWrapper.wrap(status=404, message="Connected Extension not found").to_response()

        # Get the extension service
        extension_service_info = extension_service_manager.get_service(str(connected_extension.extension_enum))
        if extension_service_info is None or extension_service_info.service_object is None:
            return ResponseWrapper.wrap(status=404, message="Extension Info or Extension Service not found").to_response()

        extension_service = extension_service_info.service_object

        # Get the account id
        if connected_extension.connected_account_id is None:
            return ResponseWrapper.wrap(status=404, message="Account not found").to_response()

        account_id = str(connected_extension.connected_account_id)

        # Disconnect the account
        result = extension_service.disconnect(account_id)

        # Delete the account from the database
        if result.status == "success":
            if x_user_role in ["admin", "super admin"]:
                statement = (
                    update(ConnectedExtension)
                    .where(
                        ConnectedExtension.id == connected_extension.connected_account_id,
                        ConnectedExtension.is_deleted.is_(False),
                    )
                    .values(
                        is_deleted=True,
                        deleted_at=datetime.now(),
                    )
                )

            else:
                statement = (
                    update(ConnectedExtension)
                    .where(
                        ConnectedExtension.id == connected_extension.connected_account_id,
                        ConnectedExtension.user_id == connected_extension.user_id,
                        ConnectedExtension.is_deleted.is_(False),
                    )
                    .values(
                        is_deleted=True,
                        deleted_at=datetime.now(),
                    )
                )

            await session.execute(statement)
            await session.commit()

        response_data = DeleteConnectionResponse.model_validate(result)
        return ResponseWrapper.wrap(status=200, data=response_data).to_response()
    except Exception as e:
        logger.exception("Disconnect failed: %s", str(e), exc_info=True)
        # Rollback the session in case of an error
        await session.rollback()
        return ResponseWrapper.wrap(status=500, message="Internal server error").to_response()


@router.get(path="/check-active", summary="Check the connection.", response_model=ResponseWrapper[CheckConnectionResponse])
async def check_active(
    session: SessionDep,
    connected_extension_id: str,
    x_user_id: str = Header(None),
    x_user_role: str = Header(None),
):
    try:
        # Get the connected extension
        if x_user_role in ["admin", "super admin"]:
            statement = (
                select(ConnectedExtension).where(ConnectedExtension.id == connected_extension_id, ConnectedExtension.is_deleted.is_(False)).limit(1)
            )
        else:
            statement = (
                select(ConnectedExtension)
                .where(
                    ConnectedExtension.id == connected_extension_id,
                    ConnectedExtension.user_id == x_user_id,
                    ConnectedExtension.is_deleted.is_(False),
                )
                .limit(1)
            )

        result = await session.execute(statement)
        connected_extension = result.scalar_one_or_none()
        if connected_extension is None:
            return ResponseWrapper.wrap(status=404, message="Connected Extension not found").to_response()

        # Get the extension service
        extension_service_info = extension_service_manager.get_service(service_enum=str(connected_extension.extension_enum))
        if extension_service_info is None or extension_service_info.service_object is None:
            logger.warning("Extension service not found for enum: %s", connected_extension.extension_enum)
            return ResponseWrapper.wrap(status=404, message="Extension Info or Extension Service not found").to_response()

        extension_service = extension_service_info.service_object

        # Check the connection
        result = extension_service.check_connection(user_id=x_user_id)

        response_data = CheckConnectionResponse(is_connected=result)
        return ResponseWrapper.wrap(status=200, data=response_data).to_response()

    except Exception as e:
        logger.exception("Check connection failed: %s", str(e))
        return ResponseWrapper.wrap(status=500, message="Internal server error").to_response()
