from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db_session import get_db_session

SessionDep = Annotated[AsyncSession, Depends(get_db_session)]
