import logging
import traceback
from fastapi import APIRouter
from fastapi.responses import RedirectResponse
from starlette.responses import HTMLResponse
from starlette.requests import Request as StarletteRequest
from sse_starlette import EventSourceResponse

from app.models.request_models import GmailAgentRequest
from app.models.response_model import GmailAgentResponse, AnswerMessage
from app.services.gmail_service import GmailService
from app.utils.exceptions import ExecutingException


logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/auth/authorize", tags=["Gmail"], description="Ask permission to access Gmail API.")
async def authorize():
    """
    Step 1: Redirect user to Google's OAuth 2.0 server to get permission.
    """
    flow = GmailService.get_flow()
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt='consent'
    )
    return RedirectResponse(authorization_url)

@router.get("/auth/callback", tags=["Gmail"], description="Callback for Gmail API.")
async def callback(request: StarletteRequest):
    """
    Step 2: Handle Google's response and fetch tokens.
    """
    flow = GmailService.get_flow()

    flow.fetch_token(authorization_response=str(request.url))
    credentials = flow.credentials

    print("credentials", GmailService.credentials_to_dict(credentials))

    return HTMLResponse("Credentials stored successfully!")

#Todo: Implement database to storage tokens that contain the user's Gmail API permissions

@router.post("/sync", tags=["Gmail"], description="Sync Database: Gmail API permissions.")
async def sync_database(request: dict) -> None:
    """
    Sync Database: Gmail API permissions.
    """
    #Todo: Implement logic to sync database
    try:
        pass
    except Exception as e:
        logger.error("Error in execute gmail API", exc_info=e)
        raise

@router.get("/actions", tags=["Gmail"], description="Get Gmail actions.")
async def get_actions() -> dict:
    """
    Get Gmail actions.
    """
    return GmailService.get_supported_actions()

@router.post("/chat", tags=["Gmail"], description="Chat with Gmail.")
async def chat(request: GmailAgentRequest) -> GmailAgentResponse:
    try:
        response = await GmailService.execute_gmail_debug(
            user_id="",
            thread_id=request.tid,
            user_input=request.input,
            max_recursion=5
        )

        return GmailAgentResponse(
            status=200,
            message="",
            data=AnswerMessage(
                tid=request.tid,
                output=response
            )
        )
    except Exception as e:
        logger.error("Error in execute gmail API", exc_info=e)
        raise ExecutingException(
            status=500,
            thread_id=request.tid,
            output="Error in execute gmail API",
            detail=traceback.format_exc()
        )

@router.post("/stream", tags=["Gmail"], description="Chat with Gmail.")
async def stream(request: GmailAgentRequest):
    try:
        return EventSourceResponse(GmailService.stream_gmail(
            user_id="",
            thread_id=request.tid,
            user_input=request.input,
            max_recursion=5
        ))
    except Exception as e:
        logger.error("Error in execute gmail API", exc_info=e)
        raise ExecutingException(
            status=500,
            thread_id=request.tid,
            output="Error in execute gmail API",
            detail=traceback.format_exc()
        )