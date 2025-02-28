from fastapi import APIRouter, Depends, Request
from starlette.responses import HTMLResponse

from app.core import logging
from app.services.database.connected_app_service import ConnectedAppService
from app.services.database.deps import get_connected_app_service

logger = logging.get_logger(__name__)

router = APIRouter()


@router.get("/extension/{user_id}", description="Handle connection success.")
async def connection_success(
    user_id: str,
    request: Request,
    connected_app_service: ConnectedAppService = Depends(get_connected_app_service),
):
    connection_status = request.query_params.get("status")
    connected_account_id = request.query_params.get("connectedAccountId")
    app_name = request.query_params.get("appName")

    if connection_status is None or connected_account_id is None or app_name is None:
        return HTMLResponse("Missing parameters.", status_code=400)

    if connection_status != "success":
        return HTMLResponse("Connection failed or is still pending.", status_code=400)

    result = await connected_app_service.create_connected_app(
        user_id = user_id,
        app_name= app_name,
        connected_account_id= connected_account_id
    )
    
    if result:
        return HTMLResponse("Connection successful!")
    return HTMLResponse("Error creating connection.", status_code=500)
