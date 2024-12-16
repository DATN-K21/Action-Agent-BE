from fastapi import APIRouter

from app.api.general import router as general_router
from app.api.chatbot import router as chatbot_router
from app.api.rag_bot import router as rag_bot_router
from app.api.search_bot import router as search_bot_router
from app.api.multi_agent import router as multi_agent_router
from app.api.gmail_agent import router as gmail_bot_router
from app.api.user import router as user_router
from app.api.thread import router as thread_router


router = APIRouter()

router.include_router(
    general_router,
    prefix="",
    tags=["General"]
)

router.include_router(
    chatbot_router,
    prefix="/chatbot",
    tags=["Chatbot"]
)

router.include_router(
    rag_bot_router,
    prefix="/rag",
    tags=["RAG Bot"]
)

router.include_router(
    search_bot_router,
    prefix="/search",
    tags=["Search Bot"]
)

router.include_router(
    multi_agent_router,
    prefix="/multi_agent",
    tags=["Multi agent"]
)

router.include_router(
    gmail_bot_router,
    prefix="/gmail",
    tags=["Gmail"]
)

router.include_router(
    user_router,
    prefix="/user",
    tags=["User"]
)

router.include_router(
    thread_router,
    prefix="/thread",
    tags=["Thread"]
)
