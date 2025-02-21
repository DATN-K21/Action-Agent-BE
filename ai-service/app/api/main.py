from fastapi import APIRouter

from app.api.routes import callback, chatbot, general, gmail_agent, multi_agent, rag, search, thread, user

router = APIRouter()

router.include_router(general.router, prefix="", tags=["General"])

router.include_router(chatbot.router, prefix="/chatbot", tags=["Chatbot"])

router.include_router(rag.router, prefix="/rag", tags=["RAG Bot"])

router.include_router(search.router, prefix="/search", tags=["Search Bot"])

router.include_router(multi_agent.router, prefix="/multi_agent", tags=["Multi agent"])

router.include_router(gmail_agent.router, prefix="/gmail", tags=["Gmail"])

router.include_router(callback.router, prefix="/callback", tags=["Callback"])

router.include_router(user.router, prefix="/user", tags=["User"])

router.include_router(thread.router, prefix="/thread", tags=["Thread"])
