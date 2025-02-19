from fastapi import APIRouter

from app.api.v1.callback import router as callback_router
from app.api.v1.chatbot import router as chatbot_router
from app.api.v1.general import router as general_router
from app.api.v1.gmail_agent import router as gmail_agent_router
from app.api.v1.multi_agent import router as multi_agent_router
from app.api.v1.rag import router as rag_router
from app.api.v1.search import router as search_router
from app.api.v1.thread import router as thread_router
from app.api.v1.user import router as user_router

router = APIRouter()

router.include_router(general_router, prefix="", tags=["General"])

router.include_router(chatbot_router, prefix="/chatbot", tags=["Chatbot"])

router.include_router(rag_router, prefix="/rag", tags=["RAG Bot"])

router.include_router(search_router, prefix="/search", tags=["Search Bot"])

router.include_router(multi_agent_router, prefix="/multi_agent", tags=["Multi agent"])

router.include_router(gmail_agent_router, prefix="/gmail", tags=["Gmail"])

router.include_router(callback_router, prefix="/callback", tags=["Callback"])

router.include_router(user_router, prefix="/user", tags=["User"])

router.include_router(thread_router, prefix="/thread", tags=["Thread"])
