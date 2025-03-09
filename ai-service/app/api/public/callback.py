from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse

from app.api.deps import ensure_user_id
from app.core import logging
from app.core.settings import env_settings
from app.services.database.connected_app_service import ConnectedAppService
from app.services.database.deps import get_connected_app_service

logger = logging.get_logger(__name__)

router = APIRouter(prefix="/callback", tags=["Callback"], include_in_schema=False)


@router.get("/extension/{user_id}", summary="Handle connection success.")
async def connection_success(
    user_id: str,
    request: Request,
    connected_app_service: ConnectedAppService = Depends(get_connected_app_service),
    _: bool = Depends(ensure_user_id),
):
    connection_status = request.query_params.get("status")
    connected_account_id = request.query_params.get("connectedAccountId")
    app_name = request.query_params.get("appName")
    url = env_settings.FRONTEND_REDIRECT_URL

    if connection_status is None or connected_account_id is None or app_name is None:
        full_url = f"{url}?success=false&message=missing%20parameters"
        return RedirectResponse(full_url)

    if connection_status != "success":
        full_url = f"{url}?success=false&message=connection%20failed%20or%20is%20still%20pending"
        return RedirectResponse(full_url)

    result = await connected_app_service.create_connected_app(
        user_id=user_id, app_name=app_name, connected_account_id=connected_account_id
    )

    if result:
        full_url = f"{url}?success=true&message=successfully%20connected"
        return RedirectResponse(full_url)

    full_url = f"{url}?success=false&message=failed%20to%20establish%20connection"
    return RedirectResponse(full_url)
