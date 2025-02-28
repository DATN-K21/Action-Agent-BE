# Database Service Dependencies
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.session import get_db_session
from app.services.database.connected_app_service import ConnectedAppService
from app.services.database.thread_service import ThreadService
from app.services.database.user_service import UserService


def get_user_service(db: AsyncSession = Depends(get_db_session)):
    return UserService(db)


def get_thread_service(db: AsyncSession = Depends(get_db_session)):
    return ThreadService(db)


def get_connected_app_service(db: AsyncSession = Depends(get_db_session)):
    return ConnectedAppService(db)