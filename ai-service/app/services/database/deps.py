# Database Service Dependencies
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from functools import lru_cache


from app.core.session import get_db_session
from app.services.database.connected_app_service import ConnectedAppService
from app.services.database.thread_service import ThreadService
from app.services.database.user_service import UserService

@lru_cache()
def get_user_service(db: AsyncSession = Depends(get_db_session)):
    return UserService(db)

@lru_cache()
def get_thread_service(db: AsyncSession = Depends(get_db_session)):
    return ThreadService(db)

@lru_cache()
def get_connected_app_service(db: AsyncSession = Depends(get_db_session)):
    return ConnectedAppService(db)