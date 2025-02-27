from fastapi import APIRouter, Depends

from app.core import logging
from app.schemas.base import ResponseWrapper
from app.schemas.connection import ActiveAccountResponse
from app.services.database.connected_app_service import ConnectedAppService
from app.services.deps import get_gmail_service, get_connected_app_service
from app.services.extensions.extension_service import ExtensionService
from app.services.extensions.gmail_service import GmailService

logger = logging.get_logger(__name__)

router = APIRouter()


@router.post("/active", tags=["Extension"],description="Initialize the connection.", response_model=ResponseWrapper[ActiveAccountResponse])
async def active(
    user_id: str,
    extension_service: ExtensionService = Depends(get_gmail_service),
):
    try:
        connection_request = extension_service.initialize_connection(str(user_id))

        if connection_request is None:
            response_data = ActiveAccountResponse(is_existed=True, redirect_url=None)
            return ResponseWrapper.wrap(status=200, data=response_data).to_response()

        response_data = ActiveAccountResponse(is_existed=False, redirect_url=connection_request.redirectUrl)
        return ResponseWrapper.wrap(status=200, data=response_data).to_response()

    except Exception as e:
        logger.error(f"[extension/active] Error in activating account: {str(e)}")
        return ResponseWrapper.wrap(status=500, message="Internal server error").to_response()


@router.post("/disconnect", tags=["Extension"], description="Disconnect the account.")
async def logout(
    user_id: str,
    connected_app_service: ConnectedAppService = Depends(get_connected_app_service),
    extension_service: GmailService = Depends(get_gmail_service),
):
    try:
        account_id = await connected_app_service.get_account_id(user_id, "gmail")
        if account_id is None:
            return ResponseWrapper.wrap(status=404, message="Account not found").to_response()
        response_data = extension_service.logout(account_id)
        return ResponseWrapper.wrap(status=200, data=response_data).to_response()
    except Exception as e:
        logger.error(f"[extension/logout] Error in logging out: {str(e)}")
        return ResponseWrapper.wrap(status=500, message="Internal server error").to_response()