from sqlalchemy import text

from app.core import logging
from app.core.db_session import AsyncSessionLocal

logger = logging.get_logger(__name__)


async def decrease_user_credits(user_id: str, amount: int) -> None:
    """
    Decrease the user's credits by a specified amount.
    """
    try:
        async with AsyncSessionLocal() as session:
            sql = text("UPDATE users SET credits = credits - :amount WHERE id = :user_id")
            await session.execute(sql, {"amount": amount, "user_id": user_id})
            await session.commit()
    except Exception as e:
        logger.error(f"Error decreasing credits for user {user_id}: {e}")
        await session.rollback()
