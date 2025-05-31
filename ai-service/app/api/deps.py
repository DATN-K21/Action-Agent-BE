from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import ensure_user_id
from app.core.db_session import get_db_session

SessionDep = Annotated[AsyncSession, Depends(get_db_session)]
IdentityUser = Annotated[bool, Depends(ensure_user_id)]
