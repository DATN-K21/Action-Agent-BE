
from fastapi import Depends, Request
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.session import get_db_session
from app.memory.deps import get_checkpointer
from app.services.database.connected_app_service import ConnectedAppService
from app.services.database.thread_service import ThreadService
from app.services.database.user_service import UserService
from app.services.extensions.gmail_service import GmailService
from app.services.identity_service import IdentityService
from app.services.multi_agent.multi_agent_service import MultiAgentService


# Identity Dependencies
def get_identity_service(request: Request):
    return IdentityService(request)


# Database Service Dependencies
def get_user_service(db: AsyncSession = Depends(get_db_session)):
    return UserService(db)


def get_thread_service(db: AsyncSession = Depends(get_db_session)):
    return ThreadService(db)


def get_connected_app_service(db: AsyncSession = Depends(get_db_session)):
    return ConnectedAppService(db)


# AI Dependencies
def get_multi_agent_service(checkpointer: AsyncPostgresSaver = Depends(get_checkpointer)):
    return MultiAgentService(checkpointer)

def get_gmail_service():
    return GmailService()
