from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse

from app.core import logging
from app.core.settings import env_settings
from app.services.database.connected_extension_service import ConnectedExtensionService, get_connected_extension_service

logger = logging.get_logger(__name__)

router = APIRouter(prefix="/callback", tags=["Callback"], include_in_schema=False)


@router.get("/extension/{user_id}", summary="Handle connection success.")
async def connection_success(
        user_id: str,
        request: Request,
        connected_extension_service: ConnectedExtensionService = Depends(get_connected_extension_service),
):
    url = env_settings.FRONTEND_REDIRECT_URL

    connection_status = request.query_params.get("status")
    connected_account_id = request.query_params.get("connectedAccountId")
    app_name = request.query_params.get("appName")

    if connection_status is None or connected_account_id is None or app_name is None:
        full_url = f"{url}?success=false&message=missing%20parameters"
        return RedirectResponse(full_url)

    if connection_status != "success":
        full_url = f"{url}?success=false&message=connection%20failed%20or%20is%20still%20pending"
        return RedirectResponse(full_url)

    result = await connected_extension_service.create_connected_extension(
        user_id=user_id, extension_name=app_name, connected_account_id=connected_account_id
    )

    if result:
        full_url = f"{url}?success=true&message=successfully%20connected"
        return RedirectResponse(full_url)

    full_url = f"{url}?success=false&message=failed%20to%20establish%20connection"
    return RedirectResponse(full_url)
